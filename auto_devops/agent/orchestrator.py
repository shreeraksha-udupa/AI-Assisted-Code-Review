from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from review.diff_parser import parse_diff, summarize_diff
from review.reviewer import review_diff
from agent.git_ops import create_branch, apply_fix, get_file_content
from tests.test_runner import run_tests
from retrieval.retriever import retrieve_context

console = Console()


def run_agent(diff_text: str, repo_path: str, collection=None) -> dict:
    """
    The 8-step agentic orchestrator.
    Returns a final decision dict with all artifacts.
    """
    state = {
        "diff": diff_text,
        "hunks": [],
        "context_chunks": [],
        "review": {},
        "branch_created": False,
        "fix_applied": False,
        "tests_passed": False,
        "test_output": "",
        "decision": "rejected",
        "explanation": ""
    }

    # ─────────────────────────────────────────────
    # STEP 1: Analyze code changes
    # ─────────────────────────────────────────────
    console.rule("[bold]Step 1 — Analyzing code changes")
    state["hunks"] = parse_diff(diff_text)
    summary = summarize_diff(state["hunks"])
    console.print(Panel(summary, title="Diff summary"))

    if not state["hunks"]:
        console.print("[yellow]No code changes found in diff. Aborting.[/yellow]")
        state["explanation"] = "No diff to review."
        return state

    # ─────────────────────────────────────────────
    # STEP 2: Retrieve repo-wide context (RAG)
    # ─────────────────────────────────────────────
    console.rule("[bold]Step 2 — Retrieving repository context (RAG)")
    rag_query = "\n".join([
        line for h in state["hunks"] for line in h["added_lines"]
    ])[:600]

    state["context_chunks"] = retrieve_context(rag_query, collection=collection)
    console.print(f"Retrieved {len(state['context_chunks'])} relevant chunks")
    for c in state["context_chunks"]:
        console.print(
            f"  → {c['path']} (lines {c['start_line']}–{c['end_line']}) "
            f"relevance={c['relevance_score']}"
        )

    # ─────────────────────────────────────────────
    # STEP 3: Reason about cross-file impact
    # ─────────────────────────────────────────────
    console.rule("[bold]Step 3 — Cross-file reasoning")
    files_in_context = {c["path"] for c in state["context_chunks"]}
    console.print(f"Context spans {len(files_in_context)} files: {', '.join(files_in_context)}")

    # ─────────────────────────────────────────────
    # STEP 4: Generate fix via LLM
    # ─────────────────────────────────────────────
    console.rule("[bold]Step 4 — Generating review and fix (LLM)")
    state["review"] = review_diff(diff_text, collection=collection)

    _print_review_table(state["review"])

    if not state["review"].get("issues"):
        console.print("[green]✓ No issues found. Code looks good.[/green]")
        state["decision"] = "accepted"
        state["explanation"] = state["review"].get("summary", "No issues detected.")
        return state

    critical_issues = [
        i for i in state["review"]["issues"]
        if i["severity"] in ("critical", "high")
    ]
    if not critical_issues:
        console.print("[yellow]Only low/medium issues found — no auto-fix needed.[/yellow]")
        state["decision"] = "accepted_with_warnings"
        state["explanation"] = state["review"].get("summary", "Minor issues only.")
        return state

    first_issue = critical_issues[0]
    target_file = first_issue.get("file", "")

    # ─────────────────────────────────────────────
    # STEP 5: Create a new branch
    # ─────────────────────────────────────────────
    console.rule("[bold]Step 5 — Creating fix branch")
    branch_name = "autofix/code-review-agent"
    state["branch_created"] = create_branch(repo_path, branch_name)

    # ─────────────────────────────────────────────
    # STEP 6: Apply the fix
    # ─────────────────────────────────────────────
    console.rule("[bold]Step 6 — Applying fix")
    if target_file and state["branch_created"]:
        try:
            original = get_file_content(repo_path, target_file)
            fixed = first_issue.get("suggested_fix", "")
            if fixed:
                state["fix_applied"] = apply_fix(repo_path, target_file, original, fixed)
            else:
                console.print("[yellow]No suggested_fix provided by LLM.[/yellow]")
        except Exception as e:
            console.print(f"[red]Fix application failed: {e}[/red]")
    else:
        console.print("[yellow]Skipping fix — no target file or branch creation failed.[/yellow]")

    # ─────────────────────────────────────────────
    # STEP 7: Run tests
    # ─────────────────────────────────────────────
    console.rule("[bold]Step 7 — Running tests")
    test_result = run_tests(repo_path)
    state["tests_passed"] = test_result["passed"]
    state["test_output"] = test_result["output"]

    if test_result["simulated"]:
        console.print("[yellow]⚠ Tests simulated (no test framework detected)[/yellow]")
    elif test_result["passed"]:
        console.print("[green]✓ Tests passed[/green]")
    else:
        console.print("[red]✗ Tests failed[/red]")
        console.print(test_result["output"][:500])

    # ─────────────────────────────────────────────
    # STEP 8: Final decision
    # ─────────────────────────────────────────────
    console.rule("[bold]Step 8 — Final decision")

    if state["tests_passed"] and state["fix_applied"]:
        state["decision"] = "fix_accepted"
        state["explanation"] = (
            f"Fix applied to '{target_file}' on branch '{branch_name}'. "
            f"Tests {'simulated' if test_result['simulated'] else 'passed'}. "
            f"Issue: {first_issue['explanation']}"
        )
    elif state["tests_passed"] and not state["fix_applied"]:
        state["decision"] = "review_only"
        state["explanation"] = "Issues found and reported. Manual fix recommended."
    else:
        state["decision"] = "fix_rejected"
        state["explanation"] = (
            "Fix was applied but tests failed. Branch preserved for manual review."
        )

    border = "green" if "accepted" in state["decision"] else "red"
    console.print(Panel(
        f"[bold]Decision:[/bold] {state['decision'].upper()}\n"
        f"[bold]Reason:[/bold] {state['explanation']}",
        title="Agent Final Decision",
        border_style=border
    ))

    return state


def _print_review_table(review: dict):
    if not review.get("issues"):
        return

    table = Table(title="Issues Found", show_lines=True)
    table.add_column("Type",       style="cyan", width=12)
    table.add_column("Severity",   width=10)
    table.add_column("File",       width=22)
    table.add_column("Explanation", width=40)

    severity_colors = {
        "critical": "bold red",
        "high":     "red",
        "medium":   "yellow",
        "low":      "dim"
    }

    for issue in review.get("issues", []):
        sev = issue.get("severity", "low")
        table.add_row(
            issue.get("issue_type", ""),
            f"[{severity_colors.get(sev, '')}]{sev}[/]",
            issue.get("file", ""),
            issue.get("explanation", "")[:80]
        )

    console.print(table)
    console.print(f"\n[bold]Overall risk:[/bold] {review.get('overall_risk', 'unknown')}")
    console.print(f"[bold]Summary:[/bold] {review.get('summary', '')}")
