import org.junit.jupiter.api.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import static org.junit.jupiter.api.Assertions.*;

class SimpleThreadPoolTest {
    @Test void testSingleTask() throws Exception {
        SimpleThreadPool pool = new SimpleThreadPool(2);
        Future<Integer> f = pool.submit(() -> 42);
        assertEquals(42, f.get());
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }

    @Test void testParallelExecution() throws Exception {
        SimpleThreadPool pool = new SimpleThreadPool(4);
        AtomicLong counter = new AtomicLong(0);
        int tasks = 20;
        for (int i = 0; i < tasks; i++) {
            pool.submit(() -> { counter.incrementAndGet(); return null; });
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        assertEquals(tasks, counter.get());
    }

    @Test void testShutdownRejectsNew() throws Exception {
        SimpleThreadPool pool = new SimpleThreadPool(1);
        pool.shutdown();
        assertThrows(RejectedExecutionException.class,
            () -> pool.submit(() -> 1));
    }

    @Test void testExceptionCaptured() throws Exception {
        SimpleThreadPool pool = new SimpleThreadPool(1);
        Future<Object> f = pool.submit(() -> { throw new RuntimeException("boom"); });
        assertThrows(ExecutionException.class, f::get);
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }

    @Test void testMultipleResults() throws Exception {
        SimpleThreadPool pool = new SimpleThreadPool(4);
        List<Future<Integer>> futures = new ArrayList<>();
        for (int i = 0; i < 10; i++) {
            final int val = i;
            futures.add(pool.submit(() -> val * 2));
        }
        for (int i = 0; i < 10; i++) {
            assertEquals(i * 2, futures.get(i).get());
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }

    @Test void testParallelFasterThanSerial() throws Exception {
        SimpleThreadPool pool = new SimpleThreadPool(4);
        long start = System.nanoTime();
        List<Future<?>> futures = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            futures.add(pool.submit(() -> { Thread.sleep(200); return null; }));
        }
        for (Future<?> f : futures) f.get();
        long elapsed = System.nanoTime() - start;
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
        assertTrue(elapsed < 600_000_000L, "Parallel should be < 600ms, was " + (elapsed/1_000_000) + "ms");
    }
}
