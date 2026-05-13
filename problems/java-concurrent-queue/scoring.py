"""Custom scoring for Java concurrent-queue problem."""

import shutil
import subprocess
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
    """Benchmark: 10 producers x 10 consumers, 10000 items total."""
    if shutil.which("mvn") is None:
        return 0.0
    try:
        compile_result = _run(["mvn", "compile", "-q"], work_dir)
        if compile_result.returncode != 0:
            return 0.0

        bench_code = """
import java.util.*;
import java.util.concurrent.atomic.*;

public class PerfBench {
    public static void main(String[] args) throws Exception {
        BoundedBlockingQueue<Integer> queue = new BoundedBlockingQueue<>(100);
        int numProducers = 10;
        int numConsumers = 10;
        int itemsPerProducer = 1000;
        int totalItems = numProducers * itemsPerProducer;
        AtomicInteger consumed = new AtomicInteger(0);
        AtomicLong sum = new AtomicLong(0);
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch doneLatch = new CountDownLatch(numProducers + numConsumers);

        for (int i = 0; i < numConsumers; i++) {
            new Thread(() -> {
                try { startLatch.await(); } catch (InterruptedException e) { return; }
                while (true) {
                    try {
                        Integer v = null;
                        if (!queue.tryTake(x -> { v = x; }, 100)) break;
                        if (v != null) {
                            consumed.incrementAndGet();
                            sum.addAndGet(v);
                        }
                    } catch (InterruptedException e) { break; }
                }
                doneLatch.countDown();
            }).start();
        }

        for (int i = 0; i < numProducers; i++) {
            final int producerId = i;
            new Thread(() -> {
                try { startLatch.await(); } catch (InterruptedException e) { return; }
                for (int j = 0; j < itemsPerProducer; j++) {
                    try {
                        queue.put(producerId * itemsPerProducer + j);
                    } catch (InterruptedException e) { break; }
                }
                doneLatch.countDown();
            }).start();
        }

        long startTime = System.nanoTime();
        startLatch.countDown();
        doneLatch.await(30, java.util.concurrent.TimeUnit.SECONDS);
        long elapsed = (System.nanoTime() - startTime) / 1_000_000;
        System.out.println("ELAPSED_MS=" + elapsed);
        System.out.println("CONSUMED=" + consumed.get());
    }
}
"""
        bench_path = Path(work_dir) / "src" / "main" / "java" / "PerfBench.java"
        bench_path.write_text(bench_code)

        _run(["mvn", "compile", "-q"], work_dir)
        run_result = _run(
            ["mvn", "exec:java", "-Dexec.mainClass=PerfBench", "-q"], work_dir
        )

        bench_path.unlink(missing_ok=True)

        output = run_result.stdout + run_result.stderr
        import re
        m = re.search(r"ELAPSED_MS=(\d+)", output)
        if m:
            elapsed_ms = int(m.group(1))
            if elapsed_ms < 5000:
                return 1.0
            elif elapsed_ms < 10000:
                return round(1.0 - (elapsed_ms - 5000) / 5000.0 * 0.5, 4)
            else:
                return 0.0
        return 0.5
    except Exception:
        return 0.0
