"""Score generated code against problem criteria."""

import ast
import importlib.util
import re
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
        if result.returncode == 0:
            return 0
        return len([line for line in result.stdout.strip().split("\n") if line.strip()])
    except Exception:
        return 0


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
        if result.returncode == 0:
            return 1.0
        output = result.stdout + result.stderr
        m = re.search(r"Tests run:\s*(\d+).*Failures:\s*(\d+)", output)
        if m:
            total = int(m.group(1))
            failures = int(m.group(2))
            passed = total - failures
            if total > 0:
                return round((passed / total) ** 1.5, 4)
        return 0.0
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


def _continuous_performance_score(
    elapsed: float, fast: float, slow: float, ok: bool = True
) -> float:
    """Continuous performance score from elapsed time.

    Returns 1.0 if elapsed <= fast, linearly interpolated to 0.3
    at slow threshold, 0.0 if elapsed >= slow or ok is False.
    """
    if not ok:
        return 0.0
    if elapsed <= fast:
        return 1.0
    if elapsed >= slow:
        return 0.0
    t = (elapsed - fast) / (slow - fast)
    return round(1.0 - 0.7 * t, 4)


def _ruff_lint_score(file_path: Path) -> float:
    """Lint score from ruff, normalized by lines of code."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(file_path),
             "--output-format", "json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return 1.0
        issues = []
        try:
            import json
            issues = json.loads(result.stdout) if result.stdout.strip() else []
        except Exception:
            pass
        issue_count = len(issues) if isinstance(issues, list) else 0
        loc = max(len(file_path.read_text().strip().split("\n")), 1)
        return round(max(0.0, 1.0 - (issue_count / max(loc / 10, 1)) * 0.3), 4)
    except Exception:
        return 0.5


def _type_hint_score(file_path: Path) -> float:
    """Score based on type annotation coverage of public function parameters and returns."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)

        total_params = 0
        hinted_params = 0
        total_returns = 0
        hinted_returns = 0

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_") and not node.name.startswith("__"):
                continue
            for arg in node.args.args:
                if arg.arg == "self":
                    continue
                total_params += 1
                if arg.annotation is not None:
                    hinted_params += 1
            total_returns += 1
            if node.returns is not None:
                hinted_returns += 1

        if total_params + total_returns == 0:
            return 0.8
        param_score = hinted_params / max(total_params, 1)
        return_score = hinted_returns / max(total_returns, 1)
        return round(0.6 * param_score + 0.4 * return_score, 4)
    except Exception:
        return 0.5


def _complexity_score(file_path: Path) -> float:
    """Score based on cyclomatic complexity relative to lines of code."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)

        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        loc = max(len(source.strip().split("\n")), 1)
        ratio = complexity / loc
        if ratio <= 0.2:
            return 1.0
        if ratio <= 0.5:
            return round(1.0 - (ratio - 0.2) / 0.3 * 0.3, 4)
        return round(max(0.0, 0.7 - (ratio - 0.5) * 0.6), 4)
    except Exception:
        return 0.5


def _docstring_score(file_path: Path) -> float:
    """Score based on docstring coverage of public functions/classes."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)

        public_count = 0
        docstring_count = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                public_count += 1
                if (node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                    docstring_count += 1
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    public_count += 1
                    if (node.body
                            and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and isinstance(node.body[0].value.value, str)):
                        docstring_count += 1

        if public_count == 0:
            return 0.8
        return round(docstring_count / public_count, 4)
    except Exception:
        return 0.5


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
        return _default_code_quality(target_path, work_dir)
    elif name == "performance":
        return 0.7
    else:
        return 0.5


def _default_correctness(work_dir: Path) -> float:
    """Default correctness: auto-detect project type and run tests."""
    if _detect_java_maven(work_dir):
        return _run_maven_test(work_dir)
    if _detect_dotnet(work_dir):
        return _run_dotnet_test(work_dir)
    passed, total = _run_pytest(work_dir)
    raw = passed / total
    return round(raw ** 1.5, 4)


def _default_code_quality(target_path: Path, work_dir: Path) -> float:
    """Default code quality: auto-detect project type."""
    if _detect_java_maven(work_dir):
        return _run_maven_compile(work_dir)
    if _detect_dotnet(work_dir):
        return _run_dotnet_build_quality(work_dir)
    if not target_path.exists():
        return 0.0
    lint = _ruff_lint_score(target_path)
    type_hints = _type_hint_score(target_path)
    complexity = _complexity_score(target_path)
    docs = _docstring_score(target_path)
    return round(0.35 * lint + 0.30 * type_hints + 0.20 * complexity + 0.15 * docs, 4)
