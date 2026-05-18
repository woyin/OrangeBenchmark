import importlib.util
import time
from pathlib import Path

def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "lru_cache_generated",
        Path(work_dir) / "solution.py",
    )
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        return 0.0
    spec.loader.exec_module(module)

    cache = module.LRUCache(512)
    start = time.perf_counter()
    for i in range(50_000):
        cache.put(i, i)
        cache.get(i)
        cache.get(i - 1)
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=1.0, slow=3.0)
