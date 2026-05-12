import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.List;

public class GraphTest {

    private Graph graph;

    @BeforeEach
    public void setUp() {
        graph = new Graph();
    }

    @Test
    public void testSimplePath() {
        graph.addEdge("A", "B", 1.0);
        graph.addEdge("B", "C", 2.0);
        graph.addEdge("C", "D", 3.0);

        assertEquals(6.0, graph.shortestPath("A", "D"), 1e-9);
        assertEquals(List.of("A", "B", "C", "D"), graph.shortestPathNodes("A", "D"));
    }

    @Test
    public void testDirectEdge() {
        graph.addEdge("A", "B", 5.0);
        assertEquals(5.0, graph.shortestPath("A", "B"), 1e-9);
        assertTrue(graph.hasPath("A", "B"));
    }

    @Test
    public void testNoPath() {
        graph.addEdge("A", "B", 1.0);
        graph.addEdge("C", "D", 1.0);

        assertEquals(-1.0, graph.shortestPath("A", "D"), 1e-9);
        assertTrue(graph.shortestPathNodes("A", "D").isEmpty());
        assertFalse(graph.hasPath("A", "D"));
    }

    @Test
    public void testSameSourceAndTarget() {
        graph.addEdge("A", "B", 1.0);

        assertEquals(0.0, graph.shortestPath("A", "A"), 1e-9);
        assertEquals(List.of("A"), graph.shortestPathNodes("A", "A"));
        assertTrue(graph.hasPath("A", "A"));
    }

    @Test
    public void testUndirectedEdge() {
        graph.addUndirectedEdge("A", "B", 3.0);

        assertEquals(3.0, graph.shortestPath("A", "B"), 1e-9);
        assertEquals(3.0, graph.shortestPath("B", "A"), 1e-9);
        assertTrue(graph.hasPath("A", "B"));
        assertTrue(graph.hasPath("B", "A"));
    }

    @Test
    public void testMultiplePathsChoosesShortest() {
        // Long path: A -> B -> C -> D = 1 + 1 + 1 = 3
        graph.addEdge("A", "B", 1.0);
        graph.addEdge("B", "C", 1.0);
        graph.addEdge("C", "D", 1.0);

        // Short path: A -> D = 2
        graph.addEdge("A", "D", 2.0);

        assertEquals(2.0, graph.shortestPath("A", "D"), 1e-9);
        assertEquals(List.of("A", "D"), graph.shortestPathNodes("A", "D"));
    }

    @Test
    public void testDisconnectedComponents() {
        // Component 1
        graph.addEdge("A", "B", 1.0);
        // Component 2
        graph.addEdge("C", "D", 1.0);

        assertFalse(graph.hasPath("A", "C"));
        assertFalse(graph.hasPath("B", "D"));
        assertTrue(graph.hasPath("A", "B"));
        assertTrue(graph.hasPath("C", "D"));
    }

    @Test
    public void testLargeGraphChain() {
        int n = 1000;
        for (int i = 0; i < n - 1; i++) {
            graph.addEdge("N" + i, "N" + (i + 1), 1.0);
        }
        assertEquals(n - 1, graph.shortestPath("N0", "N" + (n - 1)), 1e-9);
        assertTrue(graph.hasPath("N0", "N999"));
    }

    @Test
    public void testUnknownNodeThrows() {
        graph.addEdge("A", "B", 1.0);
        assertThrows(IllegalArgumentException.class, () -> graph.shortestPath("A", "Z"));
        assertThrows(IllegalArgumentException.class, () -> graph.shortestPath("Z", "A"));
        assertThrows(IllegalArgumentException.class, () -> graph.hasPath("Z", "A"));
    }

    @Test
    public void testNegativeWeightThrows() {
        assertThrows(IllegalArgumentException.class, () -> graph.addEdge("A", "B", -1.0));
    }

    @Test
    public void testComplexGraph() {
        // Diamond graph
        graph.addEdge("S", "A", 1.0);
        graph.addEdge("S", "B", 2.0);
        graph.addEdge("A", "T", 3.0);
        graph.addEdge("B", "T", 1.0);

        // Shortest: S -> B -> T = 3.0
        assertEquals(3.0, graph.shortestPath("S", "T"), 1e-9);
        assertEquals(List.of("S", "B", "T"), graph.shortestPathNodes("S", "T"));
    }
}
