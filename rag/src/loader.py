from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".markdown",
    ".json",
}


def _normalise_text(text: str) -> str:
    return " ".join(text.lower().split())


def _load_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))

    return "\n\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )


def _load_json(path: Path) -> str:
    data = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    records = data if isinstance(
        data,
        list,
    ) else [data]

    parts: list[str] = []

    for record in records:
        if isinstance(record, dict):
            title = (
                record.get("scheme_name")
                or record.get("question")
                or record.get("title")
                or "Untitled"
            )

            values = [
                record.get("description"),
                record.get("answer"),
                record.get("eligibility"),
                record.get("benefits"),
                record.get("application_process"),
                record.get("documents_required"),
            ]

            content = " ".join(
                str(value)
                for value in values
                if value
            )

            parts.append(
                f"{title}\n{content}"
            )
        else:
            parts.append(str(record))

    return "\n\n".join(parts)


def _read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
        errors="ignore",
    )


def load_source_documents(
    source_dir: str | Path,
) -> list[dict[str, Any]]:
    source_dir = Path(source_dir)

    if not source_dir.exists():
        raise FileNotFoundError(
            f"Source directory not found: "
            f"{source_dir}"
        )

    documents: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    for path in sorted(
        source_dir.rglob("*")
    ):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        try:
            if suffix == ".pdf":
                text = _load_pdf(path)
            elif suffix == ".json":
                text = _load_json(path)
            else:
                text = _read_text(path)

        except Exception as exc:
            print(
                f"Skipping {path}: {exc}"
            )
            continue

        text = text.strip()

        if not text:
            continue

        normalized = _normalise_text(text)

        content_hash = hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

        if content_hash in seen_hashes:
            continue

        seen_hashes.add(content_hash)

        documents.append(
            {
                "text": text,
                "source": str(path),
                "file_name": path.name,
                "file_type": suffix.lstrip("."),
            }
        )

    return documents