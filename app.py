# -*- coding: utf-8 -*-
import sys
import types
import importlib

# Prevent PyTorch from loading and throwing DLL errors on Windows
# since we are using cloud-based endpoints and do not need it locally.
class MockModule(types.ModuleType):
    def __init__(self, name):
        super().__init__(name)
        self.__path__ = []
        self.__spec__ = importlib.__spec__
    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError(name)
        class Dummy:
            pass
        Dummy.__name__ = name
        return Dummy

sys.modules['torch'] = MockModule('torch')
for sub in ['nn', 'cuda', 'distributed', 'multiprocessing', 'autograd', 'optim']:
    sys.modules[f'torch.{sub}'] = MockModule(f'torch.{sub}')

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="NOC RAG Bot",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for user-entered keys if not already present
if "user_gemini_key" not in st.session_state:
    st.session_state.user_gemini_key = ""
if "user_hf_token" not in st.session_state:
    st.session_state.user_hf_token = ""


# Custom CSS for Premium Look & Feel (Modern dark mode, glowing elements, custom scrollbars, glassmorphism)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

/* Main layout overrides with top radial glow */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif;
    background: radial-gradient(circle at 50% -100px, #181d33 0%, #07080c 60%, #030406 100%) !important;
    color: #e2e8f0;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
    font-weight: 800;
}

/* Custom scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #030406;
}
::-webkit-scrollbar-thumb {
    background: #1b2030;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: #2b334d;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: #040508 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.03) !important;
}

/* Sidebar Title Header Styling */
.sidebar-header {
    padding: 20px 10px;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    margin-bottom: 24px;
}

/* Style the "+ New Chat" button (it is a primary button in the sidebar) */
section[data-testid="stSidebar"] div.stButton:first-of-type button {
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
    text-align: center !important;
    justify-content: center !important;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.25) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] div.stButton:first-of-type button:hover {
    background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%) !important;
    box-shadow: 0 6px 25px rgba(99, 102, 241, 0.45) !important;
    transform: translateY(-2px) !important;
}

/* Inactive Session item buttons (secondary button inside columns) */
section[data-testid="stSidebar"] div[data-testid="column"]:first-child button[kind="secondary"] {
    background-color: transparent !important;
    color: #8a99ad !important;
    border: 1px solid transparent !important;
    border-left: 3px solid transparent !important;
    border-radius: 6px !important;
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 8px 12px !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
section[data-testid="stSidebar"] div[data-testid="column"]:first-child button[kind="secondary"]:hover {
    background-color: rgba(255, 255, 255, 0.02) !important;
    color: #e2e8f0 !important;
}

/* Active Session item buttons (primary button inside columns) */
section[data-testid="stSidebar"] div[data-testid="column"]:first-child button[kind="primary"] {
    background-color: rgba(99, 102, 241, 0.07) !important;
    color: #ffffff !important;
    border: 1px solid rgba(99, 102, 241, 0.12) !important;
    border-left: 3px solid #6366f1 !important;
    border-radius: 6px !important;
    width: 100% !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 8px 12px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    box-shadow: inset 0 0 10px rgba(99, 102, 241, 0.05) !important;
    transition: all 0.2s ease !important;
}
section[data-testid="stSidebar"] div[data-testid="column"]:first-child button[kind="primary"]:hover {
    background-color: rgba(99, 102, 241, 0.1) !important;
    border-color: rgba(99, 102, 241, 0.22) !important;
}

/* Delete (trash) buttons in column 2 */
section[data-testid="stSidebar"] div[data-testid="column"]:last-child button {
    background: transparent !important;
    border: none !important;
    color: #4b5563 !important;
    text-align: center !important;
    justify-content: center !important;
    padding: 8px 0px !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] div[data-testid="column"]:last-child button:hover {
    color: #ef4444 !important;
    background: rgba(239, 68, 68, 0.08) !important;
    border-radius: 6px !important;
}

/* Document Item vault cards style */
.doc-vault-item {
    background: rgba(255, 255, 255, 0.01);
    border: 1px solid rgba(255, 255, 255, 0.02);
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: all 0.25s ease;
}
.doc-vault-item:hover {
    background: rgba(255, 255, 255, 0.02);
    border-color: rgba(56, 189, 248, 0.2);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transform: translateX(2px);
}

/* Glassmorphic Panel Container */
.glass-panel {
    background: rgba(13, 17, 28, 0.45);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 20px;
    padding: 30px;
    margin-bottom: 24px;
    box-shadow: 0 20px 50px 0 rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* Gradient Title */
.gradient-title {
    background: linear-gradient(135deg, #a855f7 0%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 0.1rem;
    letter-spacing: -0.5px;
    text-shadow: 0 0 50px rgba(168, 85, 247, 0.12);
}

.subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-bottom: 2.2rem;
    font-weight: 300;
}

/* Chat container and custom bubbles */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin-top: 10px;
    margin-bottom: 100px;
}

.chat-bubble {
    display: flex;
    gap: 15px;
    padding: 18px 24px;
    border-radius: 20px;
    max-width: 80%;
    line-height: 1.6;
    font-size: 0.98rem;
    animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    transition: all 0.25s ease;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}

.user-bubble {
    background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
    color: #ffffff;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2);
}
.user-bubble:hover {
    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.35);
}

