import java.util.*;

public class ConflictDetector {

    private static final double EARTH_RADIUS_NM = 3440.065;

    public static class Position {
        public final double lat;
        public final double lon;
        public final double alt;
        public final double timestamp;

        public Position(double lat, double lon, double alt, double timestamp) {
            this.lat = lat;
            this.lon = lon;
            this.alt = alt;
            this.timestamp = timestamp;
        }
    }

    public static class AircraftTrack {
        public final String callsign;
        public final List<Position> positions;

        public AircraftTrack(String callsign, List<Position> positions) {
            this.callsign = callsign;
            this.positions = positions;
        }
    }

    public static class Conflict {
        public final String callsign1;
        public final String callsign2;
        public final double timestamp;
        public final double horizontalDistance;
        public final double verticalDistance;

        public Conflict(String callsign1, String callsign2, double timestamp,
                        double horizontalDistance, double verticalDistance) {
            this.callsign1 = callsign1;
            this.callsign2 = callsign2;
            this.timestamp = timestamp;
            this.horizontalDistance = horizontalDistance;
            this.verticalDistance = verticalDistance;
        }

        @Override
        public String toString() {
            return String.format("Conflict(%s, %s, t=%.1f, hDist=%.2f nm, vDist=%.1f ft)",
                    callsign1, callsign2, timestamp, horizontalDistance, verticalDistance);
        }
    }

    public List<Conflict> detectConflicts(List<AircraftTrack> tracks,
                                           double horizThresholdNm,
                                           double vertThresholdFt) {
        List<Conflict> conflicts = new ArrayList<>();
        for (int i = 0; i < tracks.size(); i++) {
            for (int j = i + 1; j < tracks.size(); j++) {
                AircraftTrack t1 = tracks.get(i);
                AircraftTrack t2 = tracks.get(j);
                Conflict conflict = findConflict(t1, t2, horizThresholdNm, vertThresholdFt);
                if (conflict != null) {
                    conflicts.add(conflict);
                }
            }
        }
        return conflicts;
    }

    private Conflict findConflict(AircraftTrack t1, AircraftTrack t2,
                                  double horizThreshNm, double vertThreshFt) {
        if (t1.positions.isEmpty() || t2.positions.isEmpty()) return null;

        double t1Start = t1.positions.get(0).timestamp;
        double t1End = t1.positions.get(t1.positions.size() - 1).timestamp;
        double t2Start = t2.positions.get(0).timestamp;
        double t2End = t2.positions.get(t2.positions.size() - 1).timestamp;

        double overlapStart = Math.max(t1Start, t2Start);
        double overlapEnd = Math.min(t1End, t2End);
        if (overlapStart > overlapEnd) return null;

        // Sample at regular intervals
        int steps = 100;
        double dt = (overlapEnd - overlapStart) / steps;

        Conflict closest = null;
        double minDist = Double.MAX_VALUE;

        for (int s = 0; s <= steps; s++) {
            double t = overlapStart + s * dt;
            Position p1 = interpolate(t1.positions, t);
            Position p2 = interpolate(t2.positions, t);
            if (p1 == null || p2 == null) continue;

            double hDist = haversineNm(p1.lat, p1.lon, p2.lat, p2.lon);
            double vDist = Math.abs(p1.alt - p2.alt);

            if (hDist < horizThreshNm && vDist < vertThreshFt) {
                double combined = hDist + vDist * 0.001;
                if (combined < minDist) {
                    minDist = combined;
                    // Ensure lexicographic ordering
                    String c1 = t1.callsign;
                    String c2 = t2.callsign;
                    if (c1.compareTo(c2) > 0) {
                        String tmp = c1; c1 = c2; c2 = tmp;
                    }
                    closest = new Conflict(c1, c2, t, hDist, vDist);
                }
            }
        }
        return closest;
    }

    private Position interpolate(List<Position> positions, double t) {
        if (positions.isEmpty()) return null;
        if (positions.size() == 1) {
            if (Math.abs(positions.get(0).timestamp - t) < 1e-9) return positions.get(0);
            return null;
        }

        // Binary search for the interval
        int lo = 0, hi = positions.size() - 1;
        while (lo < hi - 1) {
            int mid = (lo + hi) / 2;
            if (positions.get(mid).timestamp <= t) lo = mid;
            else hi = mid;
        }

        Position p1 = positions.get(lo);
        Position p2 = positions.get(hi);

        double tSpan = p2.timestamp - p1.timestamp;
        if (tSpan == 0) return p1;

        double ratio = (t - p1.timestamp) / tSpan;
        ratio = Math.max(0, Math.min(1, ratio));

        return new Position(
            p1.lat + ratio * (p2.lat - p1.lat),
            p1.lon + ratio * (p2.lon - p1.lon),
            p1.alt + ratio * (p2.alt - p1.alt),
            t
        );
    }

    private double haversineNm(double lat1, double lon1, double lat2, double lon2) {
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
                 + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2))
                 * Math.sin(dLon / 2) * Math.sin(dLon / 2);
        double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return EARTH_RADIUS_NM * c;
    }
}
