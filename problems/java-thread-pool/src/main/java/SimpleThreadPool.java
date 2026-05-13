import java.util.concurrent.*;
public class SimpleThreadPool {
    public SimpleThreadPool(int poolSize) {}
    public <T> Future<T> submit(Callable<T> task) { return null; }
    public void shutdown() {}
    public void awaitTermination(long timeout, TimeUnit unit) {}
}
