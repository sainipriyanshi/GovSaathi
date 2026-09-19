from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from rag.src.vector_store import FaissStore


INDEX_DIR = PROJECT_ROOT / "rag" / "indexes"


def main() -> None:
    store = FaissStore()
    store.load(INDEX_DIR)

    query = input(
        "Enter your question: "
    ).strip()

    if not query:
        print("Please enter a question.")
        return

    results = store.search(
        query,
        top_k=5,
    )

    if not results:
        print("No matching sources found.")
        return

    print("\nRetrieved sources:\n")

    for number, result in enumerate(results, start=1):
        print("=" * 80)
        print(f"Result: {number}")
        print(f"Score: {result['score']:.4f}")
        print(f"Source: {result['source']}")
        print(f"File: {result['file_name']}")
        print(f"Chunk: {result['chunk']}")
        print("\nText preview:")
        print(result["text"][:700])


if __name__ == "__main__":
    main()