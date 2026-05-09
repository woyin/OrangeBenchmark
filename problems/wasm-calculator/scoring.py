import shutil
import subprocess
from pathlib import Path


def _run(command: list[str], work_dir: str) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=30)


def score_correctness(generated_code: str, work_dir: str) -> float:
    if shutil.which("cargo") is None:
        return 0.0
    result = _run(["cargo", "test"], work_dir)
    return 1.0 if result.returncode == 0 else 0.0


def score_code_quality(generated_code: str, work_dir: str) -> float:
    if shutil.which("cargo") is None:
        return 0.0
    if shutil.which("cargo-clippy") is None:
        return 0.7
    result = _run(["cargo", "clippy", "--", "-D", "warnings"], work_dir)
    return 1.0 if result.returncode == 0 else 0.5


def score_performance(generated_code: str, work_dir: str) -> float:
    if shutil.which("cargo") is None:
        return 0.0
    result = subprocess.run(
        ["cargo", "test", "performance_smoke", "--", "--ignored"],
        cwd=Path(work_dir),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return 1.0 if result.returncode == 0 else 0.0
