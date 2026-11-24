"""Load .md / .txt / .csv / .pdf files from the notes folder and turn them into chunks."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from src.chunker import Chunk, chunk_text
from src.config import NOTES_DIR

SUPPORTED_EXTENSIONS = {".md", ".txt", ".csv", ".pdf"}


def _read_md_or_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_csv(path: Path) -> str:
    """Render each CSV row as a `column: value` block so rows chunk and search well."""
    blocks = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            lines = [f"{k}: {v}" for k, v in row.items()]
            blocks.append(f"Row {i + 1} ({path.name}):\n" + "\n".join(lines))
    return "\n\n".join(blocks)


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError(
            "pypdf is required to read PDFs. Install with: pip install pypdf"
        ) from e
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[Page {i + 1}]\n{text.strip()}")
    return "\n\n".join(pages)


def load_file_text(path: Path) -> str:
    """Return the plain text of a supported file."""
    ext = path.suffix.lower()
    if ext in (".md", ".txt"):
        return _read_md_or_txt(path)
    if ext == ".csv":
        return _read_csv(path)
    if ext == ".pdf":
        return _read_pdf(path)
    raise ValueError(f"Unsupported extension: {ext}")


def discover_files(notes_dir: Path = NOTES_DIR) -> List[Path]:
    """Recursively list supported files under notes_dir."""
    if not notes_dir.is_dir():
        return []
    return sorted(
        p for p in notes_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def build_all_chunks(notes_dir: Path = NOTES_DIR) -> List[Chunk]:
    """Read and chunk every supported file. Unreadable files are skipped with a warning."""
    all_chunks: List[Chunk] = []
    files = discover_files(notes_dir)
    if not files:
        raise FileNotFoundError(
            f"No supported files found in {notes_dir}. "
            f"Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
        )
    for path in files:
        try:
            text = load_file_text(path)
        except Exception as e:
            print(f"[ingest] skipping {path.name}: {e}")
            continue
        if not text.strip():
            continue
        rel_name = path.relative_to(notes_dir).as_posix()
        all_chunks.extend(chunk_text(text, source_file=rel_name))
    return all_chunks
