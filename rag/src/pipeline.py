from __future__ import annotations

from pathlib import Path
from typing import Any

from .generator import LLMGenerator
from .vector_store import FaissStore
from rag.src.config import EMBEDDING_MODEL
from collections.abc import Iterator


class RagPipeline:
    def __init__(
        self,
        index_dir: str | Path,
        llm_model: str | None = None,
    ) -> None:
        self.store = FaissStore(
            index_dir=index_dir,
            model_name=EMBEDDING_MODEL,
        )
        self.store.load(index_dir)

        self.generator = LLMGenerator(
            model_name=llm_model,
        )

    def stream_answer_query(
        self,
        query: str,
        top_k: int = 5,
    ) -> Iterator[str]:
        query = query.strip()

        if not query:
            yield "Please enter a question."
            return

        contexts = self.store.search(
            query,
            top_k=top_k,
        )

        if not contexts:
            yield (
                "I could not find relevant information "
                "in the available documents."
            )
            return

        yield from self.generator.stream_generate(
            query=query,
            contexts=contexts,
        )

    def answer_query(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        query = query.strip()

        if not query:
            return {
            "answer": "Please enter a question.",
            "sources": [],
        }

        contexts = self.store.search(
            query,
            top_k=top_k,
        )

        if not contexts:
            return {
                "answer": (
                    "I could not find relevant information "
                    "in the available documents."
                ),
                "sources": [],
            }

        answer = self.generator.generate(
            query=query,
            contexts=contexts,
        )

        sources = [

          {
            "source": item.get(
                "source",
                "Unknown",
            ),
            "file_name": item.get(
                "file_name",
                "Unknown",
            ),
            "chunk": item.get(
                "chunk",
                0,
            ),
            "score": item.get(
                "score",
                0.0,
            ),
        }
          for item in contexts
     ]

        return {
            "answer": answer,
            "sources": sources,
        }

   