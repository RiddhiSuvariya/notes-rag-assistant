"""Central configuration: paths, chunking, retrieval, and model settings.

Most values can be overridden with environment variables so the project
can point at any notes folder without editing code.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Folder that gets indexed. Override with the NOTES_DIR environment variable.
NOTES_DIR = Path(os.environ.get("NOTES_DIR", PROJECT_ROOT / "sample_data"))

# Where indexes are cached on disk.
INDEX_DIR = PROJECT_ROOT / "index"
BM25_INDEX_PATH = INDEX_DIR / "bm25_index.pkl"
EMBED_INDEX_PATH = INDEX_DIR / "embed_index.npz"
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"

# Chunking
CHUNK_SIZE_CHARS = 900
CHUNK_OVERLAP_CHARS = 150

# Retrieval
TOP_K_BM25 = 8
TOP_K_EMBED = 8
TOP_K_FINAL = 6
RRF_K = 60  # reciprocal rank fusion constant

# Embedding model (downloaded on first run, needs internet access once)
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")

# Claude Code CLI settings (`claude -p --model <alias>`)
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "sonnet")
CLAUDE_TIMEOUT_SECS = int(os.environ.get("CLAUDE_TIMEOUT_SECS", "120"))

INDEX_DIR.mkdir(parents=True, exist_ok=True)
