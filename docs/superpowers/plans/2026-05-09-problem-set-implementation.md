# OrangeBenchmark Problem Set Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved 9-problem OrangeBenchmark problem set from `docs/superpowers/specs/2026-05-09-problem-set-design.md`.

**Architecture:** Keep each benchmark problem self-contained under `problems/<name>/` with `problem.yaml`, `solution.py` or language-native source files, tests, and optional `scoring.py`. Add minimal runner support for non-Python problems by copying declared scaffold files into the work directory and letting custom `scoring.py` execute language-specific tools. Move the old `sorting-algo` sample under an ignored examples directory so benchmark discovery returns the approved 9-problem set.

**Tech Stack:** Python 3.11, uv, pytest, ruff, Typer, PyYAML, Rust/Cargo for `wasm-calculator`, optional wasm target/tooling for future full Wasm validation.

---

## File Structure

Create:
- `tests/test_executor_prepare_work_dir.py` - verifies work directory copy behavior for Python and Rust-style problems.
- `problems/two-sum/problem.yaml`
- `problems/two-sum/conftest.py`
- `problems/two-sum/solution.py`
- `problems/two-sum/tests/test_solution.py`
- `problems/csv-stats/problem.yaml`
- `problems/csv-stats/conftest.py`
- `problems/csv-stats/solution.py`
- `problems/csv-stats/tests/test_solution.py`
- `problems/url-parser/problem.yaml`
- `problems/url-parser/conftest.py`
- `problems/url-parser/solution.py`
- `problems/url-parser/tests/test_solution.py`
- `problems/lru-cache/problem.yaml`
- `problems/lru-cache/conftest.py`
- `problems/lru-cache/solution.py`
- `problems/lru-cache/tests/test_solution.py`
- `problems/lru-cache/scoring.py`
- `problems/rest-api/problem.yaml`
- `problems/rest-api/conftest.py`
- `problems/rest-api/solution.py`
- `problems/rest-api/tests/test_solution.py`
- `problems/log-analyzer/problem.yaml`
- `problems/log-analyzer/conftest.py`
- `problems/log-analyzer/solution.py`
- `problems/log-analyzer/tests/test_solution.py`
- `problems/log-analyzer/scoring.py`
- `problems/text-editor/problem.yaml`
- `problems/text-editor/conftest.py`
- `problems/text-editor/solution.py`
- `problems/text-editor/tests/test_solution.py`
- `problems/text-editor/scoring.py`
- `problems/task-scheduler/problem.yaml`
- `problems/task-scheduler/conftest.py`
- `problems/task-scheduler/solution.py`
- `problems/task-scheduler/tests/test_solution.py`
- `problems/task-scheduler/scoring.py`
- `problems/wasm-calculator/problem.yaml`
- `problems/wasm-calculator/Cargo.toml`
- `problems/wasm-calculator/src/lib.rs`
- `problems/wasm-calculator/tests/test_calculator.rs`
- `problems/wasm-calculator/index.js`
- `problems/wasm-calculator/scoring.py`

Modify:
- `runner/executor.py` - copy declared scaffold files/directories from a problem into each work directory.
- `pyproject.toml` - add pytest configuration so project tests can import `runner` consistently.

Move:
- `problems/sorting-algo/` to `problems/_examples/sorting-algo/`.

Do not modify:
- Model/provider execution behavior.
- Ranking output behavior.

---

### Task 1: Add Work Directory Copy Support

**Files:**
- Create: `tests/test_executor_prepare_work_dir.py`
- Modify: `runner/executor.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing tests for scaffold copy behavior**

Create `tests/test_executor_prepare_work_dir.py`:

```python
from pathlib import Path

from runner.executor import prepare_work_dir


def test_prepare_work_dir_copies_python_tests_and_conftest(tmp_path: Path):
    problem_dir = tmp_path / "problem"
    (problem_dir / "tests").mkdir(parents=True)
    (problem_dir / "tests" / "test_solution.py").write_text("def test_ok(): assert True\n")
    (problem_dir / "conftest.py").write_text("# conftest\n")

    work_dir = prepare_work_dir(problem_dir, tmp_path / "work")

    assert (work_dir / "tests" / "test_solution.py").exists()
    assert (work_dir / "conftest.py").exists()


