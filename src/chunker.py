"""Text chunking strategies. `chunk_text` (paragraph-based) is the default."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from src.config import CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS


@dataclass
class Chunk:
    """One retrievable piece of a source file."""

    chunk_id: str
    source_file: str
    text: str
    position: int


def _to_chunks(pieces: List[str], source_file: str) -> List[Chunk]:
    chunks = []
    position = 0

    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        cid = f"{source_file}::chunk{position}"
        chunks.append(Chunk(chunk_id=cid, source_file=source_file,
                             text=piece, position=position))
        position += 1

    return chunks


def chunk_by_char(text: str, source_file: str,
                   chunk_size: int = CHUNK_SIZE_CHARS,
                   chunk_overlap: int = CHUNK_OVERLAP_CHARS) -> List[Chunk]:
    """Fixed-size character windows with overlap."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    pieces = []
    start_idx = 0

    while start_idx < len(text):
        end_idx = min(start_idx + chunk_size, len(text))
        pieces.append(text[start_idx:end_idx])
        start_idx = end_idx - chunk_overlap if end_idx < len(text) else len(text)

    return _to_chunks(pieces, source_file)


def chunk_by_sentence(text: str, source_file: str,
                       max_sentences_per_chunk: int = 5,
                       overlap_sentences: int = 1) -> List[Chunk]:
    """Groups of N sentences, overlapping by a few sentences."""
    if overlap_sentences >= max_sentences_per_chunk:
        raise ValueError("overlap_sentences must be smaller than max_sentences_per_chunk")
    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces = []
    start_idx = 0

    while start_idx < len(sentences):
        end_idx = min(start_idx + max_sentences_per_chunk, len(sentences))
        pieces.append(" ".join(sentences[start_idx:end_idx]))
        if end_idx >= len(sentences):
            break
        start_idx += max_sentences_per_chunk - overlap_sentences

    return _to_chunks(pieces, source_file)


def chunk_by_section(text: str, source_file: str) -> List[Chunk]:
    """One chunk per Markdown `## ` section."""
    pieces = re.split(r"\n## ", text)
    return _to_chunks(pieces, source_file)


def chunk_by_paragraph(text: str, source_file: str,
                       chunk_size: int = CHUNK_SIZE_CHARS,
                       chunk_overlap: int = CHUNK_OVERLAP_CHARS) -> List[Chunk]:
    """Pack whole paragraphs into chunks of up to ~chunk_size characters.

    Paragraphs longer than chunk_size are split into overlapping windows;
    consecutive chunks share a small tail of text for context.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces = []
    buf = ""

    for para in paragraphs:
        if len(para) > chunk_size:
            if buf:
                pieces.append(buf)
                buf = ""
            start = 0
            while start < len(para):
                end = start + chunk_size
                pieces.append(para[start:end])
                if end >= len(para):
                    break
                start = end - chunk_overlap
            continue

        candidate = f"{buf}\n\n{para}" if buf else para
        if len(candidate) <= chunk_size:
            buf = candidate
        else:
            pieces.append(buf)
            tail = buf[-chunk_overlap:] if buf else ""
            buf = f"{tail}\n\n{para}".strip()

    if buf:
        pieces.append(buf)

    return _to_chunks(pieces, source_file)


# Default strategy used by ingest.py.
chunk_text = chunk_by_paragraph


if __name__ == "__main__":
    import sys

    strategies = {
        "paragraph": chunk_by_paragraph,
        "char": chunk_by_char,
        "sentence": chunk_by_sentence,
        "section": chunk_by_section,
    }

    args = sys.argv[1:]
    strategy_name = "paragraph"
    if args and args[0] in strategies:
        strategy_name = args[0]
        args = args[1:]

    if not args:
        print("Usage: python -m src.chunker [paragraph|char|sentence|section] <file1> [file2 ...]")
        sys.exit(1)

    chunk_fn = strategies[strategy_name]

    for path in args:
        with open(path, encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_fn(text, path)
        print(f"\n{path} [{strategy_name}]: {len(chunks)} chunks")
        for c in chunks:
            print(f"  {c.chunk_id}  ({len(c.text)} chars)")
