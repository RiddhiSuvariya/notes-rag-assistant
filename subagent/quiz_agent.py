"""Quiz subagent: turns retrieved note chunks into multiple-choice questions."""

from __future__ import annotations

from typing import List

from src.claude_client import chat, extract_json

QUIZ_SYSTEM_PROMPT = """You are a quiz-generation subagent for a spaced
repetition tool. You will be given a topic and chunks retrieved from the
user's own notes. Generate multiple-choice quiz questions strictly based
on that content.

Output ONLY a JSON array (no markdown fences, no preamble, no commentary).
Each element must have exactly this shape:
{
  "question": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "answer": "A",
  "explanation": "one sentence, grounded in the provided notes"
}

Rules:
- Base every question only on the provided chunks, not outside knowledge.
- Make distractors plausible, not silly, so the quiz is actually useful.
- Vary which option letter is correct across questions.
- If the chunks don't support the requested number of distinct questions,
  return fewer rather than inventing content.
"""


def generate_quiz(topic: str, context_block: str, n: int = 5) -> List[dict]:
    """Ask Claude for up to n questions grounded in context_block."""
    prompt = (
        f"Topic: {topic}\n"
        f"Number of questions requested: {n}\n\n"
        f"Notes:\n\n{context_block}"
    )
    raw = chat(prompt, system_prompt=QUIZ_SYSTEM_PROMPT)
    parsed = extract_json(raw)
    if isinstance(parsed, dict):
        parsed = [parsed]
    return parsed[:n]
