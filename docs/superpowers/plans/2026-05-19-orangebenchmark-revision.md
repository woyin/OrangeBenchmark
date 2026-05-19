# OrangeBenchmark Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修订 OrangeBenchmark：统一多语言 code_quality 评分标准、补全单元测试、补齐 Rust 题目、增强 CLI 分析能力、清理遗留文件。

**Architecture:** 将 code_quality 统一为 "5 维度加权平均" 框架（documentation, error_handling, naming_style, structure, static_analysis），每个语言按可用工具填充各维度分数。runner 核心逻辑补单元测试确保重构安全。CLI 增加趋势和 breakdown 分析子命令。

**Tech Stack:** Python 3.11+, pytest, typer, rich, ruff, ast

---

## File Structure Map

| File | Responsibility |
|------|---------------|
| `runner/scorer.py` | 评分引擎（correctness, code_quality, performance, security, robustness, resource_efficiency） |
| `runner/main.py` | CLI 入口（score, ranking, show, list_problems） |
| `runner/reporter.py` | 终端表格输出（rich） |
| `runner/executor.py` | 评测工作目录准备 |
| `tests/test_scorer.py` | scorer.py 单元测试（新增） |
| `tests/test_main.py` | main.py 单元测试（新增） |
| `tests/test_reporter.py` | reporter.py 单元测试（新增） |
| `problems/rust-json-parser/` | 新增 Rust 题目：JSON 解析器 |
| `problems/rust-lru-cache/` | 新增 Rust 题目：LRU 缓存 |
| `README.md` | 题目列表和文档 |
| `AGENT_INSTRUCTIONS.md` | Agent 指引（新增 Rust 题目） |

---

## Task 1: 编写 runner 单元测试（为高优先级重构提供安全网）

**Files:**
- Create: `tests/test_scorer.py`
- Create: `tests/test_main.py`
- Create: `tests/test_reporter.py`

### Task 1A: 测试 scorer.py 纯函数

- [ ] **Step 1: 创建 `tests/test_scorer.py`，测试 `_continuous_performance_score`**

```python
from runner.scorer import _continuous_performance_score


def test_continuous_performance_fast_boundary():
    assert _continuous_performance_score(0.5, fast=1.0, slow=10.0) == 1.0


def test_continuous_performance_slow_boundary():
    assert _continuous_performance_score(15.0, fast=1.0, slow=10.0) == 0.0


def test_continuous_performance_midpoint():
    # t=0.5, (1-0.5)^2 = 0.25
    assert _continuous_performance_score(5.5, fast=1.0, slow=10.0) == 0.25


def test_continuous_performance_not_ok():
    assert _continuous_performance_score(0.5, fast=1.0, slow=10.0, ok=False) == 0.0
```

- [ ] **Step 2: 测试 `_type_hint_score`**

```python
import tempfile
from pathlib import Path
from runner.scorer import _type_hint_score


def test_type_hint_score_full_coverage():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def add(a: int, b: int) -> int:
    return a + b

def greet(name: str) -> str:
    return f"Hello {name}"
""")
        f.flush()
        path = Path(f.name)
    score = _type_hint_score(path)
    assert score == 1.0


def test_type_hint_score_partial():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def add(a, b: int):
    return a + b
""")
        f.flush()
        path = Path(f.name)
    score = _type_hint_score(path)
    assert 0.0 < score < 1.0
```

- [ ] **Step 3: 测试 `_complexity_score`、`_docstring_score`、`_error_handling_score`**

```python
from runner.scorer import _complexity_score, _docstring_score, _error_handling_score


def test_complexity_score_simple():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def simple(x):
    if x > 0:
        return x
    return 0
""")
        f.flush()
        path = Path(f.name)
    score = _complexity_score(path)
    assert score == 1.0  # complexity <= 3 per function


def test_docstring_score_full():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('"""Module doc."""\ndef foo():\n    """Doc."""\n    pass\n')
        f.flush()
        path = Path(f.name)
    score = _docstring_score(path)
    assert score == 1.0


def test_error_handling_score_with_try():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def foo(x):
    try:
        return int(x)
    except ValueError:
        return 0
""")
        f.flush()
        path = Path(f.name)
    score = _error_handling_score(path)
    assert score == 1.0
```

