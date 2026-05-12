import java.util.*;

public class Graph {

    private final Map<String, List<Edge>> adjacency = new HashMap<>();

    private static class Edge {
        final String to;
        final double weight;

        Edge(String to, double weight) {
            this.to = to;
            this.weight = weight;
        }
    }

    public Graph() {
    }

    public void addEdge(String from, String to, double weight) {
        if (weight < 0) {
            throw new IllegalArgumentException("Edge weight cannot be negative: " + weight);
        }
        adjacency.computeIfAbsent(from, k -> new ArrayList<>()).add(new Edge(to, weight));
        adjacency.computeIfAbsent(to, k -> new ArrayList<>()); // ensure target node exists
    }

    public void addUndirectedEdge(String from, String to, double weight) {
        addEdge(from, to, weight);
        adjacency.computeIfAbsent(to, k -> new ArrayList<>()).add(new Edge(from, weight));
    }

    public double shortestPath(String from, String to) {
        validateNodes(from, to);
        if (from.equals(to)) return 0.0;

        Map<String, Double> dist = dijkstra(from);
        Double d = dist.get(to);
        return (d == null || d == Double.MAX_VALUE) ? -1.0 : d;
    }

    public List<String> shortestPathNodes(String from, String to) {
        validateNodes(from, to);
        if (from.equals(to)) return List.of(from);

        Map<String, Double> dist = new HashMap<>();
        Map<String, String> prev = new HashMap<>();
        PriorityQueue<String> pq = new PriorityQueue<>(
            Comparator.comparingDouble(n -> dist.getOrDefault(n, Double.MAX_VALUE))
        );

        for (String node : adjacency.keySet()) {
            dist.put(node, Double.MAX_VALUE);
        }
        dist.put(from, 0.0);
        pq.add(from);

        while (!pq.isEmpty()) {
            String current = pq.poll();
            double currentDist = dist.get(current);
            if (currentDist == Double.MAX_VALUE) break;
            if (current.equals(to)) break;

            for (Edge edge : adjacency.getOrDefault(current, List.of())) {
                double newDist = currentDist + edge.weight;
                if (newDist < dist.getOrDefault(edge.to, Double.MAX_VALUE)) {
                    dist.put(edge.to, newDist);
                    prev.put(edge.to, current);
                    pq.add(edge.to);
                }
            }
        }

        Double targetDist = dist.get(to);
        if (targetDist == null || targetDist == Double.MAX_VALUE) {
            return List.of();
        }

        List<String> path = new ArrayList<>();
        String node = to;
        while (node != null) {
            path.add(node);
            node = prev.get(node);
        }
        Collections.reverse(path);
        return path;
    }

    public boolean hasPath(String from, String to) {
        validateNodes(from, to);
        if (from.equals(to)) return true;
        Map<String, Double> dist = dijkstra(from);
        Double d = dist.get(to);
        return d != null && d != Double.MAX_VALUE;
    }

    private Map<String, Double> dijkstra(String source) {
        Map<String, Double> dist = new HashMap<>();
        for (String node : adjacency.keySet()) {
            dist.put(node, Double.MAX_VALUE);
        }
        dist.put(source, 0.0);

        PriorityQueue<String> pq = new PriorityQueue<>(
            Comparator.comparingDouble(n -> dist.getOrDefault(n, Double.MAX_VALUE))
        );
        pq.add(source);

        while (!pq.isEmpty()) {
            String current = pq.poll();
            double currentDist = dist.get(current);
            if (currentDist == Double.MAX_VALUE) break;

            for (Edge edge : adjacency.getOrDefault(current, List.of())) {
                double newDist = currentDist + edge.weight;
                if (newDist < dist.getOrDefault(edge.to, Double.MAX_VALUE)) {
                    dist.put(edge.to, newDist);
                    pq.add(edge.to);
                }
            }
        }
        return dist;
    }

    private void validateNodes(String from, String to) {
        if (!adjacency.containsKey(from)) {
            throw new IllegalArgumentException("Unknown node: " + from);
        }
        if (!adjacency.containsKey(to)) {
            throw new IllegalArgumentException("Unknown node: " + to);
        }
    }
}
