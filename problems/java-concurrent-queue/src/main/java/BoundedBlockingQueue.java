import java.util.LinkedList;
import java.util.function.Consumer;

public class BoundedBlockingQueue<T> {

    private final int capacity;
    private final LinkedList<T> buffer = new LinkedList<>();

    public BoundedBlockingQueue(int capacity) {
        if (capacity <= 0) {
            throw new IllegalArgumentException("Capacity must be positive");
        }
        this.capacity = capacity;
    }

    public void put(T item) throws InterruptedException {
        if (item == null) {
            throw new NullPointerException("Item cannot be null");
        }
        synchronized (buffer) {
            while (buffer.size() >= capacity) {
                buffer.wait();
            }
            buffer.addLast(item);
            buffer.notifyAll();
        }
    }

    public T take() throws InterruptedException {
        synchronized (buffer) {
            while (buffer.isEmpty()) {
                buffer.wait();
            }
            T item = buffer.removeFirst();
            buffer.notifyAll();
            return item;
        }
    }

    public boolean tryPut(T item, long timeoutMs) throws InterruptedException {
        if (item == null) {
            throw new NullPointerException("Item cannot be null");
        }
        synchronized (buffer) {
            if (timeoutMs <= 0) {
                if (buffer.size() >= capacity) {
                    return false;
                }
                buffer.addLast(item);
                buffer.notifyAll();
                return true;
            }
            long deadline = System.currentTimeMillis() + timeoutMs;
            while (buffer.size() >= capacity) {
                long remaining = deadline - System.currentTimeMillis();
                if (remaining <= 0) {
                    return false;
                }
                buffer.wait(remaining);
            }
            buffer.addLast(item);
            buffer.notifyAll();
            return true;
        }
    }

    public boolean tryTake(Consumer<T> consumer, long timeoutMs) throws InterruptedException {
        synchronized (buffer) {
            if (timeoutMs <= 0) {
                if (buffer.isEmpty()) {
                    return false;
                }
                T item = buffer.removeFirst();
                buffer.notifyAll();
                consumer.accept(item);
                return true;
            }
            long deadline = System.currentTimeMillis() + timeoutMs;
            while (buffer.isEmpty()) {
                long remaining = deadline - System.currentTimeMillis();
                if (remaining <= 0) {
                    return false;
                }
                buffer.wait(remaining);
            }
            T item = buffer.removeFirst();
            buffer.notifyAll();
            consumer.accept(item);
            return true;
        }
    }

    public int size() {
        synchronized (buffer) {
            return buffer.size();
        }
    }

    public int remainingCapacity() {
        synchronized (buffer) {
            return capacity - buffer.size();
        }
    }

    public boolean isEmpty() {
        synchronized (buffer) {
            return buffer.isEmpty();
        }
    }

    public boolean isFull() {
        synchronized (buffer) {
            return buffer.size() >= capacity;
        }
    }
}