.bot-bubble {
    background: rgba(18, 22, 36, 0.6);
    color: #f1f5f9;
    align-self: flex-start;
    border-bottom-left-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}
.bot-bubble:hover {
    border-color: rgba(255, 255, 255, 0.09);
    background: rgba(18, 22, 36, 0.7);
}

/* Avatar details */
.avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.9rem;
    flex-shrink: 0;
    font-family: 'Outfit', sans-serif;
}

.user-avatar {
    background-color: #ffffff;
    color: #4f46e5;
    box-shadow: 0 2px 10px rgba(255, 255, 255, 0.15);
}

.bot-avatar {
    background: linear-gradient(135deg, #a855f7 0%, #3b82f6 100%);
    color: #ffffff;
    box-shadow: 0 2px 10px rgba(168, 85, 247, 0.25);
}

/* Source metadata citation badges */
.source-badge {
    font-size: 0.75rem;
    background: rgba(56, 189, 248, 0.04);
    color: #38bdf8;
    padding: 5px 12px;
    border-radius: 8px;
    margin-right: 8px;
    margin-top: 10px;
    display: inline-block;
    border: 1px solid rgba(56, 189, 248, 0.15);
    transition: all 0.2s ease;
}
.source-badge:hover {
    background: rgba(56, 189, 248, 0.1);
    transform: scale(1.02);
    box-shadow: 0 2px 8px rgba(56, 189, 248, 0.2);
}

/* Status Indicator widget */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.05);
    background-color: rgba(255, 255, 255, 0.02);
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.status-active {
    background-color: #10b981;
    box-shadow: 0 0 10px #10b981;
    animation: statusPulse 2s infinite;
}

.status-inactive {
    background-color: #f59e0b;
    box-shadow: 0 0 10px #f59e0b;
    animation: statusPulse 2s infinite;
}

@keyframes statusPulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.2); opacity: 0.5; }
    100% { transform: scale(1); opacity: 1; }
}

/* Setup steps guide cards */
.step-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-top: 15px;
}

.step-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 12px;
    padding: 20px;
    transition: all 0.3s ease;
}

.step-card:hover {
    background: rgba(255, 255, 255, 0.03);
    border-color: rgba(99, 102, 241, 0.2);
    transform: translateY(-2px);
}

.step-num {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a855f7 0%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
    margin-bottom: 10px;
}

/* Main Area Column Layout & Suggestion Pills */
.stApp div[data-testid="stHorizontalBlock"] div.stButton > button {
    background: rgba(255, 255, 255, 0.03) !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 20px !important;
    padding: 8px 16px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    width: 100% !important;
    text-align: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}

.stApp div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
    background: rgba(99, 102, 241, 0.12) !important;
    border-color: rgba(99, 102, 241, 0.3) !important;
    color: #a855f7 !important;
    transform: translateY(-1.5px) !important;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15) !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------- ENVIRONMENT VARIABLES -----------------
# Keep track of keys defined in the environment (e.g. .env file)
env_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
env_hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")

# Fallback to session state if environment variables are not set
active_gemini_key = env_gemini_key or st.session_state.user_gemini_key
active_hf_token = env_hf_token or st.session_state.user_hf_token

if active_gemini_key:
    os.environ["GOOGLE_API_KEY"] = active_gemini_key
    os.environ["GEMINI_API_KEY"] = active_gemini_key

if active_hf_token:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = active_hf_token
    os.environ["HF_TOKEN"] = active_hf_token


