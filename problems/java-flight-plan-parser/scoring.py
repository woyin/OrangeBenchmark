"""Custom scoring for Java flight-plan-parser problem."""

import shutil
import subprocess
from pathlib import Path


def _run(command: list[str], work_dir: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=timeout)


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
                return round(((total - failures) / total) ** 2.0, 4)
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
    if shutil.which("mvn") is None:
        return 0.0
    try:
        compile_result = _run(["mvn", "compile", "-q"], work_dir)
        if compile_result.returncode != 0:
            return 0.0

        bench_code = """
public class PerfBench {
    public static void main(String[] args) {
        FlightPlanParser parser = new FlightPlanParser();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 500; i++) {
            sb.append("WP").append(i).append(".AW").append(i % 50).append(".WP").append(i + 1);
            if (i < 499) sb.append(" ");
        }
        String route = sb.toString();
        long start = System.nanoTime();
        for (int i = 0; i < 1000; i++) {
            parser.parseRoute(route);
        }
        long elapsed = (System.nanoTime() - start) / 1_000_000;
        System.out.println("ELAPSED_MS=" + elapsed);
    }
}
"""
        bench_path = Path(work_dir) / "src" / "main" / "java" / "PerfBench.java"
        bench_path.write_text(bench_code)

        _run(["mvn", "compile", "-q"], work_dir)
        run_result = _run(["mvn", "exec:java", "-Dexec.mainClass=PerfBench", "-q"], work_dir)
        bench_path.unlink(missing_ok=True)

        import re
        output = run_result.stdout + run_result.stderr
        m = re.search(r"ELAPSED_MS=(\d+)", output)
        if m:
            elapsed_ms = int(m.group(1))
            if elapsed_ms < 2000:
                return 1.0
            elif elapsed_ms < 5000:
                return round(1.0 - (elapsed_ms - 2000) / 3000.0 * 0.7, 4)
            else:
                return 0.0
        return 0.5
    except Exception:
        return 0.0
