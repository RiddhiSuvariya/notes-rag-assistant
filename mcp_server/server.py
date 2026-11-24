"""MCP server exposing the notes knowledge base as tools (search, ask, list files).

Run from the project root:  python mcp_server/server.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as `python mcp_server/server.py` from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from src.config import CHUNKS_PATH  # noqa: E402
from src.rag import answer as rag_answer, retrieve  # noqa: E402

mcp = FastMCP("notes-kb")


@mcp.tool()
def search_notes(query: str, top_k: int = 6) -> str:
    """Search the indexed notes and return the most relevant raw chunks with their sources."""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return "No matching chunks found. Has the index been built yet?"
    formatted = []
    for c in chunks:
        formatted.append(
            f"[{c['source_file']} | {c['chunk_id']} | score={c['score']:.3f}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(formatted)


@mcp.tool()
def ask_notes(question: str, top_k: int = 6) -> str:
    """Answer a question using only the indexed notes, with source citations."""
    result = rag_answer(question, top_k=top_k)
    sources = sorted(set(c["source_file"] for c in result["chunks_used"]))
    return f"{result['answer']}\n\nSources: {', '.join(sources)}"


@mcp.tool()
def list_indexed_files() -> str:
    """List the source files currently in the index."""
    if not CHUNKS_PATH.exists():
        return "No index built yet. Run `python -m src.cli index` first."
    files = set()
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            files.add(json.loads(line)["source_file"])
    return "\n".join(sorted(files)) if files else "Index is empty."


if __name__ == "__main__":
    mcp.run()
