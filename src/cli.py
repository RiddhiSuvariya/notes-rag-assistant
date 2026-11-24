"""Command-line interface.

Usage (from the project root):
    python -m src.cli index [--no-embeddings]
    python -m src.cli ask "question"
    python -m src.cli summarize "topic"
    python -m src.cli quiz "topic" --n 5
"""

from __future__ import annotations

import argparse
import sys

from src.build_index import run_indexing
from src.claude_client import ClaudeCLIError
from src.rag import answer


def cmd_index(args):
    run_indexing(skip_embeddings=args.no_embeddings)


def cmd_ask(args):
    result = answer(args.query, top_k=args.top_k)
    print("\n" + result["answer"] + "\n")
    print(f"[{len(result['chunks_used'])} chunks used: "
          f"{', '.join(sorted(set(c['source_file'] for c in result['chunks_used'])))}]")


def cmd_summarize(args):
    query = f"Summarize everything in my notes about: {args.topic}"
    result = answer(query, top_k=args.top_k)
    print("\n" + result["answer"] + "\n")


def cmd_quiz(args):
    from src.rag import build_context_block, retrieve
    from subagent.quiz_agent import generate_quiz

    chunks = retrieve(args.topic, top_k=args.top_k)
    if not chunks:
        print("No relevant notes found for that topic. Run `index` first, "
              "or try a broader topic.")
        return
    context_block = build_context_block(chunks)
    quiz = generate_quiz(topic=args.topic, context_block=context_block, n=args.n)
    for i, q in enumerate(quiz, 1):
        print(f"\nQ{i}. {q.get('question', '')}")
        for opt_letter, opt_text in q.get("options", {}).items():
            print(f"   {opt_letter}) {opt_text}")
        print(f"   Answer: {q.get('answer', '?')}")
        print(f"   Why: {q.get('explanation', '')}")


def main():
    parser = argparse.ArgumentParser(
        prog="minigpt",
        description="Ask questions, summarize, and quiz yourself on your own notes.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_index = sub.add_parser("index", help="Build/rebuild BM25 + embedding indexes")
    p_index.add_argument("--no-embeddings", action="store_true",
                          help="Skip embedding index (BM25 only, no model download)")
    p_index.set_defaults(func=cmd_index)

    p_ask = sub.add_parser("ask", help="Ask a cited question against your notes")
    p_ask.add_argument("query")
    p_ask.add_argument("--top-k", type=int, default=6)
    p_ask.set_defaults(func=cmd_ask)

    p_sum = sub.add_parser("summarize", help="Summarize a topic from your notes")
    p_sum.add_argument("topic")
    p_sum.add_argument("--top-k", type=int, default=8)
    p_sum.set_defaults(func=cmd_summarize)

    p_quiz = sub.add_parser("quiz", help="Generate quiz questions from your notes")
    p_quiz.add_argument("topic")
    p_quiz.add_argument("--n", type=int, default=5, help="Number of questions")
    p_quiz.add_argument("--top-k", type=int, default=8)
    p_quiz.set_defaults(func=cmd_quiz)

    args = parser.parse_args()
    try:
        args.func(args)
    except (FileNotFoundError, ClaudeCLIError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
