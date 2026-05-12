"""Custom scoring for .NET Rate Limiter problem."""

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
        if result.returncode == 0:
            return 1.0
        return 0.0
    except Exception:
        return 0.0


def score_code_quality(generated_code: str, work_dir: str) -> float:
    if shutil.which("dotnet") is None:
        return 0.0
    try:
        result = _run(["dotnet", "build", "--verbosity", "normal"], work_dir)
        if result.returncode != 0:
            return 0.5
        warnings = result.stdout.count("warning")
        if warnings == 0:
            return 1.0
        return round(max(0.0, 1.0 - warnings * 0.1), 4)
    except Exception:
        return 0.0


def score_performance(generated_code: str, work_dir: str) -> float:
    """Run 10k concurrent TryAcquire calls from 10 threads. Score 1.0 if <2s."""
    if shutil.which("dotnet") is None:
        return 0.0
    try:
        build = _run(["dotnet", "build", "--verbosity", "quiet"], work_dir)
        if build.returncode != 0:
            return 0.0

        test_script = """
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;

public class PerfTest
{
    public static int Main()
    {
        var limiter = RateLimiter.CreateSlidingWindow(100000, TimeSpan.FromSeconds(60));
        var sw = Stopwatch.StartNew();

        var threads = new List<Thread>();
        for (int t = 0; t < 10; t++)
        {
            threads.Add(new Thread(() =>
            {
                for (int i = 0; i < 1000; i++)
                {
                    limiter.TryAcquire();
                }
            }));
        }

        foreach (var th in threads) th.Start();
        foreach (var th in threads) th.Join();

        sw.Stop();
        Console.WriteLine(sw.ElapsedMilliseconds);
        return 0;
    }
}
"""
        perf_file = Path(work_dir) / "PerfTest.cs"
        perf_file.write_text(test_script)

        result = _run(
            ["dotnet", "run", "--no-build", "--property:OutputType=Exe",
             "--property:StartupObject=PerfTest"],
            work_dir,
            timeout=30,
        )
        perf_file.unlink(missing_ok=True)

        if result.returncode != 0:
            return 0.5

        try:
            ms = int(result.stdout.Trim())
        except (ValueError, AttributeError):
            return 0.5

        if ms < 2000:
            return 1.0
        elif ms > 10000:
            return 0.0
        else:
            return round(1.0 - (ms - 2000) / 8000.0, 4)
    except Exception:
        return 0.5
