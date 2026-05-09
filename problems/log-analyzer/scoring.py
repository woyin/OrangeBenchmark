import importlib.util
import time
from pathlib import Path


def score_performance(generated_code: str, work_dir: str) -> float:
    work_path = Path(work_dir)
    spec = importlib.util.spec_from_file_location(
        "log_analyzer_generated",
        work_path / "solution.py",
    )
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        return 0.0
    spec.loader.exec_module(module)

    log_path = work_path / "large.log"
    line = (
        '192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] '
        '"GET /index.html HTTP/1.1" 200 2326 '
        '"http://example.com" "Mozilla/5.0" 0.001\n'
    )
    with open(log_path, "w") as f:
        for _ in range(100_000):
            f.write(line)

    start = time.perf_counter()
    result = module.analyze_log(str(log_path))
    elapsed = time.perf_counter() - start
    if result.get("total_requests") != 100_000:
        return 0.0
    if elapsed < 2.0:
        return 1.0
    if elapsed < 5.0:
        return 0.5
    return 0.0
