import org.junit.jupiter.api.*;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;

import static org.junit.jupiter.api.Assertions.*;

class SimpleHttpServerTest {
    private static SimpleHttpServer server;
    private static int port;

    @BeforeAll
    static void setUp() throws Exception {
        port = 18080 + (int)(Math.random() * 1000);
        server = new SimpleHttpServer(port);
        server.get("/hello", req -> HttpResponse.ok("world"));
        server.get("/echo-name", req -> {
            String query = req.path.contains("?") ? req.path.substring(req.path.indexOf("?") + 1) : "";
            return HttpResponse.ok(query);
        });
        server.post("/data", req -> HttpResponse.ok("got: " + req.body));
        server.get("/not-found-test", req -> HttpResponse.notFound());
        new Thread(() -> {
            try { server.start(); } catch (Exception e) {}
        }).start();
        Thread.sleep(500);
    }

    @AfterAll
    static void tearDown() {
        server.stop();
    }

    private String doGet(String path) throws Exception {
        URL url = new URL("http://localhost:" + port + path);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setConnectTimeout(2000);
        conn.setReadTimeout(2000);
        BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) sb.append(line);
        reader.close();
        return sb.toString();
    }

    private String doPost(String path, String body) throws Exception {
        URL url = new URL("http://localhost:" + port + path);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        conn.setConnectTimeout(2000);
        conn.setReadTimeout(2000);
        conn.getOutputStream().write(body.getBytes());
        conn.getOutputStream().flush();
        BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) sb.append(line);
        reader.close();
        return sb.toString();
    }

    @Test
    void testGetHello() throws Exception {
        assertEquals("world", doGet("/hello"));
    }

    @Test
    void testPostData() throws Exception {
        assertEquals("got: test-body", doPost("/data", "test-body"));
    }

    @Test
    void testUnregisteredPath() throws Exception {
        URL url = new URL("http://localhost:" + port + "/nonexistent");
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        assertEquals(404, conn.getResponseCode());
    }

    @Test
    void testConcurrentRequests() throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(10);
        CountDownLatch latch = new CountDownLatch(10);
        for (int i = 0; i < 10; i++) {
            executor.submit(() -> {
                try {
                    String result = doGet("/hello");
                    assertEquals("world", result);
                } catch (Exception e) {
                    fail(e.getMessage());
                } finally {
                    latch.countDown();
                }
            });
        }
        assertTrue(latch.await(5, TimeUnit.SECONDS));
        executor.shutdown();
    }

    @Test
    void testStopAndRestart() throws Exception {
        server.stop();
        Thread.sleep(200);
        SimpleHttpServer server2 = new SimpleHttpServer(port);
        server2.get("/ping", req -> HttpResponse.ok("pong"));
        new Thread(() -> {
            try { server2.start(); } catch (Exception e) {}
        }).start();
        Thread.sleep(500);
        assertEquals("pong", doGet("/ping"));
        server2.stop();
    }
}
