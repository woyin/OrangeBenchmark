# OrangeBenchmark — Coding Agent Instructions

You are being evaluated on your ability to solve coding problems. Follow these instructions carefully.

> **File location**: This file is at the repository root. All paths below are relative to the repository root.

## Environment Requirements

- **Python**: Use `uv` for all environment management and dependency resolution. Solutions must use standard-library-only imports unless `problem.yaml` explicitly allows external packages.
- **Java**: Maven (`mvn`) is available. Projects include a `pom.xml`.
- **.NET/C#**: `dotnet` CLI is available. Projects include a `.csproj` file.
- **Rust**: `cargo` is available. Projects include a `Cargo.toml`.
- **React**: Node.js and `npm` are available. Projects include `package.json` with Vite + React + TypeScript + Vitest.
- **Bash**: Scripts are tested with `bash`. Make scripts executable (`chmod +x`).

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
| **code_quality** | 30-40% | Lint, type hints, complexity, docstrings | Add type annotations, keep functions simple, add docstrings |
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
| 12 | `problems/python-jwt-decoder/` | medium | security | `solution.py` | `uv run pytest problems/python-jwt-decoder/tests/test_solution.py -v` |
| 13 | `problems/python-metar-parser/` | medium | aviation | `solution.py` | `uv run pytest problems/python-metar-parser/tests/test_solution.py -v` |
| 14 | `problems/python-route-planner/` | hard | aviation | `solution.py` | `uv run pytest problems/python-route-planner/tests/test_solution.py -v` |
| 15 | `problems/python-word-ladder/` | hard | algorithm | `solution.py` | `uv run pytest problems/python-word-ladder/tests/test_solution.py -v` |
| 16 | `problems/python-markdown-parser/` | medium | parsing | `solution.py` | `uv run pytest problems/python-markdown-parser/tests/test_solution.py -v` |

### Java

| # | Problem | Difficulty | Category | Target File | Run Tests |
|---|---------|-----------|----------|-------------|-----------|
| 17 | `problems/java-reverse-string/` | easy | string | `src/main/java/StringReverser.java` | `cd problems/java-reverse-string && mvn test` |
| 18 | `problems/java-flight-plan-parser/` | medium | aviation | `src/main/java/FlightPlanParser.java` | `cd problems/java-flight-plan-parser && mvn test` |
| 19 | `problems/java-conflict-detector/` | hard | aviation | `src/main/java/ConflictDetector.java` | `cd problems/java-conflict-detector && mvn test` |
| 20 | `problems/java-expression-evaluator/` | medium | algorithm | `src/main/java/ExpressionEvaluator.java` | `cd problems/java-expression-evaluator && mvn test` |
| 21 | `problems/java-concurrent-queue/` | hard | concurrency | `src/main/java/BoundedBlockingQueue.java` | `cd problems/java-concurrent-queue && mvn test` |
| 22 | `problems/java-graph-shortest-path/` | medium | algorithm | `src/main/java/Graph.java` | `cd problems/java-graph-shortest-path && mvn test` |
| 23 | `problems/java-http-server/` | hard | system | `src/main/java/SimpleHttpServer.java` | `cd problems/java-http-server && mvn test` |
| 24 | `problems/java-fizz-buzz/` | easy | algorithm | `src/main/java/FizzBuzz.java` | `cd problems/java-fizz-buzz && mvn test` |
| 25 | `problems/java-palindrome-checker/` | easy | string | `src/main/java/PalindromeChecker.java` | `cd problems/java-palindrome-checker && mvn test` |
| 26 | `problems/java-json-parser/` | medium | parsing | `src/main/java/JsonParser.java` | `cd problems/java-json-parser && mvn test` |
| 27 | `problems/java-sorting-library/` | medium | algorithm | `src/main/java/SortingLibrary.java` | `cd problems/java-sorting-library && mvn test` |
| 28 | `problems/java-thread-pool/` | hard | concurrency | `src/main/java/SimpleThreadPool.java` | `cd problems/java-thread-pool && mvn test` |
| 29 | `problems/java-matrix-ops/` | medium | math | `src/main/java/Matrix.java` | `cd problems/java-matrix-ops && mvn test` |
| 30 | `problems/java-aircraft-scheduler/` | hard | aviation | `src/main/java/AircraftScheduler.java` | `cd problems/java-aircraft-scheduler && mvn test` |
| 31 | `problems/java-password-validator/` | easy | security | `src/main/java/PasswordValidator.java` | `cd problems/java-password-validator && mvn test` |
| 32 | `problems/java-morse-code/` | easy | encoding | `src/main/java/MorseCode.java` | `cd problems/java-morse-code && mvn test` |
| 33 | `problems/java-tcp-chat-server/` | hard | system | `src/main/java/ChatServer.java` | `cd problems/java-tcp-chat-server && mvn test` |

