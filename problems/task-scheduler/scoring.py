import importlib.util
import time
from pathlib import Path


def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "task_scheduler_generated",
        Path(work_dir) / "solution.py",
    )
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        return 0.0
    spec.loader.exec_module(module)

    def sleeper():
        time.sleep(0.2)
        return "ok"

    serial = module.TaskScheduler(max_workers=1)
    parallel = module.TaskScheduler(max_workers=4)
    for idx in range(4):
        serial.add_task(str(idx), sleeper)
        parallel.add_task(str(idx), sleeper)

    start = time.perf_counter()
    serial.run_all()
    serial_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    parallel.run_all()
    parallel_elapsed = time.perf_counter() - start

    ratio = parallel_elapsed / max(serial_elapsed, 0.001)
    if ratio <= 0.4:
        return 1.0
    if ratio >= 1.0:
        return 0.0
    return round(1.0 - (ratio - 0.4) / 0.6, 4)
