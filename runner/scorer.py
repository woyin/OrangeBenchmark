"""Score generated code against problem criteria."""

import importlib.util
import subprocess
import sys
from pathlib import Path

from runner.scoring.behavior import score_cost_efficiency, score_tool_efficiency


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
            return len([line for line in result.stdout.strip().split("\n") if line.strip()])
        return 0
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Java / Maven helpers
# ---------------------------------------------------------------------------

def _detect_java_maven(work_dir: Path) -> bool:
    return (work_dir / "pom.xml").exists()


def _run_maven_test(work_dir: Path) -> float:
    try:
        result = subprocess.run(
            ["mvn", "test", "-q"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return 1.0 if result.returncode == 0 else 0.0
    except Exception:
        return 0.0


def _run_maven_compile(work_dir: Path) -> float:
    try:
        result = subprocess.run(
            ["mvn", "compile", "-q"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return 1.0 if result.returncode == 0 else 0.5
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# .NET helpers
# ---------------------------------------------------------------------------

def _detect_dotnet(work_dir: Path) -> bool:
    return any(f.suffix == ".csproj" for f in work_dir.iterdir())


def _run_dotnet_test(work_dir: Path) -> float:
    try:
        build = subprocess.run(
            ["dotnet", "build", "--verbosity", "quiet"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if build.returncode != 0:
            return 0.0
        result = subprocess.run(
            ["dotnet", "test", "--no-build", "--verbosity", "quiet"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return 1.0 if result.returncode == 0 else 0.0
    except Exception:
        return 0.0


def _run_dotnet_build_quality(work_dir: Path) -> float:
    try:
        result = subprocess.run(
            ["dotnet", "build", "--verbosity", "normal"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return 0.5
        warnings = result.stdout.count("warning")
        if warnings == 0:
            return 1.0
        return round(max(0.0, 1.0 - warnings * 0.1), 4)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Custom scorer loading
# ---------------------------------------------------------------------------

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
    trace_data: dict | None = None,
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
                scores[name] = _default_score(name, target_path, work_dir, trace_data, problem_config)
            except Exception:
                scores[name] = 0.0
        else:
            scores[name] = _default_score(name, target_path, work_dir, trace_data, problem_config)

    total = sum(scores[dim["name"]] * dim["weight"] for dim in dimensions)
    total = min(max(total, 0.0), 1.0)

    return {"scores": scores, "total": round(total, 4)}


def _default_score(
    name: str,
    target_path: Path,
    work_dir: Path,
    trace_data: dict | None = None,
    problem_config: dict | None = None,
) -> float:
    """Get default score for a dimension."""
    if name == "correctness":
        return _default_correctness(work_dir)
    elif name == "code_quality":
        return _default_code_quality(target_path, work_dir)
    elif name == "performance":
        return 0.7
    elif name == "cost_efficiency":
        return score_cost_efficiency("", str(work_dir), trace_data, problem_config)
    elif name == "tool_efficiency":
        return score_tool_efficiency("", str(work_dir), trace_data, problem_config)
    else:
        return 0.5


def _default_correctness(work_dir: Path) -> float:
    """Default correctness: auto-detect project type and run tests."""
    if _detect_java_maven(work_dir):
        return _run_maven_test(work_dir)
    if _detect_dotnet(work_dir):
        return _run_dotnet_test(work_dir)
    passed, total = _run_pytest(work_dir)
    return round(passed / total, 4)


def _default_code_quality(target_path: Path, work_dir: Path) -> float:
    """Default code quality: auto-detect project type."""
    if _detect_java_maven(work_dir):
        return _run_maven_compile(work_dir)
    if _detect_dotnet(work_dir):
        return _run_dotnet_build_quality(work_dir)
    if not target_path.exists():
        return 0.0
    issues = _run_ruff_check(target_path)
    if issues == 0:
        return 1.0
    return round(max(0.0, 1.0 - issues * 0.1), 4)
