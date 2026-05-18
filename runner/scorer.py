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


def _run_maven_test(work_dir: Path, exponent: float = 4.0) -> float:
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
        return round(max(0.0, 1.0 - issue_count / loc), 4)
    except Exception:
        return 0.5


def _count_ruff_issues(file_path: Path) -> int:
    """Count ruff lint issues."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(file_path),
             "--output-format", "json"],
            capture_output=True, text=True, timeout=10,
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
    """Java code quality: Javadoc + exception handling + naming + structure."""
    java_files = list(work_dir.rglob("*.java"))
    if not java_files:
        return 0.5
    # Filter out test files
    src_files = [f for f in java_files if "test" not in str(f).lower()]
    if not src_files:
        src_files = java_files

    total_score = 0.0
    for f in src_files:
        try:
            source = f.read_text()
        except Exception:
            continue

        score = 0.0
        lines = source.split("\n")

        # +0.35 Javadoc on public methods/classes
        import re as _re
        public_methods = _re.findall(r'public\s+(?:static\s+)?(?:\w+\s+)+(\w+)\s*\(', source)
        public_classes = _re.findall(r'public\s+class\s+(\w+)', source)
        public_count = len(public_methods) + len(public_classes)
        javadoc_count = source.count("/**")
        if public_count > 0:
            score += 0.35 * min(javadoc_count / public_count, 1.0)
        else:
            score += 0.20

        # +0.20 exception handling
        if "try" in source and ("catch" in source or "throws" in source):
            score += 0.20

        # +0.20 naming conventions (camelCase methods, PascalCase classes)
        if public_classes:
            score += 0.10
        if public_methods:
            camel_ok = sum(1 for m in public_methods if m[0].islower())
            score += 0.10 * (camel_ok / len(public_methods) if public_methods else 0.5)

        # +0.25 code structure (imports + class definition)
        if "import " in source:
            score += 0.10
        if "class " in source:
            score += 0.15

        total_score += score

    return round(max(0.10, min(1.0, total_score / len(src_files))), 4)


def _dotnet_code_quality(work_dir: Path) -> float:
    """Code quality: XML doc + exception handling + naming + build warnings."""
    cs_files = list(work_dir.rglob("*.cs"))
    if not cs_files:
        return 0.5
    src_files = [f for f in cs_files if "test" not in str(f).lower() and "Test" not in f.name]
    if not src_files:
        src_files = cs_files

    total_score = 0.0
    for f in src_files:
        try:
            source = f.read_text()
        except Exception:
            continue

        score = 0.0

        # +0.30 XML doc comments (/// on public methods/classes)
        import re as _re
        public_methods = _re.findall(r'public\s+(?:static\s+)?(?:override\s+)?(?:\w+\s+)+(\w+)\s*[\(<]', source)
        public_classes = _re.findall(r'public\s+class\s+(\w+)', source)
        public_count = len(public_methods) + len(public_classes)
        xml_doc_count = source.count("/// <summary>")
        if public_count > 0:
            score += 0.30 * min(xml_doc_count / public_count, 1.0)
        else:
            score += 0.15

        # +0.20 exception handling
        if "try" in source and "catch" in source:
            score += 0.20

        # +0.20 naming (PascalCase methods)
        if public_methods:
            pascal_ok = sum(1 for m in public_methods if m[0].isupper())
            score += 0.20 * (pascal_ok / len(public_methods))
        else:
            score += 0.10

        # +0.15 structure (using + class)
        if "using " in source:
            score += 0.05
        if "class " in source or "struct " in source:
            score += 0.10

        total_score += score

    base = total_score / len(src_files)

    # +0.15 build warnings (deduction-based)
    try:
        result = subprocess.run(
            ["dotnet", "build", "--verbosity", "normal"],
            cwd=work_dir, capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            base -= 0.20
        else:
            warnings = result.stdout.lower().count("warning")
            base -= min(warnings * 0.03, 0.15)
    except Exception:
        pass

    return round(max(0.10, min(1.0, base)), 4)


def _react_code_quality(work_dir: Path) -> float:
    """React code quality: TypeScript types + component structure + events."""
    ts_files = list(work_dir.rglob("*.tsx")) + list(work_dir.rglob("*.ts"))
    if not ts_files:
        return 0.5
    src_files = [f for f in ts_files if "test" not in str(f).lower() and "node_modules" not in str(f)]
    if not src_files:
        src_files = ts_files[:3]

    total_score = 0.0
    for f in src_files:
        try:
            source = f.read_text()
        except Exception:
            continue

        score = 0.0

        # +0.30 TypeScript types (interface/type/React.FC)
        if "interface " in source or "type " in source:
            score += 0.20
        if ": " in source and ("string" in source or "number" in source or "boolean" in source):
            score += 0.10

        # +0.30 component structure (export default/function component)
        if "export default" in source or "export function" in source:
            score += 0.15
        if "return (" in source or "return <" in source:
            score += 0.15

        # +0.20 event handling (onClick/onChange/etc)
        import re as _re
        if _re.search(r'on[A-Z]\w+', source):
            score += 0.20

        # +0.20 code organization (imports)
        if "import " in source:
            score += 0.10
        if "from " in source:
            score += 0.10

        total_score += score

    return round(max(0.10, min(1.0, total_score / len(src_files))), 4)


def _bash_code_quality(work_dir: Path) -> float:
    """Bash code quality: shebang + quoting + error handling + functions."""
    sh_files = list(work_dir.rglob("*.sh"))
    if not sh_files:
        return 0.5
    src_files = [f for f in sh_files if "test" not in str(f).lower()]
    if not src_files:
        src_files = sh_files

    total_score = 0.0
    for f in src_files:
        try:
            source = f.read_text()
        except Exception:
            continue

        score = 0.0
        lines = source.split("\n")

        # +0.15 shebang
        if lines and lines[0].startswith("#!"):
            score += 0.15

        # +0.25 variable quoting ($var in double quotes)
        import re as _re
        var_refs = _re.findall(r'\$\w+', source)
        quoted_vars = _re.findall(r'"\$\w+', source)
        if var_refs:
            quote_ratio = len(quoted_vars) / len(var_refs)
            score += 0.25 * min(quote_ratio * 1.5, 1.0)  # Boost a bit
        else:
            score += 0.10

        # +0.30 error handling (set -e / trap / exit)
        if "set -e" in source or "set -o errexit" in source:
            score += 0.15
        elif "trap " in source:
            score += 0.10
        if "exit " in source or "return " in source:
            score += 0.15

        # +0.30 function definitions
        func_count = source.count("()") + len(_re.findall(r'^\s*function\s+\w+', source, _re.MULTILINE))
        if func_count > 0:
            score += 0.30
        elif len(lines) > 20:
            score += 0.10  # Non-trivial script without functions

        total_score += score

    return round(max(0.10, min(1.0, total_score / len(src_files))), 4)


def _rust_code_quality(work_dir: Path) -> float:
    """Rust code quality: docs + error handling + naming + structure."""
    rs_files = list(work_dir.rglob("*.rs"))
    if not rs_files:
        return 0.5
    src_files = [f for f in rs_files if "test" not in str(f).lower() and "target" not in str(f)]
    if not src_files:
        src_files = rs_files

    total_score = 0.0
    for f in src_files:
        try:
            source = f.read_text()
        except Exception:
            continue

        score = 0.0

        # +0.30 documentation comments (/// or //!)
        doc_lines = sum(1 for line in source.split("\n") if line.strip().startswith("///") or line.strip().startswith("//!"))
        func_count = source.count("fn ")
        if func_count > 0:
            score += 0.30 * min(doc_lines / func_count, 1.0)
        else:
            score += 0.15

        # +0.25 error handling (Result/unwrap/expect/?)
        if "Result<" in source or "unwrap()" in source or "expect(" in source:
            score += 0.15
        if "?" in source:
            score += 0.10

        # +0.20 naming (snake_case functions)
        import re as _re
        fns = _re.findall(r'fn\s+(\w+)', source)
        if fns:
            snake_ok = sum(1 for fn in fns if "_" in fn or fn.islower())
            score += 0.20 * (snake_ok / len(fns))
        else:
            score += 0.10

        # +0.25 structure (mod/use/pub)
        if "use " in source or "mod " in source:
            score += 0.10
        if "pub " in source:
            score += 0.15

        total_score += score

    return round(max(0.10, min(1.0, total_score / len(src_files))), 4)


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

    deductions = 0.0

    # Lint violations: -0.03 each, max -0.30
    lint_issues = _count_ruff_issues(target_path)
    deductions += min(lint_issues * 0.03, 0.30)

    # Missing type hints: proportional, max -0.25
    type_score = _type_hint_score(target_path)
    deductions += min((1 - type_score) * 0.25, 0.25)

    # Missing docstrings: proportional, max -0.20
    doc_score = _docstring_score(target_path)
    deductions += min((1 - doc_score) * 0.20, 0.20)

    # Cyclomatic complexity excess: -0.05 per 0.1 over 0.3, max -0.20
    complexity_score = _complexity_score(target_path)
    excess = 1 - complexity_score
    if excess > 0.3:
        deductions += min(((excess - 0.3) / 0.1) * 0.05, 0.20)

    # Missing error handling: proportional, max -0.20
    error_score = _error_handling_score(target_path)
    deductions += min((1 - error_score) * 0.20, 0.20)

    return round(max(0.10, 1.0 - deductions * 0.80), 4)
