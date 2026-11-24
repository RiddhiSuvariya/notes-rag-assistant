"""BM25 keyword index: build, persist, load, and search."""

from __future__ import annotations

import pickle
import re
from pathlib import Path
from typing import List, Tuple

from rank_bm25 import BM25Okapi

from src.chunker import Chunk
from src.config import BM25_INDEX_PATH

_TOKEN_RE = re.compile(r"[a-zA-Z0-9%]+")


def tokenize(text: str) -> List[str]:
    """Lowercase alphanumeric tokenizer (keeps `%` so '15%' stays searchable)."""
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def build_bm25_index(chunks: List[Chunk], save_path: Path = BM25_INDEX_PATH) -> BM25Okapi:
    """Build a BM25 index over the chunks and pickle it to disk."""
    tokenized_corpus = [tokenize(c.text) for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    with open(save_path, "wb") as f:
        pickle.dump({"bm25": bm25, "chunk_ids": [c.chunk_id for c in chunks]}, f)
    return bm25


def load_bm25_index(save_path: Path = BM25_INDEX_PATH):
    """Load the pickled BM25 index. Only load files this project created."""
    if not save_path.exists():
        raise FileNotFoundError(
            f"BM25 index not found at {save_path}. Run `python -m src.cli index` first."
        )
    with open(save_path, "rb") as f:
        data = pickle.load(f)
    return data["bm25"], data["chunk_ids"]


def search_bm25(query: str, top_k: int, save_path: Path = BM25_INDEX_PATH) -> List[Tuple[str, float]]:
    """Return the top_k (chunk_id, score) pairs for the query."""
    bm25, chunk_ids = load_bm25_index(save_path)
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(zip(chunk_ids, scores), key=lambda x: x[1], reverse=True)
    return ranked[:top_k]
