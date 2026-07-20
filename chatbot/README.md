# 🌤️ Regulasi Internasional Meteorologi — AI Chatbot

Intelligent RAG-based chatbot for answering questions from Indonesian Meteorology
learning materials. Built with **Google Gemini 2.5 Flash-Lite**, **LangChain**,
**FAISS**, and **Streamlit**.

---

## ✨ Features

- 📂 Recursively parses all `.pptx` files (titles, bullets, tables, notes, sections)
- 🧠 Semantic chunking (300–500 tokens, 20% overlap) with tiktoken
- 🔍 FAISS similarity search with score-threshold filtering (top-K = 5)
- 💬 Streaming answers in Indonesian with slide citations
- 🗂️ Short-term conversation memory with follow-up question support
- 🎨 Dark-themed Streamlit UI with sidebar statistics
- ☁️ One-click deploy to Streamlit Community Cloud via GitHub

---

## 🗂️ Project Structure

```
chatbot/
│
├── app.py                        # Streamlit UI (entry point)
├── config.py                     # Config — reads st.secrets OR .env
├── rag.py                        # Core RAG chain
├── build_index.py                # CLI index builder
├── prompt.py                     # Prompt templates + citations
├── retriever.py                  # FAISS retriever
├── embeddings.py                 # Embedding wrapper + chunker
├── parser.py                     # PowerPoint parser
├── utils.py                      # Helpers + example questions
│
├── requirements.txt              # Pinned dependencies
├── .env.example                  # Local env variable template
├── .gitignore                    # Excludes secrets, index, venvs
├── README.md
├── PANDUAN_PENGGUNA.md           # Indonesian user guide
│
├── .streamlit/
│   ├── config.toml               # Dark theme + server settings
│   └── secrets.toml.example      # Streamlit secrets template
│
├── data/                         # ← place .pptx files here
├── faiss/                        # Auto-generated FAISS index (gitignored)
├── assets/
└── logs/
```

---

## 📋 Requirements

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| LangChain | 0.3.25 |
| langchain-google-genai | 2.1.5 |
| google-generativeai | 0.8.5 |
| faiss-cpu | 1.11.0 |
| python-pptx | 1.0.2 |
| streamlit | 1.45.1 |
| tiktoken | 0.9.0 |

---

## 🚀 Option A — Run Locally

### 1. Clone your GitHub repository

```powershell
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set your values:

```env
GEMINI_API_KEY=***
GEMINI_MODEL=gemini-2.5-flash-lite-preview-06-17
DATA_DIR=d:/Regulasi Internasional Meteorologi/UAS
```

### 5. Build the FAISS index

```powershell
python build_index.py
```

Force rebuild (if index already exists):

```powershell
python build_index.py --force
```

### 6. Launch the chatbot

```powershell
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## ☁️ Option B — Deploy to Streamlit Community Cloud

### Step 1 — Prepare the GitHub repository

#### 1a. Initialise Git (first time only)

```powershell
git init
git add .
git commit -m "Initial commit: Regulasi Meteorologi Chatbot"
```

#### 1b. Create a new repo on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Name it e.g. `regulasi-meteorologi-chatbot`
3. Set visibility to **Private** (recommended — keeps your PPT files private)
4. Do **not** initialise with README (you already have one)
5. Click **Create repository**

#### 1c. Add remote and push

```powershell
git remote add origin https://github.com/<your-username>/regulasi-meteorologi-chatbot.git
git branch -M main
git push -u origin main
```

> **Important:** The `.gitignore` excludes `.env` and `faiss/` automatically.
> Your API key is never pushed to GitHub.

#### 1d. Add PPTX files to the repo

Because Streamlit Cloud has no persistent local storage, the `.pptx` files
**must be committed** to the repository inside the `data/` folder:

```powershell
# Copy your PPTX files into data/
Copy-Item "d:\Regulasi Internasional Meteorologi\UAS\*.pptx" "data\"

git add data/
git commit -m "Add PPTX learning materials"
git push
```

#### 1e. Commit the pre-built FAISS index

Build the index locally first, then commit it so Streamlit Cloud doesn't
need to rebuild on every cold start:

```powershell
python build_index.py

# The index files are gitignored by default — force-add them
git add -f faiss/index.faiss faiss/index.pkl faiss/metadata.pkl
git commit -m "Add pre-built FAISS index"
git push
```

