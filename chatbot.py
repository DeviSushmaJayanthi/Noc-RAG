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

# Load environment variables
load_dotenv()

# Verify API keys
gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")

if not gemini_key:
    print("Warning: Neither GEMINI_API_KEY nor GOOGLE_API_KEY found in environment variables.")
    print("Please set your Gemini API key in a '.env' file. Example: GEMINI_API_KEY=AIzaSy...")

if not hf_token:
    print("Warning: Neither HUGGINGFACEHUB_API_TOKEN nor HF_TOKEN found in environment variables.")
    print("Please set your HuggingFace Hub API Token in a '.env' file. Example: HUGGINGFACEHUB_API_TOKEN=hf_...")

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains import create_retrieval_chain, create_history_aware_retriever

DB_FAISS_PATH = 'faiss_index'

def load_rag_chain():
    # 1. Load FAISS index
    if not os.path.exists(DB_FAISS_PATH):
        print(f"Error: Vector store index '{DB_FAISS_PATH}' not found.")
        print("Please run the ingestion script first: python ingest.py")
        sys.exit(1)
        
    print("Loading HuggingFace Endpoint Embeddings model...")
    embeddings = HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        huggingfacehub_api_token=hf_token
    )
    
    print("Loading FAISS Vector Database...")
    # Allow dangerous deserialization since this is a local FAISS database we control
    vector_store = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    
    # 2. Setup retriever
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})
    
    # 3. Initialize Gemini model
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
        
    print("Initializing Gemini model (gemini-3.5-flash)...")
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.2)
    
    # 4. Create query contextualization prompt
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
    
    # 5. Create prompt template for answering
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
    
    # 6. Combine prompt and LLM using create_stuff_documents_chain
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # 7. Combine history_aware_retriever and question_answer_chain using create_retrieval_chain
    retrieval_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    return retrieval_chain

def start_chatbot():
    try:
        chain = load_rag_chain()
    except Exception as e:
        print(f"\nFailed to load RAG Chain: {e}")
        print("Please make sure your GEMINI_API_KEY and HUGGINGFACEHUB_API_TOKEN are valid.")
        sys.exit(1)
        
    print("\n" + "="*50)
    print(" RAG Chatbot is Ready! Type your query below.")
    print(" (Type 'exit' or 'quit' to close the chatbot)")
    print("="*50 + "\n")
    
    chat_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                print("Exiting RAG Chatbot. Goodbye!")
                break
                
            print("Bot thinking...")
            response = chain.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            
            # Print response
            print(f"\nBot: {response['answer']}\n")
            
            # Update history
            chat_history.append(HumanMessage(content=user_input))
            chat_history.append(AIMessage(content=response['answer']))
            
        except KeyboardInterrupt:
            print("\nExiting RAG Chatbot. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    start_chatbot()
