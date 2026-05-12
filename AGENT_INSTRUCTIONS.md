# OrangeBenchmark — Coding Agent Instructions

You are being evaluated on your ability to solve coding problems. Follow these instructions carefully.

## Your Task

For each problem listed below, read the `problem.yaml` file to understand the requirements, then implement the solution in the specified `target_file`.

**Important:** Overwrite the existing placeholder/reference solution with your own implementation.

## Problems to Solve

Read each `problems/<name>/problem.yaml` for the full prompt and requirements:

### Python

| # | Problem | Difficulty | Category | Target File |
|---|---------|-----------|----------|-------------|
| 1 | `problems/two-sum/` | easy | algorithm | `solution.py` |
| 2 | `problems/csv-stats/` | easy | data | `solution.py` |
| 3 | `problems/url-parser/` | easy | string | `solution.py` |
| 4 | `problems/lru-cache/` | medium | algorithm | `solution.py` |
| 5 | `problems/rest-api/` | medium | api | `solution.py` |
| 6 | `problems/log-analyzer/` | medium | data | `solution.py` |
| 7 | `problems/text-editor/` | hard | algorithm | `solution.py` |
| 8 | `problems/task-scheduler/` | hard | system | `solution.py` |
| 9 | `problems/python-runway-monitor/` | medium | aviation | `solution.py` |

### Java

| # | Problem | Difficulty | Category | Target File |
|---|---------|-----------|----------|-------------|
| 10 | `problems/java-reverse-string/` | easy | string | `src/main/java/StringReverser.java` |
| 11 | `problems/java-flight-plan-parser/` | medium | aviation | `src/main/java/FlightPlanParser.java` |
| 12 | `problems/java-conflict-detector/` | hard | aviation | `src/main/java/ConflictDetector.java` |
| 13 | `problems/java-expression-evaluator/` | medium | algorithm | `src/main/java/ExpressionEvaluator.java` |
| 14 | `problems/java-concurrent-queue/` | hard | concurrency | `src/main/java/BoundedBlockingQueue.java` |
| 15 | `problems/java-graph-shortest-path/` | medium | algorithm | `src/main/java/Graph.java` |

### .NET / C#

| # | Problem | Difficulty | Category | Target File |
|---|---------|-----------|----------|-------------|
| 16 | `problems/dotnet-fizz-buzz/` | easy | algorithm | `FizzBuzz.cs` |
| 17 | `problems/dotnet-adsb-decoder/` | hard | aviation | `AdsbDecoder.cs` |
| 18 | `problems/dotnet-crew-scheduler/` | hard | aviation | `CrewScheduler.cs` |
| 19 | `problems/dotnet-json-transform/` | medium | data | `JsonTransformer.cs` |
| 20 | `problems/dotnet-rate-limiter/` | hard | concurrency | `RateLimiter.cs` |
| 21 | `problems/dotnet-text-search/` | medium | algorithm | `TextSearchIndex.cs` |

### Rust

| # | Problem | Difficulty | Category | Target File |
|---|---------|-----------|----------|-------------|
| 22 | `problems/wasm-calculator/` | hard | multi-lang | `src/lib.rs` |

## Workflow

1. Read each `problem.yaml` for the full prompt and scoring configuration.
2. Look at `tests/test_solution.py` (or language-equivalent) to understand expected behavior.
3. Implement the solution in the `target_file` specified in `problem.yaml`.
4. Run the tests locally to verify your solution passes:
   - Python: `uv run pytest problems/<name>/tests/test_solution.py -v`
   - Java: `cd problems/<name> && mvn test`
   - .NET: `cd problems/<name> && dotnet test`
   - Rust: `cargo test --manifest-path problems/wasm-calculator/Cargo.toml`
5. After solving all problems, run the scoring command:
   ```bash
   uv run orangebench score
   ```

## Tips

- Read the test files carefully — they define the exact expected behavior.
- Handle edge cases mentioned in `problem.yaml` prompts.
- For Python problems, keep imports standard-library-only unless the problem allows otherwise.
- The scoring system runs tests in an isolated work directory, so your solution must be self-contained in the target file.

## After Completion

Once you've solved all problems, run:
```bash
uv run orangebench score
```

This will score all your solutions and display a summary table. Results are saved to `results/` for historical tracking.

To view past results:
```bash
uv run orangebench ranking
```