# ----------------- CACHED RESOURCES -----------------
@st.cache_resource
def get_embeddings_model(hf_token):
    from langchain_huggingface import HuggingFaceEndpointEmbeddings
    return HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        huggingfacehub_api_token=hf_token
    )

@st.cache_resource
def load_vector_store(hf_token):
    if not hf_token:
        return None
    from langchain_community.vectorstores import FAISS
    db_path = "faiss_index"
    if os.path.exists(db_path):
        try:
            embeddings = get_embeddings_model(hf_token)
            return FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            st.sidebar.error(f"Error loading vector index: {e}")
            return None
    return None

# Ingestion trigger inside the UI
def trigger_ingestion(hf_token):
    if not hf_token:
        st.sidebar.error("HuggingFace Token is required for ingestion.")
        return False
        
    from langchain_community.document_loaders import PyPDFDirectoryLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    
    docs_dir = "docs"
    if not os.path.exists(docs_dir):
        st.sidebar.error(f"'{docs_dir}' directory does not exist.")
        return False
        
    pdfs = [f for f in os.listdir(docs_dir) if f.lower().endswith('.pdf')]
    if not pdfs:
        st.sidebar.error("No PDF files found in docs/")
        return False
        
    progress_bar = st.sidebar.progress(0.0)
    status = st.sidebar.empty()
    
    try:
        status.text("Loading PDFs...")
        progress_bar.progress(0.2)
        loader = PyPDFDirectoryLoader(docs_dir)
        documents = loader.load()
        
        status.text(f"Splitting {len(documents)} pages...")
        progress_bar.progress(0.5)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        
        status.text("Generating embeddings (cloud-based)...")
        progress_bar.progress(0.7)
        embeddings = get_embeddings_model(hf_token)
        
        status.text("Building FAISS index...")
        progress_bar.progress(0.9)
        vector_store = FAISS.from_documents(chunks, embeddings)
        vector_store.save_local("faiss_index")
        
        progress_bar.progress(1.0)
        status.success("FAISS Database created successfully!")
        
        # Reset resource cache
        load_vector_store.clear()
        return True
    except Exception as e:
        status.error(f"Ingestion failed: {e}")
        return False

# Build retrieval chain (not cached to dynamically adapt when database is rebuilt)
def get_rag_chain(hf_token, gemini_key):
    global vector_db
    if vector_db is None or not gemini_key or not hf_token:
        return None
        
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_classic.chains.combine_documents import create_stuff_documents_chain
    from langchain_classic.chains import create_retrieval_chain, create_history_aware_retriever
    
    # 1. Setup retriever
    retriever = vector_db.as_retriever(search_kwargs={"k": 4})
    
    # 2. Setup Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.2)
    
    # 3. Create query contextualization prompt
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    # Create history-aware retriever
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    
    # 4. Create prompt template for answering
    qa_system_prompt = (
        "You are an expert RAG chatbot. Answer the question based ONLY on the provided context. "
        "If you cannot find the answer in the provided context, state clearly that you cannot find the answer in the documents. "
        "Do not assume or extrapolate.\n\n"
        "Context:\n"
        "{context}"
    )
    
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    # 5. Combine prompt and LLM
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # 6. Combine history_aware_retriever and chain
    retrieval_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return retrieval_chain

def get_followup_suggestions(question, answer, gemini_key):
    if not gemini_key:
        return []
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.7)
        prompt = (
            f"Based on the following user question and assistant's response, suggest exactly 3 short, "
            f"context-relevant follow-up questions that the user might want to ask next. "
            f"Keep them conversational, interesting, and under 12 words each. "
            f"Format your response as a simple list with one question per line, starting with a bullet point like '- '."
            f"\n\nUser Question: {question}\nAssistant Response: {answer}"
        )
        response = llm.invoke(prompt)
        
        # Handle list-type or string-type response content in langchain-google-genai
        content = response.content
        if isinstance(content, list):
            content_text = ""
            for block in content:
                if isinstance(block, dict) and "text" in block:
                    content_text += block["text"]
                elif isinstance(block, str):
                    content_text += block
            content = content_text
            
        lines = content.strip().split('\n')
        suggestions = []
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('*') or (len(line) > 2 and line[0].isdigit() and line[1] in ['.', ')']):
                cleaned = line.lstrip('-*•0123456789. \t').strip()
                if cleaned:
                    suggestions.append(cleaned)
        return suggestions[:3]
    except Exception as e:
        print(f"Error generating follow-up suggestions: {e}")
        return []


