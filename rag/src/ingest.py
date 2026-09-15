# src/ingest.py
import json
import os

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_chroma import Chroma  # standardized package (matches retriever.py)
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

RAW_DATA_DIR = "data/raw"
VECTOR_DB_DIR = "data/chroma_db"


def load_scheme_json(file_path: str) -> list[Document]:
    """
    Structured loader for hand-curated or scraped JSON with real fields
    (e.g. incometax_faqs.json from scraper.py: question/answer/source_url).
    NOT used for the myscheme PDF corpus, which has no structured fields.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    docs = []
    for rec in records:
        title = rec.get("scheme_name") or rec.get("question") or "Untitled"
        source_url = rec.get("source_url") or rec.get("official_link", "")
        section = rec.get("section", "")
        assessment_year = rec.get("assessment_year", "")
        tax_year = rec.get("tax_year", "")  # Income Tax Act, 2025 terminology

        field_groups = {
            "overview": [rec.get("description"), rec.get("answer")],
            "eligibility": [rec.get("eligibility")],
            "benefits": [rec.get("benefits")],
            "application_process": [rec.get("application_process")],
            "documents_required": [rec.get("documents_required")],
        }

        for group_name, values in field_groups.items():
            text = " ".join(v for v in values if v)
            if not text.strip():
                continue
            docs.append(
                Document(
                    page_content=f"{title} — {group_name}: {text}",
                    metadata={
                        "title": title,
                        "field": group_name,
                        "source_url": source_url,
                        "section": section,
                        "assessment_year": assessment_year,
                        "tax_year": tax_year,
                    },
                )
            )
    return docs


def _normalize_text(text: str) -> str:
    """Collapse whitespace/case so near-identical PDF re-scrapes hash the same."""
    return " ".join(text.lower().split())


def load_documents():
    """
    Recursively walks data/raw/ so files inside subfolders (e.g.
    data/raw/myscheme_pdfs/text_data/*.pdf) are picked up, not just
    top-level files.

    The myscheme PDF corpus contains ~4x duplicate files (e.g. nsigse.pdf,
    nsigse(1).pdf, nsigse(2).pdf all have the same content) — dedupe by
    content hash, not filename, since filename patterns aren't consistent.
    """
    import hashlib

    documents = []
    seen_hashes = set()
    duplicate_count = 0

    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
        print(f"Created directory: {RAW_DATA_DIR}. Add .txt, .pdf, or .json files.")
        return documents

    for root, _dirs, files in os.walk(RAW_DATA_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                loaded = loader.load()
                # Hash by combined page text of the whole PDF (not per-page)
                full_text = _normalize_text("".join(d.page_content for d in loaded))
                content_hash = hashlib.md5(full_text.encode("utf-8")).hexdigest()
                if content_hash in seen_hashes:
                    duplicate_count += 1
                    continue
                seen_hashes.add(content_hash)
                documents.extend(loaded)
            elif file.endswith(".txt"):
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
            elif file.endswith(".json"):
                documents.extend(load_scheme_json(file_path))

    if duplicate_count:
        print(f"Skipped {duplicate_count} duplicate PDF(s) by content hash.")
    return documents


def build_vector_store():
    docs = load_documents()
    if not docs:
        print("No documents found in data/raw. Run download_myscheme.py and "
              "scraper.py first.")
        return

    # JSON docs (tax FAQs) already chunked by natural field — don't re-split.
    # PDF/TXT docs (myscheme corpus, unstructured) still need character splitting.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,  # characters, not tokens
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
    )

    pdf_txt_docs = [d for d in docs if d.metadata.get("field") is None]
    json_docs = [d for d in docs if d.metadata.get("field") is not None]

    split_pdf_txt = text_splitter.split_documents(pdf_txt_docs) if pdf_txt_docs else []
    chunks = split_pdf_txt + json_docs

    print(f"Total chunks: {len(chunks)} "
          f"({len(split_pdf_txt)} from myscheme PDFs, {len(json_docs)} from tax JSON).")

    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR,
    )
    print(f"Saved vector index to {VECTOR_DB_DIR}")


if __name__ == "__main__":
    build_vector_store()