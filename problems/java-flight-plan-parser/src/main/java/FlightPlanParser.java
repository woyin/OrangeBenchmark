import java.util.*;

public class FlightPlanParser {

    public static class RouteSegment {
        private final String type;
        private final String from;
        private final String to;
        private final String airway;

        public RouteSegment(String type, String from, String to, String airway) {
            this.type = type;
            this.from = from;
            this.to = to;
            this.airway = airway;
        }

        public String getType() { return type; }
        public String getFrom() { return from; }
        public String getTo() { return to; }
        public String getAirway() { return airway; }

        @Override
        public String toString() {
            if ("DIRECT".equals(type)) {
                return "DIRECT(" + from + ")";
            }
            return "AIRWAY(" + from + " -> " + airway + " -> " + to + ")";
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            RouteSegment that = (RouteSegment) o;
            return Objects.equals(type, that.type) &&
                   Objects.equals(from, that.from) &&
                   Objects.equals(to, that.to) &&
                   Objects.equals(airway, that.airway);
        }

        @Override
        public int hashCode() {
            return Objects.hash(type, from, to, airway);
        }
    }

    public List<RouteSegment> parseRoute(String route) {
        List<RouteSegment> segments = new ArrayList<>();
        if (route == null || route.isBlank()) {
            return segments;
        }

        String[] parts = route.trim().split("\\s+");
        for (String part : parts) {
            if (part.isEmpty()) continue;
            segments.add(parseSegment(part));
        }
        return segments;
    }

    private RouteSegment parseSegment(String part) {
        String[] components = part.split("\\.");
        if (components.length == 3) {
            return new RouteSegment("AIRWAY", components[0], components[2], components[1]);
        } else {
            return new RouteSegment("DIRECT", part, part, null);
        }
    }

    public List<String> getWaypoints(String route) {
        List<String> waypoints = new ArrayList<>();
        LinkedHashSet<String> seen = new LinkedHashSet<>();
        List<RouteSegment> segments = parseRoute(route);

        for (RouteSegment seg : segments) {
            if (seen.add(seg.getFrom())) {
                waypoints.add(seg.getFrom());
            }
            if (!seg.getTo().equals(seg.getFrom()) && seen.add(seg.getTo())) {
                waypoints.add(seg.getTo());
            }
        }
        return waypoints;
    }

    public List<RouteSegment> getAirwaySegments(String route) {
        List<RouteSegment> result = new ArrayList<>();
        for (RouteSegment seg : parseRoute(route)) {
            if ("AIRWAY".equals(seg.getType())) {
                result.add(seg);
            }
        }
        return result;
    }
}
