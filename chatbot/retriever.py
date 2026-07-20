"""
retriever.py
============
Retrieval layer for the Regulasi Meteorologi Chatbot.

Responsibilities:
- Load the persisted FAISS index from disk (with caching)
- Perform similarity search with score threshold filtering
- Merge chunks that discuss the same topic/slide
- Return retrieved Documents with source metadata

Author : Regulasi Meteorologi Chatbot
Version: 1.0.0
"""

from __future__ import annotations

import logging
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Optional

from langchain.schema import Document
from langchain_community.vectorstores import FAISS

from config import AppConfig, FAISSConfig, RetrieverConfig
from embeddings import get_embeddings

logger = logging.getLogger("meteorologi_chatbot.retriever")


# ---------------------------------------------------------------------------
# Index loader (cached singleton)
# ---------------------------------------------------------------------------

_vectorstore_cache: Optional[FAISS] = None
_metadata_cache: Optional[dict] = None


def _load_vectorstore() -> FAISS:
    """Load (or return cached) FAISS vectorstore from disk."""
    global _vectorstore_cache

    if _vectorstore_cache is not None:
        return _vectorstore_cache

    if not FAISSConfig.index_exists():
        raise FileNotFoundError(
            "FAISS index not found. Please run: python build_index.py\n"
            f"Expected index at: {FAISSConfig.INDEX_PATH.parent}"
        )

    logger.info("Loading FAISS index from: %s", FAISSConfig.INDEX_PATH.parent)
    emb_model = get_embeddings().embeddings

    _vectorstore_cache = FAISS.load_local(
        folder_path=str(FAISSConfig.INDEX_PATH.parent),
        embeddings=emb_model,
        allow_dangerous_deserialization=True,
    )
    logger.info("FAISS index loaded successfully.")
    return _vectorstore_cache


def _load_metadata() -> dict:
    """Load (or return cached) metadata dictionary from disk."""
    global _metadata_cache

    if _metadata_cache is not None:
        return _metadata_cache

    if not FAISSConfig.METADATA_PATH.exists():
        return {}

    with open(FAISSConfig.METADATA_PATH, "rb") as f:
        _metadata_cache = pickle.load(f)

    logger.info(
        "Metadata loaded: %d chunks across %d files.",
        _metadata_cache.get("total_chunks", 0),
        _metadata_cache.get("total_files", 0),
    )
    return _metadata_cache


def reset_cache() -> None:
    """Force reload of FAISS index and metadata on next access."""
    global _vectorstore_cache, _metadata_cache
    _vectorstore_cache = None
    _metadata_cache = None
    logger.info("Retriever cache cleared.")


# ---------------------------------------------------------------------------
# Context merger
# ---------------------------------------------------------------------------

def _merge_context(documents: list[Document]) -> list[Document]:
    """
    If multiple chunks come from the same slide, merge them into a single
    Document to provide more coherent context to the LLM.

    Merging key: (filename, slide_number)
    """
    from collections import OrderedDict

    groups: OrderedDict[tuple, list[Document]] = OrderedDict()

    for doc in documents:
        key = (doc.metadata.get("filename", ""), doc.metadata.get("slide", 0))
        groups.setdefault(key, []).append(doc)

    merged: list[Document] = []
    for (filename, slide_num), docs in groups.items():
        if len(docs) == 1:
            merged.append(docs[0])
        else:
            # Combine text, keep metadata from first chunk
            combined_text = "\n".join(d.page_content for d in docs)
            combined_meta = docs[0].metadata.copy()
            combined_meta["chunk_id"] = f"{filename}__s{slide_num}__merged"
            combined_meta["merged_chunks"] = len(docs)
            merged.append(
                Document(page_content=combined_text, metadata=combined_meta)
            )
            logger.debug(
                "Merged %d chunks from %s slide %d",
                len(docs),
                filename,
                slide_num,
            )

    return merged


# ---------------------------------------------------------------------------
# Public retrieval API
# ---------------------------------------------------------------------------

