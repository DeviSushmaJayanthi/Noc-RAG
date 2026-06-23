# NOC RAG Bot 🧠

A premium, enterprise-grade Retrieval-Augmented Generation (RAG) conversational assistant designed for Network Operations Center (NOC) documentation. Powered by **LangChain**, **Streamlit**, **FAISS** vector store, and **Gemini 3.5**.

---

## 📂 Code & Repository Structure

Here is the directory structure of the project:

```bash
noc-rag-bot/
├── .env                 # Local API credentials (IGNORED, never committed)
├── .env.example         # Template for environment configuration
├── .gitignore           # Specifies files ignored by Git tracking
├── README.md            # Project documentation & architecture overview
├── app.py               # Main Streamlit dashboard application (Branded UI)
├── chatbot.py           # CLI-based chatbot for quick terminal testing
├── ingest.py            # Local document parsing & FAISS indexing script
├── requirements.txt     # Python dependency list
│
├── docs/                # Directory containing PDF documentation
│   └── Final_NOC_POC_English_V1.pdf   # Primary NOC reference PDF
│
└── faiss_index/         # Local FAISS database store (IGNORED, built locally)
    ├── index.faiss
    └── index.pkl
```

### File Breakdown
* **`app.py`**: The core frontend dashboard. Integrates custom CSS styling, dynamic file uploading, background auto-ingestion, multi-session chat logging, dynamic timestamping of conversation titles, and AI-suggested follow-up questions.
* **`ingest.py`**: Reads PDF documents from `docs/`, splits them into text chunks, downloads and generates sentence-transformer embeddings, and serializes the local FAISS index database.
* **`chatbot.py`**: A lightweight CLI interface for executing RAG queries in the terminal.
* **`requirements.txt`**: Manages exact library versions to ensure environment consistency.
* **`.gitignore`**: Critically configured to block virtual environments (`.venv`), caching files (`__pycache__`), local database storage (`faiss_index/`), and credentials (`.env`).

---

## 🔒 Security Best Practices

To protect your API keys and tokens:
1. **Never commit `.env`**: The project includes a pre-configured `.gitignore` file that excludes the `.env` file from git staging.
2. **Use `.env.example`**: Keep `.env.example` updated with mock values to guide other developers on what environment variables are needed.

### Configuration Variables
* `GEMINI_API_KEY`: API credential for the ChatGoogleGenerativeAI model.
* `HUGGINGFACEHUB_API_TOKEN`: Used to generate document sentence embeddings.

---

## ✨ Features

1. **Ambient radial Glow & Glossy Glassmorphism**: Premium modern dark-theme visual aesthetics with glowing backdrops and inner highlights on cards.
2. **Auto-Ingestion Pipeline**: Drag-and-drop a PDF in the sidebar upload utility, and the app instantly chunks and embeds the document in the background, making it ready for query immediately.
3. **Conversational Multi-Sessions**: Support for starting multiple conversations, deleting sessions, and switching history.
4. **Time-Stamped Conversation Titles**: Chat session list items in the sidebar update from "New Chat" to show the question query text followed by the exact time the session was started (e.g. `What documents are ind... (07:33 PM)`).
5. **Interactive Suggestion Pills**: The AI uses context to recommend 3 follow-up questions below its answers. Clicking a suggested question instantly submits it.
6. **Detailed Citation Badges**: AI answers list the page numbers of the source documents retrieved from the database to guarantee fact-checking capability.

---

## ⚙️ Installation & Setup

### Prerequisites
* Python 3.10+
* Git

### 1. Clone the repository
```bash
git clone https://github.com/DeviSushmaJayanthi/Noc-RAG.git
cd Noc-RAG
```

### 2. Set up virtual environment
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in the root folder:
```ini
GEMINI_API_KEY="your-gemini-api-key-here"
HUGGINGFACEHUB_API_TOKEN="your-huggingface-token-here"
```

### 5. Ingest initial documents
Place your PDF files into the `docs/` folder, then run the parser:
```bash
python ingest.py
```

### 6. Run the application
```bash
python -m streamlit run app.py
```
Open `http://localhost:8501` in your browser.