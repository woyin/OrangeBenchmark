"""Score generated code against problem criteria."""

import importlib.util
import subprocess
import sys
from pathlib import Path


def _run_pytest(work_dir: Path) -> tuple[int, int]:
    """Run pytest in work_dir, return (passed, total)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(work_dir), "-v", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
        import re
        # Try "X passed" pattern
        m_passed = re.search(r"(\d+) passed", output)
        m_failed = re.search(r"(\d+) failed", output)
        passed = int(m_passed.group(1)) if m_passed else 0
        failed = int(m_failed.group(1)) if m_failed else 0
        total = passed + failed
        if total == 0:
            return 0, 1
        return passed, total
    except Exception:
        return 0, 1


def _run_ruff_check(file_path: Path) -> int:
    """Run ruff check, return number of issues."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(file_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.stdout.strip():
            return len([l for l in result.stdout.strip().split("\n") if l.strip()])
        return 0
    except Exception:
        return 0


def _load_custom_scorer(problem_dir: Path):
    """Load custom scoring.py from problem directory if it exists."""
    scoring_path = problem_dir / "scoring.py"
    if not scoring_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("scoring", scoring_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score_problem(
    problem_dir: Path,
    work_dir: Path,
    generated_code: str,
    problem_config: dict,
) -> dict:
    """Score a problem result. Returns dict with dimension scores and total."""
    scoring_config = problem_config.get("scoring", {})
    dimensions = scoring_config.get("dimensions", [
        {"name": "correctness", "weight": 0.5},
        {"name": "code_quality", "weight": 0.3},
        {"name": "performance", "weight": 0.2},
    ])

    custom_scorer = _load_custom_scorer(problem_dir)
    target_file = problem_config.get("target_file", "solution.py")
    target_path = work_dir / target_file

    scores = {}
    for dim in dimensions:
        name = dim["name"]
        score_func_name = f"score_{name}"

        if custom_scorer and hasattr(custom_scorer, score_func_name):
            func = getattr(custom_scorer, score_func_name)
            try:
                scores[name] = float(func(generated_code, str(work_dir)))
            except NotImplementedError:
                scores[name] = _default_score(name, target_path, work_dir)
            except Exception:
                scores[name] = 0.0
        else:
            scores[name] = _default_score(name, target_path, work_dir)

    total = sum(scores[dim["name"]] * dim["weight"] for dim in dimensions)
    total = min(max(total, 0.0), 1.0)

    return {"scores": scores, "total": round(total, 4)}


def _default_score(name: str, target_path: Path, work_dir: Path) -> float:
    """Get default score for a dimension."""
    if name == "correctness":
        return _default_correctness(work_dir)
    elif name == "code_quality":
        return _default_code_quality(target_path)
    elif name == "performance":
        return 0.7
    else:
        return 0.5


def _default_correctness(work_dir: Path) -> float:
    """Default correctness: pytest pass rate."""
    passed, total = _run_pytest(work_dir)
    return round(passed / total, 4)


def _default_code_quality(file_path: Path) -> float:
    """Default code quality: inverse of ruff issues."""
    if not file_path.exists():
        return 0.0
    issues = _run_ruff_check(file_path)
    if issues == 0:
        return 1.0
    return round(max(0.0, 1.0 - issues * 0.1), 4)
