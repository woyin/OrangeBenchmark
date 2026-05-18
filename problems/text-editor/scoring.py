import importlib.util
import time
from pathlib import Path

def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "text_editor_generated",
        Path(work_dir) / "solution.py",
    )
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        return 0.0
    spec.loader.exec_module(module)

    editor = module.TextEditor()
    start = time.perf_counter()
    editor.insert(0, 0, "\n".join(str(i) for i in range(10_000)))
    for _ in range(1_000):
        editor.insert(9_999, 4, "x")
    for _ in range(1_000):
        editor.undo()
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=3.0, slow=8.0)
