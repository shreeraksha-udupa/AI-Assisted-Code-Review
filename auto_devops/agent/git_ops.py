import subprocess
import shutil
import os


def create_branch(repo_path: str, branch_name: str) -> bool:
    """Create a new Git branch for the fix."""
    try:
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=repo_path, check=True, capture_output=True
        )
        print(f"[git] Created branch: {branch_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[git] Branch creation failed: {e.stderr.decode()}")
        return False


def apply_fix(repo_path: str, file_path: str, original_code: str, fixed_code: str) -> bool:
    """
    Overwrite a file with the fixed code.
    Backs up the original first.
    """
    full_path = os.path.join(repo_path, file_path)
    backup_path = full_path + ".bak"

    try:
        shutil.copy(full_path, backup_path)
        with open(full_path, "w") as f:
            f.write(fixed_code)
        print(f"[git] Applied fix to {file_path}")
        return True
    except Exception as e:
        print(f"[git] Could not apply fix: {e}")
        return False


def get_file_content(repo_path: str, file_path: str) -> str:
    full_path = os.path.join(repo_path, file_path)
    with open(full_path, "r", errors="replace") as f:
        return f.read()
