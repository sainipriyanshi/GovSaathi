from __future__ import annotations


import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from rag.src.config import INDEX_DIR
from rag.src.pipeline import RagPipeline


def main() -> None:
    print(
        "Starting standalone GovSaathi "
        "RAG pipeline..."
    )

    print(
        f"Using index directory: {INDEX_DIR}"
    )

    try:
        pipeline = RagPipeline(
            index_dir=INDEX_DIR,
        )

    except Exception as exc:
        print("\nINITIALIZATION ERROR")
        print("Type:", type(exc).__name__)
        print("Details:", repr(exc))
        traceback.print_exc()
        return

    query = input(
        "Enter your question: "
    ).strip()

    if not query:
        print("Please enter a question.")
        return

    try:
        print(
            "\nRetrieving relevant documents..."
        )

        result = pipeline.answer_query(
            query,
            top_k=5,
        )

    except Exception as exc:
        print("\nRAG REQUEST ERROR")
        print("Type:", type(exc).__name__)
        print("Details:", repr(exc))
        traceback.print_exc()
        return

    print("\nANSWER\n")
    print(result["answer"])

    print("\nSOURCES\n")

    if not result["sources"]:
        print("- No sources found")
        return

    for source in result["sources"]:
        print(
            f"- {source.get('file_name', 'Unknown')} "
            f"(score={source.get('score', 0.0):.4f}, "
            f"chunk={source.get('chunk', 0)})"
        )


if __name__ == "__main__":
    main()