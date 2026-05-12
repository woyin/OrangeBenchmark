"""Custom scoring for .NET Crew Scheduler problem."""

import shutil
import subprocess
import time
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
    """Schedule 100 flights with 20 crew. Score 1.0 if <3s, degrade to 0 at 10s."""
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

public class PerfTest
{
    public static int Main()
    {
        var baseTime = new DateTime(2024, 6, 1, 6, 0, 0);
        var rand = new Random(42);
        var flights = new List<FlightSegment>();
        var aircraftTypes = new[] { "B737", "A320", "B777" };

        for (int i = 0; i < 100; i++)
        {
            var dep = baseTime.AddHours(rand.Next(0, 72));
            var arr = dep.AddHours(rand.Next(1, 5));
            flights.Add(new FlightSegment(
                "F" + i, dep, arr, "A", "B", aircraftTypes[rand.Next(3)]
            ));
        }

        var crew = new List<CrewMember>();
        for (int i = 0; i < 20; i++)
        {
            var quals = new HashSet<string> { aircraftTypes[i % 3] };
            crew.Add(new CrewMember("C" + i, quals));
        }

        var scheduler = new CrewScheduler();
        var sw = Stopwatch.StartNew();
        for (int i = 0; i < 10; i++)
        {
            scheduler.Schedule(flights, crew, 10, 8);
        }
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

        if ms < 3000:
            return 1.0
        elif ms > 10000:
            return 0.0
        else:
            return round(1.0 - (ms - 3000) / 7000.0, 4)
    except Exception:
        return 0.5
