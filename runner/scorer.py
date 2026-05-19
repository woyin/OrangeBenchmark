"""Score generated code against problem criteria."""

import ast
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

# Subprocess timeouts (seconds)
_TIMEOUT_SHORT = 10
_TIMEOUT_DEFAULT = 30
_TIMEOUT_LONG = 60
_TIMEOUT_VERY_LONG = 120



# Unified quality dimension weights (applied across all languages)
_QUALITY_DIMENSION_WEIGHTS = {
    "documentation": 0.20,
    "error_handling": 0.20,
    "naming_style": 0.20,
    "structure": 0.20,
    "static_analysis": 0.20,
}


def _summarize_quality(dimensions: dict[str, float]) -> float:
    """Weighted average of quality dimension scores (0-1 each)."""
    total = 0.0
    weight_sum = 0.0
    for dim, weight in _QUALITY_DIMENSION_WEIGHTS.items():
        score = dimensions.get(dim, 0.5)
        total += score * weight
        weight_sum += weight
    if weight_sum == 0:
        return 0.5
    return round(min(max(total / weight_sum, 0.10), 1.0), 4)



def _run_pytest(work_dir: Path) -> tuple[int, int]:
    """Run pytest in work_dir, return (passed, total)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(work_dir), "-v", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_DEFAULT,
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

def _detect_java_maven(work_dir: Path) -> bool:
    return (work_dir / "pom.xml").exists()


def _run_maven_test(work_dir: Path, exponent: float = 4.0) -> float:
    try:
        result = subprocess.run(
            ["mvn", "test", "-q"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_LONG,
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
                return round((passed / total) ** exponent, 4)
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
            timeout=_TIMEOUT_LONG,
        )
        return 1.0 if result.returncode == 0 else 0.5
    except Exception:
        return 0.0


def _detect_dotnet(work_dir: Path) -> bool:
    return any(f.suffix == ".csproj" for f in work_dir.iterdir())


def _run_dotnet_test(work_dir: Path, exponent: float = 4.0) -> float:
    try:
        build = subprocess.run(
            ["dotnet", "build", "--verbosity", "quiet"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_LONG,
        )
        if build.returncode != 0:
            return 0.0
        result = subprocess.run(
            ["dotnet", "test", "--no-build", "--verbosity", "normal"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_LONG,
        )
        if result.returncode == 0:
            return 1.0
        output = result.stdout + result.stderr
        # Parse "X passed, Y failed" or "Total tests: X Failed: Y"
        m = re.search(r"(\d+) passed", output)
        if m:
            passed = int(m.group(1))
            failed_match = re.search(r"(\d+) failed", output)
            failed = int(failed_match.group(1)) if failed_match else 0
            total = passed + failed
            if total > 0:
                return round((passed / total) ** exponent, 4)
        return 0.0
    except Exception:
        return 0.0


def _continuous_performance_score(
    elapsed: float, fast: float, slow: float, ok: bool = True
) -> float:
    """Continuous performance score from elapsed time using squared decay."""
    if not ok:
        return 0.0
    if elapsed <= fast:
        return 1.0
    if elapsed >= slow:
        return 0.0
    t = (elapsed - fast) / (slow - fast)
    return round((1 - t) ** 2, 4)


def _ruff_lint_score(file_path: Path) -> float:
    """Lint score from ruff, normalized by lines of code."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(file_path),
             "--output-format", "json"],
            capture_output=True, text=True, timeout=_TIMEOUT_SHORT,
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
        return round(max(0.0, 1.0 - issue_count / loc), 4)
    except Exception:
        return 0.5


