from pathlib import Path

import yaml

from runner.main import _discover_problems


EXPECTED_PROBLEMS = {
    "bash-backup-rotation",
    "bash-csv-merger",
    "bash-file-renamer",
    "bash-log-summary",
    "bash-process-monitor",
    "csv-stats",
    "dotnet-adsb-decoder",
    "dotnet-crew-scheduler",
    "dotnet-fizz-buzz",
    "dotnet-json-transform",
    "dotnet-rate-limiter",
    "dotnet-text-search",
    "java-aircraft-scheduler",
    "java-concurrent-queue",
    "java-conflict-detector",
    "java-expression-evaluator",
    "java-fizz-buzz",
    "java-flight-plan-parser",
    "java-graph-shortest-path",
    "java-http-server",
    "java-json-parser",
    "java-matrix-ops",
    "java-morse-code",
    "java-palindrome-checker",
    "java-password-validator",
    "java-reverse-string",
    "java-sorting-library",
    "java-tcp-chat-server",
    "java-thread-pool",
    "log-analyzer",
    "lru-cache",
    "mini-db",
    "python-jwt-decoder",
    "python-markdown-parser",
    "python-metar-parser",
    "python-route-planner",
    "python-runway-monitor",
    "python-word-ladder",
    "react-color-picker",
    "react-counter-app",
    "react-data-table",
    "react-drag-kanban",
    "react-form-validator",
    "react-infinite-scroll",
    "react-todo-list",
    "regex-engine",
    "rest-api",
    "task-scheduler",
    "text-editor",
    "two-sum",
    "url-parser",
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
            "aviation",
            "concurrency",
            "security",
            "parsing",
            "encoding",
            "math",
            "frontend",
        }
        assert "prompt" in config and config["prompt"].strip()
        assert "scoring" in config
