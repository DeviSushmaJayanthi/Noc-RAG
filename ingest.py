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
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_community.vectorstores import FAISS

# Load environment variables
load_dotenv()

DB_FAISS_PATH = 'faiss_index'
DOCS_DIR = 'docs'

def run_ingestion():
    # Verify Hugging Face Token is set
    hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
    if not hf_token:
        print("Error: HUGGINGFACEHUB_API_TOKEN (or HF_TOKEN) is not set in environment.")
        print("Please add it to your '.env' file. You can get a free token at https://huggingface.co/settings/tokens")
        sys.exit(1)

    if not os.path.exists(DOCS_DIR):
        print(f"Error: Directory '{DOCS_DIR}' not found. Please create it and add PDFs.")
        sys.exit(1)
        
    pdf_files = [f for f in os.listdir(DOCS_DIR) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"Error: No PDF files found in '{DOCS_DIR}' directory.")
        sys.exit(1)
        
    print(f"Found PDF documents to process: {pdf_files}")
    
    print("Loading PDF documents...")
    loader = PyPDFDirectoryLoader(DOCS_DIR)
    documents = loader.load()
    print(f"Loaded {len(documents)} pages from documents.")
    
    if not documents:
        print("Error: No content extracted from the documents. Please verify PDFs are not scanned or empty.")
        sys.exit(1)
    
    print("Splitting text into chunks (chunk_size=500, chunk_overlap=100)...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks.")
    
    print("Initializing HuggingFace Endpoint Embeddings (model: sentence-transformers/all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        huggingfacehub_api_token=hf_token
    )
    
    print("Generating FAISS Vector Database index...")
    vector_store = FAISS.from_documents(chunks, embeddings)
    
    print(f"Saving FAISS vector database to '{DB_FAISS_PATH}'...")
    vector_store.save_local(DB_FAISS_PATH)
    print("Ingestion completed successfully!")

if __name__ == "__main__":
    run_ingestion()
