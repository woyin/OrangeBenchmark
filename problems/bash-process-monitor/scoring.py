"""Custom scoring for bash problem."""
import subprocess
from pathlib import Path


def _run_test(work_dir: str) -> tuple[int, int]:
    test_script = Path(work_dir) / "tests" / "test_solution.sh"
    if not test_script.exists():
        return 0, 1
    try:
        result = subprocess.run(
            ["bash", str(test_script)],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        import re
        m_passed = re.search(r"PASSED:\s*(\d+)", output)
        m_failed = re.search(r"FAILED:\s*(\d+)", output)
        passed = int(m_passed.group(1)) if m_passed else 0
        failed = int(m_failed.group(1)) if m_failed else (0 if result.returncode == 0 else 1)
        return passed, passed + failed
    except Exception:
        return 0, 1


def score_correctness(generated_code: str, work_dir: str) -> float:
    passed, total = _run_test(work_dir)
    if total == 0:
        return 0.0
    raw = passed / total
    return round(raw ** 2.0, 4)


def score_code_quality(generated_code: str, work_dir: str) -> float:
    target = Path(work_dir) / "solution.sh"
    if not target.exists():
        return 0.0
    try:
        result = subprocess.run(
            ["shellcheck", str(target), "--severity=warning"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return 1.0
        issues = result.stdout.strip().count("
") + 1
        return round(max(0.0, 1.0 - issues * 0.05), 4)
    except FileNotFoundError:
        return 0.8
    except Exception:
        return 0.5


def score_performance(generated_code: str, work_dir: str) -> float:
    return 0.7
