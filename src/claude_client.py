"""Thin wrapper around the Claude Code CLI (`claude -p`) used as the LLM backend.

Using the CLI means no API key handling in this project: whatever account
the local `claude` command is logged in with is used.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess

from src.config import CLAUDE_MODEL, CLAUDE_TIMEOUT_SECS


class ClaudeCLIError(RuntimeError):
    """Raised when the Claude CLI is missing, fails, or returns unusable output."""


def _claude_executable() -> str:
    # shutil.which also resolves `claude.cmd` on Windows.
    exe = shutil.which("claude")
    if not exe:
        raise ClaudeCLIError(
            "The `claude` CLI was not found on PATH. Install Claude Code "
            "(npm install -g @anthropic-ai/claude-code) and log in first."
        )
    return exe


def chat(prompt: str, system_prompt: str | None = None, model: str = CLAUDE_MODEL) -> str:
    """Send a single prompt to Claude and return the text reply."""
    cmd = [_claude_executable(), "-p", "--model", model, "--output-format", "json"]
    if system_prompt:
        # Collapse whitespace so the prompt passes cleanly as one argument.
        cmd += ["--append-system-prompt", " ".join(system_prompt.split())]

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=CLAUDE_TIMEOUT_SECS,
        )
    except subprocess.TimeoutExpired as e:
        raise ClaudeCLIError(f"claude CLI timed out after {CLAUDE_TIMEOUT_SECS}s") from e

    if result.returncode != 0:
        raise ClaudeCLIError(
            f"claude CLI exited {result.returncode}: {result.stderr.strip()}"
        )

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise ClaudeCLIError(
            f"Could not parse CLI JSON output: {e}\nRaw: {result.stdout[:500]}"
        ) from e

    # `claude -p --output-format json` wraps the reply under "result".
    text = payload.get("result") or payload.get("response") or ""
    if not text:
        raise ClaudeCLIError(f"Empty response in CLI payload: {payload}")
    return text


def extract_json(text: str):
    """Pull the first JSON object or array out of a model reply."""
    match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in response: {text[:300]}")
    return json.loads(match.group(0))
