"""Custom scoring for Java problem."""
import shutil
import subprocess
from pathlib import Path

def _run(command, work_dir, timeout=60):
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=timeout)

def score_correctness(generated_code, work_dir):
    if shutil.which("mvn") is None: return 0.0
    try:
        result = _run(["mvn", "test", "-q"], work_dir, timeout=120)
        if result.returncode == 0: return 1.0
        import re
        output = result.stdout + result.stderr
        m = re.search(r"Tests run:\s*(\d+).*Failures:\s*(\d+)", output)
        if m:
            total, failures = int(m.group(1)), int(m.group(2))
            if total > 0: return round(((total - failures) / total) ** 2.0, 4)
        return 0.0
    except: return 0.0

def score_performance(generated_code, work_dir):
    return 0.7
