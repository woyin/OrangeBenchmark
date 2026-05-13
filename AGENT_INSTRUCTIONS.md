# OrangeBenchmark — Coding Agent Instructions

You are being evaluated on your ability to solve coding problems. Follow these instructions carefully.

> **File location**: This file is at the repository root. All paths below are relative to the repository root.

## Environment Requirements

- **Python**: Use `uv` for all environment management and dependency resolution. Solutions must use standard-library-only imports unless `problem.yaml` explicitly allows external packages.
- **Java**: Maven (`mvn`) is available. Projects include a `pom.xml`.
- **.NET/C#**: `dotnet` CLI is available. Projects include a `.csproj` file.
- **Rust**: `cargo` is available. Projects include a `Cargo.toml`.

## Your Task

For each problem listed below:

1. Read `problems/<name>/problem.yaml` to understand the full requirements.
2. Read the test files (`tests/test_solution.py` or language equivalent) to understand expected behavior and edge cases.
3. **Overwrite** the existing placeholder in the specified `target_file` with your own implementation.
4. Run tests locally to verify your solution before proceeding to the next problem.

## Scoring Criteria

Your solutions are evaluated on multiple dimensions (weights vary per problem):

| Dimension | Weight | What it measures | How to maximize |
|-----------|--------|-----------------|-----------------|
| **correctness** | 40-60% | Test pass rate with all-or-nothing emphasis | Pass ALL tests — the scoring formula heavily penalizes partial correctness |
| **code_quality** | 30-40% | Lint (ruff for Python), type hints, cyclomatic complexity, docstrings | Add type annotations, keep functions simple, add docstrings to public APIs |
| **performance** | 20-30% | Execution time on benchmark inputs | Use efficient algorithms; O(n²) may fail on large inputs |

**Key insight**: Getting 100% of tests right is far more valuable than 90%. The scoring formula rewards full correctness disproportionately.

## Problems to Solve

### Python

| # | Problem | Difficulty | Category | Target File | Run Tests |
|---|---------|-----------|----------|-------------|-----------|
| 1 | `problems/two-sum/` | easy | algorithm | `solution.py` | `uv run pytest problems/two-sum/tests/test_solution.py -v` |
| 2 | `problems/csv-stats/` | easy | data | `solution.py` | `uv run pytest problems/csv-stats/tests/test_solution.py -v` |
| 3 | `problems/url-parser/` | easy | string | `solution.py` | `uv run pytest problems/url-parser/tests/test_solution.py -v` |
| 4 | `problems/lru-cache/` | medium | algorithm | `solution.py` | `uv run pytest problems/lru-cache/tests/test_solution.py -v` |
| 5 | `problems/rest-api/` | medium | api | `solution.py` | `uv run pytest problems/rest-api/tests/test_solution.py -v` |
| 6 | `problems/log-analyzer/` | medium | data | `solution.py` | `uv run pytest problems/log-analyzer/tests/test_solution.py -v` |
| 7 | `problems/text-editor/` | hard | algorithm | `solution.py` | `uv run pytest problems/text-editor/tests/test_solution.py -v` |
| 8 | `problems/task-scheduler/` | hard | system | `solution.py` | `uv run pytest problems/task-scheduler/tests/test_solution.py -v` |
| 9 | `problems/python-runway-monitor/` | medium | aviation | `solution.py` | `uv run pytest problems/python-runway-monitor/tests/test_solution.py -v` |
| 10 | `problems/regex-engine/` | hard | algorithm | `solution.py` | `uv run pytest problems/regex-engine/tests/test_solution.py -v` |
| 11 | `problems/mini-db/` | hard | system | `solution.py` | `uv run pytest problems/mini-db/tests/test_solution.py -v` |

### Java

| # | Problem | Difficulty | Category | Target File | Run Tests |
|---|---------|-----------|----------|-------------|-----------|
| 12 | `problems/java-reverse-string/` | easy | string | `src/main/java/StringReverser.java` | `cd problems/java-reverse-string && mvn test` |
| 13 | `problems/java-flight-plan-parser/` | medium | aviation | `src/main/java/FlightPlanParser.java` | `cd problems/java-flight-plan-parser && mvn test` |
| 14 | `problems/java-conflict-detector/` | hard | aviation | `src/main/java/ConflictDetector.java` | `cd problems/java-conflict-detector && mvn test` |
| 15 | `problems/java-expression-evaluator/` | medium | algorithm | `src/main/java/ExpressionEvaluator.java` | `cd problems/java-expression-evaluator && mvn test` |
| 16 | `problems/java-concurrent-queue/` | hard | concurrency | `src/main/java/BoundedBlockingQueue.java` | `cd problems/java-concurrent-queue && mvn test` |
| 17 | `problems/java-graph-shortest-path/` | medium | algorithm | `src/main/java/Graph.java` | `cd problems/java-graph-shortest-path && mvn test` |
| 18 | `problems/java-http-server/` | hard | system | `src/main/java/SimpleHttpServer.java` | `cd problems/java-http-server && mvn test` |

### .NET / C#

| # | Problem | Difficulty | Category | Target File | Run Tests |
|---|---------|-----------|----------|-------------|-----------|
| 19 | `problems/dotnet-fizz-buzz/` | easy | algorithm | `FizzBuzz.cs` | `cd problems/dotnet-fizz-buzz && dotnet test` |
| 20 | `problems/dotnet-adsb-decoder/` | hard | aviation | `AdsbDecoder.cs` | `cd problems/dotnet-adsb-decoder && dotnet test` |
| 21 | `problems/dotnet-crew-scheduler/` | hard | aviation | `CrewScheduler.cs` | `cd problems/dotnet-crew-scheduler && dotnet test` |
| 22 | `problems/dotnet-json-transform/` | medium | data | `JsonTransformer.cs` | `cd problems/dotnet-json-transform && dotnet test` |
| 23 | `problems/dotnet-rate-limiter/` | hard | concurrency | `RateLimiter.cs` | `cd problems/dotnet-rate-limiter && dotnet test` |
| 24 | `problems/dotnet-text-search/` | medium | algorithm | `TextSearchIndex.cs` | `cd problems/dotnet-text-search && dotnet test` |

### Rust

| # | Problem | Difficulty | Category | Target File | Run Tests |
|---|---------|-----------|----------|-------------|-----------|
| 25 | `problems/wasm-calculator/` | hard | multi-lang | `src/lib.rs` | `cargo test --manifest-path problems/wasm-calculator/Cargo.toml` |

## Common Pitfalls

- **Self-contained solutions**: Your `target_file` is copied to an isolated directory for scoring. Do not import from other files in the problem directory.
- **Edge cases**: Test files include edge cases (empty inputs, invalid positions, concurrency limits). Read them carefully and handle them.
- **Performance**: Some problems benchmark against large inputs. Naive O(n²) solutions may fail the performance dimension.
- **Module interface**: Your code must export the exact function/class names expected by the tests. Check test files for the expected interface.

## Workflow

1. For each problem: read `problem.yaml` → read test files → implement solution in `target_file` → run tests locally.
2. Fix any failing tests before moving to the next problem.
3. After solving all problems, run the scoring command:
   ```bash
   uv run orangebench score
   ```

## After Completion

The scoring command produces a summary table and saves results to `results/` for historical tracking.

To view past results:
```bash
uv run orangebench ranking
```
