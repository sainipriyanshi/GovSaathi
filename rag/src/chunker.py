from __future__ import annotations

from typing import Any


def chunk_documents(
    documents: list[dict[str, Any]],
    chunk_size: int = 900,
    overlap: int = 150,
) -> list[dict[str, Any]]:
    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero"
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative"
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks: list[dict[str, Any]] = []

    for document in documents:
        text = " ".join(
            document.get("text", "").split()
        )

        if not text:
            continue

        start = 0
        chunk_number = 0

        while start < len(text):
            end = min(
                start + chunk_size,
                len(text),
            )

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "text": chunk_text,
                        "source": document.get(
                            "source",
                            "Unknown",
                        ),
                        "file_name": document.get(
                            "file_name",
                            "Unknown",
                        ),
                        "chunk": chunk_number,
                    }
                )

            if end >= len(text):
                break

            start = end - overlap
            chunk_number += 1

    return chunks