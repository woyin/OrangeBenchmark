import importlib.util
import time
from pathlib import Path


def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "word_ladder_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    import random
    rng = random.Random(42)
    words = set()
    for _ in range(5000):
        w = ''.join(rng.choices('abcde', k=4))
        words.add(w)
    dictionary = list(words)

    start = time.perf_counter()
    for _ in range(100):
        a, b = rng.choice(dictionary), rng.choice(dictionary)
        module.word_ladder(a, b, dictionary)
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=3.0, slow=10.0)