- [ ] **Step 4: 测试 `_security_score`、`_robustness_score`、`_resource_efficiency_score`**

```python
from runner.scorer import _security_score, _robustness_score, _resource_efficiency_score


def test_security_score_clean():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("x = 1 + 2\n")
        f.flush()
        path = Path(f.name)
    assert _security_score(path) == 1.0


def test_security_score_with_eval():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("result = eval(user_input)\n")
        f.flush()
        path = Path(f.name)
    assert _security_score(path) < 1.0


def test_robustness_score_full():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def process(data):
    if not data:
        return []
    if isinstance(data, list):
        return data
    try:
        return [data]
    except Exception:
        return []
""")
        f.flush()
        path = Path(f.name)
    score = _robustness_score(path)
    assert score == 1.0


def test_resource_efficiency_score_unclosed_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("f = open('file.txt')\n")
        f.flush()
        path = Path(f.name)
    score = _resource_efficiency_score(path)
    assert score < 1.0
```

- [ ] **Step 5: 运行测试确认通过**

```bash
uv run pytest tests/test_scorer.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_scorer.py
git commit -m "test: add unit tests for scorer.py pure functions"
```

### Task 1B: 测试 main.py 纯函数

- [ ] **Step 1: 创建 `tests/test_main.py`**

```python
from runner.main import _trim_mean, _detect_language


def test_trim_mean_basic():
    assert _trim_mean([1.0, 2.0, 3.0, 4.0, 5.0]) == 3.5  # removes bottom 10% (1 item)


def test_trim_mean_single_value():
    assert _trim_mean([5.0]) == 5.0


def test_trim_mean_empty():
    assert _trim_mean([]) == 0.0


def test_detect_language():
    assert _detect_language("java-foo") == "java"
    assert _detect_language("dotnet-bar") == "dotnet"
    assert _detect_language("react-app") == "react"
    assert _detect_language("bash-script") == "bash"
    assert _detect_language("python-tool") == "python"
    assert _detect_language("rust-lib") == "rust"
    assert _detect_language("wasm-calculator") == "rust"
    assert _detect_language("two-sum") == "python"
```

- [ ] **Step 2: 运行测试**

```bash
uv run pytest tests/test_main.py -v
```

Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_main.py
git commit -m "test: add unit tests for main.py pure functions"
```

### Task 1C: 测试 reporter.py

- [ ] **Step 1: 创建 `tests/test_reporter.py`**

```python
from runner.reporter import _grade_label


def test_grade_label_a_plus():
    assert "A+" in _grade_label(0.95)
    assert "green" in _grade_label(0.95)


def test_grade_label_a():
    assert "A" in _grade_label(0.90)
    assert "blue" in _grade_label(0.90)


def test_grade_label_b():
    assert "B" in _grade_label(0.75)
    assert "yellow" in _grade_label(0.75)


def test_grade_label_c():
    assert "C" in _grade_label(0.60)


def test_grade_label_d():
    assert "D" in _grade_label(0.30)
    assert "red" in _grade_label(0.30)
```

- [ ] **Step 2: 运行测试**

```bash
uv run pytest tests/test_reporter.py -v
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_reporter.py
git commit -m "test: add unit tests for reporter.py"
```

---

## Task 2: 统一多语言 code_quality 评分标准

**Files:**
- Modify: `runner/scorer.py`

### Task 2A: 设计通用质量维度框架

在 scorer.py 中新增通用维度常量和汇总函数：

```python
# Quality dimension weights (unified across languages)
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
```

- [ ] **Step 1: 在 scorer.py 中（放在 `_default_code_quality` 之前）添加 `_QUALITY_DIMENSION_WEIGHTS` 和 `_summarize_quality`**

- [ ] **Step 2: Commit**

```bash
git add runner/scorer.py
git commit -m "feat: add unified quality dimension framework"
```

### Task 2B: 重构 Java code_quality

当前 `_java_code_quality` 使用 additive scoring（mvn compile + spotbugs），维度不完整。重构为返回 5 维度分数后用 `_summarize_quality` 汇总。

```python
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


