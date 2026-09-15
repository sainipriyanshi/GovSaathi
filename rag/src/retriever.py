# src/retriever.py
import os

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.ingest import load_documents  # reuse the SAME loader ingest.py uses

load_dotenv()

VECTOR_DB_DIR = "data/chroma_db"


class HybridRetriever:
    def __init__(self):
        # 1. Dense retriever — reads the already-built Chroma index
        self.embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
        self.vector_db = Chroma(
            persist_directory=VECTOR_DB_DIR,
            embedding_function=self.embeddings,
        )
        self.dense_retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})

        # 2. BM25 — MUST see the same document set as the vector DB, including
        # JSON-sourced scheme/tax chunks, or hybrid search silently degrades
        # to dense-only for that content.
        docs = load_documents()  # same function ingest.py uses to build Chroma

        # Only re-split PDF/TXT docs (no "field" metadata); JSON docs are
        # already chunked by natural field in ingest.py and shouldn't be
        # re-split here either — keep this logic identical to ingest.py.
        pdf_txt_docs = [d for d in docs if d.metadata.get("field") is None]
        json_docs = [d for d in docs if d.metadata.get("field") is not None]

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
        split_pdf_txt = text_splitter.split_documents(pdf_txt_docs) if pdf_txt_docs else []

        bm25_corpus = split_pdf_txt + json_docs
        if not bm25_corpus:
            raise RuntimeError(
                "No documents found for BM25 index. Run `python src/ingest.py` "
                "first to populate data/raw and data/chroma_db."
            )

        self.bm25_retriever = BM25Retriever.from_documents(bm25_corpus)
        self.bm25_retriever.k = 3

    def get_relevant_documents(self, query: str):
        dense_results = self.dense_retriever.invoke(query)
        bm25_results = self.bm25_retriever.invoke(query)

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
        print(f"Metadata: {doc.metadata}")