def _count_ruff_issues(file_path: Path) -> int:
    """Count ruff lint issues."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(file_path),
             "--output-format", "json"],
            capture_output=True, text=True, timeout=_TIMEOUT_SHORT,
        )
        if result.returncode == 0:
            return 0
        import json
        issues = json.loads(result.stdout) if result.stdout.strip() else []
        return len(issues) if isinstance(issues, list) else 0
    except Exception:
        return 0


def _type_hint_score(file_path: Path) -> float:
    """Score based on type hint coverage for public functions."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)

        total_params = 0
        typed_params = 0
        has_return = 0
        func_count = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                func_count += 1
                for arg in node.args.args:
                    if arg.arg == "self":
                        continue
                    total_params += 1
                    if arg.annotation is not None:
                        typed_params += 1
                if node.returns is not None:
                    has_return += 1

        if func_count == 0:
            return 0.8

        param_score = typed_params / total_params if total_params > 0 else 1.0
        return_score = has_return / func_count
        return round(0.6 * param_score + 0.4 * return_score, 4)
    except Exception:
        return 0.5


def _complexity_score(file_path: Path) -> float:
    """Score based on cyclomatic complexity of public functions."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)

        complexities = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                cc = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                        cc += 1
                    elif isinstance(child, ast.BoolOp):
                        cc += len(child.values) - 1
                complexities.append(cc)

        if not complexities:
            return 0.8

        avg_cc = sum(complexities) / len(complexities)
        return round(max(0.0, min(1.0, 1.0 - (avg_cc - 1) * 0.1)), 4)
    except Exception:
        return 0.5


def _docstring_score(file_path: Path) -> float:
    """Score based on docstring presence in public functions/classes."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)

        public_count = 0
        docstring_count = 0

        for node in ast.iter_child_nodes(tree):
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
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
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


def _error_handling_score(file_path: Path) -> float:
    """Score based on presence of error handling (try/except, raise, input validation)."""
    try:
        source = file_path.read_text()
        tree = ast.parse(source)

        public_funcs = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") and not node.name.startswith("__"):
                    continue
                public_funcs.append(node)

        if not public_funcs:
            return 0.8

        handled = 0
        for func in public_funcs:
            has_try = False
            has_raise = False
            has_if_validation = False
            for child in ast.walk(func):
                if isinstance(child, ast.Try):
                    has_try = True
                if isinstance(child, ast.Raise):
                    has_raise = True
                if isinstance(child, ast.If):
                    for sub in ast.walk(child):
                        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                            if sub.func.id in ("isinstance", "type", "len", "hasattr"):
                                has_if_validation = True
            if has_try or has_raise or has_if_validation:
                handled += 1

        return round(handled / len(public_funcs), 4)
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


def _security_score(target_path: Path) -> float:
    """Security: scan for dangerous patterns, deduction-based."""
    if not target_path.exists():
        return 0.5
    try:
        source = target_path.read_text()
    except Exception:
        return 0.5

    issues = 0
    # Check for subprocess with shell=True
    if re.search(r'subprocess\.\w+\(.*shell\s*=\s*True', source):
        issues += 1
    # Check for eval/exec
    if re.search(r'\beval\s*\(', source):
        issues += 1
    if re.search(r'\bexec\s*\(', source):
        issues += 1
    # Check for os.system
    if re.search(r'os\.system\s*\(', source):
        issues += 1
    # Check for SQL string concatenation patterns
    if re.search(r'(SELECT|INSERT|UPDATE|DELETE).*\+\s*["\']', source, re.IGNORECASE):
        issues += 1
    # Check for unsanitized path traversal
    if re.search(r'open\s*\(\s*.*\+', source) and re.search(r'\.\.', source):
        issues += 1

    return round(max(0.0, 1.0 - issues * 0.25), 4)


