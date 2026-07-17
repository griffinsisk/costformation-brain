import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "evals" / "harness_run.py"


def test_harness_golden_cases_pass():
    result = subprocess.run(
        [sys.executable, str(RUNNER)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "2/2 passed" in result.stdout
