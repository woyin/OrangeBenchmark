"""Custom scoring for .NET FizzBuzz problem."""

import shutil
import subprocess
from pathlib import Path


def _run(command: list[str], work_dir: str) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=60)


def score_correctness(generated_code: str, work_dir: str) -> float:
    if shutil.which("dotnet") is None:
        return 0.0
    result = _run(["dotnet", "test", "--no-build", "--verbosity", "quiet"], work_dir)
    if result.returncode != 0:
        return 0.0
    return 1.0


def score_code_quality(generated_code: str, work_dir: str) -> float:
    if shutil.which("dotnet") is None:
        return 0.0
    # Build first, then check warnings count
    result = _run(["dotnet", "build", "--verbosity", "quiet"], work_dir)
    if result.returncode != 0:
        return 0.5
    # Count warnings in output
    warnings = result.stdout.count("warning")
    if warnings == 0:
        return 1.0
    return round(max(0.0, 1.0 - warnings * 0.1), 4)


def score_performance(generated_code: str, work_dir: str) -> float:
    return 0.7
