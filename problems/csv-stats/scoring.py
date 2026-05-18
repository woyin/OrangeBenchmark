import importlib.util
import os
import tempfile
import time
from pathlib import Path

def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "csv_stats_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        header = "id,name,value,category\n"
        f.write(header)
        for i in range(50_000):
            f.write(f"{i},item_{i},{i * 1.5},cat_{i % 10}\n")
        tmp_path = f.name

    try:
        start = time.perf_counter()
        module.analyze_csv(tmp_path)
        elapsed = time.perf_counter() - start
        from runner.scorer import _continuous_performance_score
        return _continuous_performance_score(elapsed, fast=1.0, slow=4.0)
    finally:
        os.unlink(tmp_path)
