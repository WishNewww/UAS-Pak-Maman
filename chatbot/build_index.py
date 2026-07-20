"""
build_index.py
==============
FAISS index builder for the Regulasi Meteorologi Chatbot.

Workflow:
    1. Parse all .pptx files via PowerPointParser
    2. Chunk slides into LangChain Documents via chunk_documents()
    3. Generate embeddings via GeminiEmbeddings
    4. Build a FAISS index and persist:
         faiss/index.faiss
         faiss/metadata.pkl
    5. Print a summary table

Run:
    python build_index.py
    python build_index.py --force   # rebuild even if index already exists

Author : Regulasi Meteorologi Chatbot
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import logging
import pickle
import sys
import time
from pathlib import Path

from tqdm import tqdm

from config import AppConfig, FAISSConfig, PathConfig
from embeddings import chunk_documents, get_embeddings
from parser import PowerPointParser

logger = logging.getLogger("meteorologi_chatbot.build_index")


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------

def _print_stats(slides: list, documents: list) -> None:
    """Print a compact statistics table to stdout."""
    from collections import Counter

    file_counter: Counter = Counter(s.filename for s in slides)
    folder_counter: Counter = Counter(s.folder for s in slides)

    print("\n" + "=" * 60)
    print("  INDEX BUILD STATISTICS")
    print("=" * 60)
    print(f"  Total folders scanned : {len(folder_counter)}")
    print(f"  Total PPTX files      : {len(file_counter)}")
    print(f"  Total slides parsed   : {len(slides)}")
    print(f"  Total chunks created  : {len(documents)}")
    print()

    print("  Per-file breakdown:")
    for fname, slide_count in sorted(file_counter.items()):
        chunk_count = sum(
            1 for d in documents if d.metadata["filename"] == fname
        )
        print(f"    {fname:<55} {slide_count:>3} slides  {chunk_count:>4} chunks")

    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# FAISS persistence helpers
# ---------------------------------------------------------------------------

def _save_faiss(vectorstore, metadata: dict) -> None:
    """Persist the FAISS index and metadata dictionary to disk."""
    FAISSConfig.INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

    # LangChain FAISS: save_local writes index.faiss + index.pkl
    # We use a custom path scheme:
    #   faiss/index.faiss  ← raw FAISS binary
    #   faiss/metadata.pkl ← our enriched metadata dict
    vectorstore.save_local(str(FAISSConfig.INDEX_PATH.parent))

    with open(FAISSConfig.METADATA_PATH, "wb") as f:
        pickle.dump(metadata, f, protocol=pickle.HIGHEST_PROTOCOL)

    logger.info("FAISS index saved to: %s", FAISSConfig.INDEX_PATH.parent)
    logger.info("Metadata saved to   : %s", FAISSConfig.METADATA_PATH)


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_index(force: bool = False) -> None:
    """
    Full index-build pipeline.

    Parameters
    ----------
    force : bool
        If True, rebuild the index even when it already exists.
    """
    PathConfig.ensure_dirs()

    # ------------------------------------------------------------------
    # Guard: skip if index already exists and force=False
    # ------------------------------------------------------------------
    if FAISSConfig.index_exists() and not force:
        logger.info(
            "FAISS index already exists at '%s'. "
            "Use --force to rebuild.",
            FAISSConfig.INDEX_PATH.parent,
        )
        print(
            "⚠️  Index already exists. Run with --force to rebuild.\n"
            f"   Location: {FAISSConfig.INDEX_PATH.parent}"
        )
        return

    start_time = time.perf_counter()
    print("\n🔧 Starting index build pipeline…\n")

    # ------------------------------------------------------------------
    # Step 1: Parse PowerPoint files
    # ------------------------------------------------------------------
    print("📂 Step 1/4 — Parsing PowerPoint files…")
    parser = PowerPointParser()

    try:
        pptx_files = parser.discover_files()
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        print(f"\n❌ {exc}")
        sys.exit(1)

    if not pptx_files:
        print("❌ No .pptx files found. Check your DATA_DIR in .env")
        sys.exit(1)

    all_slides = []
    for fp in tqdm(pptx_files, desc="  Parsing files", unit="file"):
        slides = parser.parse_file(fp)
        all_slides.extend(slides)

    print(f"   ✔ {len(pptx_files)} file(s) parsed → {len(all_slides)} slides\n")

    # ------------------------------------------------------------------
    # Step 2: Chunk documents
    # ------------------------------------------------------------------
    print("✂️  Step 2/4 — Chunking slides into semantic chunks…")
    documents = chunk_documents(all_slides)
    print(f"   ✔ {len(documents)} chunks created\n")

    if not documents:
        print("❌ No chunks generated. Check your source files.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 3: Generate embeddings & build FAISS index
    # ------------------------------------------------------------------
    print("🧠 Step 3/4 — Generating embeddings (this may take a while)…")

    emb_wrapper = get_embeddings()
    emb_model = emb_wrapper.embeddings

    # Process in batches to avoid API rate limits and show progress
    BATCH_SIZE = 50
    from langchain_community.vectorstores import FAISS

    vectorstore = None
    batches = [
        documents[i : i + BATCH_SIZE]
        for i in range(0, len(documents), BATCH_SIZE)
    ]

    for batch in tqdm(batches, desc="  Embedding batches", unit="batch"):
        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, emb_model)
        else:
            vectorstore.add_documents(batch)

    print(f"   ✔ Embeddings generated and FAISS index built\n")

    # ------------------------------------------------------------------
    # Step 4: Persist index + metadata
    # ------------------------------------------------------------------
    print("💾 Step 4/4 — Saving index to disk…")

    # Build enriched metadata dictionary for fast lookup
    metadata: dict = {
        "total_slides": len(all_slides),
        "total_chunks": len(documents),
        "total_files": len(pptx_files),
        "files": [str(fp) for fp in pptx_files],
        "documents": [
            {
                "chunk_id": d.metadata["chunk_id"],
                "filename": d.metadata["filename"],
                "folder": d.metadata["folder"],
                "slide": d.metadata["slide"],
                "slide_title": d.metadata["slide_title"],
                "section": d.metadata["section"],
                "topic": d.metadata["topic"],
                "token_count": d.metadata["token_count"],
            }
            for d in documents
        ],
    }

    _save_faiss(vectorstore, metadata)
    print(f"   ✔ Index saved to: {FAISSConfig.INDEX_PATH.parent}\n")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    elapsed = time.perf_counter() - start_time
    _print_stats(all_slides, documents)
    print(f"⏱️  Total build time: {elapsed:.1f}s")
    print("✅ Index build complete! You can now run: streamlit run app.py\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    AppConfig.log.configure()

    parser_cli = argparse.ArgumentParser(
        description="Build FAISS vector index from Meteorologi PPTX files."
    )
    parser_cli.add_argument(
        "--force",
        action="store_true",
        help="Rebuild the index even if it already exists.",
    )
    args = parser_cli.parse_args()

    build_index(force=args.force)