def _robustness_score(target_path: Path) -> float:
    """Robustness: check for edge case handling, additive scoring."""
    if not target_path.exists():
        return 0.25
    try:
        source = target_path.read_text()
        tree = ast.parse(source)
    except Exception:
        return 0.25

    score = 0.0

    # +0.25 for empty input handling (check for None, "", [], {} checks)
    empty_patterns = [
        r'if\s+\w+\s*(is\s+None|==\s*None|==\s*""|==\s*\[\]|==\s*\{\}|not\s+\w+)',
        r'if\s+not\s+\w+',
        r'if\s+len\s*\(\s*\w+\s*\)\s*==\s*0',
    ]
    for pat in empty_patterns:
        if re.search(pat, source):
            score += 0.25
            break

    # +0.25 for exception type handling (specific except clauses)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is not None:
            score += 0.25
            break

    # +0.25 for boundary value checking (comparison with 0, -1, max, min)
    boundary_patterns = [r'==\s*0', r'>=\s*0', r'>\s*0', r'<\s*0', r'<=\s*-1', r'==\s*-1']
    for pat in boundary_patterns:
        if re.search(pat, source):
            score += 0.25
            break

    # +0.25 for input validation (isinstance, type checks)
    validation_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("isinstance", "type", "hasattr"):
                validation_found = True
                break
    if validation_found:
        score += 0.25

    return round(min(score, 1.0), 4)


def _resource_efficiency_score(target_path: Path) -> float:
    """Resource efficiency: check for unclosed resources, deduction-based."""
    if not target_path.exists():
        return 0.5
    try:
        source = target_path.read_text()
    except Exception:
        return 0.5

    deductions = 0.0

    # Check for open() without with statement
    if re.search(r'(?<!with\s)\bopen\s*\(', source):
        # Count standalone opens (not in with context)
        lines = source.split('\n')
        for line in lines:
            stripped = line.strip()
            if 'open(' in stripped and not stripped.startswith('with ') and 'with ' not in stripped:
                deductions += 0.10
                break

    # Check for socket without with
    if re.search(r'socket\.socket\s*\(', source):
        if 'with ' not in source or not re.search(r'with\s+.*socket', source):
            deductions += 0.10

    # Check for unnecessary list creation in loops
    if re.search(r'for\s+\w+\s+in\s+list\s*\(\s*range', source):
        deductions += 0.10

    return round(max(0.0, 1.0 - deductions), 4)