def test_prepare_work_dir_copies_declared_copy_paths(tmp_path: Path):
    problem_dir = tmp_path / "rust-problem"
    (problem_dir / "src").mkdir(parents=True)
    (problem_dir / "tests").mkdir()
    (problem_dir / "src" / "lib.rs").write_text("pub fn add(a: f64, b: f64) -> f64 { a + b }\n")
    (problem_dir / "Cargo.toml").write_text("[package]\nname = \"calc\"\nversion = \"0.1.0\"\nedition = \"2021\"\n")
    problem_config = {
        "copy_paths": ["Cargo.toml", "src", "tests"],
    }

    work_dir = prepare_work_dir(problem_dir, tmp_path / "work", problem_config)

    assert (work_dir / "Cargo.toml").exists()
    assert (work_dir / "src" / "lib.rs").exists()
    assert (work_dir / "tests").exists()
```

- [ ] **Step 2: Run tests and verify the signature/copy-path test fails**

Run:

```bash
uv run pytest tests/test_executor_prepare_work_dir.py -v
```

Expected: first test passes or reaches current behavior, second test fails because `prepare_work_dir` does not accept `problem_config`.

- [ ] **Step 3: Implement `copy_paths` support**

Update `runner/executor.py`:

```python
def prepare_work_dir(
    problem_dir: Path,
    base_work_dir: Path,
    problem_config: dict | None = None,
) -> Path:
    """Create a temp work dir and copy problem scaffold files into it."""
    work_dir = base_work_dir / problem_dir.name
    work_dir.mkdir(parents=True, exist_ok=True)

    copy_paths = (problem_config or {}).get("copy_paths")
    if copy_paths:
        for rel_path in copy_paths:
            src = problem_dir / rel_path
            dst = work_dir / rel_path
            if not src.exists():
                continue
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        return work_dir

    tests_src = problem_dir / "tests"
    if tests_src.exists():
        tests_dst = work_dir / "tests"
        if tests_dst.exists():
            shutil.rmtree(tests_dst)
        shutil.copytree(tests_src, tests_dst)

    conftest_src = problem_dir / "conftest.py"
    if conftest_src.exists():
        shutil.copy2(conftest_src, work_dir / "conftest.py")

    return work_dir
```

Update the call site in `runner/main.py`:

```python
work_dir = prepare_work_dir(
    prob_dir,
    tmpdir_path / f"{model_name}__{agent_name}",
    prob_config,
)
```

- [ ] **Step 4: Add pytest import configuration**

Append to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest tests/test_executor_prepare_work_dir.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add runner/executor.py runner/main.py pyproject.toml tests/test_executor_prepare_work_dir.py
git commit -m "feat: support problem scaffold copy paths"
```

---

### Task 2: Align Existing Problems With Approved Set

**Files:**
- Move: `problems/sorting-algo/` to `problems/_examples/sorting-algo/`

- [ ] **Step 1: Move the legacy sample into an ignored examples directory**

Run:

```bash
mkdir -p problems/_examples
git mv problems/sorting-algo problems/_examples/sorting-algo
```

- [ ] **Step 2: Verify discovery ignores the moved example**

Run:

```bash
uv run python -c "from runner.main import _discover_problems; print([p[0] for p in _discover_problems()])"
```

Expected: `[]` before adding the new set.

- [ ] **Step 3: Commit**

```bash
git add problems/_examples/sorting-algo
git commit -m "chore: move legacy sorting example out of benchmark set"
```

---

### Task 3: Add Easy Problem `two-sum`

**Files:**
- Create: `problems/two-sum/problem.yaml`
- Create: `problems/two-sum/conftest.py`
- Create: `problems/two-sum/solution.py`
- Create: `problems/two-sum/tests/test_solution.py`

- [ ] **Step 1: Create problem metadata**

`problems/two-sum/problem.yaml`:

