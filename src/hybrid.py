"""Hybrid retrieval: BM25 keyword search + embedding search, merged with RRF."""

from __future__ import annotations

from typing import Dict, List, Tuple

from src.bm25_index import search_bm25
from src.config import EMBED_INDEX_PATH, RRF_K, TOP_K_BM25, TOP_K_EMBED, TOP_K_FINAL


def reciprocal_rank_fusion(
    ranked_lists: List[List[Tuple[str, float]]], k: int = RRF_K
) -> List[Tuple[str, float]]:
    """Merge ranked lists by summing 1 / (k + rank) for every list a chunk appears in."""
    fused: Dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, (chunk_id, _score) in enumerate(ranked):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


def hybrid_search(query: str, top_k: int = TOP_K_FINAL) -> List[Tuple[str, float]]:
    """Return the top chunk ids for a query.

    Falls back to BM25 only when the embedding index was not built
    (e.g. after `index --no-embeddings`).
    """
    ranked_lists = [search_bm25(query, top_k=TOP_K_BM25)]

    if EMBED_INDEX_PATH.exists():
        from src.embed_index import search_embed

        ranked_lists.append(search_embed(query, top_k=TOP_K_EMBED))

    fused = reciprocal_rank_fusion(ranked_lists)
    return fused[:top_k]
