import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "log_analyzer_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
analyze_log = solution.analyze_log


def write_log(path, lines):
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def line(method, path, status, response_time="0.010"):
    return (
        '192.168.1.1 - - [10/Oct/2023:13:55:36 +0000] '
        f'"{method} {path} HTTP/1.1" {status} 2326 '
        '"http://example.com" "Mozilla/5.0"'
        + (f" {response_time}" if response_time is not None else "")
    )


def test_mixed_log_stats(tmp_path):
    path = tmp_path / "access.log"
    write_log(path, [line("GET", "/a", 200, "0.010"), line("POST", "/b", 404, "0.030")])
    assert analyze_log(str(path)) == {
        "total_requests": 2,
        "methods": {"GET": 1, "POST": 1},
        "status_codes": {"200": 1, "404": 1},
        "top_paths": [("/a", 1), ("/b", 1)],
        "avg_response_time": 0.02,
    }


def test_empty_file(tmp_path):
    path = tmp_path / "empty.log"
    write_log(path, [])
    assert analyze_log(str(path)) == {
        "total_requests": 0,
        "methods": {},
        "status_codes": {},
        "top_paths": [],
        "avg_response_time": 0.0,
    }


def test_skips_malformed_lines_and_missing_response_time(tmp_path):
    path = tmp_path / "access.log"
    write_log(path, ["bad line", line("GET", "/ok", 200, None), line("GET", "/timed", 200, "0.050")])
    result = analyze_log(str(path))
    assert result["total_requests"] == 2
    assert result["avg_response_time"] == 0.05


def test_top_paths_ordered_by_count(tmp_path):
    path = tmp_path / "access.log"
    write_log(path, [line("GET", "/b", 200), line("GET", "/a", 200), line("GET", "/a", 200)])
    assert analyze_log(str(path))["top_paths"][:2] == [("/a", 2), ("/b", 1)]


def test_all_same_status(tmp_path):
    path = tmp_path / "access.log"
    write_log(path, [line("GET", "/a", 500) for _ in range(5)])
    result = analyze_log(str(path))
    assert result["status_codes"] == {"500": 5}
    assert result["total_requests"] == 5


def test_many_distinct_paths(tmp_path):
    path = tmp_path / "access.log"
    lines = [line("GET", f"/path/{i}", 200, "0.010") for i in range(100)]
    write_log(path, lines)
    result = analyze_log(str(path))
    assert result["total_requests"] == 100
    assert len(result["top_paths"]) <= 10


def test_large_response_times(tmp_path):
    path = tmp_path / "access.log"
    write_log(path, [line("GET", "/slow", 200, "999.999")])
    result = analyze_log(str(path))
    assert result["avg_response_time"] == 999.999


def test_completely_malformed_file(tmp_path):
    path = tmp_path / "garbage.log"
    write_log(path, ["not a log line", "also not", ""])
    result = analyze_log(str(path))
    assert result["total_requests"] == 0
