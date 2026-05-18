import importlib.util
import time
from pathlib import Path

def score_performance(generated_code: str, work_dir: str) -> float:
    spec = importlib.util.spec_from_file_location(
        "url_parser_generated",
        Path(work_dir) / "solution.py",
    )
    if spec is None or spec.loader is None:
        return 0.0
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    urls = [
        "https://example.com/path/to/resource?key=value&foo=bar#section",
        "http://localhost:8080/api/v1/users?limit=100&offset=200",
        "https://sub.domain.org:443/deep/nested/path?a=1&b=2&c=3&d=4",
        "/relative/path/only?query=yes",
        "https://user:pass@host.com:9090/secret?token=abc#frag",
    ] * 20_000

    start = time.perf_counter()
    for url in urls:
        module.parse_url(url)
    elapsed = time.perf_counter() - start
    from runner.scorer import _continuous_performance_score
    return _continuous_performance_score(elapsed, fast=2.0, slow=6.0)
