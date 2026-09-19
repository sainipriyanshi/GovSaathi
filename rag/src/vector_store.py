from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from rag.src.config import EMBEDDING_MODEL


class FaissStore:
    def __init__(
        self,
        index_dir,
        model_name=None,
    ):
        self.index_dir = Path(index_dir)

        self.model_name = (
            model_name or EMBEDDING_MODEL
        )

        print(
            f"Loading embedding model: "
            f"{self.model_name}"
        )

        self.model = SentenceTransformer(
            self.model_name
        )

        self.index = None
        self.records = []

    def build(
        self,
        chunks: list[dict[str, Any]],
    ) -> None:
        if not chunks:
            raise ValueError(
                "Cannot build FAISS index without chunks."
            )

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        vectors = np.asarray(
            vectors,
            dtype="float32",
        )

        self.index = faiss.IndexFlatIP(
            vectors.shape[1]
        )

        self.index.add(vectors)
        self.records = chunks

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        if self.index is None:
            raise RuntimeError(
                "FAISS index has not been built or loaded."
            )

        query = query.strip()

        if not query:
            return []

        top_k = max(
            1,
            min(top_k, self.index.ntotal),
        )

        query_vector = self.model.encode(
            [query],
            normalize_embeddings=True,
        )

        query_vector = np.asarray(
            query_vector,
            dtype="float32",
        )

        scores, positions = self.index.search(
            query_vector,
            top_k,
        )

        results: list[dict[str, Any]] = []

        for score, position in zip(
            scores[0],
            positions[0],
        ):
            if position < 0:
                continue

            result = dict(
                self.records[position]
            )

            result["score"] = float(score)
            results.append(result)

        return results

    def save(
        self,
        directory: str | Path,
    ) -> None:
        if self.index is None:
            raise RuntimeError(
                "Build the index before saving."
            )

        directory = Path(directory)
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            str(directory / "index.faiss"),
        )

        (directory / "records.json").write_text(
            json.dumps(
                self.records,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(
        self,
        directory: str | Path,
    ) -> None:
        directory = Path(directory)

        index_path = directory / "index.faiss"
        records_path = directory / "records.json"

        if not index_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}"
            )

        if not records_path.exists():
            raise FileNotFoundError(
                f"Records file not found: {records_path}"
            )

        self.index = faiss.read_index(
            str(index_path)
        )

        self.records = json.loads(
            records_path.read_text(
                encoding="utf-8"
            )
        )

        if self.index.ntotal != len(
            self.records
        ):
            raise RuntimeError(
                "FAISS index count does not match "
                "records.json count."
            )