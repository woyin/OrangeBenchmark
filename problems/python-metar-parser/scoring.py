import importlib.util
import time
from pathlib import Path

METAR_SAMPLES = [
    "KJFK 121851Z 27010G15KT 10SM FEW060 SCT100 22/12 A3012 RMK AO2",
    "KLAX 010000Z VRB03KT 9999 SKC 25/10 A2995",
    "EGLL 151020Z AUTO 24015G28KT 9999 BKN025 12/08 Q1013",
    "RJTT 050000Z 18012KT 9999 FEW030 SCT080 20/16 A2980 RMK SLP125",
]


def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "metar_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    start = time.perf_counter()
    for _ in range(10000):
        for sample in METAR_SAMPLES:
            module.parse_metar(sample)
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=2.0, slow=6.0)
