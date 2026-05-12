import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;

public class BoundedBlockingQueueTest {

    private BoundedBlockingQueue<Integer> queue;

    @BeforeEach
    public void setUp() {
        queue = new BoundedBlockingQueue<>(3);
    }

    @Test
    public void testBasicPutAndTake() throws InterruptedException {
        queue.put(1);
        queue.put(2);
        queue.put(3);
        assertEquals(3, queue.size());
        assertEquals(1, queue.take());
        assertEquals(2, queue.take());
        assertEquals(3, queue.take());
        assertTrue(queue.isEmpty());
    }

    @Test
    public void testBlockingOnFullQueue() throws Exception {
        queue.put(1);
        queue.put(2);
        queue.put(3);
        assertTrue(queue.isFull());

        // Try to put in a separate thread; it should block
        Thread t = new Thread(() -> {
            try {
                queue.put(4);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
        t.start();
        Thread.sleep(100);
        assertTrue(t.isAlive(), "Put should block when queue is full");

        // Take one item to unblock
        queue.take();
        t.join(1000);
        assertFalse(t.isAlive(), "Put should complete after space is available");
        assertEquals(3, queue.size());
    }

    @Test
    public void testBlockingOnEmptyQueue() throws Exception {
        assertTrue(queue.isEmpty());

        AtomicReference<Integer> result = new AtomicReference<>();
        Thread t = new Thread(() -> {
            try {
                result.set(queue.take());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
        t.start();
        Thread.sleep(100);
        assertTrue(t.isAlive(), "Take should block when queue is empty");

        queue.put(42);
        t.join(1000);
        assertFalse(t.isAlive(), "Take should complete after item is available");
        assertEquals(42, result.get());
    }

    @Test
    public void testTryPutTimeout() throws InterruptedException {
        queue.put(1);
        queue.put(2);
        queue.put(3);
        assertTrue(queue.isFull());

        boolean result = queue.tryPut(4, 50);
        assertFalse(result, "tryPut should return false on timeout when full");
        assertEquals(3, queue.size());
    }

    @Test
    public void testTryTakeTimeout() throws InterruptedException {
        assertTrue(queue.isEmpty());

        AtomicInteger consumed = new AtomicInteger(0);
        Consumer<Integer> consumer = consumed::set;
        boolean result = queue.tryTake(consumer, 50);
        assertFalse(result, "tryTake should return false on timeout when empty");
    }

    @Test
    public void testTryPutImmediateSuccess() throws InterruptedException {
        assertTrue(queue.isEmpty());
        boolean result = queue.tryPut(1, 100);
        assertTrue(result);
        assertEquals(1, queue.size());
    }

    @Test
    public void testTryTakeImmediateSuccess() throws InterruptedException {
        queue.put(99);
        AtomicInteger consumed = new AtomicInteger(0);
        boolean result = queue.tryTake(consumed::set, 100);
        assertTrue(result);
        assertEquals(99, consumed.get());
    }

    @Test
    public void testInterruptionDuringPut() throws Exception {
        Thread t = new Thread(() -> {
            try {
                queue.put(1);
                queue.put(2);
                queue.put(3);
                // Queue is now full, next put should block
                queue.put(4);
                fail("Should have thrown InterruptedException");
            } catch (InterruptedException e) {
                // Expected
            }
        });
        t.start();
        Thread.sleep(100);
        assertTrue(t.isAlive());
        t.interrupt();
        t.join(1000);
        assertFalse(t.isAlive(), "Thread should finish after interruption");
        assertTrue(Thread.currentThread().interrupted() == false);
    }

    @Test
    public void testMultipleProducerConsumers() throws Exception {
        int numProducers = 5;
        int numConsumers = 5;
        int itemsPerProducer = 100;
        BoundedBlockingQueue<Integer> q = new BoundedBlockingQueue<>(10);
        List<Integer> consumed = Collections.synchronizedList(new ArrayList<>());

        Thread[] producers = new Thread[numProducers];
        for (int i = 0; i < numProducers; i++) {
            final int producerId = i;
            producers[i] = new Thread(() -> {
                for (int j = 0; j < itemsPerProducer; j++) {
                    try {
                        q.put(producerId * itemsPerProducer + j);
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        return;
                    }
                }
            });
        }

        Thread[] consumers = new Thread[numConsumers];
        for (int i = 0; i < numConsumers; i++) {
            consumers[i] = new Thread(() -> {
                for (int j = 0; j < (numProducers * itemsPerProducer) / numConsumers; j++) {
                    try {
                        q.take();
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        return;
                    }
                }
            });
        }

        for (Thread t : producers) t.start();
        for (Thread t : consumers) t.start();
        for (Thread t : producers) t.join(5000);
        for (Thread t : consumers) t.join(5000);

        assertTrue(q.isEmpty(), "Queue should be empty after all items consumed");
    }

    @Test
    public void testSizeTracking() throws InterruptedException {
        assertEquals(0, queue.size());
        assertEquals(3, queue.remainingCapacity());

        queue.put(1);
        assertEquals(1, queue.size());
        assertEquals(2, queue.remainingCapacity());

        queue.put(2);
        assertEquals(2, queue.size());
        assertEquals(1, queue.remainingCapacity());

        queue.take();
        assertEquals(1, queue.size());
        assertEquals(2, queue.remainingCapacity());
    }

    @Test
    public void testInvalidCapacity() {
        assertThrows(IllegalArgumentException.class, () -> new BoundedBlockingQueue<>(0));
        assertThrows(IllegalArgumentException.class, () -> new BoundedBlockingQueue<>(-1));
    }

    @Test
    public void testNullItem() {
        assertThrows(NullPointerException.class, () -> queue.put(null));
        assertThrows(NullPointerException.class, () -> queue.tryPut(null, 100));
    }
}
