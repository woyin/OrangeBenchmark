import importlib.util
import time
from pathlib import Path

def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "route_planner_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    p = module.RoutePlanner()
    for i in range(1000):
        module.Waypoint(f"WP{i}", i * 0.01, i * 0.01)
        p.add_waypoint(module.Waypoint(f"WP{i}", i * 0.01, i * 0.01))
        if i > 0:
            p.add_airway(f"WP{i-1}", f"WP{i}")

    start = time.perf_counter()
    for _ in range(100):
        p.find_shortest_route("WP0", "WP999")
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=3.0, slow=10.0)
