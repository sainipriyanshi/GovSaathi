from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from rag.src.chunker import chunk_documents
from rag.src.config import (
    EMBEDDING_MODEL,
    INDEX_DIR,
    SOURCE_DIR,
)
from rag.src.loader import load_source_documents
from rag.src.vector_store import FaissStore


def build_index() -> None:
    print(
        f"Loading documents from: {SOURCE_DIR}"
    )

    documents = load_source_documents(
        SOURCE_DIR
    )

    if not documents:
        raise RuntimeError(
            "No supported documents found."
        )

    print(
        f"Loaded unique documents: "
        f"{len(documents)}"
    )

    chunks = chunk_documents(
        documents,
        chunk_size=900,
        overlap=150,
    )
    
    print(
        f"Created chunks: {len(chunks)}"
    )

    if not chunks:
        raise RuntimeError(
            "No chunks were created."
        )

    print(
        f"Created chunks: {len(chunks)}"
    )

    store = FaissStore(
    index_dir=INDEX_DIR,
    model_name=EMBEDDING_MODEL,
)

    print(
        "Starting embedding generation..."
    )

    store.build(chunks)

    print(
        "Embedding generation completed."
    )

    store.save(INDEX_DIR)

    print(
        f"Saved FAISS index to: {INDEX_DIR}"
    )


if __name__ == "__main__":
    build_index()