```yaml
name: "two-sum"
difficulty: easy
category: algorithm
tags: [array, hash-map, edge-cases]

prompt: |
  Implement two_sum(nums: list[int], target: int) -> list[int].
  Return the indices of two distinct elements whose values add up to target.
  If no valid pair exists, return an empty list.
  The same element may not be used twice. Write the code in solution.py.

scoring:
  dimensions:
    - name: correctness
      weight: 0.6
    - name: code_quality
      weight: 0.4

target_file: "solution.py"
timeout: 30
```

- [ ] **Step 2: Add import helper**

`problems/two-sum/conftest.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
```

- [ ] **Step 3: Add reference solution**

`problems/two-sum/solution.py`:

```python
def two_sum(nums: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}
    for idx, value in enumerate(nums):
        need = target - value
        if need in seen:
            return [seen[need], idx]
        seen[value] = idx
    return []
```

- [ ] **Step 4: Add tests**

`problems/two-sum/tests/test_solution.py`:

```python
from solution import two_sum


def assert_pair(nums: list[int], target: int, result: list[int]):
    assert len(result) == 2
    i, j = result
    assert i != j
    assert nums[i] + nums[j] == target


def test_basic_pair():
    assert two_sum([2, 7, 11, 15], 9) == [0, 1]


def test_duplicates():
    assert two_sum([3, 3], 6) == [0, 1]


def test_negative_numbers():
    assert two_sum([-1, -2, -3, -4, -5], -8) == [2, 4]


def test_no_solution_returns_empty_list():
    assert two_sum([1, 2, 3], 99) == []


def test_empty_and_single_item():
    assert two_sum([], 1) == []
    assert two_sum([1], 1) == []


def test_zero_sum_pair():
    assert_pair([10, -5, 3, 5], 0, two_sum([10, -5, 3, 5], 0))


def test_large_input():
    nums = list(range(100_000))
    result = two_sum(nums, 199_997)
    assert_pair(nums, 199_997, result)
```

- [ ] **Step 5: Run tests**

Run:

```bash
uv run pytest problems/two-sum/tests -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add problems/two-sum
git commit -m "feat: add two-sum benchmark problem"
```

---

### Task 4: Add Easy Problem `csv-stats`

**Files:**
- Create: `problems/csv-stats/problem.yaml`
- Create: `problems/csv-stats/conftest.py`
- Create: `problems/csv-stats/solution.py`
- Create: `problems/csv-stats/tests/test_solution.py`

- [ ] **Step 1: Create problem metadata**

Use `difficulty: easy`, `category: data`, `target_file: solution.py`, and scoring weights `correctness: 0.6`, `code_quality: 0.4`. The prompt must require `analyze_csv(filepath: str) -> dict`, numeric stats, `None` for empty numeric columns, missing cells counted as nulls, and non-numeric columns marked as `{"type": "non-numeric"}`.

- [ ] **Step 2: Add reference implementation**

`problems/csv-stats/solution.py`:

```python
import csv


def analyze_csv(filepath: str) -> dict:
    try:
        with open(filepath, newline="") as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        raise

    if not rows:
        return {}

    headers = rows[0]
    values = {header: [] for header in headers}
    nulls = {header: 0 for header in headers}
    non_numeric = set()

    for row in rows[1:]:
        for idx, header in enumerate(headers):
            cell = row[idx].strip() if idx < len(row) else ""
            if cell == "":
                nulls[header] += 1
                continue
            try:
                values[header].append(float(cell))
            except ValueError:
                non_numeric.add(header)

    result = {}
    for header in headers:
        if header in non_numeric:
            result[header] = {"type": "non-numeric", "null_count": nulls[header]}
            continue
        nums = values[header]
        result[header] = {
            "mean": sum(nums) / len(nums) if nums else None,
            "max": max(nums) if nums else None,
            "min": min(nums) if nums else None,
            "null_count": nulls[header],
        }
    return result
```

- [ ] **Step 3: Add tests with temp CSV files**

Test cases must cover normal numeric columns, empty file, header-only file, non-numeric columns, ragged rows, mixed text/numeric columns, and single-column CSV. Use `tmp_path` to create files and assert exact dict values.

- [ ] **Step 4: Run tests**

Run:

```bash
uv run pytest problems/csv-stats/tests -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add problems/csv-stats
git commit -m "feat: add csv-stats benchmark problem"
```

---

### Task 5: Add Easy Problem `url-parser`

