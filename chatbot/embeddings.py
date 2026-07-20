"""
embeddings.py
=============
Embedding model wrapper for the Regulasi Meteorologi Chatbot.

Uses Google's text-embedding-004 model via the LangChain Google GenAI
integration. Provides:

- GeminiEmbeddings   : LangChain-compatible embeddings wrapper
- chunk_documents    : Semantic chunker that splits SlideContent into
                       LangChain Documents with full metadata
- token_length       : tiktoken-based token counter used by the chunker

Author : Regulasi Meteorologi Chatbot
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import List

import tiktoken
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import AppConfig, ChunkConfig, EmbeddingConfig, GeminiConfig

logger = logging.getLogger("meteorologi_chatbot.embeddings")


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
    Thin wrapper around LangChain's GoogleGenerativeAIEmbeddings.

    Exposes the underlying LangChain embeddings object so it can be passed
    directly to FAISS.from_documents() and FAISSVectorStore.
    """

    def __init__(self) -> None:
        logger.info(
            "Initialising embedding model: %s", EmbeddingConfig.MODEL
        )
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=EmbeddingConfig.MODEL,
            google_api_key=GeminiConfig.API_KEY,
            task_type="retrieval_document",
        )

    @property
    def embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Return the raw LangChain embeddings object."""
        return self._embeddings

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string (uses retrieval_query task type)."""
        query_embeddings = GoogleGenerativeAIEmbeddings(
            model=EmbeddingConfig.MODEL,
            google_api_key=GeminiConfig.API_KEY,
            task_type="retrieval_query",
        )
        return query_embeddings.embed_query(text)

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

    chunk_size  = ChunkConfig.CHUNK_SIZE  (default 400 tokens)
    chunk_overlap = ChunkConfig.CHUNK_OVERLAP (default 80 tokens ≈ 20%)
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=ChunkConfig.CHUNK_SIZE,
        chunk_overlap=ChunkConfig.CHUNK_OVERLAP,
        length_function=token_length,
        separators=[
            "\n\n",   # paragraph break
            "\n",     # line break
            "。",     # full-width period (rare, safety)
            ". ",     # sentence boundary
            ", ",     # clause boundary
            " ",      # word boundary
            "",       # character fallback
        ],
        keep_separator=True,
        add_start_index=True,
    )


def chunk_documents(slide_contents: list) -> list[Document]:
    """
    Convert a list of SlideContent objects into a flat list of
    LangChain Documents, each with rich metadata and a unique chunk_id.

    Parameters
    ----------
    slide_contents : list[SlideContent]
        Output of PowerPointParser.parse_all()

    Returns
    -------
    list[Document]
        Chunked LangChain Documents ready for embedding and FAISS ingestion.
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

        # Build base metadata from slide
        base_meta = {
            "folder": slide.folder,
            "filename": slide.filename,
            "file_path": slide.file_path,
            "slide": slide.slide_number,
            "slide_title": slide.slide_title,
            "section": slide.section,
            "topic": slide.topic,
        }

        # Split the slide text into chunks
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


# ---------------------------------------------------------------------------
# Quick-test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    from parser import PowerPointParser

    parser = PowerPointParser()
    try:
        slides = parser.parse_all()
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    docs = chunk_documents(slides)
    print(f"\n✅ Total chunks produced: {len(docs)}")

    # Preview first 2 chunks
    for doc in docs[:2]:
        print("\n" + "=" * 60)
        print(f"chunk_id   : {doc.metadata['chunk_id']}")
        print(f"filename   : {doc.metadata['filename']}")
        print(f"slide      : {doc.metadata['slide']}")
        print(f"tokens     : {doc.metadata['token_count']}")
        print(f"content    :\n{doc.page_content[:300]}")