# ----------------- SESSION STATE SETUP -----------------
import uuid

if "sessions" not in st.session_state:
    initial_sid = str(uuid.uuid4())
    st.session_state.sessions = {
        initial_sid: {
            "title": "New Chat",
            "chat_history": []
        }
    }
    st.session_state.current_session_id = initial_sid

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

current_sid = st.session_state.current_session_id
# Fallback if current_sid was deleted somehow
if current_sid not in st.session_state.sessions:
    current_sid = list(st.session_state.sessions.keys())[0]
    st.session_state.current_session_id = current_sid

current_chat = st.session_state.sessions[current_sid]
current_chat_history = current_chat["chat_history"]

# Database setup check
vector_db = load_vector_store(active_hf_token)

# ----------------- SIDEBAR -----------------
# ----------------- SIDEBAR -----------------
st.sidebar.markdown("""
<div class="sidebar-header">
    <span style='font-family: "Outfit", sans-serif; font-size: 1.6rem; font-weight: 800; background: linear-gradient(135deg, #a855f7 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🧠 NOC RAG Bot</span>
</div>
""", unsafe_allow_html=True)

# "+ New Chat" Button
if st.sidebar.button("➕ New Chat", use_container_width=True, type="primary"):
    new_sid = str(uuid.uuid4())
    st.session_state.sessions[new_sid] = {
        "title": "New Chat",
        "chat_history": []
    }
    st.session_state.current_session_id = new_sid
    st.session_state.pending_query = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 💬 Conversations")

# Render conversation sessions
for sid, sess in list(st.session_state.sessions.items()):
    is_active = (sid == st.session_state.current_session_id)
    label = f"💬 {sess['title']}"
    
    col1, col2 = st.sidebar.columns([0.82, 0.18])
    with col1:
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"sess_{sid}", use_container_width=True, type=btn_type):
            st.session_state.current_session_id = sid
            st.session_state.pending_query = None
            st.rerun()
    with col2:
        if st.button("🗑️", key=f"del_{sid}", use_container_width=True):
            del st.session_state.sessions[sid]
            if not st.session_state.sessions:
                new_sid = str(uuid.uuid4())
                st.session_state.sessions = {
                    new_sid: {
                        "title": "New Chat",
                        "chat_history": []
                    }
                }
                st.session_state.current_session_id = new_sid
            elif st.session_state.current_session_id == sid:
                st.session_state.current_session_id = list(st.session_state.sessions.keys())[0]
            st.session_state.pending_query = None
            st.rerun()

# Document Management section in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 📄 Document Upload")

uploaded_file = st.sidebar.file_uploader("Upload PDF Document", type=["pdf"], label_visibility="collapsed")
if uploaded_file is not None:
    docs_dir = "docs"
    os.makedirs(docs_dir, exist_ok=True)
    file_path = os.path.join(docs_dir, uploaded_file.name)
    if not os.path.exists(file_path):
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.sidebar.info(f"Indexing '{uploaded_file.name}'...")
        if trigger_ingestion(active_hf_token):
            st.sidebar.success("Document indexed successfully!")
            st.rerun()

