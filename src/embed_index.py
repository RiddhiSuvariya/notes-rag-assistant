"""Dense embedding index using sentence-transformers, stored as a .npz file."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np

from src.chunker import Chunk
from src.config import EMBED_INDEX_PATH, EMBED_MODEL_NAME

_model = None


def get_model():
    """Lazily load the embedding model (downloaded on first use)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def build_embed_index(chunks: List[Chunk], save_path: Path = EMBED_INDEX_PATH) -> np.ndarray:
    """Embed every chunk and save the normalized vectors with their chunk ids."""
    model = get_model()
    texts = [c.text for c in chunks]
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    vectors = np.asarray(vectors, dtype=np.float32)
    chunk_ids = np.array([c.chunk_id for c in chunks])
    np.savez(save_path, vectors=vectors, chunk_ids=chunk_ids)
    return vectors


def load_embed_index(save_path: Path = EMBED_INDEX_PATH):
    """Load vectors and chunk ids from disk."""
    data = np.load(save_path, allow_pickle=False)
    return data["vectors"], data["chunk_ids"]


def search_embed(query: str, top_k: int, save_path: Path = EMBED_INDEX_PATH) -> List[Tuple[str, float]]:
    """Return the top_k (chunk_id, cosine similarity) pairs for the query."""
    vectors, chunk_ids = load_embed_index(save_path)
    model = get_model()
    q_vec = model.encode([query], normalize_embeddings=True)[0].astype(np.float32)
    # Vectors are L2-normalized, so the dot product equals cosine similarity.
    sims = vectors @ q_vec
    top_idx = np.argsort(-sims)[:top_k]
    return [(str(chunk_ids[i]), float(sims[i])) for i in top_idx]
