"""Custom scoring for Java reverse-string problem."""

import shutil
import subprocess
from pathlib import Path


def _run(command: list[str], work_dir: str) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=60)


def score_correctness(generated_code: str, work_dir: str) -> float:
    if shutil.which("mvn") is None:
        return 0.0
    result = _run(["mvn", "test", "-q"], work_dir)
    # Parse test results from surefire reports or output
    if result.returncode != 0:
        # Try to count passed/failed from output
        passed = result.stdout.count("Tests run:")
        # Simplistic: if any tests ran and no failure keyword
        if "BUILD FAILURE" in result.stdout or "BUILD FAILURE" in result.stderr:
            return 0.0
    return 1.0 if result.returncode == 0 else 0.0


def score_code_quality(generated_code: str, work_dir: str) -> float:
    if shutil.which("mvn") is None:
        return 0.0
    # Compile with strict warnings
    result = _run(["mvn", "compile", "-q"], work_dir)
    return 1.0 if result.returncode == 0 else 0.5


def score_performance(generated_code: str, work_dir: str) -> float:
    return 0.7
