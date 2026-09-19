from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

load_dotenv(
    PROJECT_ROOT / ".env"
)


DATA_DIR = (
    PROJECT_ROOT / "rag" / "data"
)

SOURCE_DIR = Path(
    os.getenv(
        "RAG_SOURCE_DIR",
        str(DATA_DIR / "dataset_extracted"),
    )
)

INDEX_DIR = Path(
    os.getenv(
        "RAG_INDEX_DIR",
        str(PROJECT_ROOT / "rag" / "indexes"),
    )
)

EMBEDDING_MODEL = os.getenv(
    "RAG_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "qwen/qwen3.8-27b",
)