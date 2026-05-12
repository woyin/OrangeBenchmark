"""Custom scoring for Java expression-evaluator problem."""

import shutil
import subprocess
from pathlib import Path


def _run(command: list[str], work_dir: str) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=60)


def score_correctness(generated_code: str, work_dir: str) -> float:
    if shutil.which("mvn") is None:
        return 0.0
    try:
        result = _run(["mvn", "test", "-q"], work_dir)
        if result.returncode == 0:
            return 1.0
        import re
        output = result.stdout + result.stderr
        m = re.search(r"Tests run:\s*(\d+).*Failures:\s*(\d+)", output)
        if m:
            total = int(m.group(1))
            failures = int(m.group(2))
            if total > 0:
                return round(((total - failures) / total) ** 1.5, 4)
        return 0.0
    except Exception:
        return 0.0


def score_code_quality(generated_code: str, work_dir: str) -> float:
    if shutil.which("mvn") is None:
        return 0.0
    try:
        result = _run(["mvn", "compile", "-q"], work_dir)
        return 1.0 if result.returncode == 0 else 0.5
    except Exception:
        return 0.0
