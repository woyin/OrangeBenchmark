"""Custom scoring for React problem."""
import shutil
import subprocess
import re
from pathlib import Path

def score_correctness(generated_code: str, work_dir: str) -> float:
    if shutil.which("npm") is None:
        return 0.0
    try:
        install = subprocess.run(
            ["npm", "install"], cwd=work_dir,
            capture_output=True, text=True, timeout=120,
        )
        result = subprocess.run(
            ["npm", "test", "--", "--reporter=verbose"],
            cwd=work_dir, capture_output=True, text=True, timeout=60,
        )
        output = result.stdout + result.stderr
        m_passed = re.search(r"Tests\s+(\d+)\s+passed", output)
        m_failed = re.search(r"Tests\s+(\d+)\s+failed", output)
        if m_passed:
            passed = int(m_passed.group(1))
            failed = int(m_failed.group(1)) if m_failed else 0
            total = passed + failed
            if total > 0:
                return round((passed / total) ** 2.0, 4)
        if "passed" in output and result.returncode == 0:
            return 1.0
        return 0.0
    except Exception:
        return 0.0

def score_performance(generated_code: str, work_dir: str) -> float:
    return 0.7
