import importlib.util
import time
from pathlib import Path


def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "rest_api_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    server = module.create_app()
    port = server.server_address[1]

    import http.client
    import json

    start = time.perf_counter()
    for i in range(200):
        conn = http.client.HTTPConnection("localhost", port)
        body = json.dumps({"title": f"task-{i}", "status": "pending"})
        conn.request("POST", "/tasks", body=body, headers={"Content-Type": "application/json"})
        conn.getresponse().read()
        conn.close()

    for i in range(200):
        conn = http.client.HTTPConnection("localhost", port)
        conn.request("GET", f"/tasks/{i+1}")
        conn.getresponse().read()
        conn.close()

    elapsed = time.perf_counter() - start
    server.server_close()

    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=5.0, slow=15.0)