class MeteorologiRetriever:
    """
    Wraps FAISS similarity search with score-threshold filtering and
    context merging.
    """

    def __init__(
        self,
        top_k: int = RetrieverConfig.TOP_K,
        score_threshold: float = RetrieverConfig.SCORE_THRESHOLD,
    ) -> None:
        self.top_k = top_k
        self.score_threshold = score_threshold
        self._vs: Optional[FAISS] = None

    def _get_vectorstore(self) -> FAISS:
        if self._vs is None:
            self._vs = _load_vectorstore()
        return self._vs

    def retrieve(self, query: str) -> list[Document]:
        """
        Retrieve the most relevant Document chunks for *query*.

        Steps:
        1. similarity_search_with_score (top_k * 2 candidates)
        2. Filter by score_threshold (FAISS score = L2 distance → lower is better
           but LangChain normalises to cosine similarity 0–1 with FAISS-IP)
        3. Keep top_k results
        4. Merge chunks from same slide
        5. Return final list

        Returns
        -------
        list[Document]
            Relevant documents with metadata, or empty list if none qualify.
        """
        vs = self._get_vectorstore()

        # Fetch more candidates before threshold filtering
        candidates_k = max(self.top_k * 3, 15)

        try:
            results_with_scores = vs.similarity_search_with_relevance_scores(
                query=query,
                k=candidates_k,
            )
        except Exception as exc:
            logger.error("FAISS search error: %s", exc)
            return []

        # Filter by relevance score threshold
        filtered = [
            doc
            for doc, score in results_with_scores
            if score >= self.score_threshold
        ]

        if not filtered:
            logger.info(
                "No results above threshold %.2f for query: '%s'",
                self.score_threshold,
                query[:80],
            )
            # Fallback: return top-k regardless of threshold so the LLM
            # can at least say "tidak ditemukan" with context awareness
            filtered = [doc for doc, _ in results_with_scores[: self.top_k]]

        # Limit to top_k before merging
        filtered = filtered[: self.top_k]

        # Merge same-slide chunks
        merged = _merge_context(filtered)

        logger.info(
            "Retrieved %d doc(s) → merged to %d context block(s) for query: '%s'",
            len(filtered),
            len(merged),
            query[:80],
        )
        return merged

    def get_index_stats(self) -> dict:
        """Return basic statistics about the loaded index."""
        meta = _load_metadata()
        return {
            "total_files": meta.get("total_files", 0),
            "total_slides": meta.get("total_slides", 0),
            "total_chunks": meta.get("total_chunks", 0),
            "index_path": str(FAISSConfig.INDEX_PATH.parent),
        }

    def format_sources(self, documents: list[Document]) -> str:
        """
        Format a human-readable source citation block from retrieved docs.

        Example output:
            Sumber:
            • Materi 09 — Slide 3 (Regulasi Internasional Met 09_M8C_250526.pptx)
            • Materi 10 — Slide 7 (Regulasi Internasional Met 10_M8C_080626.pptx)
        """
        if not documents:
            return ""

        seen: set[str] = set()
        lines: list[str] = ["**Sumber:**"]

        for doc in documents:
            meta = doc.metadata
            topic = meta.get("topic", "Materi")
            slide = meta.get("slide", "?")
            filename = meta.get("filename", "")
            slide_title = meta.get("slide_title", "")

            key = f"{filename}__s{slide}"
            if key in seen:
                continue
            seen.add(key)

            title_part = f" — *{slide_title}*" if slide_title else ""
            lines.append(f"• {topic} — Slide {slide}{title_part} ({filename})")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_retriever_instance: Optional[MeteorologiRetriever] = None


def get_retriever() -> MeteorologiRetriever:
    """Return a cached MeteorologiRetriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = MeteorologiRetriever()
    return _retriever_instance


# ---------------------------------------------------------------------------
# Quick-test entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    retriever = MeteorologiRetriever()

    try:
        stats = retriever.get_index_stats()
        print("\n📊 Index Stats:")
        for k, v in stats.items():
            print(f"   {k}: {v}")
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    query = "Apa itu regulasi internasional meteorologi?"
    print(f"\n🔍 Query: {query}")
    docs = retriever.retrieve(query)

    print(f"\n📄 Retrieved {len(docs)} document(s):")
    for i, doc in enumerate(docs, 1):
        print(f"\n  [{i}] {doc.metadata.get('filename')} | Slide {doc.metadata.get('slide')}")
        print(f"      {doc.page_content[:200]}…")

    print(f"\n{retriever.format_sources(docs)}")
