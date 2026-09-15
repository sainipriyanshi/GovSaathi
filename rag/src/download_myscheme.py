# src/download_myscheme.py
"""
Downloads the shrijayan/gov_myscheme dataset (723 PDFs, one per scheme,
cryptic filenames, no metadata mapping) into data/raw/myscheme_pdfs/,
so ingest.py's existing PyPDFLoader branch can pick them up.
"""
import os

from huggingface_hub import snapshot_download

TARGET_DIR = "data/raw/myscheme_pdfs"


def download():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print("Downloading shrijayan/gov_myscheme (723 PDFs)...")
    local_path = snapshot_download(
        repo_id="shrijayan/gov_myscheme",
        repo_type="dataset",
        local_dir=TARGET_DIR,
        allow_patterns=["text_data/*.pdf"],
    )
    print(f"Downloaded to: {local_path}")
    print("PDFs are under text_data/ inside that folder — ingest.py needs to "
          "scan subfolders recursively (see updated load_documents()).")


if __name__ == "__main__":
    download()