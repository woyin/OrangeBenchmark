import importlib.util
import time
from pathlib import Path

def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "jwt_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    start = time.perf_counter()
    for i in range(1000):
        payload = {"sub": f"user{i}", "data": "test"}
        token = module.create_token(payload, "benchmark_secret")
        module.verify(token, "benchmark_secret")
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=3.0, slow=8.0)
