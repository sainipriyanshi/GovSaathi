# src/ingest.py
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Define Paths
RAW_DATA_DIR = "data/raw"
VECTOR_DB_DIR = "data/chroma_db"

def load_documents():
    documents = []
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
        print(f"Created directory: {RAW_DATA_DIR}. Please place raw .txt or .pdf files here.")
        return documents

    for file in os.listdir(RAW_DATA_DIR):
        file_path = os.path.join(RAW_DATA_DIR, file)
        if file.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())
        elif file.endswith(".txt"):
            loader = TextLoader(file_path, encoding="utf-8")
            documents.extend(loader.load())
    return documents

def build_vector_store():
    docs = load_documents()
    if not docs:
        print("No documents found in data/raw. Add sample PDF/TXT files first.")
        return

    # 2. Chunking strategy (512 token limit with 50 overlap)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Total documents processed into {len(chunks)} chunks.")

    # 3. Dense Embeddings (Using BGE-M3 or sentence-transformers)
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    # 4. Save to ChromaDB
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR
    )
    print(f"Successfully saved vector index to {VECTOR_DB_DIR}")

if __name__ == "__main__":
    build_vector_store()