from pathlib import Path

import yaml

from runner.main import _discover_problems


EXPECTED_PROBLEMS = {
    "two-sum",
    "csv-stats",
    "url-parser",
    "lru-cache",
    "rest-api",
    "log-analyzer",
    "text-editor",
    "task-scheduler",
    "wasm-calculator",
}


def test_discovered_problem_set_matches_spec():
    discovered = {name for name, _, _ in _discover_problems()}
    assert discovered == EXPECTED_PROBLEMS


def test_each_problem_has_required_files():
    root = Path("problems")
    for name in EXPECTED_PROBLEMS:
        problem_dir = root / name
        assert (problem_dir / "problem.yaml").exists()
        config = yaml.safe_load((problem_dir / "problem.yaml").read_text())
        target = problem_dir / config["target_file"]
        assert target.exists()
        assert config["difficulty"] in {"easy", "medium", "hard"}
        assert config["category"] in {
            "algorithm",
            "string",
            "api",
            "data",
            "system",
            "multi-lang",
        }
        assert "prompt" in config and config["prompt"].strip()
        assert "scoring" in config
