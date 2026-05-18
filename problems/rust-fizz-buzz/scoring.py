"""Custom scoring for rust fizz-buzz problem."""
import shutil
import subprocess
from pathlib import Path


def _run(command: list[str], work_dir: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=timeout)


def score_correctness(generated_code: str, work_dir: str) -> float:
    if shutil.which("cargo") is None:
        return 0.0
    try:
        result = _run(["cargo", "test"], work_dir, timeout=120)
        if result.returncode == 0:
            return 1.0
        import re
        output = result.stdout + result.stderr
        m = re.search(r"test result: FAILED\.\s+(\d+)\s+passed;\s+(\d+)\s+failed", output)
        if m:
            passed = int(m.group(1))
            failed = int(m.group(2))
            total = passed + failed
            if total > 0:
                return round((passed / total) ** 4.0, 4)
        return 0.0
    except Exception:
        return 0.0


def score_performance(generated_code: str, work_dir: str) -> float:
    return 0.7