**Files:**
- Create: `problems/url-parser/problem.yaml`
- Create: `problems/url-parser/conftest.py`
- Create: `problems/url-parser/solution.py`
- Create: `problems/url-parser/tests/test_solution.py`

- [ ] **Step 1: Create metadata and tests before implementation**

The metadata must use `difficulty: easy`, `category: string`, and scoring weights `correctness: 0.6`, `code_quality: 0.4`. Tests must assert full URL parsing, missing scheme, default HTTP/HTTPS ports, no path, empty query, percent-decoded query values, empty URL, path-only URL, and empty fragment.

- [ ] **Step 2: Add reference implementation**

`problems/url-parser/solution.py`:

```python
from urllib.parse import unquote_plus


def parse_url(url: str) -> dict:
    result = {
        "scheme": None,
        "host": None,
        "port": None,
        "path": "",
        "query_params": {},
        "fragment": None,
    }
    if url == "":
        return result

    rest = url
    if "://" in rest:
        result["scheme"], rest = rest.split("://", 1)

    if "#" in rest:
        rest, result["fragment"] = rest.split("#", 1)

    query = ""
    if "?" in rest:
        rest, query = rest.split("?", 1)

    if result["scheme"] or (rest and not rest.startswith("/")):
        host_part = rest
        path = ""
        if "/" in rest:
            host_part, path = rest.split("/", 1)
            path = "/" + path
        if host_part:
            if ":" in host_part:
                host, port = host_part.rsplit(":", 1)
                result["host"] = host or None
                result["port"] = int(port) if port else None
            else:
                result["host"] = host_part
        result["path"] = path
    else:
        result["path"] = rest

    if result["port"] is None:
        if result["scheme"] == "http":
            result["port"] = 80
        elif result["scheme"] == "https":
            result["port"] = 443

    if query:
        params = {}
        for pair in query.split("&"):
            if pair == "":
                continue
            key, value = pair.split("=", 1) if "=" in pair else (pair, "")
            params[unquote_plus(key)] = unquote_plus(value)
        result["query_params"] = params

    return result
```

- [ ] **Step 3: Run tests and commit**

Run:

```bash
uv run pytest problems/url-parser/tests -v
```

Expected: all tests pass.

Commit:

```bash
git add problems/url-parser
git commit -m "feat: add url-parser benchmark problem"
```

---

### Task 6: Add Medium Problem `lru-cache`

**Files:**
- Create: `problems/lru-cache/problem.yaml`
- Create: `problems/lru-cache/conftest.py`
- Create: `problems/lru-cache/solution.py`
- Create: `problems/lru-cache/tests/test_solution.py`
- Create: `problems/lru-cache/scoring.py`

- [ ] **Step 1: Create metadata**

Use `difficulty: medium`, `category: algorithm`, and scoring weights `correctness: 0.4`, `code_quality: 0.3`, `performance: 0.3`. Prompt must require `LRUCache.__init__`, `get`, `put`, missing keys returning `-1`, capacity zero behavior, and O(1) operations.

- [ ] **Step 2: Add tests**

Tests must cover basic eviction, `get` refreshing order, capacity 1, capacity 0, updating existing keys, repeated get, and 10,000 mixed operations.

- [ ] **Step 3: Add reference implementation**

Use `collections.OrderedDict`:

```python
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = max(0, capacity)
        self.items: OrderedDict[int, int] = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.items:
            return -1
        self.items.move_to_end(key)
        return self.items[key]

    def put(self, key: int, value: int) -> None:
        if self.capacity == 0:
            return
        if key in self.items:
            self.items[key] = value
            self.items.move_to_end(key)
            return
        if len(self.items) >= self.capacity:
            self.items.popitem(last=False)
        self.items[key] = value
```

- [ ] **Step 4: Add performance scoring**

`problems/lru-cache/scoring.py` must import the generated `solution.py`, execute at least 50,000 `put/get` operations, and return `1.0` when elapsed time is under 1 second, `0.5` under 3 seconds, otherwise `0.0`.

- [ ] **Step 5: Verify and commit**

Run:

```bash
uv run pytest problems/lru-cache/tests -v
```

Expected: all tests pass.

