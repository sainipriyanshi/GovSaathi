from pathlib import Path
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[2]
archive = PROJECT_ROOT / "rag" / "data" / "GovSaathi Dataset.zip"
destination = PROJECT_ROOT / "rag" / "data" / "dataset_extracted"
dataset_root = destination / "GovSaathi Dataset"

destination.mkdir(parents=True, exist_ok=True)

with ZipFile(archive) as archive_file:
    for member in archive_file.infolist():
        member_path = Path(member.filename)

        if not member.filename.startswith("GovSaathi Dataset/"):
            continue

        if member.filename.startswith("__MACOSX/"):
            continue

        relative_path = member_path.relative_to("GovSaathi Dataset")
        output_path = (destination / relative_path).resolve()

        if not output_path.is_relative_to(destination.resolve()):
            raise RuntimeError(f"Unsafe archive path: {member.filename}")

        if member.is_dir():
            output_path.mkdir(parents=True, exist_ok=True)
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(archive_file.read(member))

print(f"Extracted dataset to: {destination}")