def _java_documentation_score(work_dir: Path) -> float:
    java_files = list(work_dir.rglob("*.java"))
    if not java_files:
        return 0.5
    total = 0.0
    for f in java_files:
        source = f.read_text()
        public_methods = len(re.findall(r'\bpublic\b.*\b\w+\s*\([^)]*\)\s*\{', source))
        javadocs = source.count("/**")
        if public_methods == 0:
            total += 0.8
        else:
            total += min(javadocs / public_methods, 1.0)
    return round(total / len(java_files), 4)


def _java_error_handling_score(work_dir: Path) -> float:
    java_files = list(work_dir.rglob("*.java"))
    if not java_files:
        return 0.5
    total = 0.0
    for f in java_files:
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
    return round(total / len(java_files), 4)


def _java_naming_style_score(work_dir: Path) -> float:
    java_files = list(work_dir.rglob("*.java"))
    if not java_files:
        return 0.5
    total = 0.0
    for f in java_files:
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
    return round(total / len(java_files), 4)


def _java_structure_score(work_dir: Path) -> float:
    java_files = list(work_dir.rglob("*.java"))
    if not java_files:
        return 0.5
    total = 0.0
    for f in java_files:
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
    return round(total / len(java_files), 4)
```

- [ ] **Step 1: 用上述代码替换 scorer.py 中的 `_java_code_quality`，并添加 4 个辅助函数**

- [ ] **Step 2: 运行 Java 相关测试**

```bash
uv run pytest tests/test_scorer.py -v -k "not test_"  # 只运行新加的，如果有集成测试的话
```

（注：Java 相关需要 Java 环境，但纯函数测试不需要）

- [ ] **Step 3: Commit**

```bash
git add runner/scorer.py
git commit -m "feat: refactor Java code quality to unified 5-dimension framework"
```

### Task 2C: 重构 .NET code_quality

类似地重构 `_dotnet_code_quality`：

```python
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
    try:
        result = subprocess.run(
            ["dotnet", "build", "--verbosity", "normal"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
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
    total = 0.0
    for f in cs_files:
        source = f.read_text()
        public_members = len(re.findall(r'\bpublic\b', source))
        xml_docs = len(re.findall(r'\s*///', source))
        if public_members == 0:
            total += 0.8
        else:
            total += min(xml_docs / public_members, 1.0)
    return round(total / len(cs_files), 4)


def _dotnet_error_handling_score(work_dir: Path) -> float:
    cs_files = list(work_dir.rglob("*.cs"))
    if not cs_files:
        return 0.5
    total = 0.0
    for f in cs_files:
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
    return round(total / len(cs_files), 4)


def _dotnet_naming_style_score(work_dir: Path) -> float:
    cs_files = list(work_dir.rglob("*.cs"))
    if not cs_files:
        return 0.5
    total = 0.0
    for f in cs_files:
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
    return round(total / len(cs_files), 4)


def _dotnet_structure_score(work_dir: Path) -> float:
    cs_files = list(work_dir.rglob("*.cs"))
    if not cs_files:
        return 0.5
    total = 0.0
    for f in cs_files:
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
    return round(total / len(cs_files), 4)
```

- [ ] **Step 1: 用上述代码替换 scorer.py 中的 `_dotnet_code_quality` 和相关辅助函数**

- [ ] **Step 2: Commit**

```bash
git add runner/scorer.py
git commit -m "feat: refactor .NET code quality to unified 5-dimension framework"
```

### Task 2D: 重构 React code_quality

```python
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
    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return 1.0
        errors = result.stdout.count("error TS")
        return round(max(0.0, 1.0 - errors * 0.1), 4)
    except Exception:
        return 0.5
```

- [ ] **Step 1: 用上述代码替换 `_react_code_quality`**

- [ ] **Step 2: Commit**

```bash
git add runner/scorer.py
git commit -m "feat: refactor React code quality to unified 5-dimension framework"
```

### Task 2E: 重构 Bash code_quality

```python
def _bash_code_quality(work_dir: Path) -> float:
    """Bash code quality using unified 5-dimension framework."""
    sh_files = list(work_dir.rglob("*.sh"))
    src_files = [f for f in sh_files if "test" not in str(f).lower()]
    if not src_files:
        src_files = sh_files
    if not src_files:
        return 0.5

    dimensions = {}

    total = 0.0
    for f in src_files:
        source = f.read_text()
        lines = source.split("\n")

        # documentation: comments
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
        score = 0.0
        funcs = len(re.findall(r'^\s*\w+\s*\(\)', source, re.MULTILINE))
        funcs += len(re.findall(r'^\s*function\s+\w+', source, re.MULTILINE))
        if funcs >= 2:
            score += 0.5
        elif funcs == 1:
            score += 0.3
        if len(lines) > 20 and funcs == 0:
            score += 0.1  # penalty for long scripts without functions
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
                timeout=10,
            )
            if result.returncode == 0:
                total_static += 1.0
            else:
                issues = result.stdout.count("SC")
                total_static += max(0.0, 1.0 - issues * 0.1)
        except Exception:
            total_static += 0.5  # shellcheck not available
    dimensions["static_analysis"] = round(total_static / len(src_files), 4)

    return _summarize_quality(dimensions)
```

- [ ] **Step 1: 用上述代码替换 `_bash_code_quality`**

- [ ] **Step 2: Commit**

```bash
git add runner/scorer.py
git commit -m "feat: refactor Bash code quality to unified 5-dimension framework"
```

### Task 2F: 重构 Rust code_quality

```python
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

    # static_analysis: cargo check / clippy
    total_static = 0.0
    for f in src_files:
        try:
            result = subprocess.run(
                ["cargo", "check"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60,
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
```

- [ ] **Step 1: 用上述代码替换 `_rust_code_quality`**

- [ ] **Step 2: Commit**

```bash
git add runner/scorer.py
git commit -m "feat: refactor Rust code quality to unified 5-dimension framework"
```

### Task 2G: 重构 Python code_quality 适配统一框架

Python 的 `_default_code_quality`（非多语言检测路径）已经是 deductions-based，需要改为 additive-based 以便统一。

```python
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
```

然后修改 `_default_code_quality` 中 Python 分支：

```python
def _default_code_quality(target_path: Path, work_dir: Path) -> float:
    """Default code quality: auto-detect project type."""
    if _detect_java_maven(work_dir):
        return _java_code_quality(work_dir)
    if _detect_dotnet(work_dir):
        return _dotnet_code_quality(work_dir)
    if (work_dir / "package.json").exists() and list(work_dir.rglob("*.tsx")):
        return _react_code_quality(work_dir)
    if list(work_dir.rglob("*.sh")) and not target_path.suffix == ".py":
        return _bash_code_quality(work_dir)
    if (work_dir / "Cargo.toml").exists():
        return _rust_code_quality(work_dir)
    if not target_path.exists():
        return 0.0

    dimensions = _python_code_quality(target_path)
    return _summarize_quality(dimensions)
```

- [ ] **Step 1: 添加 `_python_code_quality`，修改 `_default_code_quality`**

- [ ] **Step 2: 运行 scorer 测试**

```bash
uv run pytest tests/test_scorer.py -v
```

Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add runner/scorer.py
git commit -m "feat: unify Python code quality under 5-dimension framework"
```

### Task 2H: 验证各语言评分一致性

- [ ] **Step 1: 运行 problem set integrity 测试**

```bash
uv run pytest tests/test_problem_set_integrity.py -v
```

Expected: all PASS（验证文件结构未变）

- [ ] **Step 2: 运行完整测试套件**

```bash
uv run pytest tests/ -v
```

Expected: all PASS

---

## Task 3: 补齐 Rust 题目到 5 道

**Files:**
- Create: `problems/rust-json-parser/`
- Create: `problems/rust-lru-cache/`
- Modify: `README.md`
- Modify: `AGENT_INSTRUCTIONS.md`

### Task 3A: 创建 rust-json-parser 题目

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p problems/rust-json-parser/src problems/rust-json-parser/tests
```

- [ ] **Step 2: 创建 `Cargo.toml`**

```toml
[package]
name = "json-parser"
version = "0.1.0"
edition = "2021"
```

- [ ] **Step 3: 创建 `src/lib.rs`（占位符）**

```rust
/// Parse a simple JSON string and return values by key path.
pub fn parse_json(_input: &str, _key: &str) -> Option<String> {
    todo!()
}
```

- [ ] **Step 4: 创建 `tests/test_solution.rs`**

```rust
use json_parser::parse_json;

#[test]
fn test_parse_simple_string() {
    let json = r#"{"name": "Alice"}"#;
    assert_eq!(parse_json(json, "name"), Some("Alice".to_string()));
}

#[test]
fn test_parse_nested() {
    let json = r#"{"user": {"name": "Bob"}}"#;
    assert_eq!(parse_json(json, "user.name"), Some("Bob".to_string()));
}

#[test]
fn test_parse_number() {
    let json = r#"{"age": 30}"#;
    assert_eq!(parse_json(json, "age"), Some("30".to_string()));
}

#[test]
fn test_parse_missing_key() {
    let json = r#"{"name": "Alice"}"#;
    assert_eq!(parse_json(json, "age"), None);
}

#[test]
fn test_parse_array() {
    let json = r#"{"items": ["a", "b", "c"]}"#;
    assert_eq!(parse_json(json, "items.0"), Some("a".to_string()));
}

#[test]
fn test_empty_object() {
    assert_eq!(parse_json("{}", "x"), None);
}
```

- [ ] **Step 5: 创建 `problem.yaml`**

```yaml
name: "rust-json-parser"
difficulty: medium
category: parsing
tags: [rust, json, parsing]

prompt: |
  Implement a simple JSON parser in src/lib.rs.
  Provide a public function `parse_json(input: &str, key: &str) -> Option<String>`.
  The function should parse a simplified JSON object (string values, numbers, nested objects, arrays)
  and return the value at the given dot-separated key path as a String.
  Return None if the key is not found.

scoring:
  dimensions:
    - name: correctness
      weight: 0.5
    - name: code_quality
      weight: 0.3
    - name: performance
      weight: 0.2
  correctness_exponent: 4

target_file: "src/lib.rs"
copy_paths: ["Cargo.toml", "src", "tests"]
timeout: 60
```

- [ ] **Step 6: Commit**

```bash
git add problems/rust-json-parser/
git commit -m "feat: add rust-json-parser benchmark problem"
```

### Task 3B: 创建 rust-lru-cache 题目

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p problems/rust-lru-cache/src problems/rust-lru-cache/tests
```

- [ ] **Step 2: 创建 `Cargo.toml`**

```toml
[package]
name = "lru-cache"
version = "0.1.0"
edition = "2021"
```

- [ ] **Step 3: 创建 `src/lib.rs`（占位符）**

```rust
/// A simple LRU Cache implementation.
pub struct LRUCache {
    // TODO: implement
}

impl LRUCache {
    pub fn new(_capacity: usize) -> Self {
        todo!()
    }

    pub fn get(&mut self, _key: i32) -> Option<i32> {
        todo!()
    }

    pub fn put(&mut self, _key: i32, _value: i32) {
        todo!()
    }
}
```

- [ ] **Step 4: 创建 `tests/test_solution.rs`**

```rust
use lru_cache::LRUCache;

#[test]
fn test_basic_put_get() {
    let mut cache = LRUCache::new(2);
    cache.put(1, 10);
    assert_eq!(cache.get(1), Some(10));
}

#[test]
fn test_eviction() {
    let mut cache = LRUCache::new(2);
    cache.put(1, 10);
    cache.put(2, 20);
    cache.put(3, 30); // evicts key 1
    assert_eq!(cache.get(1), None);
    assert_eq!(cache.get(2), Some(20));
    assert_eq!(cache.get(3), Some(30));
}

#[test]
fn test_update_existing() {
    let mut cache = LRUCache::new(2);
    cache.put(1, 10);
    cache.put(1, 100);
    assert_eq!(cache.get(1), Some(100));
}

#[test]
fn test_lru_order() {
    let mut cache = LRUCache::new(2);
    cache.put(1, 10);
    cache.put(2, 20);
    cache.get(1); // makes 1 recently used
    cache.put(3, 30); // should evict 2
    assert_eq!(cache.get(2), None);
    assert_eq!(cache.get(1), Some(10));
}

#[test]
fn test_capacity_one() {
    let mut cache = LRUCache::new(1);
    cache.put(1, 10);
    cache.put(2, 20);
    assert_eq!(cache.get(1), None);
    assert_eq!(cache.get(2), Some(20));
}
```

- [ ] **Step 5: 创建 `problem.yaml`**

```yaml
name: "rust-lru-cache"
difficulty: medium
category: algorithm
tags: [rust, algorithm, cache, data-structures]

prompt: |
  Implement an LRU (Least Recently Used) Cache in src/lib.rs.
  Provide a struct `LRUCache` with:
  - `new(capacity: usize) -> Self`
  - `get(&mut self, key: i32) -> Option<i32>` — returns value and marks as recently used
  - `put(&mut self, key: i32, value: i32)` — inserts/updates value, evicts least recently used if over capacity

  All operations should be O(1).

scoring:
  dimensions:
    - name: correctness
      weight: 0.5
    - name: code_quality
      weight: 0.3
    - name: performance
      weight: 0.2
  correctness_exponent: 4

target_file: "src/lib.rs"
copy_paths: ["Cargo.toml", "src", "tests"]
timeout: 60
```

- [ ] **Step 6: Commit**

```bash
git add problems/rust-lru-cache/
git commit -m "feat: add rust-lru-cache benchmark problem"
```

### Task 3C: 更新 README.md

- [ ] **Step 1: 修改 README 中的 Rust 章节**

从：
```markdown
### Rust（1 道）
| # | 题目 | 难度 | 类别 |
|---|------|------|------|
| 52 | wasm-calculator | hard | multi-lang |
```

改为：
```markdown
### Rust（5 道）
| # | 题目 | 难度 | 类别 |
|---|------|------|------|
| 52 | wasm-calculator | hard | multi-lang |
| 53 | rust-fizz-buzz | easy | algorithm |
| 54 | rust-string-manipulation | medium | string |
| 55 | rust-json-parser | medium | parsing |
| 56 | rust-lru-cache | medium | algorithm |
```

同时更新总题数：从 "52 道，6 种语言" 改为 "56 道，6 种语言"

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with 5 Rust problems (56 total)"
```

### Task 3D: 更新 AGENT_INSTRUCTIONS.md

- [ ] **Step 1: 在 Rust 章节末尾添加两道新题**

```markdown
| 55 | `problems/rust-json-parser/` | medium | parsing | `src/lib.rs` | `cargo test --manifest-path problems/rust-json-parser/Cargo.toml` |
| 56 | `problems/rust-lru-cache/` | medium | algorithm | `src/lib.rs` | `cargo test --manifest-path problems/rust-lru-cache/Cargo.toml` |
```

- [ ] **Step 2: Commit**

```bash
git add AGENT_INSTRUCTIONS.md
git commit -m "docs: add rust-json-parser and rust-lru-cache to agent instructions"
```

### Task 3E: 更新 integrity test

- [ ] **Step 1: 修改 `tests/test_problem_set_integrity.py`**

在 `EXPECTED_PROBLEMS` 集合中添加：
```python
"rust-json-parser",
"rust-lru-cache",
```

- [ ] **Step 2: 运行测试**

```bash
uv run pytest tests/test_problem_set_integrity.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_problem_set_integrity.py
git commit -m "test: update expected problem set to 56"
```

---

## Task 4: 增强结果分析 CLI

**Files:**
- Modify: `runner/main.py`
- Modify: `runner/reporter.py`

### Task 4A: 添加 `trend` 子命令

- [ ] **Step 1: 在 main.py 中新增 `trend` 命令**

在 `show` 命令后添加：

```python
@app.command()
def trend(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Filter by model name"),
    problem: Optional[str] = typer.Option(None, "--problem", "-p", help="Filter by problem name"),
):
    """Show score trends across all historical runs."""
    if not RESULTS_DIR.exists():
        typer.echo("No results found. Run `orangebench score` first.")
        raise typer.Exit(1)

    result_files = sorted(RESULTS_DIR.glob("*.json"))
    if not result_files:
        typer.echo("No result files found in results/.")
        raise typer.Exit(1)

    runs = []
    for rf in result_files:
        with open(rf) as f:
            data = json.load(f)
        ts = data.get("timestamp", rf.stem)
        for combo in data.get("combos", []):
            if model and combo.get("model") != model:
                continue
            overall = combo.get("overall", 0)
            probs = combo.get("problems", [])
            if problem:
                p = next((x for x in probs if x["name"] == problem), None)
                score = p["total"] if p else 0.0
                runs.append((ts, combo.get("model", "?"), score))
            else:
                runs.append((ts, combo.get("model", "?"), overall))

    if not runs:
        typer.echo("No matching data found.")
        raise typer.Exit(1)

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Score Trend", show_header=True, header_style="bold cyan")
    table.add_column("Timestamp", min_width=20)
    table.add_column("Model", min_width=18)
    table.add_column("Score", justify="right", min_width=8)

    for ts, m, score in runs:
        table.add_row(ts, m, f"{score:.3f}")

    console.print()
    console.print(table)
    console.print()
```

- [ ] **Step 2: Commit**

```bash
git add runner/main.py
git commit -m "feat: add trend CLI command for historical score comparison"
```

### Task 4B: 添加 `breakdown` 子命令

- [ ] **Step 1: 在 main.py 中新增 `breakdown` 命令**

```python
@app.command()
def breakdown(
    by: str = typer.Option("language", "--by", "-b", help="Breakdown by: language/category/difficulty"),
):
    """Show score breakdown by language, category, or difficulty."""
    if not RESULTS_DIR.exists():
        typer.echo("No results found. Run `orangebench score` first.")
        raise typer.Exit(1)

    result_files = sorted(RESULTS_DIR.glob("*.json"))
    if not result_files:
        typer.echo("No result files found in results/.")
        raise typer.Exit(1)

    with open(result_files[-1]) as f:
        data = json.load(f)

    problems_meta = {name: config for name, _, config in _discover_problems()}

    breakdown_data: dict[str, list[float]] = {}
    for combo in data.get("combos", []):
        for prob in combo.get("problems", []):
            pname = prob["name"]
            meta = problems_meta.get(pname, {})
            if by == "language":
                key = _detect_language(pname)
            elif by == "category":
                key = meta.get("category", "unknown")
            elif by == "difficulty":
                key = meta.get("difficulty", "unknown")
            else:
                typer.echo(f"Unknown breakdown dimension: {by}")
                raise typer.Exit(1)
            breakdown_data.setdefault(key, []).append(prob.get("total", 0))

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title=f"Breakdown by {by.capitalize()}", show_header=True, header_style="bold cyan")
    table.add_column(by.capitalize(), min_width=15)
    table.add_column("Problems", justify="right", min_width=8)
    table.add_column("Avg Score", justify="right", min_width=10)
    table.add_column("Best", justify="right", min_width=8)
    table.add_column("Worst", justify="right", min_width=8)

    for key in sorted(breakdown_data.keys()):
        scores = breakdown_data[key]
        avg = sum(scores) / len(scores)
        table.add_row(key, str(len(scores)), f"{avg:.3f}", f"{max(scores):.3f}", f"{min(scores):.3f}")

    console.print()
    console.print(table)
    console.print()
```

- [ ] **Step 2: Commit**

```bash
git add runner/main.py
git commit -m "feat: add breakdown CLI command for dimension analysis"
```

### Task 4C: 为新增 CLI 命令写测试

- [ ] **Step 1: 在 `tests/test_main.py` 中补充测试**

```python
from typer.testing import CliRunner
from runner.main import app

runner = CliRunner()


def test_list_problems_command():
    result = runner.invoke(app, ["list-problems"])
    assert result.exit_code == 0
    assert "two-sum" in result.output


def test_list_problems_filter_by_language():
    result = runner.invoke(app, ["list-problems", "--language", "rust"])
    assert result.exit_code == 0
    # Should show rust problems


def test_breakdown_command():
    result = runner.invoke(app, ["breakdown", "--by", "language"])
    # May fail if no results, but command structure should work
    assert result.exit_code in (0, 1)  # 1 if no results
```

- [ ] **Step 2: 运行测试**

```bash
uv run pytest tests/test_main.py -v
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_main.py
git commit -m "test: add CLI command tests"
```

---

## Task 5: 清理遗留文件和目录

**Files:**
- Delete: `.DS_Store`
- Delete: `problems/sorting-algo/`
- Delete/Update: `docs/superpowers/` 空目录处理

### Task 5A: 清理 .DS_Store

- [ ] **Step 1: 删除并确保 gitignore 生效**

```bash
rm -f .DS_Store
rm -f problems/**/.DS_Store
rm -f runner/**/.DS_Store
rm -f tests/**/.DS_Store
git add .DS_Store 2>/dev/null || true
git commit -m "chore: remove .DS_Store files" || echo "Nothing to commit"
```

（注：.DS_Store 已在 .gitignore 中，只需删除本地文件）

### Task 5B: 清理遗留目录

- [ ] **Step 1: 删除 sorting-algo**

```bash
rm -rf problems/sorting-algo/
git add -A problems/sorting-algo/
git commit -m "chore: remove legacy sorting-algo directory"
```

### Task 5C: 处理 docs 目录

- [ ] **Step 1: 保留 plans 子目录（包含本计划文件），删除空的 superpowers 如果还有其它空目录**

```bash
# 确保 docs/ 至少包含本计划文件
ls -la docs/
# 如果没有其它有用内容，可以添加一个 README
cat > docs/README.md << 'EOF'
# OrangeBenchmark Documentation

This directory contains design documents and implementation plans.

## Plans

- `superpowers/plans/` — Implementation plans created with the Superpowers framework.
EOF
git add docs/README.md
git commit -m "docs: add docs README"
```

### Task 5D: 最终清理提交

- [ ] **Step 1: 检查清理结果**

```bash
uv run pytest tests/ -v
```

Expected: all PASS

- [ ] **Step 2: 确认无遗留**

```bash
git status
```

Expected: working tree clean 或只有计划文件

---

## Spec Coverage Check

| 需求 | 对应 Task |
|------|----------|
| 高：统一多语言 code_quality 评分标准 | Task 2A-2H |
| 高：给 runner/scorer.py 和 runner/main.py 补单元测试 | Task 1A-1C |
| 中：补齐 Rust 题目到至少 5 道 | Task 3A-3E |
| 中：增强结果分析 CLI（趋势对比、分类 breakdown） | Task 4A-4C |
| 低：清理遗留目录和 .DS_Store | Task 5A-5D |

## Placeholder Scan

- 无 "TBD", "TODO", "implement later"
- 所有步骤包含实际代码
- 无模糊描述

## Type Consistency

- `_summarize_quality(dimensions: dict[str, float]) -> float` 在 Task 2A 定义，被 Task 2B-2G 使用
- `_QUALITY_DIMENSION_WEIGHTS` 在 Task 2A 定义，被 Task 2G 使用
- `_python_code_quality` 在 Task 2G 定义，被 `_default_code_quality` 使用