Commit:

```bash
git add problems/lru-cache
git commit -m "feat: add lru-cache benchmark problem"
```

---

### Task 7: Add Medium Problem `rest-api`

**Files:**
- Create: `problems/rest-api/problem.yaml`
- Create: `problems/rest-api/conftest.py`
- Create: `problems/rest-api/solution.py`
- Create: `problems/rest-api/tests/test_solution.py`

- [ ] **Step 1: Create metadata**

Use `difficulty: medium`, `category: api`, and scoring weights `correctness: 0.6`, `code_quality: 0.4`. Prompt must require a standard-library `http.server` implementation and `create_app()`.

- [ ] **Step 2: Define test harness**

Tests must start the returned server on localhost with port 0 in a background thread, send HTTP requests via `http.client`, and call `server.shutdown()` in teardown. Tests must cover GET empty list, POST create, PUT existing, PUT missing, DELETE existing, DELETE missing, status filter, malformed JSON, auto-increment IDs, and repeated GET idempotence.

- [ ] **Step 3: Add reference implementation**

Implement `create_app()` using `ThreadingHTTPServer` and `BaseHTTPRequestHandler`, in-memory task storage on the server object, JSON response helpers, route parsing for `/tasks` and `/tasks/{id}`, and ISO timestamps via `datetime.now(timezone.utc).isoformat()`.

- [ ] **Step 4: Verify and commit**

Run:

```bash
uv run pytest problems/rest-api/tests -v
```

Expected: all tests pass without hanging.

Commit:

```bash
git add problems/rest-api
git commit -m "feat: add rest-api benchmark problem"
```

---

### Task 8: Add Medium Problem `log-analyzer`

**Files:**
- Create: `problems/log-analyzer/problem.yaml`
- Create: `problems/log-analyzer/conftest.py`
- Create: `problems/log-analyzer/solution.py`
- Create: `problems/log-analyzer/tests/test_solution.py`
- Create: `problems/log-analyzer/scoring.py`

- [ ] **Step 1: Create metadata**

Use `difficulty: medium`, `category: data`, and scoring weights `correctness: 0.4`, `code_quality: 0.3`, `performance: 0.3`. Prompt must include the nginx combined sample line and the expected return keys.

- [ ] **Step 2: Add tests**

Tests must create log files with `tmp_path` and cover mixed methods/statuses, empty file, malformed lines skipped, missing response time excluded from average, single line, repeated same path, and Top 10 path ordering by count descending.

- [ ] **Step 3: Add reference implementation**

Use a compiled regex to parse request method/path/status and optional trailing response time, stream line-by-line from the file, use `collections.Counter`, and compute `avg_response_time` as `0.0` when no timed rows exist.

- [ ] **Step 4: Add performance scoring**

`scoring.py` must generate a large temporary log file inside `work_dir`, import `analyze_log`, time execution, and return `1.0` under 2 seconds, `0.5` under 5 seconds, otherwise `0.0`.

- [ ] **Step 5: Verify and commit**

Run:

```bash
uv run pytest problems/log-analyzer/tests -v
```

Expected: all tests pass.

Commit:

```bash
git add problems/log-analyzer
git commit -m "feat: add log-analyzer benchmark problem"
```

---

### Task 9: Add Hard Problem `text-editor`

**Files:**
- Create: `problems/text-editor/problem.yaml`
- Create: `problems/text-editor/conftest.py`
- Create: `problems/text-editor/solution.py`
- Create: `problems/text-editor/tests/test_solution.py`
- Create: `problems/text-editor/scoring.py`

- [ ] **Step 1: Create metadata**

Use `difficulty: hard`, `category: algorithm`, and scoring weights `correctness: 0.4`, `code_quality: 0.3`, `performance: 0.3`. Prompt must define `TextEditor` exactly as approved, zero-based line/column indexing, newline support, `IndexError` for invalid positions, undo no-op at initial state, redo no-op when empty, and new edits clearing redo history.

- [ ] **Step 2: Add tests**

Tests must cover single-line insert, multi-line insert, cross-line delete, replace, undo/redo for insert/delete/replace, repeated undo to empty, redo stack cleared after new edit, invalid line/column raising `IndexError`, large 10,000-line document, and undo on empty document.

