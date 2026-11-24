"""Indexing pipeline: read notes -> chunk -> write chunks.jsonl, BM25, and embeddings."""

from __future__ import annotations

import json
from pathlib import Path

from src.bm25_index import build_bm25_index
from src.config import CHUNKS_PATH, EMBED_INDEX_PATH, NOTES_DIR
from src.ingest import build_all_chunks


def run_indexing(notes_dir: Path = NOTES_DIR, skip_embeddings: bool = False) -> int:
    """Rebuild every index from scratch. Returns the number of chunks indexed."""
    print(f"[index] scanning {notes_dir} ...")
    chunks = build_all_chunks(notes_dir)
    print(f"[index] {len(chunks)} chunks from source files")

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({
                "chunk_id": c.chunk_id,
                "source_file": c.source_file,
                "text": c.text,
                "position": c.position,
            }) + "\n")

    print("[index] building BM25 keyword index ...")
    build_bm25_index(chunks)

    if skip_embeddings:
        # Remove any old embedding index so search does not mix stale chunk ids.
        EMBED_INDEX_PATH.unlink(missing_ok=True)
        print("[index] skipping embedding index (--no-embeddings)")
    else:
        from src.embed_index import build_embed_index

        print("[index] building embedding index (downloads model on first run) ...")
        build_embed_index(chunks)

    print("[index] done.")
    return len(chunks)


if __name__ == "__main__":
    run_indexing()
