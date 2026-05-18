"""Custom scoring for .NET FizzBuzz problem."""

import shutil
import subprocess
from pathlib import Path

def _run(command: list[str], work_dir: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=timeout)

def score_correctness(generated_code: str, work_dir: str) -> float:
    if shutil.which("dotnet") is None:
        return 0.0
    try:
        build = _run(["dotnet", "build", "--verbosity", "quiet"], work_dir)
        if build.returncode != 0:
            return 0.0
        result = _run(["dotnet", "test", "--no-build", "--verbosity", "quiet"], work_dir)
        return 1.0 if result.returncode == 0 else 0.0
    except Exception:
        return 0.0

def score_performance(generated_code: str, work_dir: str) -> float:
    if shutil.which("dotnet") is None:
        return 0.0
    try:
        build = _run(["dotnet", "build", "--verbosity", "quiet"], work_dir)
        if build.returncode != 0:
            return 0.0

        bench_code = """
using System;
using System.Diagnostics;
using System.Collections.Generic;

public class PerfBench {
    public static int Main() {
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < 1000; i++) {
            FizzBuzz.Generate(100_000);
        }
        sw.Stop();
        Console.WriteLine(sw.ElapsedMilliseconds);
        return 0;
    }
}
"""
        perf_file = Path(work_dir) / "PerfBench.cs"
        perf_file.write_text(bench_code)

        result = _run(
            ["dotnet", "run", "--no-build", "--property:OutputType=Exe",
             "--property:StartupObject=PerfBench"],
            work_dir,
            timeout=60,
        )
        perf_file.unlink(missing_ok=True)

        if result.returncode != 0:
            return 0.5

        try:
            ms = int(result.stdout.strip())
        except (ValueError, AttributeError):
            return 0.5

        if ms < 5000:
            return 1.0
        elif ms > 15000:
            return 0.0
        else:
            return round(1.0 - (ms - 5000) / 10000.0, 4)
    except Exception:
        return 0.5
