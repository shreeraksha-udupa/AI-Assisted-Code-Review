import os
import git
from pathlib import Path
from config.settings import SUPPORTED_EXTENSIONS


def clone_or_load(repo_url: str, dest: str = "./repo") -> list:
    """Clone a GitHub repo (or reuse if already cloned) and return a list of file records."""
    if not os.path.exists(dest):
        print(f"[ingestion] Cloning {repo_url} → {dest}")
        git.Repo.clone_from(repo_url, dest)
    else:
        print(f"[ingestion] Reusing existing repo at {dest}")

    files = []
    for path in Path(dest).rglob("*"):
        if path.is_file() and path.suffix in SUPPORTED_EXTENSIONS:
            try:
                content = path.read_text(errors="replace")
                files.append({
                    "path": str(path.relative_to(dest)),
                    "content": content,
                    "language": path.suffix.lstrip(".")
                })
            except Exception as e:
                print(f"  [warn] Could not read {path}: {e}")

    print(f"[ingestion] Found {len(files)} source files")
    return files