### .NET / C#

| # | Problem | Difficulty | Category | Target File | Run Tests |
|---|---------|-----------|----------|-------------|-----------|
| 34 | `problems/dotnet-fizz-buzz/` | easy | algorithm | `FizzBuzz.cs` | `cd problems/dotnet-fizz-buzz && dotnet test` |
| 35 | `problems/dotnet-adsb-decoder/` | hard | aviation | `AdsbDecoder.cs` | `cd problems/dotnet-adsb-decoder && dotnet test` |
| 36 | `problems/dotnet-crew-scheduler/` | hard | aviation | `CrewScheduler.cs` | `cd problems/dotnet-crew-scheduler && dotnet test` |
| 37 | `problems/dotnet-json-transform/` | medium | data | `JsonTransformer.cs` | `cd problems/dotnet-json-transform && dotnet test` |
| 38 | `problems/dotnet-rate-limiter/` | hard | concurrency | `RateLimiter.cs` | `cd problems/dotnet-rate-limiter && dotnet test` |
| 39 | `problems/dotnet-text-search/` | medium | algorithm | `TextSearchIndex.cs` | `cd problems/dotnet-text-search && dotnet test` |

### React

| # | Problem | Difficulty | Category | Target File | Run Tests |
|---|---------|-----------|----------|-------------|-----------|
| 40 | `problems/react-counter-app/` | easy | frontend | `src/Counter.tsx` | `cd problems/react-counter-app && npm install && npm test` |
| 41 | `problems/react-todo-list/` | easy | frontend | `src/TodoList.tsx` | `cd problems/react-todo-list && npm install && npm test` |
| 42 | `problems/react-color-picker/` | medium | frontend | `src/ColorPicker.tsx` | `cd problems/react-color-picker && npm install && npm test` |
| 43 | `problems/react-data-table/` | medium | frontend | `src/DataTable.tsx` | `cd problems/react-data-table && npm install && npm test` |
| 44 | `problems/react-form-validator/` | medium | frontend | `src/FormValidator.tsx` | `cd problems/react-form-validator && npm install && npm test` |
| 45 | `problems/react-drag-kanban/` | hard | frontend | `src/KanbanBoard.tsx` | `cd problems/react-drag-kanban && npm install && npm test` |
| 46 | `problems/react-infinite-scroll/` | hard | frontend | `src/InfiniteScroll.tsx` | `cd problems/react-infinite-scroll && npm install && npm test` |

### Bash

| # | Problem | Difficulty | Category | Target File | Run Tests |
|---|---------|-----------|----------|-------------|-----------|
| 47 | `problems/bash-file-renamer/` | easy | system | `solution.sh` | `cd problems/bash-file-renamer && bash tests/test_solution.sh` |
| 48 | `problems/bash-log-summary/` | easy | data | `solution.sh` | `cd problems/bash-log-summary && bash tests/test_solution.sh` |
| 49 | `problems/bash-csv-merger/` | medium | data | `solution.sh` | `cd problems/bash-csv-merger && bash tests/test_solution.sh` |
| 50 | `problems/bash-process-monitor/` | medium | system | `solution.sh` | `cd problems/bash-process-monitor && bash tests/test_solution.sh` |
| 51 | `problems/bash-backup-rotation/` | hard | system | `solution.sh` | `cd problems/bash-backup-rotation && bash tests/test_solution.sh` |

### Rust

| # | Problem | Difficulty | Category | Target File | Run Tests |
|---|---------|-----------|----------|-------------|-----------|
| 52 | `problems/wasm-calculator/` | hard | multi-lang | `src/lib.rs` | `cargo test --manifest-path problems/wasm-calculator/Cargo.toml` |
| 55 | `problems/rust-json-parser/` | medium | parsing | `src/lib.rs` | `cargo test --manifest-path problems/rust-json-parser/Cargo.toml` |
| 56 | `problems/rust-lru-cache/` | medium | algorithm | `src/lib.rs` | `cargo test --manifest-path problems/rust-lru-cache/Cargo.toml` |

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
