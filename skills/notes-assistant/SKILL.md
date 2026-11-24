---
name: notes-assistant
description: Use when the user asks to summarize, quiz, search, or answer questions from their personal notes/course material (e.g. "summarize what I learned about X", "quiz me on Y", "what do my notes say about Z"). Do NOT use for general knowledge questions unrelated to the user's indexed notes folder.
---

# Notes Assistant Skill

This skill governs how to answer questions using the user's personal
knowledge base (indexed notes in `NOTES_DIR`, searchable via the
`notes-kb` MCP server or the CLI in `src/cli.py`).

## When to use this skill

Trigger on requests like:
- "summarize what I learned about MCP servers"
- "quiz me on tokenization"
- "what does my course material say about prefilling"
- "search my notes for X"

Do not trigger on general knowledge questions the user isn't asking
against their own notes (e.g. "what is tokenization" with no reference to
notes/course material) -- answer those directly instead.

## How to answer

1. Prefer the `ask_notes` or `search_notes` MCP tools if the `notes-kb`
   MCP server is connected. Otherwise fall back to:
   `python -m src.cli ask "<question>"` from the project root.
2. Never answer from general/model knowledge when the user is asking
   about their notes specifically -- always retrieve first.
3. Always preserve and surface the source file citations returned by the
   tool/CLI. Do not strip them out for brevity.
4. If retrieval returns no relevant chunks, say so plainly and suggest the
   user re-check `NOTES_DIR` or re-run indexing, rather than guessing.

## Summarize requests

Use `ask_notes("Summarize everything about <topic>")` or
`python -m src.cli summarize "<topic>"`. Keep the summary structured
(headers or bullets) if the source material spans multiple files.

## Quiz requests

Use `python -m src.cli quiz "<topic>" --n <count>` (default 5 questions).
This routes to the dedicated quiz subagent (`subagent/quiz_agent.py`),
which is a separate persona from the main Q&A path -- don't try to
generate quiz questions yourself from raw search results; call the
subagent so answer/distractor quality stays consistent.

## Re-indexing

If the user has added new files to `NOTES_DIR` and asks a question that
should be answerable but isn't, suggest running:
`python -m src.cli index`
before retrying the query.
