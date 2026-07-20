"""
utils.py
========
Utility functions for the Regulasi Meteorologi Chatbot.

Covers:
- Index status helpers
- Chat history management
- Text formatting helpers
- Streamlit session-state utilities
- Example question bank
- Error formatting

Author : Regulasi Meteorologi Chatbot
Version: 1.0.0
"""

from __future__ import annotations

import logging
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from config import AppConfig, FAISSConfig

logger = logging.getLogger("meteorologi_chatbot.utils")


# ---------------------------------------------------------------------------
# Index status
# ---------------------------------------------------------------------------

def index_exists() -> bool:
    """Return True when the FAISS index and metadata files are present."""
    return FAISSConfig.index_exists()


def get_index_stats() -> dict[str, Any]:
    """
    Load and return summary statistics from the persisted metadata file.

    Returns an empty dict (with zero-values) when the index does not exist.
    """
    defaults = {
        "total_files": 0,
        "total_slides": 0,
        "total_chunks": 0,
        "files": [],
        "index_path": str(FAISSConfig.INDEX_PATH.parent),
        "index_size_mb": 0.0,
        "last_built": "Belum dibuat",
    }

    if not FAISSConfig.METADATA_PATH.exists():
        return defaults

    try:
        with open(FAISSConfig.METADATA_PATH, "rb") as f:
            meta: dict = pickle.load(f)
    except Exception as exc:
        logger.warning("Could not load metadata: %s", exc)
        return defaults

    # Compute FAISS file size
    index_file = FAISSConfig.INDEX_PATH.parent / "index.faiss"
    size_mb = 0.0
    if index_file.exists():
        size_mb = index_file.stat().st_size / (1024 * 1024)

    # Last-built timestamp from file mtime
    last_built = "Tidak diketahui"
    if FAISSConfig.METADATA_PATH.exists():
        ts = FAISSConfig.METADATA_PATH.stat().st_mtime
        last_built = datetime.fromtimestamp(ts).strftime("%d %b %Y, %H:%M")

    return {
        "total_files": meta.get("total_files", 0),
        "total_slides": meta.get("total_slides", 0),
        "total_chunks": meta.get("total_chunks", 0),
        "files": meta.get("files", []),
        "index_path": str(FAISSConfig.INDEX_PATH.parent),
        "index_size_mb": round(size_mb, 2),
        "last_built": last_built,
    }


# ---------------------------------------------------------------------------
# Chat history management
# ---------------------------------------------------------------------------

def init_chat_history() -> list[dict]:
    """Return an empty chat history list."""
    return []


def append_user_message(history: list[dict], content: str) -> list[dict]:
    """Append a user message to chat history."""
    history.append({"role": "user", "content": content, "timestamp": _now()})
    return history


def append_assistant_message(history: list[dict], content: str, sources: str = "") -> list[dict]:
    """Append an assistant message (with optional citation) to chat history."""
    history.append({
        "role": "assistant",
        "content": content,
        "sources": sources,
        "timestamp": _now(),
    })
    return history


def trim_history(history: list[dict], max_turns: int | None = None) -> list[dict]:
    """
    Keep only the most recent *max_turns* conversation pairs.
    One turn = one user message + one assistant message.
    """
    if max_turns is None:
        max_turns = AppConfig.memory.MAX_HISTORY
    return history[-(max_turns * 2):]


def history_for_rag(history: list[dict]) -> list[dict]:
    """
    Return a cleaned version of chat history suitable for passing to RAGChain.
    Strips UI-only fields (timestamp, sources) leaving only role + content.
    """
    return [
        {"role": turn["role"], "content": turn["content"]}
        for turn in history
        if turn.get("content")
    ]


# ---------------------------------------------------------------------------
# Text & formatting helpers
# ---------------------------------------------------------------------------

def truncate(text: str, max_chars: int = 200, suffix: str = "…") -> str:
    """Truncate *text* to *max_chars*, appending *suffix* if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + suffix


def format_file_list(file_paths: list[str]) -> str:
    """Convert a list of absolute file paths to a display-friendly string."""
    lines = []
    for fp in file_paths:
        lines.append(f"• {Path(fp).name}")
    return "\n".join(lines) if lines else "Tidak ada file."


def answer_with_citation(answer: str, citation: str) -> str:
    """
    Concatenate the LLM answer and citation block into a single string
    for display.
    """
    if not citation:
        return answer
    return f"{answer}\n\n{citation}"


# ---------------------------------------------------------------------------
# Example questions (shown in the Streamlit sidebar)
# ---------------------------------------------------------------------------

EXAMPLE_QUESTIONS: list[str] = [
    "Apa itu regulasi internasional meteorologi?",
    "Jelaskan peran WMO dalam regulasi meteorologi internasional.",
    "Apa yang dimaksud dengan ICAO Annex 3?",
    "Bagaimana prosedur penyebaran informasi cuaca untuk penerbangan?",
    "Apa itu SIGMET dan kapan diterbitkan?",
    "Jelaskan perbedaan antara METAR dan TAF.",
    "Apa fungsi VAAC dalam layanan informasi penerbangan?",
    "Bagaimana regulasi IMO terkait layanan meteorologi maritim?",
    "Apa yang dimaksud dengan GCOS dan apa tujuannya?",
    "Jelaskan tentang sistem peringatan dini bencana hidrometeorologi.",
]


def get_example_questions() -> list[str]:
    """Return the full list of example questions."""
    return EXAMPLE_QUESTIONS


# ---------------------------------------------------------------------------
# Error message formatter
# ---------------------------------------------------------------------------

def format_error(exc: Exception) -> str:
    """Return a user-friendly error message from an exception."""
    exc_type = type(exc).__name__
    return (
        f"⚠️ Terjadi kesalahan: **{exc_type}**\n\n"
        f"```\n{str(exc)}\n```\n\n"
        "Silakan periksa log untuk informasi lebih lanjut."
    )


# ---------------------------------------------------------------------------
# Timing helper
# ---------------------------------------------------------------------------

class Timer:
    """Simple context-manager stopwatch for performance logging."""

    def __init__(self, label: str = "") -> None:
        self.label = label
        self._start: float = 0.0
        self.elapsed: float = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_) -> None:
        self.elapsed = time.perf_counter() - self._start
        if self.label:
            logger.debug("%s: %.3fs", self.label, self.elapsed)

    def __str__(self) -> str:
        return f"{self.elapsed:.3f}s"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")
