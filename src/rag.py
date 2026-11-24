"""Retrieval-augmented answering: retrieve chunks, then ask Claude to answer with citations."""

from __future__ import annotations

import json
from typing import Dict, List

from src.claude_client import chat
from src.config import CHUNKS_PATH
from src.hybrid import hybrid_search

RAG_SYSTEM_PROMPT = """You are a note-answering assistant. You will be given
a user question and a set of retrieved chunks from the user's own notes,
each tagged with a source file and chunk id.

Rules:
1. Answer ONLY using the information in the retrieved chunks. Do not use
   outside/general knowledge, even if you know more about the topic.
2. If the chunks do not contain enough information to answer, say so
   explicitly instead of guessing.
3. After every claim, cite the source in square brackets like
   [source: filename.md, chunk 2].
4. Keep the answer concise and directly responsive to the question.
5. If chunks disagree with each other, point out the conflict and cite both.
"""


def _load_chunk_lookup() -> Dict[str, dict]:
    """Load a chunk_id -> chunk record lookup from the persisted chunks file."""
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"No index found at {CHUNKS_PATH}. Run `python -m src.cli index` first."
        )
    lookup = {}
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            lookup[obj["chunk_id"]] = obj
    return lookup


def retrieve(query: str, top_k: int = 6) -> List[dict]:
    """Return the top_k chunk records (with a fused `score`) for the query."""
    hits = hybrid_search(query, top_k=top_k)
    lookup = _load_chunk_lookup()
    results = []
    for chunk_id, score in hits:
        obj = lookup.get(chunk_id)
        if obj:
            results.append({**obj, "score": score})
    return results


def build_context_block(chunks: List[dict]) -> str:
    """Format chunks with their source labels for the prompt."""
    parts = []
    for c in chunks:
        parts.append(
            f"--- source: {c['source_file']} | chunk_id: {c['chunk_id']} ---\n{c['text']}"
        )
    return "\n\n".join(parts)


def answer(query: str, top_k: int = 6) -> dict:
    """Answer a question from the notes. Returns {"answer": str, "chunks_used": [...]}."""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        raise RuntimeError(
            "No indexed chunks found. Run `python -m src.cli index` first."
        )

    context_block = build_context_block(chunks)
    prompt = (
        f"Question: {query}\n\n"
        f"Retrieved chunks from the user's notes:\n\n{context_block}"
    )
    response_text = chat(prompt, system_prompt=RAG_SYSTEM_PROMPT)
    return {"answer": response_text, "chunks_used": chunks}
