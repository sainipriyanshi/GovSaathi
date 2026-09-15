# src/main.py
import sys
import os
from dotenv import load_dotenv

# Path resolution for root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.retriever import HybridRetriever

# Load environment variables
load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY is not set in environment or .env file.")

app = FastAPI(
    title="GovSaathi RAG API",
    description="Backend API for Government Scheme & Income Tax Assistance",
    version="1.0.0"
)

# 1. Initialize Custom Hybrid Retriever
print("Initializing Hybrid Retriever (BM25 + ChromaDB)...")
retriever_obj = HybridRetriever()

# 2. Setup Groq LLM & Prompt Template
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.2
)

system_prompt = (
    "You are GovSaathi, an expert AI assistant specializing in Indian government schemes "
    "and Income Tax regulations. Use the following retrieved context to answer "
    "the user's question accurately. If you don't know the answer or if it's not present "
    "in the context, explicitly state that you don't know based on available data. "
    "Keep your answer concise, clear, and easy to understand.\n\n"
    "Context:\n{context}"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{question}"),
])

# Helper function to combine document texts
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Request & Response Schemas
class QueryRequest(BaseModel):
    query: str = Field(..., example="What are the tax benefits under Section 80C?")

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[str]


@app.get("/")
def health_check():
    return {"status": "ok", "message": "GovSaathi API is running smoothly."}


@app.post("/api/v1/chat", response_model=QueryResponse)
def query_govsaathi(request: QueryRequest):
    try:
        # Retrieve context docs via your custom HybridRetriever method
        docs = retriever_obj.get_relevant_documents(request.query)
        context_str = format_docs(docs)

        # Build and invoke LCEL chain directly
        rag_chain = prompt | llm | StrOutputParser()
        answer = rag_chain.invoke({
            "context": context_str,
            "question": request.query
        })

        # Extract source metadata cleanly
        extracted_sources = []
        for doc in docs:
            src = doc.metadata.get("source_url") or doc.metadata.get("source", "Unknown Document")
            if src not in extracted_sources:
                extracted_sources.append(src)

        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=extracted_sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)