- [ ] **Step 3: Add reference implementation**

Represent text as a single string internally for correctness clarity. Convert `(line, col)` to absolute offset using `splitlines(keepends=True)`, store undo/redo snapshots as strings, and clear redo on any new mutating operation.

- [ ] **Step 4: Add performance scoring**

`scoring.py` must create a `TextEditor`, insert 10,000 lines, perform 1,000 small inserts and 1,000 undo calls, and return `1.0` under 3 seconds, `0.5` under 8 seconds, otherwise `0.0`.

- [ ] **Step 5: Verify and commit**

Run:

```bash
uv run pytest problems/text-editor/tests -v
```

Expected: all tests pass.

Commit:

```bash
git add problems/text-editor
git commit -m "feat: add text-editor benchmark problem"
```

---

### Task 10: Add Hard Problem `task-scheduler`

**Files:**
- Create: `problems/task-scheduler/problem.yaml`
- Create: `problems/task-scheduler/conftest.py`
- Create: `problems/task-scheduler/solution.py`
- Create: `problems/task-scheduler/tests/test_solution.py`
- Create: `problems/task-scheduler/scoring.py`

- [ ] **Step 1: Create metadata**

Use `difficulty: hard`, `category: system`, and scoring weights `correctness: 0.4`, `code_quality: 0.3`, `performance: 0.3`. Prompt must require `TaskScheduler(max_workers=4)`, `add_task`, `run_all`, dependency-aware execution, `ValueError("Cycle detected")`, and exception collection.

- [ ] **Step 2: Add tests**

Tests must cover single task, linear chain, diamond dependencies, cycle detection, failing task recorded as an exception object or error string, `max_workers=1` serial behavior, parallel execution faster than serial for independent sleep tasks, empty scheduler returning `{}`, and `None` task results.

- [ ] **Step 3: Add reference implementation**

Use `concurrent.futures.ThreadPoolExecutor`, Kahn topological scheduling, maps for dependencies/dependents, a ready queue, result dict, and error recording for exceptions without crashing `run_all`.

- [ ] **Step 4: Add performance scoring**

`scoring.py` must compare four independent 0.2-second tasks with `max_workers=1` versus `max_workers=4`; return `1.0` when parallel runtime is less than 60% of serial runtime, `0.5` when less than 90%, otherwise `0.0`.

- [ ] **Step 5: Verify and commit**

Run:

```bash
uv run pytest problems/task-scheduler/tests -v
```

Expected: all tests pass.

Commit:

```bash
git add problems/task-scheduler
git commit -m "feat: add task-scheduler benchmark problem"
```

---

### Task 11: Add Hard Problem `wasm-calculator`

**Files:**
- Create: `problems/wasm-calculator/problem.yaml`
- Create: `problems/wasm-calculator/Cargo.toml`
- Create: `problems/wasm-calculator/src/lib.rs`
- Create: `problems/wasm-calculator/tests/test_calculator.rs`
- Create: `problems/wasm-calculator/index.js`
- Create: `problems/wasm-calculator/scoring.py`

- [ ] **Step 1: Create metadata**

`problems/wasm-calculator/problem.yaml`:

```yaml
name: "wasm-calculator"
difficulty: hard
category: multi-lang
tags: [rust, wasm, parser, expression-evaluation]

prompt: |
  Use Rust to implement a calculator library in src/lib.rs.
  Expose add(a, b), sub(a, b), mul(a, b), div(a, b), and
  eval_expression(expr: &str) -> f64.
  eval_expression must support +, -, *, /, parentheses, whitespace,
  floating point numbers, nested parentheses, and unary negative numbers.
  Division by zero should return f64::INFINITY. Invalid expressions may
  panic or return f64::NAN.

scoring:
  dimensions:
    - name: correctness
      weight: 0.5
    - name: code_quality
      weight: 0.3
    - name: performance
      weight: 0.2

target_file: "src/lib.rs"
copy_paths: ["Cargo.toml", "src", "tests", "index.js"]
timeout: 60
```

- [ ] **Step 2: Create Cargo project files**

