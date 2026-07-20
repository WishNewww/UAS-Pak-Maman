"""
rag.py
======
Core Retrieval-Augmented Generation chain for the Regulasi Meteorologi Chatbot.

Architecture:
    User question
        │
        ▼
    [Condense question] ← chat_history  (if follow-up question)
        │
        ▼
    [FAISS Retriever]   → top-K chunks with score filtering
        │
        ▼
    [Context formatter] → structured context string
        │
        ▼
    [Gemini LLM]        ← RAG system prompt + context + question
        │
        ▼
    Answer + Citation

Public API:
    RAGChain.ask(question, chat_history) → dict{answer, sources, documents}
    get_rag_chain()                       → cached RAGChain singleton

Author : Regulasi Meteorologi Chatbot
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Optional

from langchain.schema import AIMessage, BaseMessage, Document, HumanMessage
from langchain_groq import ChatGroq

from config import AppConfig, GeminiConfig, MemoryConfig
from prompt import (
    NO_CONTEXT_RESPONSE,
    build_condense_question_prompt,
    build_rag_prompt,
    format_citation,
    format_context,
)
from retriever import MeteorologiRetriever, get_retriever

logger = logging.getLogger("meteorologi_chatbot.rag")


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------

def _build_llm() -> ChatGroq:
    """Instantiate and return the Groq LLM (free, open-source models)."""
    logger.info("Initialising LLM: %s", GeminiConfig.MODEL)
    return ChatGroq(
        model=GeminiConfig.MODEL,
        api_key=GeminiConfig.API_KEY,
        temperature=GeminiConfig.TEMPERATURE,
        max_tokens=GeminiConfig.MAX_OUTPUT_TOKENS,
        streaming=True,
    )


# ---------------------------------------------------------------------------
# Conversation history helpers
# ---------------------------------------------------------------------------

def _build_history_messages(
    chat_history: list[dict],
) -> list[BaseMessage]:
    """
    Convert the app's chat_history list-of-dicts to LangChain message objects.

    Expected format of each dict:
        {"role": "user" | "assistant", "content": "..."}
    """
    messages: list[BaseMessage] = []
    # Keep only the last MAX_HISTORY turns to avoid token overflow
    recent = chat_history[-(MemoryConfig.MAX_HISTORY * 2):]
    for turn in recent:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages


def _should_condense(question: str, chat_history: list[dict]) -> bool:
    """
    Decide whether the question needs to be condensed into a standalone
    question using prior history.

    Returns True for follow-up cues like "jelaskan lebih lanjut", "maksudnya?",
    "contohnya?", "kenapa?", etc.
    """
    if not chat_history:
        return False

    follow_up_patterns = [
        "jelaskan lebih",
        "lebih detail",
        "contoh",
        "maksud",
        "kenapa",
        "mengapa",
        "bagaimana caranya",
        "apa bedanya",
        "lanjutkan",
        "teruskan",
        "selanjutnya",
        "itu apa",
        "apa itu",
    ]
    q_lower = question.lower().strip()
    return any(p in q_lower for p in follow_up_patterns) or len(q_lower.split()) <= 4


# ---------------------------------------------------------------------------
# RAG Chain
# ---------------------------------------------------------------------------

class RAGChain:
    """
    Orchestrates retrieval + generation for the chatbot.

    Usage:
        chain = RAGChain()
        result = chain.ask("Apa itu ICAO Annex 3?", chat_history=[])
        print(result["answer"])
        print(result["sources"])
    """

    def __init__(self) -> None:
        self._llm: Optional[ChatGroq] = None
        self._retriever: Optional[MeteorologiRetriever] = None
        self._rag_prompt = build_rag_prompt()
        self._condense_prompt = build_condense_question_prompt()

    # ------------------------------------------------------------------
    # Lazy initialisation (avoids slow startup in Streamlit)
    # ------------------------------------------------------------------

    @property
    def llm(self) -> ChatGroq:
        if self._llm is None:
            self._llm = _build_llm()
        return self._llm

    @property
    def retriever(self) -> MeteorologiRetriever:
        if self._retriever is None:
            self._retriever = get_retriever()
        return self._retriever

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ask(
        self,
        question: str,
        chat_history: list[dict] | None = None,
    ) -> dict:
        """
        Answer a question using RAG.

        Parameters
        ----------
        question : str
            The user's question in Indonesian.
        chat_history : list[dict]
            Previous turns: [{"role": "user"|"assistant", "content": "..."}]

        Returns
        -------
        dict with keys:
            answer    : str   — the LLM's answer
            sources   : str   — formatted citation block
            documents : list  — raw retrieved Document objects
            question  : str   — possibly condensed question used for retrieval
        """
        if chat_history is None:
            chat_history = []

        # -- Step 1: Optionally condense follow-up question ---------------
        retrieval_question = question
        if _should_condense(question, chat_history):
            retrieval_question = self._condense_question(question, chat_history)
            logger.info("Condensed question: '%s'", retrieval_question)

        # -- Step 2: Retrieve relevant context ----------------------------
        documents = self.retriever.retrieve(retrieval_question)

        # -- Step 3: Format context ---------------------------------------
        context_str = format_context(documents)

        # -- Step 4: Build LangChain messages and call LLM ----------------
        history_messages = _build_history_messages(chat_history)

        prompt_value = self._rag_prompt.format_prompt(
            context=context_str,
            chat_history=history_messages,
            question=question,
        )

        logger.debug("Sending prompt to LLM…")
        try:
            response = self.llm.invoke(prompt_value.to_messages())
            raw_answer: str = response.content
        except Exception as exc:
            logger.error("LLM invocation failed: %s", exc)
            raw_answer = (
                "Maaf, terjadi kesalahan saat memproses permintaan Anda. "
                "Silakan coba lagi."
            )
            documents = []

        # -- Step 5: Safety check — if no docs retrieved, override --------
        if not documents:
            final_answer = NO_CONTEXT_RESPONSE
            citation = ""
        else:
            final_answer = raw_answer
            citation = format_citation(documents)

        return {
            "answer": final_answer,
            "sources": citation,
            "documents": documents,
            "question": retrieval_question,
        }

    def stream_ask(
        self,
        question: str,
        chat_history: list[dict] | None = None,
    ):
        """
        Streaming version of ask().

        Yields str tokens as they arrive from the LLM, then yields a final
        dict sentinel {"__done__": True, "sources": ..., "documents": ...}.
        """
        if chat_history is None:
            chat_history = []

        retrieval_question = question
        if _should_condense(question, chat_history):
            retrieval_question = self._condense_question(question, chat_history)

        documents = self.retriever.retrieve(retrieval_question)

        if not documents:
            yield NO_CONTEXT_RESPONSE
            yield {"__done__": True, "sources": "", "documents": []}
            return

        context_str = format_context(documents)
        history_messages = _build_history_messages(chat_history)
        prompt_value = self._rag_prompt.format_prompt(
            context=context_str,
            chat_history=history_messages,
            question=question,
        )

        citation = format_citation(documents)

        try:
            for chunk in self.llm.stream(prompt_value.to_messages()):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
        except Exception as exc:
            logger.error("LLM streaming error: %s", exc, exc_info=True)
            yield f"Maaf, terjadi kesalahan LLM: {type(exc).__name__}: {str(exc)[:300]}"

        yield {"__done__": True, "sources": citation, "documents": documents}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _condense_question(
        self,
        question: str,
        chat_history: list[dict],
    ) -> str:
        """
        Use the LLM to rewrite a follow-up question as a standalone question.
        Falls back to the original question on error.
        """
        # Format history as a simple string for the condense prompt
        history_text = "\n".join(
            f"{'Pengguna' if t['role'] == 'user' else 'Asisten'}: {t['content']}"
            for t in chat_history[-(MemoryConfig.MAX_HISTORY * 2):]
        )

        try:
            prompt_value = self._condense_prompt.format_prompt(
                chat_history=history_text,
                question=question,
            )
            response = self.llm.invoke(prompt_value.to_messages())
            condensed = response.content.strip()
            return condensed if condensed else question
        except Exception as exc:
            logger.warning("Question condensation failed: %s", exc)
            return question


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_rag_chain_instance: Optional[RAGChain] = None


def get_rag_chain() -> RAGChain:
    """Return a cached RAGChain instance (lazy singleton)."""
    global _rag_chain_instance
    if _rag_chain_instance is None:
        _rag_chain_instance = RAGChain()
    return _rag_chain_instance


# ---------------------------------------------------------------------------
# Quick-test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    chain = get_rag_chain()

    questions = [
        "Apa itu regulasi internasional meteorologi?",
        "Jelaskan lebih detail tentang ICAO.",
    ]

    history: list[dict] = []

    for q in questions:
        print(f"\n{'='*60}")
        print(f"❓ Pertanyaan: {q}")
        result = chain.ask(q, chat_history=history)
        print(f"\n💬 Jawaban:\n{result['answer']}")
        print(f"\n{result['sources']}")

        # Update history
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": result["answer"]})
