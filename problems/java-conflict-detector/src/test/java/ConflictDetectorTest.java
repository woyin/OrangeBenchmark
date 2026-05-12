import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.*;

public class ConflictDetectorTest {

    private ConflictDetector detector;

    @BeforeEach
    public void setUp() {
        detector = new ConflictDetector();
    }

    private ConflictDetector.AircraftTrack track(String callsign, ConflictDetector.Position... positions) {
        return new ConflictDetector.AircraftTrack(callsign, Arrays.asList(positions));
    }

    @Test
    public void testNoConflictsWellSeparated() {
        // Two tracks far apart
        ConflictDetector.AircraftTrack t1 = track("AAL100",
            new ConflictDetector.Position(40.0, -74.0, 35000, 0),
            new ConflictDetector.Position(41.0, -74.0, 35000, 600)
        );
        ConflictDetector.AircraftTrack t2 = track("DAL200",
            new ConflictDetector.Position(34.0, -118.0, 35000, 0),
            new ConflictDetector.Position(35.0, -118.0, 35000, 600)
        );
        List<ConflictDetector.Conflict> conflicts = detector.detectConflicts(
            Arrays.asList(t1, t2), 5.0, 1000.0);
        assertTrue(conflicts.isEmpty(), "Well-separated tracks should have no conflicts");
    }

    @Test
    public void testHeadOnConflict() {
        // Two tracks approaching head-on, crossing at midpoint
        ConflictDetector.AircraftTrack t1 = track("AAL100",
            new ConflictDetector.Position(40.0, -74.0, 35000, 0),
            new ConflictDetector.Position(40.01, -74.0, 35000, 600)
        );
        ConflictDetector.AircraftTrack t2 = track("DAL200",
            new ConflictDetector.Position(40.02, -74.0, 35000, 0),
            new ConflictDetector.Position(40.0, -74.0, 35000, 600)
        );
        List<ConflictDetector.Conflict> conflicts = detector.detectConflicts(
            Arrays.asList(t1, t2), 5.0, 1000.0);
        assertFalse(conflicts.isEmpty(), "Head-on tracks should conflict");
        ConflictDetector.Conflict c = conflicts.get(0);
        assertEquals("AAL100", c.callsign1);
        assertEquals("DAL200", c.callsign2);
        assertTrue(c.horizontalDistance < 5.0);
        assertTrue(c.verticalDistance < 1000.0);
    }

    @Test
    public void testParallelTracksNoConflict() {
        // Two parallel tracks, same direction, but horizontally separated
        ConflictDetector.AircraftTrack t1 = track("AAL100",
            new ConflictDetector.Position(40.0, -74.0, 35000, 0),
            new ConflictDetector.Position(41.0, -74.0, 35000, 600)
        );
        ConflictDetector.AircraftTrack t2 = track("DAL200",
            new ConflictDetector.Position(40.0, -73.0, 35000, 0),
            new ConflictDetector.Position(41.0, -73.0, 35000, 600)
        );
        List<ConflictDetector.Conflict> conflicts = detector.detectConflicts(
            Arrays.asList(t1, t2), 5.0, 1000.0);
        assertTrue(conflicts.isEmpty(), "Parallel tracks ~40nm apart should not conflict");
    }

    @Test
    public void testCrossingPathsConflict() {
        // Two tracks that cross paths at the same altitude
        ConflictDetector.AircraftTrack t1 = track("AAL100",
            new ConflictDetector.Position(40.0, -74.0, 35000, 0),
            new ConflictDetector.Position(40.02, -74.0, 35000, 600)
        );
        ConflictDetector.AircraftTrack t2 = track("DAL200",
            new ConflictDetector.Position(40.01, -74.02, 35000, 0),
            new ConflictDetector.Position(40.01, -73.98, 35000, 600)
        );
        List<ConflictDetector.Conflict> conflicts = detector.detectConflicts(
            Arrays.asList(t1, t2), 5.0, 1000.0);
        assertFalse(conflicts.isEmpty(), "Crossing paths should conflict");
    }

    @Test
    public void testMultipleConflicts() {
        // Three tracks where two pairs conflict
        ConflictDetector.AircraftTrack t1 = track("AAL100",
            new ConflictDetector.Position(40.0, -74.0, 35000, 0),
            new ConflictDetector.Position(40.01, -74.0, 35000, 600)
        );
        ConflictDetector.AircraftTrack t2 = track("DAL200",
            new ConflictDetector.Position(40.005, -74.0, 35000, 0),
            new ConflictDetector.Position(40.015, -74.0, 35000, 600)
        );
        ConflictDetector.AircraftTrack t3 = track("UAL300",
            new ConflictDetector.Position(40.01, -74.0, 35000, 0),
            new ConflictDetector.Position(40.02, -74.0, 35000, 600)
        );
        List<ConflictDetector.Conflict> conflicts = detector.detectConflicts(
            Arrays.asList(t1, t2, t3), 5.0, 1000.0);
        // Should have conflicts: AAL100-DAL200, AAL100-UAL300, DAL200-UAL300
        // At minimum 2 conflicts expected (they're all close)
        assertTrue(conflicts.size() >= 2,
            "Three nearby tracks should produce at least 2 conflict pairs, got " + conflicts.size());
    }

    @Test
    public void testSingleTrackNoPairs() {
        ConflictDetector.AircraftTrack t1 = track("AAL100",
            new ConflictDetector.Position(40.0, -74.0, 35000, 0),
            new ConflictDetector.Position(41.0, -74.0, 35000, 600)
        );
        List<ConflictDetector.Conflict> conflicts = detector.detectConflicts(
            Arrays.asList(t1), 5.0, 1000.0);
        assertTrue(conflicts.isEmpty(), "Single track should have no conflicts");
    }

    @Test
    public void testDifferentTimeRangesNoConflict() {
        // Two tracks that don't overlap in time
        ConflictDetector.AircraftTrack t1 = track("AAL100",
            new ConflictDetector.Position(40.0, -74.0, 35000, 0),
            new ConflictDetector.Position(40.01, -74.0, 35000, 600)
        );
        ConflictDetector.AircraftTrack t2 = track("DAL200",
            new ConflictDetector.Position(40.0, -74.0, 35000, 1000),
            new ConflictDetector.Position(40.01, -74.0, 35000, 1600)
        );
        List<ConflictDetector.Conflict> conflicts = detector.detectConflicts(
            Arrays.asList(t1, t2), 5.0, 1000.0);
        assertTrue(conflicts.isEmpty(),
            "Tracks with non-overlapping time ranges should not conflict");
    }

    @Test
    public void testVerticalSeparationNoConflict() {
        // Same horizontal position but different altitudes
        ConflictDetector.AircraftTrack t1 = track("AAL100",
            new ConflictDetector.Position(40.0, -74.0, 35000, 0),
            new ConflictDetector.Position(40.01, -74.0, 35000, 600)
        );
        ConflictDetector.AircraftTrack t2 = track("DAL200",
            new ConflictDetector.Position(40.0, -74.0, 40000, 0),
            new ConflictDetector.Position(40.01, -74.0, 40000, 600)
        );
        List<ConflictDetector.Conflict> conflicts = detector.detectConflicts(
            Arrays.asList(t1, t2), 5.0, 1000.0);
        assertTrue(conflicts.isEmpty(),
            "Tracks separated by 5000ft vertically should not conflict with 1000ft threshold");
    }
}
