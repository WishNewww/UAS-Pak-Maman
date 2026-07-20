"""
app.py
======
Streamlit UI for the Regulasi Meteorologi Chatbot.

Features:
- Dark-themed chat interface with streaming responses
- Sidebar with document statistics, index builder, and example questions
- Conversation memory with clear-chat button
- Loading animations and typing indicator
- Responsive layout
- Error handling with user-friendly messages

Run:
    streamlit run app.py

Author : Regulasi Meteorologi Chatbot
Version: 1.0.0
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# Page config MUST be the very first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Regulasi Meteorologi Chatbot",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Regulasi Internasional Meteorologi — AI Chatbot v1.0.0",
    },
)

# Now safe to import project modules
from config import AppConfig
from utils import (
    answer_with_citation,
    append_assistant_message,
    append_user_message,
    format_error,
    format_file_list,
    get_example_questions,
    get_index_stats,
    history_for_rag,
    index_exists,
    init_chat_history,
    trim_history,
)

AppConfig.log.configure()
logger = logging.getLogger("meteorologi_chatbot.app")


# ===========================================================================
# Custom CSS — Dark Theme + Chat Bubbles
# ===========================================================================

CUSTOM_CSS = """
<style>
/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0e1117;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #58a6ff;
}

/* ── Chat container ── */
.chat-container {
    max-width: 860px;
    margin: 0 auto;
    padding-bottom: 120px;
}

/* ── Message bubbles ── */
.msg-user {
    background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%);
    color: #ffffff;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 16px;
    margin: 8px 0 8px 15%;
    box-shadow: 0 2px 8px rgba(31,111,235,0.3);
    line-height: 1.6;
}

.msg-assistant {
    background: #161b22;
    color: #e0e0e0;
    border: 1px solid #30363d;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 16px;
    margin: 8px 15% 8px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    line-height: 1.6;
}

.msg-timestamp {
    font-size: 0.72rem;
    color: #8b949e;
    margin-top: 4px;
    text-align: right;
}

.msg-sources {
    font-size: 0.82rem;
    color: #8b949e;
    border-top: 1px solid #30363d;
    margin-top: 8px;
    padding-top: 8px;
}

/* ── Typing indicator ── */
.typing-indicator {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 12px 16px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 15% 8px 0;
    width: fit-content;
}
.typing-dot {
    width: 8px;
    height: 8px;
    background: #58a6ff;
    border-radius: 50%;
    animation: typing-bounce 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
    30% { transform: translateY(-6px); opacity: 1; }
}

/* ── Stat cards ── */
.stat-card {
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    text-align: center;
}
.stat-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #58a6ff;
}
.stat-label {
    font-size: 0.78rem;
    color: #8b949e;
    margin-top: 2px;
}

/* ── Example question button ── */
.stButton > button {
    background: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 8px;
    text-align: left;
    font-size: 0.82rem;
    padding: 8px 12px;
    width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: #30363d;
    border-color: #58a6ff;
    color: #58a6ff;
}

/* ── Input box ── */
[data-testid="stChatInput"] textarea {
    background: #161b22 !important;
    color: #e0e0e0 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 2px rgba(88,166,255,0.2) !important;
}

