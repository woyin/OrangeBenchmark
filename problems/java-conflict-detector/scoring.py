"""Custom scoring for Java conflict-detector problem."""

import shutil
import subprocess
import time
from pathlib import Path


def _run(command: list[str], work_dir: str) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=60)


def score_correctness(generated_code: str, work_dir: str) -> float:
    if shutil.which("mvn") is None:
        return 0.0
    try:
        result = _run(["mvn", "test", "-q"], work_dir)
        if result.returncode == 0:
            return 1.0
        import re
        output = result.stdout + result.stderr
        m = re.search(r"Tests run:\s*(\d+).*Failures:\s*(\d+)", output)
        if m:
            total = int(m.group(1))
            failures = int(m.group(2))
            if total > 0:
                return round(((total - failures) / total) ** 1.5, 4)
        return 0.0
    except Exception:
        return 0.0


def score_code_quality(generated_code: str, work_dir: str) -> float:
    if shutil.which("mvn") is None:
        return 0.0
    try:
        result = _run(["mvn", "compile", "-q"], work_dir)
        return 1.0 if result.returncode == 0 else 0.5
    except Exception:
        return 0.0


def score_performance(generated_code: str, work_dir: str) -> float:
    """Benchmark with 50 tracks of 100 points each."""
    if shutil.which("mvn") is None:
        return 0.0
    try:
        # Compile first
        compile_result = _run(["mvn", "compile", "-q"], work_dir)
        if compile_result.returncode != 0:
            return 0.0

        # Run performance benchmark
        bench_code = """
import java.util.*;
public class PerfBench {
    public static void main(String[] args) {
        Random rng = new Random(42);
        ConflictDetector detector = new ConflictDetector();
        List<AircraftTrack> tracks = new ArrayList<>();
        for (int i = 0; i < 50; i++) {
            List<Position> positions = new ArrayList<>();
            double lat = 30 + rng.nextDouble() * 20;
            double lon = -120 + rng.nextDouble() * 40;
            for (int j = 0; j < 100; j++) {
                lat += (rng.nextDouble() - 0.5) * 0.1;
                lon += (rng.nextDouble() - 0.5) * 0.1;
                positions.add(new Position(lat, lon, 30000 + rng.nextDouble() * 1000, j * 60.0));
            }
            tracks.add(new AircraftTrack("FL" + String.format("%03d", i), positions));
        }
        long start = System.nanoTime();
        detector.detectConflicts(tracks, 5.0, 1000.0);
        long elapsed = (System.nanoTime() - start) / 1_000_000;
        System.out.println("ELAPSED_MS=" + elapsed);
    }
}
"""
        bench_path = Path(work_dir) / "src" / "main" / "java" / "PerfBench.java"
        bench_path.write_text(bench_code)

        # Compile and run
        compile_result = _run(
            ["mvn", "compile", "-q", "-Dmaven.compiler.includes=**/*.java"], work_dir
        )
        run_result = _run(
            ["mvn", "exec:java", "-Dexec.mainClass=PerfBench", "-q"], work_dir
        )

        bench_path.unlink(missing_ok=True)

        output = run_result.stdout + run_result.stderr
        import re
        m = re.search(r"ELAPSED_MS=(\d+)", output)
        if m:
            elapsed_ms = int(m.group(1))
            if elapsed_ms < 2000:
                return 1.0
            elif elapsed_ms < 5000:
                return round(1.0 - (elapsed_ms - 2000) / 3000.0 * 0.5, 4)
            else:
                return 0.0
        return 0.5
    except Exception:
        return 0.0
