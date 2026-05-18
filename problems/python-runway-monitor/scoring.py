"""Custom performance scorer for runway monitor benchmark."""

import importlib.util
import time
from pathlib import Path

def score_performance(generated_code: str, work_dir: str) -> float:
    """Score performance by processing 1000 positions over a 4-runway airport."""
    work_path = Path(work_dir)
    spec = importlib.util.spec_from_file_location(
        "runway_monitor_generated",
        work_path / "solution.py",
    )
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        return 0.0
    spec.loader.exec_module(module)

    Runway = module.Runway
    Taxiway = module.Taxiway
    AirportLayout = module.AirportLayout
    AircraftPosition = module.AircraftPosition
    RunwayMonitor = module.RunwayMonitor

    runways = [
        Runway("09L/27R", (0.0, 0.0), (3000.0, 0.0), 60.0),
        Runway("09R/27L", (0.0, 500.0), (3000.0, 500.0), 60.0),
        Runway("18/36", (1500.0, -200.0), (1500.0, 800.0), 45.0),
        Runway("04/22", (0.0, 0.0), (2000.0, 2000.0), 45.0),
    ]
    taxiways = [
        Taxiway("Alpha", [(500.0, -100.0), (500.0, 600.0)], 30.0),
        Taxiway("Bravo", [(2500.0, -100.0), (2500.0, 600.0)], 30.0),
    ]
    crossings = [
        {"taxiway": "Alpha", "runway": "09L/27R", "point": (500.0, 0.0)},
        {"taxiway": "Alpha", "runway": "09R/27L", "point": (500.0, 500.0)},
        {"taxiway": "Bravo", "runway": "09L/27R", "point": (2500.0, 0.0)},
        {"taxiway": "Bravo", "runway": "09R/27L", "point": (2500.0, 500.0)},
    ]
    layout = AirportLayout(runways, taxiways, crossings)

    monitor = RunwayMonitor(layout)
    monitor.set_active_runway("09L/27R", "A")
    monitor.set_active_runway("09R/27L", "B")
    monitor.set_crossing_active("Alpha", "09L/27R", True)

    start = time.perf_counter()
    for i in range(1000):
        x = float(i * 3)
        y = float(i % 60 - 30)
        pos = AircraftPosition(f"AC{i:04d}", x, y, float(i), True)
        monitor.update_position(pos)
    elapsed = time.perf_counter() - start

    from runner.scorer import _continuous_performance_score

    return _continuous_performance_score(elapsed, fast=1.0, slow=3.0)
