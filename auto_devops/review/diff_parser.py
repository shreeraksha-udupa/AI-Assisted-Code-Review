def parse_diff(diff_text: str) -> list:
    """
    Parse a unified diff into a structured list of changed hunks.
    Each hunk: { file, added_lines, removed_lines, raw_hunk }
    """
    hunks = []
    current_file = None
    added, removed = [], []
    raw_lines = []

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            if current_file and (added or removed):
                hunks.append({
                    "file": current_file,
                    "added_lines": added,
                    "removed_lines": removed,
                    "raw_hunk": "\n".join(raw_lines)
                })
            current_file = line[6:]
            added, removed, raw_lines = [], [], []

        elif line.startswith("@@"):
            raw_lines.append(line)

        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
            raw_lines.append(line)

        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
            raw_lines.append(line)

        else:
            raw_lines.append(line)

    if current_file and (added or removed):
        hunks.append({
            "file": current_file,
            "added_lines": added,
            "removed_lines": removed,
            "raw_hunk": "\n".join(raw_lines)
        })

    return hunks


def summarize_diff(hunks: list) -> str:
    """Return a human-readable summary of what changed."""
    lines = []
    for h in hunks:
        lines.append(
            f"File: {h['file']} | +{len(h['added_lines'])} lines / -{len(h['removed_lines'])} lines"
        )
    return "\n".join(lines) if lines else "No changes detected."