/* ── Index status badge ── */
.badge-ok  { color: #3fb950; font-weight: 600; }
.badge-err { color: #f85149; font-weight: 600; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0e1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #58a6ff; }

/* ── Progress bar ── */
.stProgress > div > div {
    background: linear-gradient(90deg, #1f6feb, #388bfd) !important;
    border-radius: 4px;
}

/* ── Divider ── */
hr { border-color: #21262d; }

/* ── Welcome card ── */
.welcome-card {
    background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 24px 28px;
    margin: 20px 0;
    text-align: center;
}
.welcome-card h2 { color: #58a6ff; margin-bottom: 8px; }
.welcome-card p  { color: #8b949e; font-size: 0.95rem; }
</style>
"""


# ===========================================================================
# Session State Initialisation
# ===========================================================================

def _init_session() -> None:
    """Initialise all required session-state keys on first load."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = init_chat_history()
    if "rag_chain" not in st.session_state:
        st.session_state.rag_chain = None
    if "index_stats" not in st.session_state:
        st.session_state.index_stats = None
    if "example_clicked" not in st.session_state:
        st.session_state.example_clicked = None
    if "is_building" not in st.session_state:
        st.session_state.is_building = False


# ===========================================================================
# Lazy RAG chain loader
# ===========================================================================

@st.cache_resource(show_spinner=False)
def _load_rag_chain():
    """Load and cache the RAG chain (runs only once per session)."""
    from rag import get_rag_chain
    return get_rag_chain()


@st.cache_data(show_spinner=False, ttl=300)
def _load_index_stats() -> dict:
    """Cache index statistics for 5 minutes."""
    return get_index_stats()


# ===========================================================================
# Sidebar
# ===========================================================================

def _render_sidebar() -> None:
    with st.sidebar:
        # ── App header ────────────────────────────────────────────────
        st.markdown(
            f"<h2 style='color:#58a6ff;margin-bottom:0'>"
            f"{AppConfig.APP_ICON} {AppConfig.APP_NAME}</h2>"
            f"<p style='color:#8b949e;font-size:0.8rem;margin-top:4px'>"
            f"v{AppConfig.APP_VERSION}</p>",
            unsafe_allow_html=True,
        )
        st.divider()

        # ── Index status ──────────────────────────────────────────────
        st.markdown("### 📊 Statistik Dokumen")

        if index_exists():
            stats = _load_index_stats()
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(
                    f"<div class='stat-card'>"
                    f"<div class='stat-value'>{stats['total_files']}</div>"
                    f"<div class='stat-label'>File PPT</div></div>",
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    f"<div class='stat-card'>"
                    f"<div class='stat-value'>{stats['total_slides']}</div>"
                    f"<div class='stat-label'>Total Slide</div></div>",
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    f"<div class='stat-card'>"
                    f"<div class='stat-value'>{stats['total_chunks']}</div>"
                    f"<div class='stat-label'>Chunk</div></div>",
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"<p style='font-size:0.78rem;color:#8b949e;margin-top:6px'>"
                f"📁 Ukuran Index: <b>{stats['index_size_mb']} MB</b> &nbsp;|&nbsp; "
                f"🕒 Dibuat: <b>{stats['last_built']}</b></p>",
                unsafe_allow_html=True,
            )

            with st.expander("📄 Daftar File", expanded=False):
                st.markdown(
                    f"<pre style='font-size:0.75rem;color:#8b949e'>"
                    f"{format_file_list(stats['files'])}</pre>",
                    unsafe_allow_html=True,
                )

            st.markdown(
                "<span class='badge-ok'>✔ Index siap digunakan</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<span class='badge-err'>✘ Index belum dibuat</span>",
                unsafe_allow_html=True,
            )
            st.warning(
                "Index FAISS belum ditemukan. Klik tombol di bawah untuk "
                "membangun index dari file PowerPoint.",
                icon="⚠️",
            )

        st.divider()

        # ── Build / Rebuild index ─────────────────────────────────────
        st.markdown("### 🔧 Kelola Index")

        build_label = "🔄 Rebuild Index" if index_exists() else "⚡ Bangun Index"
        if st.button(build_label, use_container_width=True, type="primary"):
            _run_index_builder()

        if index_exists():
            if st.button("🗑️ Hapus Index", use_container_width=True):
                _delete_index()

        st.divider()

        # ── Example questions ─────────────────────────────────────────
        st.markdown("### 💡 Contoh Pertanyaan")
        questions = get_example_questions()
        for q in questions:
            if st.button(q, key=f"ex_{q[:30]}", use_container_width=True):
                st.session_state.example_clicked = q

        st.divider()

        # ── Clear chat ────────────────────────────────────────────────
        if st.button(
            "🗑️ Hapus Riwayat Chat",
            use_container_width=True,
            help="Hapus semua riwayat percakapan",
        ):
            st.session_state.chat_history = init_chat_history()
            st.success("Riwayat chat dihapus.", icon="✅")
            st.rerun()

        # ── Deployment info ───────────────────────────────────────────
        with st.expander("ℹ️ Info Deployment", expanded=False):
            st.markdown(
                """
**Lokal:**
Buat file `.env` dari `.env.example` lalu jalankan:
```
python build_index.py
streamlit run app.py
```

**Streamlit Cloud:**
1. Push repo ke GitHub
2. Di Streamlit Cloud → *Settings* → *Secrets*, tambahkan:
```toml
GEMINI_API_KEY = "..."
GEMINI_MODEL   = "gemini-2.5-flash-lite-preview-06-17"
```
3. Pastikan file `.pptx` ada di folder `data/` dalam repo
4. Klik *Reboot app* setelah update secrets
                """,
                unsafe_allow_html=False,
            )

        # ── Footer ────────────────────────────────────────────────────
        st.markdown(
            "<p style='font-size:0.72rem;color:#484f58;text-align:center;"
            "margin-top:20px'>"
            "Powered by Gemini · LangChain · FAISS · Streamlit</p>",
            unsafe_allow_html=True,
        )


# ===========================================================================
# Index builder (runs inside Streamlit with progress feedback)
# ===========================================================================

def _run_index_builder() -> None:
    """Run the FAISS index build pipeline with progress display."""
    st.session_state.is_building = True

    progress_placeholder = st.empty()

    with progress_placeholder.container():
        st.markdown("#### ⚙️ Membangun Index…")
        progress_bar = st.progress(0, text="Memulai…")
        status_text = st.empty()

        try:
            # Step 1: Parse
            status_text.markdown("📂 **Step 1/4** — Membaca file PowerPoint…")
            progress_bar.progress(10, text="Membaca file PowerPoint…")

            from parser import PowerPointParser
            parser = PowerPointParser()
            pptx_files = parser.discover_files()

            if not pptx_files:
                st.error("Tidak ada file .pptx ditemukan. Periksa DATA_DIR di .env")
                return

            all_slides = []
            for i, fp in enumerate(pptx_files):
                slides = parser.parse_file(fp)
                all_slides.extend(slides)
                pct = 10 + int(20 * (i + 1) / len(pptx_files))
                progress_bar.progress(
                    pct,
                    text=f"Parsing: {fp.name} ({i+1}/{len(pptx_files)})",
                )

            status_text.markdown(
                f"✔ {len(pptx_files)} file → {len(all_slides)} slide"
            )

            # Step 2: Chunk
            status_text.markdown("✂️ **Step 2/4** — Membuat chunk semantik…")
            progress_bar.progress(35, text="Membuat chunk semantik…")

            from embeddings import chunk_documents
            documents = chunk_documents(all_slides)
            progress_bar.progress(45, text=f"{len(documents)} chunk dibuat")
            status_text.markdown(f"✔ {len(documents)} chunk")

            # Step 3: Embed
            status_text.markdown(
                "🧠 **Step 3/4** — Membuat embedding (harap tunggu)…"
            )
            progress_bar.progress(50, text="Membuat embedding…")

            from embeddings import get_embeddings
            from langchain_community.vectorstores import FAISS

            emb_model = get_embeddings().embeddings
            BATCH_SIZE = 50
            batches = [
                documents[i : i + BATCH_SIZE]
                for i in range(0, len(documents), BATCH_SIZE)
            ]
            vectorstore = None
            for b_idx, batch in enumerate(batches):
                if vectorstore is None:
                    vectorstore = FAISS.from_documents(batch, emb_model)
                else:
                    vectorstore.add_documents(batch)
                pct = 50 + int(40 * (b_idx + 1) / len(batches))
                progress_bar.progress(
                    pct,
                    text=f"Embedding batch {b_idx+1}/{len(batches)}…",
                )

            # Step 4: Save
            status_text.markdown("💾 **Step 4/4** — Menyimpan index…")
            progress_bar.progress(92, text="Menyimpan index ke disk…")

            import pickle
            from config import FAISSConfig, PathConfig

            PathConfig.ensure_dirs()
            vectorstore.save_local(str(FAISSConfig.INDEX_PATH.parent))

            metadata = {
                "total_slides": len(all_slides),
                "total_chunks": len(documents),
                "total_files": len(pptx_files),
                "files": [str(fp) for fp in pptx_files],
            }
            with open(FAISSConfig.METADATA_PATH, "wb") as f:
                pickle.dump(metadata, f, protocol=pickle.HIGHEST_PROTOCOL)

            progress_bar.progress(100, text="✅ Selesai!")
            status_text.markdown(
                f"**✅ Index berhasil dibuat!** "
                f"{len(pptx_files)} file · {len(all_slides)} slide · "
                f"{len(documents)} chunk"
            )

            # Invalidate caches
            from retriever import reset_cache
            reset_cache()
            _load_index_stats.clear()
            st.session_state.rag_chain = None

            time.sleep(1.5)

        except Exception as exc:
            logger.error("Index build failed: %s", exc, exc_info=True)
            st.error(format_error(exc))
        finally:
            st.session_state.is_building = False

    progress_placeholder.empty()
    st.rerun()


def _delete_index() -> None:
    """Delete the FAISS index files."""
    import shutil
    from config import FAISSConfig

    try:
        for p in [
            FAISSConfig.INDEX_PATH.parent / "index.faiss",
            FAISSConfig.INDEX_PATH.parent / "index.pkl",
            FAISSConfig.METADATA_PATH,
        ]:
            if p.exists():
                p.unlink()

        from retriever import reset_cache
        reset_cache()
        _load_index_stats.clear()
        st.session_state.rag_chain = None
        st.success("Index dihapus.", icon="🗑️")
        st.rerun()
    except Exception as exc:
        st.error(format_error(exc))


# ===========================================================================
# Chat message renderers
# ===========================================================================

def _render_message(turn: dict) -> None:
    """Render a single chat message bubble."""
    role = turn["role"]
    content = turn["content"]
    timestamp = turn.get("timestamp", "")
    sources = turn.get("sources", "")

    if role == "user":
        st.markdown(
            f"<div class='msg-user'>{content}"
            f"<div class='msg-timestamp'>{timestamp} 👤</div></div>",
            unsafe_allow_html=True,
        )
    else:
        sources_html = (
            f"<div class='msg-sources'>{sources}</div>" if sources else ""
        )
        # Use st.markdown for assistant content to render markdown properly
        with st.container():
            st.markdown(
                f"<div class='msg-assistant'>",
                unsafe_allow_html=True,
            )
            st.markdown(content)
            if sources:
                st.markdown(sources)
            st.markdown(
                f"<div class='msg-timestamp'>🤖 {timestamp}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


def _render_chat_history() -> None:
    """Render all messages in the current chat history."""
    history = st.session_state.chat_history

    if not history:
        _render_welcome_card()
        return

    for turn in history:
        with st.chat_message(
            turn["role"],
            avatar="👤" if turn["role"] == "user" else "🌤️",
        ):
            st.markdown(turn["content"])
            if turn["role"] == "assistant" and turn.get("sources"):
                st.markdown(turn["sources"])


def _render_welcome_card() -> None:
    """Render the welcome card shown when no messages exist yet."""
    st.markdown(
        """
        <div class='welcome-card'>
            <h2>🌤️ Selamat Datang!</h2>
            <p>Saya adalah asisten AI untuk materi <b>Regulasi Internasional Meteorologi</b>.</p>
            <p>Tanyakan apa saja tentang materi kuliah yang tersedia — saya akan menjawab
            berdasarkan slide yang telah diunggah.</p>
            <br>
            <p style='color:#484f58;font-size:0.82rem'>
                💡 Pilih contoh pertanyaan dari sidebar, atau ketik pertanyaan Anda sendiri.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# Streaming answer renderer
# ===========================================================================

def _stream_answer(question: str) -> None:
    """
    Stream the RAG chain's answer token by token into the chat interface.
    Appends the final answer + citation to session history.
    """
    chain = _load_rag_chain()

    with st.chat_message("assistant", avatar="🌤️"):
        # Typing indicator
        typing_placeholder = st.empty()
        typing_placeholder.markdown(
            "<div class='typing-indicator'>"
            "<div class='typing-dot'></div>"
            "<div class='typing-dot'></div>"
            "<div class='typing-dot'></div>"
            "</div>",
            unsafe_allow_html=True,
        )

        answer_tokens: list[str] = []
        final_meta: dict = {}
        answer_placeholder = st.empty()

        history = history_for_rag(
            trim_history(st.session_state.chat_history)
        )

        try:
            for chunk in chain.stream_ask(question, chat_history=history):
                if isinstance(chunk, dict) and chunk.get("__done__"):
                    final_meta = chunk
                    break
                if isinstance(chunk, str):
                    answer_tokens.append(chunk)
                    # Update live display
                    typing_placeholder.empty()
                    answer_placeholder.markdown("".join(answer_tokens))

        except Exception as exc:
            logger.error("Streaming error: %s", exc, exc_info=True)
            typing_placeholder.empty()
            error_msg = format_error(exc)
            answer_placeholder.markdown(error_msg)
            append_assistant_message(
                st.session_state.chat_history, error_msg
            )
            return

        typing_placeholder.empty()
        full_answer = "".join(answer_tokens)
        sources = final_meta.get("sources", "")

        # Re-render cleanly (remove streaming artefacts)
        answer_placeholder.empty()
        st.markdown(full_answer)
        if sources:
            st.markdown(sources)

    # Persist to session state
    append_assistant_message(
        st.session_state.chat_history,
        full_answer,
        sources=sources,
    )


# ===========================================================================
# Main app
# ===========================================================================

def main() -> None:
    _init_session()

    # Inject CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Sidebar
    _render_sidebar()

    # ── Main chat area ────────────────────────────────────────────────
    st.markdown(
        f"<h1 style='color:#58a6ff;margin-bottom:0'>"
        f"{AppConfig.APP_ICON} {AppConfig.APP_NAME}</h1>"
        f"<p style='color:#8b949e;font-size:0.88rem;margin-top:2px'>"
        f"Tanyakan apa saja tentang materi Regulasi Internasional Meteorologi</p>",
        unsafe_allow_html=True,
    )

    # Index not ready warning
    if not index_exists():
        st.warning(
            "⚠️ Index belum dibuat. Buka sidebar dan klik **Bangun Index** "
            "untuk memulai.",
            icon="⚠️",
        )

    st.divider()

    # Chat history
    chat_container = st.container()
    with chat_container:
        _render_chat_history()

    # ── Input handling ────────────────────────────────────────────────
    # Handle example question click from sidebar
    if st.session_state.example_clicked:
        question = st.session_state.example_clicked
        st.session_state.example_clicked = None
        _handle_question(question)

    # Chat input box (pinned at bottom by Streamlit)
    if prompt := st.chat_input(
        "Ketik pertanyaan Anda tentang materi meteorologi…",
        disabled=not index_exists(),
    ):
        _handle_question(prompt)


def _handle_question(question: str) -> None:
    """Process a user question: display it, stream answer, update history."""
    question = question.strip()
    if not question:
        return

    if not index_exists():
        st.error(
            "Index belum dibuat. Silakan bangun index terlebih dahulu "
            "melalui sidebar.",
            icon="❌",
        )
        return

    # Show user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(question)

    # Record in history
    append_user_message(st.session_state.chat_history, question)

    # Stream answer
    _stream_answer(question)


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    main()
