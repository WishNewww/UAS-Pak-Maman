"""
embeddings.py
=============
Embedding model wrapper for the Regulasi Meteorologi Chatbot.

Uses a LOCAL sentence-transformers model (no API key, no network call).
Model: paraphrase-multilingual-MiniLM-L12-v2
  - Supports Indonesian natively
  - 118 MB download on first run, cached locally after that
  - 384-dimensional vectors, fast CPU inference

The LLM (Gemini) still uses the Google API — only embeddings are local.

Author : Regulasi Meteorologi Chatbot
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import List

import tiktoken
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

from config import ChunkConfig

logger = logging.getLogger("meteorologi_chatbot.embeddings")

# ---------------------------------------------------------------------------
# Embedding model name — multilingual, supports Indonesian
# ---------------------------------------------------------------------------
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ---------------------------------------------------------------------------
# Token counter (used as length_function for the splitter)
# ---------------------------------------------------------------------------

_tokenizer = tiktoken.get_encoding("cl100k_base")


def token_length(text: str) -> int:
    """Return the number of tokens in *text* using cl100k_base encoding."""
    return len(_tokenizer.encode(text))


# ---------------------------------------------------------------------------
# Embeddings wrapper
# ---------------------------------------------------------------------------

class GeminiEmbeddings:
    """
    Local HuggingFace sentence-transformers embedding wrapper.

    Despite the class name (kept for compatibility), this uses a local
    multilingual model — no Google Embedding API is called.
    """

    def __init__(self) -> None:
        logger.info("Initialising local embedding model: %s", EMBEDDING_MODEL_NAME)
        self._embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Local embedding model loaded successfully.")

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        """Return the raw LangChain embeddings object."""
        return self._embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        return self._embeddings.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of document strings."""
        return self._embeddings.embed_documents(texts)


# ---------------------------------------------------------------------------
# Semantic chunker
# ---------------------------------------------------------------------------

def _build_splitter() -> RecursiveCharacterTextSplitter:
    """
    Build a RecursiveCharacterTextSplitter calibrated to 300–500 tokens
    with 20% overlap.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=ChunkConfig.CHUNK_SIZE,
        chunk_overlap=ChunkConfig.CHUNK_OVERLAP,
        length_function=token_length,
        separators=[
            "\n\n",
            "\n",
            ". ",
            ", ",
            " ",
            "",
        ],
        keep_separator=True,
        add_start_index=True,
    )


def chunk_documents(slide_contents: list) -> list[Document]:
    """
    Convert a list of SlideContent objects into LangChain Documents
    with rich metadata and a unique chunk_id.
    """
    splitter = _build_splitter()
    documents: list[Document] = []
    chunk_counter: int = 0

    for slide in slide_contents:
        raw_text = slide.to_text_block()
        if not raw_text.strip():
            logger.debug(
                "Skipping empty slide: %s slide %d",
                slide.filename,
                slide.slide_number,
            )
            continue

        base_meta = {
            "folder": slide.folder,
            "filename": slide.filename,
            "file_path": slide.file_path,
            "slide": slide.slide_number,
            "slide_title": slide.slide_title,
            "section": slide.section,
            "topic": slide.topic,
        }

        chunks = splitter.split_text(raw_text)

        for chunk_idx, chunk_text in enumerate(chunks):
            chunk_counter += 1
            meta = {
                **base_meta,
                "chunk_id": f"{slide.filename}__s{slide.slide_number}__c{chunk_idx}",
                "chunk_index": chunk_idx,
                "total_chunks_in_slide": len(chunks),
                "token_count": token_length(chunk_text),
            }
            documents.append(Document(page_content=chunk_text, metadata=meta))

    logger.info(
        "Chunking complete: %d slide(s) → %d chunk(s)",
        len(slide_contents),
        chunk_counter,
    )
    return documents


# ---------------------------------------------------------------------------
# Singleton accessor (lazy init, cached)
# ---------------------------------------------------------------------------

_embeddings_instance: GeminiEmbeddings | None = None


def get_embeddings() -> GeminiEmbeddings:
    """Return a cached GeminiEmbeddings instance (lazy singleton)."""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = GeminiEmbeddings()
    return _embeddings_instance
