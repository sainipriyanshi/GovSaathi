# src/retriever.py
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv

load_dotenv()

RAW_DATA_DIR = "data/raw"
VECTOR_DB_DIR = "data/chroma_db"

class HybridRetriever:
    def __init__(self):
        # 1. Initialize Dense Embeddings & Vector Database
        self.embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
        self.vector_db = Chroma(
            persist_directory=VECTOR_DB_DIR, 
            embedding_function=self.embeddings
        )
        
        # Dense Retriever with similarity search
        self.dense_retriever = self.vector_db.as_retriever(
            search_kwargs={"k": 3}
        )

        # 2. Initialize Sparse Keyword Search (BM25)
        documents = []
        if os.path.exists(RAW_DATA_DIR):
            for file in os.listdir(RAW_DATA_DIR):
                file_path = os.path.join(RAW_DATA_DIR, file)
                if file.endswith(".txt"):
                    loader = TextLoader(file_path, encoding="utf-8")
                    documents.extend(loader.load())
                elif file.endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                    documents.extend(loader.load())

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)

        self.bm25_retriever = BM25Retriever.from_documents(chunks)
        self.bm25_retriever.k = 3

    def get_relevant_documents(self, query: str):
        dense_results = self.dense_retriever.invoke(query)
        bm25_results = self.bm25_retriever.invoke(query)

        # Deduplicate retrieved context chunks
        combined_docs = {}
        for doc in dense_results + bm25_results:
            if doc.page_content not in combined_docs:
                combined_docs[doc.page_content] = doc

        return list(combined_docs.values())

if __name__ == "__main__":
    retriever = HybridRetriever()
    test_query = "What are the tax benefits under Section 80C?"
    results = retriever.get_relevant_documents(test_query)

    print(f"\n--- Hybrid Search Results for: '{test_query}' ---")
    for idx, doc in enumerate(results, 1):
        print(f"\n[Result {idx}]:\n{doc.page_content}")