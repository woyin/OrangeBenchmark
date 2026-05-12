import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.List;

public class FlightPlanParserTest {

    private FlightPlanParser parser;

    @BeforeEach
    public void setUp() {
        parser = new FlightPlanParser();
    }

    @Test
    public void testBasicRoute() {
        // Route: KJFK (DIRECT) JFK.V1.DIKES (AIRWAY) DIKES (DIRECT) ULW700 (DIRECT) KOISE (DIRECT) KOISE.V3.KLAX (AIRWAY) KLAX (DIRECT)
        List<FlightPlanParser.RouteSegment> segments = parser.parseRoute(
            "KJFK JFK.V1.DIKES DIKES ULW700 KOISE KOISE.V3.KLAX KLAX"
        );
        assertEquals(7, segments.size());

        assertEquals("DIRECT", segments.get(0).getType());
        assertEquals("KJFK", segments.get(0).getFrom());

        assertEquals("AIRWAY", segments.get(1).getType());
        assertEquals("JFK", segments.get(1).getFrom());
        assertEquals("DIKES", segments.get(1).getTo());
        assertEquals("V1", segments.get(1).getAirway());

        assertEquals("DIRECT", segments.get(2).getType());
        assertEquals("DIKES", segments.get(2).getFrom());

        assertEquals("DIRECT", segments.get(3).getType());
        assertEquals("ULW700", segments.get(3).getFrom());

        assertEquals("DIRECT", segments.get(4).getType());
        assertEquals("KOISE", segments.get(4).getFrom());

        assertEquals("AIRWAY", segments.get(5).getType());
        assertEquals("KOISE", segments.get(5).getFrom());
        assertEquals("KLAX", segments.get(5).getTo());
        assertEquals("V3", segments.get(5).getAirway());

        assertEquals("DIRECT", segments.get(6).getType());
        assertEquals("KLAX", segments.get(6).getFrom());
    }

    @Test
    public void testDirectOnlyRoute() {
        List<FlightPlanParser.RouteSegment> segments = parser.parseRoute("ALPHA BRAVO CHARLIE");
        assertEquals(3, segments.size());
        for (FlightPlanParser.RouteSegment seg : segments) {
            assertEquals("DIRECT", seg.getType());
            assertNull(seg.getAirway());
        }
    }

    @Test
    public void testAirwayOnlyRoute() {
        List<FlightPlanParser.RouteSegment> segments = parser.parseRoute(
            "JFK.V1.DIKES DIKES.ULW700.KOISE"
        );
        assertEquals(2, segments.size());
        for (FlightPlanParser.RouteSegment seg : segments) {
            assertEquals("AIRWAY", seg.getType());
            assertNotNull(seg.getAirway());
        }
        assertEquals("V1", segments.get(0).getAirway());
        assertEquals("ULW700", segments.get(1).getAirway());
    }

    @Test
    public void testEmptyString() {
        List<FlightPlanParser.RouteSegment> segments = parser.parseRoute("");
        assertTrue(segments.isEmpty());
    }

    @Test
    public void testNullInput() {
        List<FlightPlanParser.RouteSegment> segments = parser.parseRoute(null);
        assertTrue(segments.isEmpty());
    }

    @Test
    public void testSingleWaypoint() {
        List<FlightPlanParser.RouteSegment> segments = parser.parseRoute("KJFK");
        assertEquals(1, segments.size());
        assertEquals("DIRECT", segments.get(0).getType());
        assertEquals("KJFK", segments.get(0).getFrom());
        assertEquals("KJFK", segments.get(0).getTo());
    }

    @Test
    public void testComplexMultiSegmentRoute() {
        String route = "KSFO SFO.V2.ODEAN ODEAN ODEAN.J209.REBSY REBSY REBSY.Q7.BETTE BETTE BETTE.V4.KJFK KJFK";
        List<FlightPlanParser.RouteSegment> segments = parser.parseRoute(route);
        assertEquals(9, segments.size());

        // Verify alternating pattern
        assertEquals("DIRECT", segments.get(0).getType());
        assertEquals("AIRWAY", segments.get(1).getType());
        assertEquals("DIRECT", segments.get(2).getType());
        assertEquals("AIRWAY", segments.get(3).getType());
        assertEquals("DIRECT", segments.get(4).getType());
        assertEquals("AIRWAY", segments.get(5).getType());
        assertEquals("DIRECT", segments.get(6).getType());
        assertEquals("AIRWAY", segments.get(7).getType());
        assertEquals("DIRECT", segments.get(8).getType());
    }

    @Test
    public void testGetWaypoints() {
        String route = "KJFK JFK.V1.DIKES DIKES ULW700 KOISE";
        List<String> waypoints = parser.getWaypoints(route);
        // Unique waypoints preserving first-occurrence order
        assertEquals(List.of("KJFK", "JFK", "DIKES", "ULW700", "KOISE"), waypoints);
    }

    @Test
    public void testGetAirwaySegments() {
        String route = "KJFK JFK.V1.DIKES DIKES ULW700 KOISE KOISE.V3.KLAX";
        List<FlightPlanParser.RouteSegment> airwaySegments = parser.getAirwaySegments(route);
        assertEquals(2, airwaySegments.size());
        assertEquals("V1", airwaySegments.get(0).getAirway());
        assertEquals("V3", airwaySegments.get(1).getAirway());
    }
}
