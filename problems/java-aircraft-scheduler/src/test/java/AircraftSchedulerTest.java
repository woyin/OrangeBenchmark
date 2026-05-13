import org.junit.jupiter.api.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class AircraftSchedulerTest {
    @Test void testSingleFlight() {
        AircraftScheduler s = new AircraftScheduler();
        s.addGate(new Gate("G1", 200));
        s.addFlight(new Flight("AA100","B737",1000,1200,150));
        List<Assignment> r = s.schedule();
        assertEquals(1, r.size());
        assertEquals("AA100", r.get(0).flightId);
    }

    @Test void testTwoFlightsSameGate() {
        AircraftScheduler s = new AircraftScheduler();
        s.addGate(new Gate("G1", 200));
        s.addFlight(new Flight("AA100","B737",1000,1200,150));
        s.addFlight(new Flight("AA200","A320",1300,1500,120));
        List<Assignment> r = s.schedule();
        assertEquals(2, r.size());
    }

    @Test void testOverlappingFlights() {
        AircraftScheduler s = new AircraftScheduler();
        s.addGate(new Gate("G1", 200));
        s.addFlight(new Flight("AA100","B737",1000,1200,150));
        s.addFlight(new Flight("AA200","A320",1100,1300,100));
        List<Assignment> r = s.schedule();
        assertEquals(1, r.size());
        assertEquals("AA100", r.get(0).flightId);
    }

    @Test void testTwoGates() {
        AircraftScheduler s = new AircraftScheduler();
        s.addGate(new Gate("G1", 200));
        s.addGate(new Gate("G2", 300));
        s.addFlight(new Flight("AA100","B737",1000,1200,150));
        s.addFlight(new Flight("AA200","A320",1100,1300,200));
        List<Assignment> r = s.schedule();
        assertEquals(2, r.size());
    }

    @Test void testSortedByFlightId() {
        AircraftScheduler s = new AircraftScheduler();
        s.addGate(new Gate("G1", 200));
        s.addGate(new Gate("G2", 300));
        s.addFlight(new Flight("BB100","B737",1000,1200,100));
        s.addFlight(new Flight("AA200","A320",1300,1500,200));
        List<Assignment> r = s.schedule();
        assertEquals("AA200", r.get(0).flightId);
        assertEquals("BB100", r.get(1).flightId);
    }

    @Test void testNoGates() {
        AircraftScheduler s = new AircraftScheduler();
        s.addFlight(new Flight("AA100","B737",1000,1200,150));
        assertEquals(Collections.emptyList(), s.schedule());
    }
}
