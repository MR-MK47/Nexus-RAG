import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.schema import Document

# Mapping from file extension to document loader class
LOADER_MAPPING = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".doc": UnstructuredWordDocumentLoader,
    ".docx": UnstructuredWordDocumentLoader,
}

def load_documents(source_dir: str) -> List[Document]:
    """
    Loads all documents from the specified source directory, using the appropriate
    loader for each file type.
    """
    all_files = []
    for ext in LOADER_MAPPING:
        # Find all files with the current extension
        all_files.extend(
            [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.endswith(ext)]
        )

    documents = []
    for file_path in all_files:
        ext = os.path.splitext(file_path)[-1]
        if ext in LOADER_MAPPING:
            try:
                loader_class = LOADER_MAPPING[ext]
                loader = loader_class(file_path)
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading file {file_path}: {e}")
                continue
    
    return documents
