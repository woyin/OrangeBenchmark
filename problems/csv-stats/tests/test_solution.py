import csv
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "csv_stats_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
analyze_csv = solution.analyze_csv


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def test_numeric_columns(tmp_path):
    path = tmp_path / "data.csv"
    write_csv(path, [["a", "b"], ["1", "2"], ["3", "4"]])
    assert analyze_csv(str(path)) == {
        "a": {"mean": 2.0, "max": 3.0, "min": 1.0, "null_count": 0},
        "b": {"mean": 3.0, "max": 4.0, "min": 2.0, "null_count": 0},
    }


def test_empty_file_returns_empty_dict(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    assert analyze_csv(str(path)) == {}


def test_header_only_file(tmp_path):
    path = tmp_path / "header.csv"
    write_csv(path, [["a", "b"]])
    assert analyze_csv(str(path)) == {
        "a": {"mean": None, "max": None, "min": None, "null_count": 0},
        "b": {"mean": None, "max": None, "min": None, "null_count": 0},
    }


def test_non_numeric_column(tmp_path):
    path = tmp_path / "names.csv"
    write_csv(path, [["name", "score"], ["alice", "10"], ["bob", "20"]])
    assert analyze_csv(str(path)) == {
        "name": {"type": "non-numeric", "null_count": 0},
        "score": {"mean": 15.0, "max": 20.0, "min": 10.0, "null_count": 0},
    }


def test_ragged_rows_count_missing_cells_as_null(tmp_path):
    path = tmp_path / "ragged.csv"
    write_csv(path, [["a", "b", "c"], ["1", "2"], ["3", "", "9"]])
    assert analyze_csv(str(path)) == {
        "a": {"mean": 2.0, "max": 3.0, "min": 1.0, "null_count": 0},
        "b": {"mean": 2.0, "max": 2.0, "min": 2.0, "null_count": 1},
        "c": {"mean": 9.0, "max": 9.0, "min": 9.0, "null_count": 1},
    }


def test_single_column(tmp_path):
    path = tmp_path / "single.csv"
    write_csv(path, [["value"], ["5"], ["7"], [""]])
    assert analyze_csv(str(path)) == {
        "value": {"mean": 6.0, "max": 7.0, "min": 5.0, "null_count": 1}
    }
