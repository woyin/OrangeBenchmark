import importlib.util
import time
from pathlib import Path

def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "regex_engine_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    patterns_and_texts = [
        ("a*b+c?", "a" * 50 + "bb"),
        ("[a-z]*.[0-9]+", "abcdef5"),
        ("a.*b", "a" + "x" * 1000 + "b"),
        ("[^abc]+d", "xyzd"),
    ]

    start = time.perf_counter()
    for _ in range(1000):
        for pattern, text in patterns_and_texts:
            module.match(pattern, text)
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=2.0, slow=6.0)
