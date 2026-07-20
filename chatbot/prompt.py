"""
prompt.py
=========
Prompt templates for the Regulasi Meteorologi Chatbot.

Contains:
- RAG_SYSTEM_PROMPT   : System-level instruction for the LLM
- RAG_HUMAN_TEMPLATE  : Human turn template with context + question injection
- build_rag_prompt()  : Assembles the final ChatPromptTemplate
- format_context()    : Renders retrieved Documents into a clean context block

Design goals:
- Strictly ground answers in retrieved context → minimise hallucination
- Cite slide sources in every answer
- Maintain an educational, professional tone in Indonesian
- Support conversational follow-up questions via chat history

Author : Regulasi Meteorologi Chatbot
Version: 1.0.0
"""

from __future__ import annotations

from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain.schema import Document

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

RAG_SYSTEM_PROMPT = """Kamu adalah asisten AI edukatif yang ahli dalam bidang Regulasi Internasional Meteorologi. \
Tugasmu adalah menjawab pertanyaan mahasiswa BERDASARKAN EKSKLUSIF dari konteks materi kuliah yang diberikan di bawah ini.

ATURAN KETAT:
1. HANYA gunakan informasi yang ada dalam konteks yang diberikan.
2. JANGAN pernah mengarang, berasumsi, atau menggunakan pengetahuan di luar konteks.
3. Jika informasi tidak ditemukan dalam konteks, jawab dengan tepat:
   "Maaf, informasi tersebut tidak ditemukan pada materi yang tersedia."
4. Setiap jawaban HARUS menyertakan sumber slide (Materi dan nomor Slide).
5. Gunakan bahasa Indonesia yang baik, jelas, dan bernada edukatif.
6. Susun jawaban secara terstruktur: ringkasan singkat → penjelasan detail → poin-poin penting (jika ada).
7. Pertahankan hierarki dan struktur dari materi asli (bullet points, penomoran, tabel).
8. Jawab pertanyaan lanjutan dengan mempertimbangkan konteks percakapan sebelumnya.

KONTEKS MATERI:
---------------------
{context}
---------------------

Ingat: Kamu HANYA boleh menjawab dari konteks di atas. Tidak ada pengecualian."""

# ---------------------------------------------------------------------------
# Human turn template
# ---------------------------------------------------------------------------

RAG_HUMAN_TEMPLATE = """{question}"""

# ---------------------------------------------------------------------------
# No-context fallback (when retrieval returns nothing)
# ---------------------------------------------------------------------------

NO_CONTEXT_RESPONSE = (
    "Maaf, informasi tersebut tidak ditemukan pada materi yang tersedia. "
    "Silakan coba pertanyaan lain yang berkaitan dengan materi Regulasi "
    "Internasional Meteorologi yang telah diunggah."
)

# ---------------------------------------------------------------------------
# Context formatter
# ---------------------------------------------------------------------------

def format_context(documents: list[Document]) -> str:
    """
    Render a list of retrieved Documents into a single context string
    to be injected into the RAG prompt.

    Each document block includes:
    - Source header (topic, slide, filename)
    - Slide title if available
    - Document text content
    """
    if not documents:
        return "Tidak ada konteks yang relevan ditemukan."

    blocks: list[str] = []

    for idx, doc in enumerate(documents, start=1):
        meta = doc.metadata
        topic = meta.get("topic", "Materi")
        slide_num = meta.get("slide", "?")
        filename = meta.get("filename", "")
        slide_title = meta.get("slide_title", "")
        section = meta.get("section", "")

        # Build source header
        header_parts = [f"[Sumber {idx}: {topic} | Slide {slide_num}]"]
        if filename:
            header_parts.append(f"File: {filename}")
        if slide_title:
            header_parts.append(f"Judul Slide: {slide_title}")
        if section:
            header_parts.append(f"Bagian: {section}")

        header = "\n".join(header_parts)
        block = f"{header}\n{doc.page_content.strip()}"
        blocks.append(block)

    return "\n\n" + ("\n\n" + "—" * 40 + "\n\n").join(blocks) + "\n"


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_rag_prompt() -> ChatPromptTemplate:
    """
    Build and return the full RAG ChatPromptTemplate.

    Structure:
        SystemMessage  : RAG_SYSTEM_PROMPT (with {context} placeholder)
        MessagesPlaceholder : chat_history (short-term memory)
        HumanMessage   : {question}
    """
    return ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(RAG_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template(RAG_HUMAN_TEMPLATE),
        ]
    )


def build_condense_question_prompt() -> ChatPromptTemplate:
    """
    A secondary prompt used to rephrase a follow-up question into a
    standalone question given the conversation history.

    This prevents unnecessary retrieval when the user asks "jelaskan lebih
    lanjut" without providing the original topic.
    """
    template = """Diberikan percakapan berikut dan pertanyaan lanjutan, \
ubah pertanyaan lanjutan menjadi pertanyaan mandiri yang lengkap dalam bahasa Indonesia. \
Pertahankan konteks topik dari percakapan sebelumnya.

Riwayat Percakapan:
{chat_history}

Pertanyaan Lanjutan: {question}

Pertanyaan Mandiri:"""

    return ChatPromptTemplate.from_template(template)


# ---------------------------------------------------------------------------
# Citation formatter
# ---------------------------------------------------------------------------

def format_citation(documents: list[Document]) -> str:
    """
    Build a formatted citation block appended to every answer.

    Example:
        ---
        📚 Sumber:
        • Materi 09 — Slide 3 (Regulasi Internasional Met 09_M8C_250526.pptx)
    """
    if not documents:
        return ""

    seen: set[str] = set()
    lines: list[str] = ["\n---\n📚 **Sumber:**"]

    for doc in documents:
        meta = doc.metadata
        topic = meta.get("topic", "Materi")
        slide = meta.get("slide", "?")
        filename = meta.get("filename", "")
        slide_title = meta.get("slide_title", "")

        key = f"{filename}__{slide}"
        if key in seen:
            continue
        seen.add(key)

        title_part = f" — *{slide_title}*" if slide_title else ""
        lines.append(f"• {topic} — Slide {slide}{title_part}  \n  `{filename}`")

    return "\n".join(lines)
