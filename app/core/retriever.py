import os
import yaml
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.ingestion.load import load_documents

# --- PATH & CONFIGURATION ---
try:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config', 'config.yaml')
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    raise FileNotFoundError(f"Configuration file not found. Ensure 'config/config.yaml' exists.")

# --- GLOBAL VARIABLES ---
UI_VECTOR_STORE_PATH = os.path.join(PROJECT_ROOT, config['vector_store_path'])
EMBEDDINGS = HuggingFaceEmbeddings(model_name=config['embedding_model'])

# --- MODULAR, REUSABLE FUNCTIONS ---

def build_index_from_path(source_dir: str, vector_store_path: str):
    """
    Generic function to build a FAISS index from a source directory 
    and save it to a specified path.
    """
    docs = load_documents(source_dir)
    if not docs:
        raise ValueError("No documents found to process in the source directory.")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config['text_splitter']['chunk_size'],
        chunk_overlap=config['text_splitter']['chunk_overlap']
    )
    texts = text_splitter.split_documents(docs)
    
    vector_store = FAISS.from_documents(texts, EMBEDDINGS)
    os.makedirs(vector_store_path, exist_ok=True)
    vector_store.save_local(vector_store_path)

def retrieve_chunks_from_path(query: str, vector_store_path: str, k: int = 5) -> list[str]:
    """
    Generic function to retrieve document chunks from a FAISS index 
    at a specified path.
    """
    if not os.path.exists(vector_store_path):
        raise FileNotFoundError(f"Vector store not found at path: {vector_store_path}")
        
    vector_store = FAISS.load_local(vector_store_path, EMBEDDINGS, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    relevant_docs = retriever.invoke(query)
    
    return [doc.page_content for doc in relevant_docs]

# --- SESSION-BASED FUNCTIONS (For UI) ---

def build_index(session_id: str, source_dir: str):
    """Builds an index for a specific session (used by the UI)."""
    session_vector_path = os.path.join(UI_VECTOR_STORE_PATH, session_id)
    build_index_from_path(source_dir, session_vector_path)

def retrieve_chunks(query: str, session_id: str, k: int = 5) -> list[str]:
    """Retrieves chunks for a specific session (used by the UI)."""
    session_vector_path = os.path.join(UI_VECTOR_STORE_PATH, session_id)
    return retrieve_chunks_from_path(query, session_vector_path, k)