> **Tip:** Whenever you update the PPTX files, rebuild locally and push
> the new index files.

---

### Step 2 — Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
2. Click **New app**
3. Fill in the form:

| Field | Value |
|-------|-------|
| Repository | `<your-username>/regulasi-meteorologi-chatbot` |
| Branch | `main` |
| Main file path | `app.py` |
| App URL | choose a custom slug (optional) |

4. Click **Deploy!**

---

### Step 3 — Add Secrets in Streamlit Cloud

> Secrets replace the `.env` file in the cloud environment.

1. In the Streamlit Cloud dashboard, find your app
2. Click **⋮ (three dots)** → **Settings** → **Secrets**
3. Paste the following (replace values as needed):

```toml
GEMINI_API_KEY            = ***
GEMINI_MODEL              = "gemini-2.5-flash-lite-preview-06-17"
GEMINI_TEMPERATURE        = "0.2"
GEMINI_MAX_OUTPUT_TOKENS  = "2048"
EMBEDDING_MODEL           = "models/text-embedding-004"
RETRIEVER_TOP_K           = "5"
RETRIEVER_SCORE_THRESHOLD = "0.75"
CHUNK_SIZE                = "400"
CHUNK_OVERLAP             = "80"
LOG_LEVEL                 = "INFO"
```

4. Click **Save** — the app reboots automatically

---

### Step 4 — Continuous Deployment (CD)

Every `git push` to the `main` branch triggers an automatic redeploy:

```powershell
# Edit a file, then:
git add .
git commit -m "Update: <description>"
git push
```

Streamlit Cloud detects the push and redeploys within ~1 minute.

To update PPTX content:
```powershell
# 1. Replace files in data/
# 2. Rebuild index locally
python build_index.py --force

# 3. Stage and push everything
git add data/ faiss/
git commit -m "Update materials and index"
git push
```

---

## ⚙️ Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | *(required)* | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash-lite-preview-06-17` | LLM model name |
| `GEMINI_TEMPERATURE` | `0.2` | LLM temperature |
| `GEMINI_MAX_OUTPUT_TOKENS` | `2048` | Max tokens in response |
| `EMBEDDING_MODEL` | `models/text-embedding-004` | Embedding model |
| `DATA_DIR` | `data/` | Path to PPTX files |
| `FAISS_INDEX_PATH` | `faiss/index.faiss` | FAISS index path |
| `FAISS_METADATA_PATH` | `faiss/metadata.pkl` | Metadata path |
| `RETRIEVER_TOP_K` | `5` | Retrieved chunks per query |
| `RETRIEVER_SCORE_THRESHOLD` | `0.75` | Min relevance score |
| `CHUNK_SIZE` | `400` | Chunk size in tokens |
| `CHUNK_OVERLAP` | `80` | Chunk overlap (~20%) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 🔄 Architecture

```
User Question
     │
     ▼
[Condense Question]  ← chat_history
     │
     ▼
[FAISS Retriever]    → top-5 chunks (score ≥ 0.75) → merged by slide
     │
     ▼
[Context Formatter]  → structured context with source headers
     │
     ▼
[Gemini 2.5 Flash-Lite]  ← Indonesian RAG system prompt
     │
     ▼
Streaming Answer + Citation (Materi XX — Slide YY)
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `GEMINI_API_KEY not set` | Add key to `.env` (local) or Streamlit Secrets (cloud) |
| `FAISS index not found` | Run `python build_index.py` |
| `No .pptx files found` | Check `DATA_DIR` or copy files into `data/` |
| API rate limit / quota | Reduce `BATCH_SIZE=20` in `build_index.py` |
| Irrelevant answers | Lower `RETRIEVER_SCORE_THRESHOLD` to `0.60` |
| Streamlit Cloud blank page | Check **Manage app → Logs** for the error |
| Index too large for GitHub | Use [Git LFS](https://git-lfs.com/) for `faiss/` files |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Google Gemini 2.5 Flash-Lite |
| Embeddings | Google text-embedding-004 |
| RAG Framework | LangChain 0.3.x |
| Vector Store | FAISS (CPU) |
| Document Parser | python-pptx |
| UI | Streamlit 1.45 |
| Tokenizer | tiktoken (cl100k_base) |
| Deployment | Streamlit Community Cloud + GitHub |

---

*Regulasi Internasional Meteorologi — AI Chatbot v1.0.0*
