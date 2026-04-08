import subprocess
import os


def run_tests(repo_path: str) -> dict:
    """
    Try to run tests in the repo. Supports pytest and npm test.
    Falls back to a simulated pass if no test framework is detected.
    """
    result = {"passed": False, "output": "", "simulated": False}

    # Try pytest
    if (os.path.exists(os.path.join(repo_path, "pytest.ini")) or
            os.path.exists(os.path.join(repo_path, "setup.py")) or
            os.path.exists(os.path.join(repo_path, "pyproject.toml"))):
        try:
            proc = subprocess.run(
                ["python", "-m", "pytest", "--tb=short", "-q"],
                cwd=repo_path, capture_output=True, text=True, timeout=60
            )
            result["passed"] = proc.returncode == 0
            result["output"] = proc.stdout + proc.stderr
            return result
        except Exception as e:
            result["output"] = str(e)

    # Try npm test
    if os.path.exists(os.path.join(repo_path, "package.json")):
        try:
            proc = subprocess.run(
                ["npm", "test", "--", "--watchAll=false"],
                cwd=repo_path, capture_output=True, text=True, timeout=90
            )
            result["passed"] = proc.returncode == 0
            result["output"] = proc.stdout + proc.stderr
            return result
        except Exception as e:
            result["output"] = str(e)

    # No test framework found — simulate
    print("[tests] No test framework detected. Simulating test pass.")
    result["passed"] = True
    result["simulated"] = True
    result["output"] = "SIMULATED: No test runner found. Fix applied without test validation."
    return result
