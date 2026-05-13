import importlib.util
import time
from pathlib import Path


def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "mini_db_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    db = module.MiniDB()
    start = time.perf_counter()
    for i in range(10_000):
        db.set(f"key:{i}", f"val:{i}")
    for i in range(10_000):
        db.get(f"key:{i}")
    for _ in range(100):
        db.begin()
        db.set("txn_key", "txn_val")
        db.commit()
    db.scan("key:")
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=2.0, slow=5.0)