def score_problem(
    problem_dir: Path,
    work_dir: Path,
    generated_code: str,
    problem_config: dict,
    elapsed_seconds: float | None = None,
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

    # Check if performance is configured
    perf_config = scoring_config.get("performance", {})
    has_perf_config = "fast_seconds" in perf_config and "slow_seconds" in perf_config

    scores = {}
    unavailable_dims = set()

    for dim in dimensions:
        name = dim["name"]
        score_func_name = f"score_{name}"

        if name == "performance" and not has_perf_config:
            unavailable_dims.add(name)
            continue

        if custom_scorer and hasattr(custom_scorer, score_func_name):
            func = getattr(custom_scorer, score_func_name)
            try:
                scores[name] = float(func(generated_code, str(work_dir)))
            except NotImplementedError:
                scores[name] = _default_score(name, target_path, work_dir, scoring_config, elapsed_seconds)
            except Exception:
                scores[name] = 0.0
        else:
            scores[name] = _default_score(name, target_path, work_dir, scoring_config, elapsed_seconds)

    # Redistribute weights for unavailable dimensions
    active_dims = [d for d in dimensions if d["name"] not in unavailable_dims]
    total_active_weight = sum(d["weight"] for d in active_dims)

    total = 0.0
    for dim in active_dims:
        effective_weight = dim["weight"] / total_active_weight if total_active_weight > 0 else 0
        total += scores.get(dim["name"], 0.0) * effective_weight

    total = min(max(total, 0.0), 1.0)

    return {"scores": scores, "total": round(total, 4)}


def _default_score(name: str, target_path: Path, work_dir: Path, scoring_config: dict | None = None, elapsed_seconds: float | None = None) -> float:
    """Get default score for a dimension."""
    scoring_config = scoring_config or {}
    if name == "correctness":
        exponent = scoring_config.get("correctness_exponent", 4.0)
        return _default_correctness(work_dir, exponent=exponent)
    elif name == "code_quality":
        return _default_code_quality(target_path, work_dir)
    elif name == "performance":
        perf_config = scoring_config.get("performance", {})
        fast = perf_config.get("fast_seconds", 1.0)
        slow = perf_config.get("slow_seconds", 10.0)
        if elapsed_seconds is not None:
            return _continuous_performance_score(elapsed_seconds, fast, slow)
        return 0.5
    elif name == "security":
        return _security_score(target_path)
    elif name == "robustness":
        return _robustness_score(target_path)
    elif name == "resource_efficiency":
        return _resource_efficiency_score(target_path)
    else:
        return 0.5


def _default_correctness(work_dir: Path, exponent: float = 4.0) -> float:
    """Default correctness: auto-detect project type and run tests."""
    if _detect_java_maven(work_dir):
        return _run_maven_test(work_dir, exponent=exponent)
    if _detect_dotnet(work_dir):
        return _run_dotnet_test(work_dir)
    passed, total = _run_pytest(work_dir)
    raw = passed / total
    return round(raw ** exponent, 4)


def _java_code_quality(work_dir: Path) -> float:
    """Java code quality using unified 5-dimension framework."""
    dimensions = {}

    # static_analysis: compile + spotbugs
    compile_ok = _run_maven_compile(work_dir) == 1.0
    spotbugs = _run_spotbugs(work_dir) if compile_ok else 0.0
    dimensions["static_analysis"] = round((compile_ok + spotbugs) / 2, 4) if compile_ok else 0.3

    # documentation: check for Javadoc on public methods
    dimensions["documentation"] = _java_documentation_score(work_dir)

    # error_handling: check for try/catch, throws declarations
    dimensions["error_handling"] = _java_error_handling_score(work_dir)

    # naming_style: check for camelCase conventions
    dimensions["naming_style"] = _java_naming_style_score(work_dir)

    # structure: check for class organization, modularity
    dimensions["structure"] = _java_structure_score(work_dir)

    return _summarize_quality(dimensions)


def _run_spotbugs(work_dir: Path) -> float:
    """Run spotbugs if available, return quality score."""
    try:
        result = subprocess.run(
            ["mvn", "spotbugs:check", "-q"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_VERY_LONG,
        )
        if result.returncode == 0:
            return 1.0
        bugs = result.stdout.count("bug")
        return round(max(0.0, 1.0 - bugs * 0.1), 4)
    except Exception:
        return 0.5


def _java_documentation_score(work_dir: Path) -> float:
    java_files = list(work_dir.rglob("*.java"))
    if not java_files:
        return 0.5
    src_files = [f for f in java_files if "test" not in str(f).lower()]
    if not src_files:
        src_files = java_files
    total = 0.0
    for f in src_files:
        source = f.read_text()
        public_methods = len(re.findall(r'\bpublic\b.*\b\w+\s*\([^)]*\)\s*\{', source))
        javadocs = source.count("/**")
        if public_methods == 0:
            total += 0.8
        else:
            total += min(javadocs / public_methods, 1.0)
    return round(total / len(src_files), 4)


def _java_error_handling_score(work_dir: Path) -> float:
    java_files = list(work_dir.rglob("*.java"))
    if not java_files:
        return 0.5
    src_files = [f for f in java_files if "test" not in str(f).lower()]
    if not src_files:
        src_files = java_files
    total = 0.0
    for f in src_files:
        source = f.read_text()
        score = 0.0
        if "try" in source:
            score += 0.3
        if "catch" in source:
            score += 0.3
        if "throws" in source:
            score += 0.2
        if "finally" in source:
            score += 0.2
        total += min(score, 1.0)
    return round(total / len(src_files), 4)


def _java_naming_style_score(work_dir: Path) -> float:
    java_files = list(work_dir.rglob("*.java"))
    if not java_files:
        return 0.5
    src_files = [f for f in java_files if "test" not in str(f).lower()]
    if not src_files:
        src_files = java_files
    total = 0.0
    for f in src_files:
        source = f.read_text()
        classes = re.findall(r'class\s+(\w+)', source)
        methods = re.findall(r'(?:public|private|protected)?\s*(?:static\s+)?\w+\s+(\w+)\s*\(', source)
        ok = 0
        total_names = 0
        for name in classes:
            total_names += 1
            if name[0].isupper():
                ok += 1
        for name in methods:
            if name in ("if", "while", "for", "switch"):
                continue
            total_names += 1
            if name[0].islower():
                ok += 1
        if total_names == 0:
            total += 0.8
        else:
            total += ok / total_names
    return round(total / len(src_files), 4)


def _java_structure_score(work_dir: Path) -> float:
    java_files = list(work_dir.rglob("*.java"))
    if not java_files:
        return 0.5
    src_files = [f for f in java_files if "test" not in str(f).lower()]
    if not src_files:
        src_files = java_files
    total = 0.0
    for f in src_files:
        source = f.read_text()
        score = 0.0
        if "class " in source:
            score += 0.3
        if "interface " in source:
            score += 0.2
        methods = len(re.findall(r'\b\w+\s+\w+\s*\([^)]*\)\s*\{', source))
        if methods >= 2:
            score += 0.3
        elif methods == 1:
            score += 0.15
        if "package " in source:
            score += 0.2
        total += min(score, 1.0)
    return round(total / len(src_files), 4)

def _dotnet_code_quality(work_dir: Path) -> float:
    """.NET code quality using unified 5-dimension framework."""
    dimensions = {}

    # static_analysis: build warnings + compile
    build_ok, warnings = _run_dotnet_build_with_warnings(work_dir)
    dimensions["static_analysis"] = round(1.0 - min(warnings * 0.05, 0.5), 4) if build_ok else 0.3

    # documentation: XML doc comments
    dimensions["documentation"] = _dotnet_documentation_score(work_dir)

    # error_handling: try/catch, throw
    dimensions["error_handling"] = _dotnet_error_handling_score(work_dir)

    # naming_style: PascalCase for methods/classes, camelCase for variables
    dimensions["naming_style"] = _dotnet_naming_style_score(work_dir)

    # structure: namespaces, classes, methods
    dimensions["structure"] = _dotnet_structure_score(work_dir)

    return _summarize_quality(dimensions)


def _run_dotnet_build_with_warnings(work_dir: Path) -> tuple[bool, int]:
    """Run dotnet build and return (success, warning_count)."""
    try:
        result = subprocess.run(
            ["dotnet", "build", "--verbosity", "normal"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_LONG,
        )
        if result.returncode != 0:
            return False, 0
        warnings = result.stdout.count("warning")
        return True, warnings
    except Exception:
        return False, 0


def _dotnet_documentation_score(work_dir: Path) -> float:
    cs_files = list(work_dir.rglob("*.cs"))
    if not cs_files:
        return 0.5
    src_files = [f for f in cs_files if "test" not in str(f).lower() and "Test" not in f.name]
    if not src_files:
        src_files = cs_files
    total = 0.0
    for f in src_files:
        source = f.read_text()
        public_members = len(re.findall(r'\bpublic\b', source))
        xml_docs = len(re.findall(r'\s*///', source))
        if public_members == 0:
            total += 0.8
        else:
            total += min(xml_docs / public_members, 1.0)
    return round(total / len(src_files), 4)


def _dotnet_error_handling_score(work_dir: Path) -> float:
    cs_files = list(work_dir.rglob("*.cs"))
    if not cs_files:
        return 0.5
    src_files = [f for f in cs_files if "test" not in str(f).lower() and "Test" not in f.name]
    if not src_files:
        src_files = cs_files
    total = 0.0
    for f in src_files:
        source = f.read_text()
        score = 0.0
        if "try" in source:
            score += 0.3
        if "catch" in source:
            score += 0.3
        if "throw" in source:
            score += 0.2
        if "finally" in source:
            score += 0.2
        total += min(score, 1.0)
    return round(total / len(src_files), 4)


def _dotnet_naming_style_score(work_dir: Path) -> float:
    cs_files = list(work_dir.rglob("*.cs"))
    if not cs_files:
        return 0.5
    src_files = [f for f in cs_files if "test" not in str(f).lower() and "Test" not in f.name]
    if not src_files:
        src_files = cs_files
    total = 0.0
    for f in src_files:
        source = f.read_text()
        classes = re.findall(r'class\s+(\w+)', source)
        methods = re.findall(r'(?:public|private|protected|internal)?\s*(?:static\s+)?\w+\s+(\w+)\s*\(', source)
        ok = 0
        total_names = 0
        for name in classes:
            total_names += 1
            if name[0].isupper():
                ok += 1
        for name in methods:
            if name in ("if", "while", "for", "switch", "using"):
                continue
            total_names += 1
            if name[0].isupper():
                ok += 1
        if total_names == 0:
            total += 0.8
        else:
            total += ok / total_names
    return round(total / len(src_files), 4)


def _dotnet_structure_score(work_dir: Path) -> float:
    cs_files = list(work_dir.rglob("*.cs"))
    if not cs_files:
        return 0.5
    src_files = [f for f in cs_files if "test" not in str(f).lower() and "Test" not in f.name]
    if not src_files:
        src_files = cs_files
    total = 0.0
    for f in src_files:
        source = f.read_text()
        score = 0.0
        if "namespace " in source:
            score += 0.2
        if "class " in source:
            score += 0.3
        if "interface " in source:
            score += 0.2
        methods = len(re.findall(r'\b\w+\s+\w+\s*\([^)]*\)\s*\{', source))
        if methods >= 2:
            score += 0.3
        elif methods == 1:
            score += 0.15
        total += min(score, 1.0)
    return round(total / len(src_files), 4)


def _react_code_quality(work_dir: Path) -> float:
    """React code quality using unified 5-dimension framework."""
    tsx_files = list(work_dir.rglob("*.tsx")) + list(work_dir.rglob("*.ts"))
    src_files = [f for f in tsx_files if "test" not in str(f).lower() and "node_modules" not in str(f)]
    if not src_files:
        src_files = tsx_files
    if not src_files:
        return 0.5

    dimensions = {}

    # static_analysis: TypeScript compilation check (tsc --noEmit)
    dimensions["static_analysis"] = _react_typescript_check(work_dir)

    # documentation: JSDoc / inline comments
    total_docs = 0.0
    for f in src_files:
        source = f.read_text()
        comments = source.count("//") + source.count("/*")
        loc = max(len(source.split("\n")), 1)
        total_docs += min(comments / (loc * 0.1), 1.0)
    dimensions["documentation"] = round(total_docs / len(src_files), 4)

    # error_handling: error boundaries, try/catch
    total_err = 0.0
    for f in src_files:
        source = f.read_text()
        score = 0.0
        if "try" in source:
            score += 0.3
        if "catch" in source:
            score += 0.3
        if "ErrorBoundary" in source or "error boundary" in source.lower():
            score += 0.4
        total_err += min(score, 1.0)
    dimensions["error_handling"] = round(total_err / len(src_files), 4)

    # naming_style: PascalCase for components, camelCase for hooks/utils
    total_name = 0.0
    for f in src_files:
        source = f.read_text()
        components = re.findall(r'(?:function|const)\s+(\w+)', source)
        ok = 0
        for name in components:
            if name[0].isupper():  # PascalCase for components
                ok += 1
            elif name.startswith("use"):  # hooks
                ok += 1
            elif name[0].islower():  # camelCase
                ok += 1
        if components:
            total_name += ok / len(components)
        else:
            total_name += 0.8
    dimensions["naming_style"] = round(total_name / len(src_files), 4)

    # structure: component decomposition (multiple components/hooks)
    total_struct = 0.0
    for f in src_files:
        source = f.read_text()
        score = 0.0
        exports = len(re.findall(r'export\s+(?:default\s+)?', source))
        if exports >= 1:
            score += 0.3
        components = len(re.findall(r'(?:function|const)\s+\w+\s*[:=].*=>', source))
        if components >= 2:
            score += 0.4
        elif components == 1:
            score += 0.2
        if "import " in source:
            score += 0.3
        total_struct += min(score, 1.0)
    dimensions["structure"] = round(total_struct / len(src_files), 4)

    return _summarize_quality(dimensions)


def _react_typescript_check(work_dir: Path) -> float:
    """Run TypeScript compiler for static analysis score."""
    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_LONG,
        )
        if result.returncode == 0:
            return 1.0
        errors = result.stdout.count("error TS")
        return round(max(0.0, 1.0 - errors * 0.1), 4)
    except Exception:
        return 0.5


def _bash_code_quality(work_dir: Path) -> float:
    """Bash code quality using unified 5-dimension framework."""
    sh_files = list(work_dir.rglob("*.sh"))
    src_files = [f for f in sh_files if "test" not in str(f).lower()]
    if not src_files:
        src_files = sh_files
    if not src_files:
        return 0.5

    dimensions = {}

    # documentation: comments
    total = 0.0
    for f in src_files:
        source = f.read_text()
        lines = source.split("\n")
        comments = sum(1 for line in lines if line.strip().startswith("#"))
        loc = max(len(lines), 1)
        total += min(comments / (loc * 0.05), 1.0)
    dimensions["documentation"] = round(total / len(src_files), 4)

    # error_handling: set -e, trap, exit checks
    total_err = 0.0
    for f in src_files:
        source = f.read_text()
        score = 0.0
        if "set -e" in source or "set -o errexit" in source:
            score += 0.4
        if "trap " in source:
            score += 0.3
        if "exit " in source or "return " in source:
            score += 0.3
        total_err += min(score, 1.0)
    dimensions["error_handling"] = round(total_err / len(src_files), 4)

    # naming_style: variable quoting (best practice)
    total_name = 0.0
    for f in src_files:
        source = f.read_text()
        var_refs = re.findall(r'\$\w+', source)
        quoted_vars = re.findall(r'"\$\w+', source)
        if var_refs:
            total_name += min(len(quoted_vars) / len(var_refs) * 1.5, 1.0)
        else:
            total_name += 0.8
    dimensions["naming_style"] = round(total_name / len(src_files), 4)

    # structure: functions, modularity
    total_struct = 0.0
    for f in src_files:
        source = f.read_text()
        lines = source.split("\n")
        score = 0.0
        funcs = len(re.findall(r'^\s*\w+\s*\(\)', source, re.MULTILINE))
        funcs += len(re.findall(r'^\s*function\s+\w+', source, re.MULTILINE))
        if funcs >= 2:
            score += 0.5
        elif funcs == 1:
            score += 0.3
        if len(lines) > 20 and funcs == 0:
            score += 0.1
        if "source " in source or ". " in source:
            score += 0.2
        total_struct += min(score, 1.0)
    dimensions["structure"] = round(total_struct / len(src_files), 4)

    # static_analysis: shellcheck (if available)
    total_static = 0.0
    for f in src_files:
        try:
            result = subprocess.run(
                ["shellcheck", str(f)],
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_SHORT,
            )
            if result.returncode == 0:
                total_static += 1.0
            else:
                issues = result.stdout.count("SC")
                total_static += max(0.0, 1.0 - issues * 0.1)
        except Exception:
            total_static += 0.5
    dimensions["static_analysis"] = round(total_static / len(src_files), 4)

    return _summarize_quality(dimensions)


def _rust_code_quality(work_dir: Path) -> float:
    """Rust code quality using unified 5-dimension framework."""
    rs_files = list(work_dir.rglob("*.rs"))
    src_files = [f for f in rs_files if "test" not in str(f).lower() and "target" not in str(f)]
    if not src_files:
        src_files = rs_files
    if not src_files:
        return 0.5

    dimensions = {}

    # documentation: doc comments (/// or //!)
    total_docs = 0.0
    for f in src_files:
        source = f.read_text()
        doc_lines = sum(1 for line in source.split("\n") if line.strip().startswith("///") or line.strip().startswith("//!"))
        funcs = source.count("fn ")
        if funcs > 0:
            total_docs += min(doc_lines / funcs, 1.0)
        else:
            total_docs += 0.8
    dimensions["documentation"] = round(total_docs / len(src_files), 4)

    # error_handling: Result, Option, ?, unwrap/expect
    total_err = 0.0
    for f in src_files:
        source = f.read_text()
        score = 0.0
        if "Result<" in source:
            score += 0.3
        if "Option<" in source:
            score += 0.2
        if "?" in source:
            score += 0.3
        if source.count("unwrap()") == 0 and source.count("expect(") == 0:
            score += 0.2
        total_err += min(score, 1.0)
    dimensions["error_handling"] = round(total_err / len(src_files), 4)

    # naming_style: snake_case for functions, PascalCase for types
    total_name = 0.0
    for f in src_files:
        source = f.read_text()
        fns = re.findall(r'fn\s+(\w+)', source)
        types = re.findall(r'(?:struct|enum|trait)\s+(\w+)', source)
        ok = 0
        total_names = 0
        for name in fns:
            total_names += 1
            if "_" in name or name.islower():
                ok += 1
        for name in types:
            total_names += 1
            if name[0].isupper():
                ok += 1
        if total_names == 0:
            total_name += 0.8
        else:
            total_name += ok / total_names
    dimensions["naming_style"] = round(total_name / len(src_files), 4)

    # structure: modules, visibility, traits
    total_struct = 0.0
    for f in src_files:
        source = f.read_text()
        score = 0.0
        if "mod " in source:
            score += 0.2
        if "use " in source:
            score += 0.2
        if "pub " in source:
            score += 0.3
        if "impl " in source or "trait " in source:
            score += 0.3
        total_struct += min(score, 1.0)
    dimensions["structure"] = round(total_struct / len(src_files), 4)

    # static_analysis: cargo check
    total_static = 0.0
    for f in src_files:
        try:
            result = subprocess.run(
                ["cargo", "check"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_LONG,
            )
            if result.returncode == 0:
                total_static += 1.0
            else:
                errors = result.stderr.count("error[")
                total_static += max(0.0, 1.0 - errors * 0.1)
        except Exception:
            total_static += 0.5
    dimensions["static_analysis"] = round(total_static / len(src_files), 4)

    return _summarize_quality(dimensions)


def _python_code_quality(target_path: Path) -> dict[str, float]:
    """Python code quality broken into unified dimensions."""
    if not target_path.exists():
        return {k: 0.0 for k in _QUALITY_DIMENSION_WEIGHTS}

    dimensions = {}

    # static_analysis: lint score
    lint_issues = _count_ruff_issues(target_path)
    loc = max(len(target_path.read_text().strip().split("\n")), 1)
    dimensions["static_analysis"] = round(max(0.0, 1.0 - lint_issues / loc), 4)

    # documentation: docstrings
    dimensions["documentation"] = _docstring_score(target_path)

    # error_handling: try/except/raise
    dimensions["error_handling"] = _error_handling_score(target_path)

    # naming_style: type hints coverage
    dimensions["naming_style"] = _type_hint_score(target_path)

    # structure: complexity
    complexity = _complexity_score(target_path)
    dimensions["structure"] = complexity

    return dimensions


def _default_code_quality(target_path: Path, work_dir: Path) -> float:
    """Default code quality: auto-detect project type."""
    if _detect_java_maven(work_dir):
        return _java_code_quality(work_dir)
    if _detect_dotnet(work_dir):
        return _dotnet_code_quality(work_dir)
    # React (package.json + .tsx/.ts files)
    if (work_dir / "package.json").exists() and list(work_dir.rglob("*.tsx")):
        return _react_code_quality(work_dir)
    # Bash (.sh files)
    if list(work_dir.rglob("*.sh")) and not target_path.suffix == ".py":
        return _bash_code_quality(work_dir)
    # Rust (Cargo.toml)
    if (work_dir / "Cargo.toml").exists():
        return _rust_code_quality(work_dir)
    if not target_path.exists():
        return 0.0

    dimensions = _python_code_quality(target_path)
    return _summarize_quality(dimensions)
