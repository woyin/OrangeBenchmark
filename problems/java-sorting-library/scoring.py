"""Custom scoring."""
import shutil, subprocess, re
from pathlib import Path

def _run(cmd, wd, timeout=60):
    return subprocess.run(cmd, cwd=wd, capture_output=True, text=True, timeout=timeout)

def score_correctness(generated_code, work_dir):
    if shutil.which("mvn") is None: return 0.0
    try:
        r = _run(["mvn","test","-q"], work_dir, timeout=120)
        if r.returncode == 0: return 1.0
        o = r.stdout + r.stderr
        m = re.search(r"Tests run:\s*(\d+).*Failures:\s*(\d+)", o)
        if m:
            t, f = int(m.group(1)), int(m.group(2))
            if t > 0: return round(((t-f)/t)**2.0, 4)
        return 0.0
    except: return 0.0

def score_code_quality(generated_code, work_dir):
    if shutil.which("mvn") is None: return 0.0
    try:
        r = _run(["mvn","compile","-q"], work_dir)
        return 1.0 if r.returncode == 0 else 0.5
    except: return 0.0

def score_performance(generated_code, work_dir):
    return 0.7
