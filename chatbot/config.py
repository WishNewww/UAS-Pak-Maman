"""
config.py
=========
Centralized configuration management for the Regulasi Meteorologi Chatbot.

Secret resolution order (first wins):
  1. Streamlit secrets  (st.secrets) — used when deployed on Streamlit Cloud
  2. Environment variables            — used with a local .env file
  3. Hardcoded defaults               — safe fallbacks for non-critical settings

This dual-source design means the same codebase runs identically both
locally (python-dotenv) and on Streamlit Community Cloud (st.secrets).

Author : Regulasi Meteorologi Chatbot
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env for local development (no-op when the file doesn't exist)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).parent.resolve()
load_dotenv(_PROJECT_ROOT / ".env", override=False)


# ---------------------------------------------------------------------------
# Secret resolver — checks st.secrets first, then os.environ
# ---------------------------------------------------------------------------

def _get_secret(key: str, default: str | None = None) -> str | None:
    """
    Return a configuration value from st.secrets (Streamlit Cloud) or
    os.environ (local .env), falling back to *default*.
    """
    # Try Streamlit secrets first (only available when running under Streamlit)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass  # Not running under Streamlit or secrets not configured

    # Fall back to environment variable
    value = os.getenv(key)
    if value is not None:
        return value

    return default


def _require_secret(key: str) -> str:
    """Return secret or raise a descriptive error if missing."""
    value = _get_secret(key)
    if not value:
        raise EnvironmentError(
            f"Required secret '{key}' is not set.\n"
            f"  • Local  : add it to your .env file\n"
            f"  • Cloud  : add it in Streamlit Cloud → Settings → Secrets"
        )
    return value


def _get_int(key: str, default: int) -> int:
    try:
        v = _get_secret(key, str(default))
        return int(v) if v else default
    except (ValueError, TypeError):
        return default


def _get_float(key: str, default: float) -> float:
    try:
        v = _get_secret(key, str(default))
        return float(v) if v else default
    except (ValueError, TypeError):
        return default


# ===========================================================================
# Google Gemini
# ===========================================================================
class GeminiConfig:
    API_KEY: str        = _require_secret("GEMINI_API_KEY")
    MODEL: str          = _get_secret("GEMINI_MODEL", "gemini-2.5-flash-lite-preview-06-17")
    TEMPERATURE: float  = _get_float("GEMINI_TEMPERATURE", 0.2)
    MAX_OUTPUT_TOKENS: int = _get_int("GEMINI_MAX_OUTPUT_TOKENS", 2048)


# ===========================================================================
# Embedding
# ===========================================================================
class EmbeddingConfig:
    MODEL: str = _get_secret("EMBEDDING_MODEL", "models/text-embedding-004")


# ===========================================================================
# FAISS Vector Store
# ===========================================================================
class FAISSConfig:
    # On Streamlit Cloud the working directory is the repo root, so
    # relative paths resolve correctly without any path manipulation.
    INDEX_PATH: Path = _PROJECT_ROOT / _get_secret(
        "FAISS_INDEX_PATH", "faiss/index.faiss"
    )
    METADATA_PATH: Path = _PROJECT_ROOT / _get_secret(
        "FAISS_METADATA_PATH", "faiss/metadata.pkl"
    )

    @classmethod
    def index_exists(cls) -> bool:
        return cls.INDEX_PATH.exists() and cls.METADATA_PATH.exists()


# ===========================================================================
# Document Source
# ===========================================================================
class DataConfig:
    # Default to a local `data/` subdirectory; override via DATA_DIR secret
    # On Streamlit Cloud the PPTX files must be committed to the repo under data/
    DATA_DIR: Path = Path(
        _get_secret("DATA_DIR", str(_PROJECT_ROOT / "data"))
    )
    SUPPORTED_EXTENSIONS: list[str] = [".pptx"]


# ===========================================================================
# Retrieval
# ===========================================================================
class RetrieverConfig:
    TOP_K: int             = _get_int("RETRIEVER_TOP_K", 5)
    SCORE_THRESHOLD: float = _get_float("RETRIEVER_SCORE_THRESHOLD", 0.75)


# ===========================================================================
# Chunking
# ===========================================================================
class ChunkConfig:
    CHUNK_SIZE: int    = _get_int("CHUNK_SIZE", 400)
    CHUNK_OVERLAP: int = _get_int("CHUNK_OVERLAP", 80)


# ===========================================================================
# Conversation Memory
# ===========================================================================
class MemoryConfig:
    MAX_HISTORY: int = 10


# ===========================================================================
# Logging
# ===========================================================================
class LogConfig:
    LEVEL: str  = _get_secret("LOG_LEVEL", "INFO")
    # On Streamlit Cloud the filesystem is ephemeral — log to stdout only
    FILE: Path  = _PROJECT_ROOT / _get_secret("LOG_FILE", "logs/chatbot.log")
    _IS_CLOUD: bool = bool(os.getenv("STREAMLIT_SHARING_MODE") or
                           os.getenv("IS_STREAMLIT_CLOUD"))

    @classmethod
    def configure(cls) -> logging.Logger:
        """Configure root logger. On Streamlit Cloud only stdout is used."""
        level = getattr(logging, cls.LEVEL.upper(), logging.INFO)
        handlers: list[logging.Handler] = [logging.StreamHandler()]

        if not cls._IS_CLOUD:
            cls.FILE.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(cls.FILE, encoding="utf-8"))

        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=handlers,
            force=True,
        )
        return logging.getLogger("meteorologi_chatbot")


# ===========================================================================
# Paths
# ===========================================================================
class PathConfig:
    ROOT:   Path = _PROJECT_ROOT
    DATA:   Path = DataConfig.DATA_DIR
    FAISS:  Path = _PROJECT_ROOT / "faiss"
    ASSETS: Path = _PROJECT_ROOT / "assets"
    LOGS:   Path = _PROJECT_ROOT / "logs"

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create all required directories if they don't exist."""
        for d in [cls.DATA, cls.FAISS, cls.ASSETS]:
            d.mkdir(parents=True, exist_ok=True)
        # Only create logs dir locally (ephemeral on Streamlit Cloud)
        if not LogConfig._IS_CLOUD:
            cls.LOGS.mkdir(parents=True, exist_ok=True)


# ===========================================================================
# App-level bundle (convenience import)
# ===========================================================================
class AppConfig:
    gemini    = GeminiConfig
    embedding = EmbeddingConfig
    faiss     = FAISSConfig
    data      = DataConfig
    retriever = RetrieverConfig
    chunk     = ChunkConfig
    memory    = MemoryConfig
    log       = LogConfig
    path      = PathConfig

    APP_NAME:    str = "Regulasi Internasional Meteorologi — AI Chatbot"
    APP_ICON:    str = "🌤️"
    APP_VERSION: str = "1.0.0"
