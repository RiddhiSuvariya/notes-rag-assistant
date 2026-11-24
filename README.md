# MiniGPT: Chat With Your Own Notes

MiniGPT is a small, local **retrieval-augmented generation (RAG)** assistant. Point it at a folder of notes (Markdown, text, CSV, or PDF) and it can:

- **Answer questions** using only your notes, with a citation after every claim
- **Summarize** everything your notes say about a topic
- **Quiz you** with multiple-choice questions generated from your notes
- **Plug into Claude** as an **MCP server**, so Claude Code or Claude Desktop can search your notes directly

Retrieval is **hybrid**: BM25 keyword search plus semantic embedding search, merged with Reciprocal Rank Fusion. Answers come from Claude through the [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI, so the project never handles an API key.

---

## Example

```text
$ python -m src.cli ask "How many casual leaves do employees get per year?"

Employees get **12 days of Casual Leave (CL) per year** [source: leave_policy.md, chunk 0].
This leave is credited at the start of the calendar year (January 1), cannot be carried
forward, and is not encashable [source: leave_policy.md, chunk 0].

[6 chunks used: leave_policy.md, salary_hike_policy.md]
```

---

## How it works

```text
 notes folder (.md .txt .csv .pdf)
            │
            ▼
   ingest.py ──► chunker.py           split into ~900-char overlapping chunks
            │
            ├──► bm25_index.py         keyword index  (index/bm25_index.pkl)
            ├──► embed_index.py        vector index   (index/embed_index.npz)
            └──► chunks.jsonl          chunk text + source file
                       │
   question ──► hybrid.py  BM25 + embeddings ──► Reciprocal Rank Fusion ──► top-k chunks
                       │
                       ▼
                rag.py ──► claude_client.py (claude -p) ──► cited answer
```

| Step | What happens |
|---|---|
| **Ingest** | Every supported file under `NOTES_DIR` is read. Each CSV row becomes a `column: value` block, and each PDF page is extracted as text. |
| **Chunk** | Paragraphs are packed into chunks of about 900 characters with 150 characters of overlap. Character, sentence, and section strategies are also included. |
| **Index** | A BM25 index catches exact terms such as names, IDs, and `15%`. A `all-MiniLM-L6-v2` embedding index catches meaning. |
| **Retrieve** | Both result lists are fused with RRF (`k = 60`). If the embedding index was skipped, BM25 alone is used. |
| **Answer** | Claude gets the question plus the retrieved chunks. Its system prompt tells it to use only those chunks and cite each claim. |

---

## Project structure

```text
.
├── src/
│   ├── cli.py            # Command-line entry point (index / ask / summarize / quiz)
│   ├── config.py         # Paths, chunk sizes, retrieval and model settings
│   ├── ingest.py         # File discovery and loaders for md / txt / csv / pdf
│   ├── chunker.py        # Chunking strategies (paragraph is the default)
│   ├── build_index.py    # Builds chunks.jsonl plus the BM25 and embedding indexes
│   ├── bm25_index.py     # Keyword search
│   ├── embed_index.py    # Semantic search (sentence-transformers)
│   ├── hybrid.py         # Reciprocal Rank Fusion of both searches
│   ├── rag.py            # Retrieval + grounded, cited answering
│   └── claude_client.py  # Wrapper around the `claude -p` CLI
├── subagent/
│   └── quiz_agent.py     # Separate quiz-generation prompt that returns JSON MCQs
├── mcp_server/
│   └── server.py         # MCP server: search_notes, ask_notes, list_indexed_files
├── skills/
│   └── notes-assistant/
│       └── SKILL.md      # Claude Code skill describing when and how to use the tools
├── sample_data/          # Demo notes for a fictional company (policies + CSVs)
├── index/                # Generated indexes (git-ignored)
└── requirements.txt
```

---

## Setup

### Prerequisites

- **Python 3.10+**
- **Claude Code CLI**, installed and logged in:
  ```bash
  npm install -g @anthropic-ai/claude-code
  claude        # log in once
  ```
  Check that `claude -p "hello"` works in your terminal before continuing.

### Install

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Usage

Run every command from the project root.

### 1. Build the index

```bash
python -m src.cli index
```

The first run downloads the embedding model (about 90 MB). To skip it and use keyword search only:

```bash
python -m src.cli index --no-embeddings
```

Re-run `index` whenever you add or change notes.

### 2. Ask a question

```bash
python -m src.cli ask "What is the hike multiplier for a rating of 5?"
python -m src.cli ask "Who is Sneha Patel's manager?" --top-k 8
```

### 3. Summarize a topic

```bash
python -m src.cli summarize "laptop and IT asset rules"
```

### 4. Quiz yourself

```bash
python -m src.cli quiz "leave policy" --n 5
```

### Use your own notes

By default the `sample_data/` folder is indexed. To index a different folder, set `NOTES_DIR`:

```bash
# Windows (PowerShell)
$env:NOTES_DIR = "D:\my-notes"
# macOS / Linux
export NOTES_DIR=~/my-notes

python -m src.cli index
```

---

## Use it from Claude (MCP server)

The MCP server exposes three tools:

| Tool | Description |
|---|---|
| `search_notes(query, top_k)` | Returns the raw matching chunks with source and score |
| `ask_notes(question, top_k)` | Returns a cited answer generated from your notes |
| `list_indexed_files()` | Lists the files currently in the index |

Build the index first, then register the server with Claude Code (run this from the project root):

```bash
claude mcp add notes-kb -- python mcp_server/server.py
```

For Claude Desktop, add this to `claude_desktop_config.json` and use absolute paths:

```json
{
  "mcpServers": {
    "notes-kb": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/mcp_server/server.py"]
    }
  }
}
```

The `skills/notes-assistant/SKILL.md` skill tells Claude when to reach for these tools, for example "quiz me on…" or "what do my notes say about…", and to always keep the citations.

---

## Configuration

Settings live in [`src/config.py`](src/config.py). Some of them can be overridden with environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `NOTES_DIR` | `sample_data/` | Folder to index |
| `CLAUDE_MODEL` | `sonnet` | Model alias passed to `claude -p --model` |
| `CLAUDE_TIMEOUT_SECS` | `120` | Timeout for each Claude call |
| `EMBED_MODEL_NAME` | `all-MiniLM-L6-v2` | sentence-transformers model |

To change chunk size, overlap, and the `top_k` values, edit `config.py` directly.

To compare chunking strategies on a file:

```bash
python -m src.chunker sentence sample_data/leave_policy.md
python -m src.chunker section  sample_data/leave_policy.md
```

---

## Sample data

`sample_data/` holds made-up HR documents for a **fictional company, "Nexora Technologies"**: leave, IT asset, and salary-hike policies, plus an employee directory and hike records as CSV. All names and numbers are invented for the demo. Replace them with your own notes.

---

## Tech stack

- [rank-bm25](https://github.com/dorianbrown/rank_bm25): keyword retrieval
- [sentence-transformers](https://www.sbert.net/): semantic embeddings
- [pypdf](https://pypdf.readthedocs.io/): PDF text extraction
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk): MCP server
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI: answer generation
