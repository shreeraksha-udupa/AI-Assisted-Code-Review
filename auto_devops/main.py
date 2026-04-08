#!/usr/bin/env python3
"""
Auto-DevOps: Self-Healing Code Reviewer  (Groq Edition)
=========================================================
Usage:
  # First-time setup (clone repo + build vector DB):
  python main.py --repo https://github.com/pallets/flask --ingest

  # Review a diff file:
  python main.py --diff path/to/changes.diff

  # Full run (ingest + review):
  python main.py --repo https://github.com/yourorg/repo --ingest --diff pr_42.diff
"""

import argparse
import sys
from rich.console import Console

from ingestion.repo_cloner import clone_or_load
from ingestion.chunker import chunk_all_files
from ingestion.embedder import embed_and_store
from retrieval.retriever import get_collection
from agent.orchestrator import run_agent
from output.reporter import generate_report
from config.settings import GROQ_API_KEY

console = Console()

# Built-in sample diff for demo / testing (SQL injection + token leak)
SAMPLE_DIFF = """--- a/app/auth.py
+++ b/app/auth.py
@@ -12,7 +12,7 @@ import db

 def login(username, password):
-    query = "SELECT * FROM users WHERE username=? AND password=?"
-    result = db.execute(query, (username, password))
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    result = db.execute(query)
     if result:
         return generate_token(result[0])
     return None
"""


def main():
    parser = argparse.ArgumentParser(
        description="Auto-DevOps Self-Healing Code Reviewer (Groq Edition)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--repo", default="https://github.com/pallets/flask",
        help="GitHub repo URL to clone and index"
    )
    parser.add_argument(
        "--dest", default="./repo",
        help="Local path to clone the repo into"
    )
    parser.add_argument(
        "--diff", default=None,
        help="Path to a unified .diff file to review"
    )
    parser.add_argument(
        "--ingest", action="store_true",
        help="Clone repo and build ChromaDB vector store (required on first run)"
    )
    parser.add_argument(
        "--report", default="./review_report.json",
        help="Output path for the JSON review report"
    )
    args = parser.parse_args()

    console.print("\n[bold cyan]━━━ Auto-DevOps: Self-Healing Code Reviewer (Groq) ━━━[/bold cyan]\n")

    # Validate API key early
    if not GROQ_API_KEY:
        console.print(
            "[red]GROQ_API_KEY not set.[/red]\n"
            "  1. Copy .env.example to .env\n"
            "  2. Add your key from https://console.groq.com"
        )
        sys.exit(1)

    # ── Phase 1: Ingestion (RAG setup) ───────────────────────────
    if args.ingest:
        console.print("[bold]Phase 1: Repository Ingestion (RAG)[/bold]")
        files = clone_or_load(args.repo, args.dest)
        chunks = chunk_all_files(files)
        collection = embed_and_store(chunks)
        console.print("[green]✓ Ingestion complete[/green]\n")
    else:
        console.print("[dim]Skipping ingestion — using existing ChromaDB[/dim]")
        try:
            collection = get_collection()
        except Exception:
            console.print(
                "[red]No ChromaDB found. Run with --ingest first.[/red]\n"
                "  Example: python main.py --repo https://github.com/pallets/flask --ingest"
            )
            sys.exit(1)

    # ── Phase 2: Load diff ───────────────────────────────────────
    if args.diff:
        console.print(f"[bold]Loading diff from:[/bold] {args.diff}")
        with open(args.diff, "r") as f:
            diff_text = f.read()
    else:
        console.print(
            "[yellow]No --diff provided. Using built-in sample diff "
            "(SQL injection vulnerability).[/yellow]\n"
        )
        diff_text = SAMPLE_DIFF

    # ── Phase 3: Run agentic pipeline ────────────────────────────
    console.print("\n[bold]Phase 2: Agentic Review Pipeline[/bold]\n")
    state = run_agent(diff_text, repo_path=args.dest, collection=collection)

    # ── Phase 4: Save report ─────────────────────────────────────
    console.print("\n[bold]Phase 3: Saving Report[/bold]")
    generate_report(state, output_path=args.report)

    console.print(f"\n[bold green]Done.[/bold green] Report saved to: {args.report}\n")


if __name__ == "__main__":
    main()
