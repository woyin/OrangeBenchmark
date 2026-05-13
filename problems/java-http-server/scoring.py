"""Custom scoring for java-http-server problem."""
import shutil
import subprocess
import time
from pathlib import Path


def _run(command: list[str], work_dir: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=work_dir, capture_output=True, text=True, timeout=timeout)


def score_correctness(generated_code: str, work_dir: str) -> float:
    if shutil.which("mvn") is None:
        return 0.0
    try:
        result = _run(["mvn", "test", "-q"], work_dir, timeout=120)
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
import java.io.*;
import java.net.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class PerfBench {
    public static void main(String[] args) throws Exception {
        int port = 19080;
        SimpleHttpServer server = new SimpleHttpServer(port);
        server.get("/bench", req -> HttpResponse.ok("ok"));
        Thread serverThread = new Thread(() -> {
            try { server.start(); } catch (Exception e) {}
        });
        serverThread.start();
        Thread.sleep(1000);

        int numRequests = 1000;
        AtomicInteger success = new AtomicInteger(0);
        ExecutorService executor = Executors.newFixedThreadPool(20);
        CountDownLatch latch = new CountDownLatch(numRequests);

        long start = System.nanoTime();
        for (int i = 0; i < numRequests; i++) {
            executor.submit(() -> {
                try {
                    URL url = new URL("http://localhost:" + port + "/bench");
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setConnectTimeout(2000);
                    conn.setReadTimeout(2000);
                    BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    String line = reader.readLine();
                    if ("ok".equals(line)) success.incrementAndGet();
                    reader.close();
                } catch (Exception e) {}
                latch.countDown();
            });
        }
        latch.await(10, TimeUnit.SECONDS);
        long elapsed = (System.nanoTime() - start) / 1_000_000;
        server.stop();
        executor.shutdown();

        double successRate = (double) success.get() / numRequests;
        if (successRate < 0.9) {
            System.out.println("ELAPSED_MS=99999");
        } else {
            System.out.println("ELAPSED_MS=" + elapsed);
        }
    }
}
"""
        bench_path = Path(work_dir) / "src" / "main" / "java" / "PerfBench.java"
        bench_path.write_text(bench_code)

        _run(["mvn", "compile", "-q"], work_dir)
        run_result = _run(["mvn", "exec:java", "-Dexec.mainClass=PerfBench", "-q"], work_dir, timeout=30)
        bench_path.unlink(missing_ok=True)

        import re
        output = run_result.stdout + run_result.stderr
        m = re.search(r"ELAPSED_MS=(\d+)", output)
        if m:
            elapsed_ms = int(m.group(1))
            if elapsed_ms >= 99999:
                return 0.0
            if elapsed_ms < 5000:
                return 1.0
            elif elapsed_ms < 15000:
                return round(1.0 - (elapsed_ms - 5000) / 10000.0 * 0.7, 4)
            else:
                return 0.0
        return 0.5
    except Exception:
        return 0.0