`Cargo.toml` must define a library crate with crate types `cdylib` and `rlib`, edition 2021, and no required external dependencies.

- [ ] **Step 3: Add Rust tests**

`tests/test_calculator.rs` must cover arithmetic functions, division by zero, precedence, parentheses, whitespace, nested parentheses, empty expression returning NaN or panic, invalid expression returning NaN or panic, large multiplication, and unary negative.

- [ ] **Step 4: Add reference implementation**

`src/lib.rs` must use a small recursive descent parser with functions for expression, term, factor, and number parsing. Export arithmetic functions with `#[no_mangle] pub extern "C"` for numeric functions and keep `eval_expression` as a normal Rust function for unit tests.

- [ ] **Step 5: Add JS glue file**

`index.js` must document the expected Wasm loading surface and export async `loadCalculator(wasmPath)` using `WebAssembly.instantiate`.

- [ ] **Step 6: Add Rust scoring**

`scoring.py` must:
- run `cargo test` in `work_dir` for correctness;
- run `cargo clippy -- -D warnings` when `cargo clippy` is available, otherwise return code quality `0.7`;
- run a small Rust benchmark via `cargo test performance_smoke -- --ignored` or a Python subprocess loop if implemented in tests.

- [ ] **Step 7: Verify and commit**

Run:

```bash
cargo test --manifest-path problems/wasm-calculator/Cargo.toml
```

Expected: all Rust tests pass when Cargo is installed.

Commit:

```bash
git add problems/wasm-calculator
git commit -m "feat: add wasm-calculator benchmark problem"
```

---

### Task 12: Add Full Problem Set Validation

**Files:**
- Create or modify: `tests/test_problem_set_integrity.py`

- [ ] **Step 1: Add integrity tests**

`tests/test_problem_set_integrity.py`:

```python
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
        assert config["category"] in {"algorithm", "string", "api", "data", "system", "multi-lang"}
        assert "prompt" in config and config["prompt"].strip()
        assert "scoring" in config
```

- [ ] **Step 2: Run Python problem tests**

Run:

```bash
uv run pytest \
  tests/test_executor_prepare_work_dir.py \
  tests/test_problem_set_integrity.py \
  problems/two-sum/tests \
  problems/csv-stats/tests \
  problems/url-parser/tests \
  problems/lru-cache/tests \
  problems/rest-api/tests \
  problems/log-analyzer/tests \
  problems/text-editor/tests \
  problems/task-scheduler/tests \
  -v
```

Expected: all Python tests pass.

- [ ] **Step 3: Run Rust tests when Cargo is available**

Run:

```bash
cargo test --manifest-path problems/wasm-calculator/Cargo.toml
```

Expected: all Rust tests pass, or document Cargo missing in the implementation summary.

- [ ] **Step 4: Validate CLI discovery**

Run:

```bash
uv run python -c "from runner.main import _discover_problems; print(len(_discover_problems()), [p[0] for p in _discover_problems()])"
```

Expected: output starts with `9` and includes only the approved problem names.

- [ ] **Step 5: Commit**

```bash
git add tests/test_problem_set_integrity.py
git commit -m "test: add problem set integrity checks"
```

---

## Final Verification

Run:

```bash
uv run pytest tests problems/two-sum/tests problems/csv-stats/tests problems/url-parser/tests problems/lru-cache/tests problems/rest-api/tests problems/log-analyzer/tests problems/text-editor/tests problems/task-scheduler/tests -v
```

Expected: all Python tests pass.

Run:

```bash
cargo test --manifest-path problems/wasm-calculator/Cargo.toml
```

Expected: all Rust tests pass when Cargo is installed.

Run:

```bash
git status --short
```

Expected: clean worktree after all commits.

## Self-Review Checklist

- Spec coverage: all 9 approved problems have explicit implementation tasks, files, tests, scoring weights, and verification commands.
- Existing repo alignment: legacy `sorting-algo` is moved under `_examples` so benchmark discovery matches the 9-problem spec.
- Runner gap covered: `copy_paths` enables Rust scaffolds and any future non-Python problem layouts.
- Test strategy: each task validates the new problem in isolation; final verification validates full discovery and Python/Rust suites.
- Scope control: no model/provider API behavior changes are included.
