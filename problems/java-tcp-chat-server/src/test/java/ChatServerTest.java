import org.junit.jupiter.api.*;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;
import static org.junit.jupiter.api.Assertions.*;

class ChatServerTest {
    private static ChatServer server;
    private static int port = 19876;

    @BeforeAll
    static void startServer() throws Exception {
        port = 19876 + (int)(Math.random()*1000);
        server = new ChatServer(port);
        new Thread(() -> { try { server.start(); } catch(Exception e){} }).start();
        Thread.sleep(500);
    }

    @AfterAll
    static void stopServer() { server.stop(); }

    private Socket connect() throws Exception {
        Socket s = new Socket("localhost", port);
        s.setSoTimeout(3000);
        return s;
    }

    private String readLine(Socket s) throws Exception {
        BufferedReader r = new BufferedReader(new InputStreamReader(s.getInputStream()));
        return r.readLine();
    }

    private void sendLine(Socket s, String msg) throws Exception {
        PrintWriter w = new PrintWriter(s.getOutputStream(), true);
        w.println(msg);
    }

    @Test void testClientReceivesWelcome() throws Exception {
        Socket c = connect();
        String welcome = readLine(c);
        assertNotNull(welcome);
        assertTrue(welcome.contains("Welcome") || welcome.contains("Client"));
        c.close();
    }

    @Test void testTwoClientsChat() throws Exception {
        Socket c1 = connect();
        readLine(c1); // welcome
        Socket c2 = connect();
        readLine(c2); // welcome
        Thread.sleep(200);
        sendLine(c1, "hello");
        Thread.sleep(500);
        String msg = readLine(c2);
        assertNotNull(msg);
        assertTrue(msg.contains("hello"));
        c1.close();
        c2.close();
    }

    @Test void testNoEchoToSelf() throws Exception {
        Socket c = connect();
        readLine(c);
        sendLine(c, "self-msg");
        c.setSoTimeout(500);
        try {
            String echo = readLine(c);
            // Should not receive own message
            if (echo != null && echo.contains("self-msg")) {
                fail("Client should not receive own message");
            }
        } catch (SocketTimeoutException e) {
            // Expected - no echo
        }
        c.close();
    }

    @Test void testConnectedCount() throws Exception {
        int before = server.getConnectedClientCount();
        Socket c = connect();
        readLine(c);
        Thread.sleep(200);
        assertTrue(server.getConnectedClientCount() >= before);
        c.close();
    }
}