# List of currently indexed files
if os.path.exists("docs"):
    files = [f for f in os.listdir("docs") if f.lower().endswith('.pdf')]
    if files:
        st.sidebar.markdown("<div style='margin-top: 15px; margin-bottom: 10px;'><span style='font-size: 0.85rem; color: #94a3b8; font-weight: 600; letter-spacing: 0.5px;'>ACTIVE DOCUMENTS</span></div>", unsafe_allow_html=True)
        for f in files:
            st.sidebar.markdown(f"""
            <div class="doc-vault-item">
                <span style="color: #38bdf8; font-size: 1.1rem; flex-shrink: 0;">📄</span>
                <span style="font-size: 0.85rem; color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex-grow: 1;" title="{f}">{f}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("*No documents uploaded yet.*")

# API Configuration section in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 API Configuration")

# Gemini Key Input
if env_gemini_key:
    st.sidebar.success("✅ Gemini API Key: Loaded from environment")
else:
    gemini_val = st.sidebar.text_input(
        "Gemini API Key",
        value=st.session_state.user_gemini_key,
        type="password",
        placeholder="Enter Gemini API Key...",
        key="sidebar_gemini_key"
    )
    if gemini_val != st.session_state.user_gemini_key:
        st.session_state.user_gemini_key = gemini_val
        st.rerun()

# HuggingFace Token Input
if env_hf_token:
    st.sidebar.success("✅ HuggingFace Token: Loaded from environment")
else:
    hf_val = st.sidebar.text_input(
        "HuggingFace Token",
        value=st.session_state.user_hf_token,
        type="password",
        placeholder="Enter HuggingFace Token...",
        key="sidebar_hf_token"
    )
    if hf_val != st.session_state.user_hf_token:
        st.session_state.user_hf_token = hf_val
        st.rerun()

# ----------------- MAIN UI -----------------
st.markdown("<div class='gradient-title'>🧠 NOC RAG Bot</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>A premium retrieval-augmented assistant for Network Operations Center (NOC) documentation. Powered by FAISS & Gemini.</div>", unsafe_allow_html=True)

# Show setup inputs on main page if configuration is incomplete
if not active_hf_token or not active_gemini_key:
    st.markdown("""
    <div class='glass-panel'>
        <h3 style='margin-top: 0; color: #ef4444;'>🔑 API Configuration Required</h3>
        <p style='color: #94a3b8;'>To start using the <strong>NOC RAG Bot</strong>, please provide the missing API keys below. 
        These keys are required for cloud-based embeddings (HuggingFace) and reasoning (Gemini). They will be held in session memory for this run.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Render neat columns for inputs on the main page
    col1, col2 = st.columns(2)
    with col1:
        if env_gemini_key:
            st.success("✅ Gemini API Key loaded from environment.")
        else:
            gemini_main = st.text_input(
                "Gemini API Key",
                value=st.session_state.user_gemini_key,
                type="password",
                placeholder="AIzaSy...",
                help="Google Gemini API Key (e.g. from Google AI Studio)",
                key="main_gemini_key"
            )
            if gemini_main != st.session_state.user_gemini_key:
                st.session_state.user_gemini_key = gemini_main
                st.rerun()
                
    with col2:
        if env_hf_token:
            st.success("✅ HuggingFace Token loaded from environment.")
        else:
            hf_main = st.text_input(
                "HuggingFace Hub Token",
                value=st.session_state.user_hf_token,
                type="password",
                placeholder="hf_...",
                help="HuggingFace Hub API token with read permissions",
                key="main_hf_token"
            )
            if hf_main != st.session_state.user_hf_token:
                st.session_state.user_hf_token = hf_main
                st.rerun()


elif vector_db is None:
    st.markdown("""
    <div class='glass-panel'>
        <h3 style='margin-top: 0; color: #f59e0b;'>⚠️ Database Setup Required</h3>
        <p style='color: #94a3b8;'>The vector database index has not been built yet. Please complete these steps:</p>
        <div class='step-container'>
            <div class='step-card'>
                <div class='step-num'>01</div>
                <h4 style='margin-top:0; margin-bottom:8px; color:#f1f5f9;'>Upload PDFs</h4>
                <p style='margin:0; font-size:0.88rem; color:#94a3b8;'>Use the <strong>"Document Upload"</strong> section in the sidebar to upload PDF documents.</p>
            </div>
            <div class='step-card'>
                <div class='step-num'>02</div>
                <h4 style='margin-top:0; margin-bottom:8px; color:#f1f5f9;'>Automatic Indexing</h4>
                <p style='margin:0; font-size:0.88rem; color:#94a3b8;'>The application will automatically read, chunk, embed, and build the FAISS index upon upload.</p>
            </div>
            <div class='step-card'>
                <div class='step-num'>03</div>
                <h4 style='margin-top:0; margin-bottom:8px; color:#f1f5f9;'>Start Chatting</h4>
                <p style='margin:0; font-size:0.88rem; color:#94a3b8;'>Once the database is indexed, the chat interface will unlock automatically.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # RAG chain setup
    rag_chain = get_rag_chain(active_hf_token, active_gemini_key)
    
    # Render chat history
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for idx, chat in enumerate(current_chat_history):
        role = chat["role"]
        content = chat["content"]
        
        if role == "user":
            st.markdown(f"""
            <div class="chat-bubble user-bubble">
                <div class="avatar user-avatar">U</div>
                <div style="flex-grow: 1;">
                    <div style="font-weight: 600; font-size: 0.85rem; opacity: 0.85; margin-bottom: 2px;">You</div>
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            sources_html = ""
            if "sources" in chat and chat["sources"]:
                sources_html = "<div style='margin-top: 10px;'>"
                for source in set(chat["sources"]):
                    sources_html += f"<span class='source-badge'>📖 {source}</span>"
                sources_html += "</div>"
                
            st.markdown(f"""
            <div class="chat-bubble bot-bubble">
                <div class="avatar bot-avatar">AI</div>
                <div style="flex-grow: 1;">
                    <div style="font-weight: 600; font-size: 0.85rem; color: #a855f7; margin-bottom: 2px;">DocuQuery AI</div>
                    {content}
                    {sources_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # If this is the latest bot response and has suggestions, render them
            is_latest = (idx == len(current_chat_history) - 1)
            if is_latest and "suggestions" in chat and chat["suggestions"]:
                st.markdown("<div style='margin-top: 15px; margin-bottom: 5px; padding-left: 50px;'><span style='font-size: 0.82rem; color: #94a3b8; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;'>Suggested Follow-up:</span></div>", unsafe_allow_html=True)
                
                # Render pills inside a container using columns
                suggestions = chat["suggestions"]
                cols = st.columns(len(suggestions))
                for s_idx, suggestion in enumerate(suggestions):
                    with cols[s_idx]:
                        if st.button(suggestion, key=f"sug_{s_idx}", use_container_width=True):
                            st.session_state.pending_query = suggestion
                            st.rerun()
                            
    st.markdown("</div>", unsafe_allow_html=True)

    # Empty history placeholder
    if not current_chat_history:
        st.markdown("""
        <div class='glass-panel' style='text-align: center; padding: 40px; margin-top: 20px;'>
            <div style='font-size: 3.5rem; margin-bottom: 15px;'>👋</div>
            <h3 style='margin-top: 0; color: #f1f5f9; font-weight: 600;'>Welcome to NOC RAG Bot!</h3>
            <p style='color: #94a3b8; max-width: 500px; margin: 0 auto 20px auto; font-size: 0.95rem;'>
                I am ready to answer questions based on your uploaded documents. Type a query below or select a suggested topic to begin.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Input handling
    query_to_process = None
    if st.session_state.pending_query:
        query_to_process = st.session_state.pending_query
        st.session_state.pending_query = None

    user_query = st.chat_input("Ask a question about your PDF documents...")
    
    if user_query or query_to_process:
        actual_query = user_query or query_to_process
        
        # Append user message immediately
        st.session_state.sessions[current_sid]["chat_history"].append({
            "role": "user",
            "content": actual_query
        })
        
        # Update session title if it was the default "New Chat"
        if st.session_state.sessions[current_sid]["title"] == "New Chat":
            from datetime import datetime
            time_str = datetime.now().strftime("%I:%M %p")
            q_part = actual_query[:22] + "..." if len(actual_query) > 22 else actual_query
            st.session_state.sessions[current_sid]["title"] = f"{q_part} ({time_str})"
            
        st.rerun()

# Process pending queries in background (renders typing indicator and fetches results)
if current_chat_history and current_chat_history[-1]["role"] == "user":
    last_user_query = current_chat_history[-1]["content"]
    
    with st.spinner("🤖 Thinking..."):
        try:
            if rag_chain is None:
                st.error("RAG chain is not initialized. Please upload document PDFs and configure API keys.")
            else:
                # Convert session chat history to LangChain messages format
                from langchain_core.messages import HumanMessage, AIMessage
                chat_history_msgs = []
                # Exclude the very last user message which we are processing now
                for chat in current_chat_history[:-1]:
                    if chat["role"] == "user":
                        chat_history_msgs.append(HumanMessage(content=chat["content"]))
                    else:
                        chat_history_msgs.append(AIMessage(content=chat["content"]))
                
                # Invoke retrieval chain
                response = rag_chain.invoke({
                    "input": last_user_query,
                    "chat_history": chat_history_msgs
                })
                answer = response["answer"]
                
                # Fetch sources
                sources = []
                for doc in response.get("context", []):
                    source_name = os.path.basename(doc.metadata.get("source", "Unknown"))
                    page = doc.metadata.get("page", 0) + 1
                    sources.append(f"{source_name} (Page {page})")
                
                # Generate suggestions
                suggestions = get_followup_suggestions(last_user_query, answer, active_gemini_key)
                
                # Append assistant response
                st.session_state.sessions[current_sid]["chat_history"].append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "suggestions": suggestions
                })
                st.rerun()
                
        except Exception as e:
            st.error(f"Error executing query: {e}")

