"""Tests for the runway incursion detection system."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "runway_monitor_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)

Runway = solution.Runway
Taxiway = solution.Taxiway
AirportLayout = solution.AirportLayout
AircraftPosition = solution.AircraftPosition
Alert = solution.Alert
RunwayMonitor = solution.RunwayMonitor


def _simple_layout():
    """Build a simple airport with one runway and one crossing taxiway."""
    runway = Runway("09L/27R", (0.0, 0.0), (1000.0, 0.0), 60.0)
    taxiway = Taxiway("Alpha", [(500.0, -200.0), (500.0, 200.0)], 30.0)
    crossings = [{"taxiway": "Alpha", "runway": "09L/27R", "point": (500.0, 0.0)}]
    return AirportLayout([runway], [taxiway], crossings)


def _multi_layout():
    """Build a multi-runway airport."""
    r1 = Runway("09L/27R", (0.0, 0.0), (2000.0, 0.0), 60.0)
    r2 = Runway("09R/27L", (0.0, 400.0), (2000.0, 400.0), 60.0)
    r3 = Runway("18/36", (1000.0, -100.0), (1000.0, 600.0), 45.0)
    tw = Taxiway("Bravo", [(1000.0, -100.0), (1000.0, 600.0)], 30.0)
    crossings = [
        {"taxiway": "Bravo", "runway": "09L/27R", "point": (1000.0, 0.0)},
        {"taxiway": "Bravo", "runway": "09R/27L", "point": (1000.0, 400.0)},
    ]
    return AirportLayout([r1, r2, r3], [tw], crossings)


class TestBasicIncursion:
    """Test 1: Aircraft enters active runway without authorization."""

    def test_alert_generated(self):
        layout = _simple_layout()
        monitor = RunwayMonitor(layout)
        monitor.set_active_runway("09L/27R", "A")
        alerts = monitor.update_position(
            AircraftPosition("BAW123", 200.0, 5.0, 100.0, True)
        )
        assert len(alerts) == 1
        assert alerts[0].alert_type == "RUNWAY_INCURSION"
        assert alerts[0].callsign == "BAW123"
        assert alerts[0].runway_name == "09L/27R"

    def test_no_alert_outside_zone(self):
        layout = _simple_layout()
        monitor = RunwayMonitor(layout)
        monitor.set_active_runway("09L/27R", "A")
        alerts = monitor.update_position(
            AircraftPosition("BAW123", 200.0, 50.0, 100.0, True)
        )
        assert len(alerts) == 0


class TestInactiveRunway:
    """Test 2: Aircraft on inactive runway produces no alert."""

    def test_no_alert_inactive(self):
        layout = _simple_layout()
        monitor = RunwayMonitor(layout)
        # Runway not activated
        alerts = monitor.update_position(
            AircraftPosition("BAW123", 200.0, 5.0, 100.0, True)
        )
        assert len(alerts) == 0


class TestAuthorizedCrossing:
    """Test 3: Aircraft crosses via active crossing, no alert."""

    def test_authorized_no_alert(self):
        layout = _simple_layout()
        monitor = RunwayMonitor(layout)
        monitor.set_active_runway("09L/27R", "A")
        monitor.set_crossing_active("Alpha", "09L/27R", True)
        # Position near the crossing point, within taxiway width
        alerts = monitor.update_position(
            AircraftPosition("BAW456", 500.0, 5.0, 200.0, True)
        )
        assert len(alerts) == 0


class TestUnauthorizedCrossing:
    """Test 4: Aircraft crosses via inactive crossing, alert generated."""

    def test_unauthorized_alert(self):
        layout = _simple_layout()
        monitor = RunwayMonitor(layout)
        monitor.set_active_runway("09L/27R", "A")
        # Crossing is NOT activated
        alerts = monitor.update_position(
            AircraftPosition("BAW789", 500.0, 5.0, 300.0, True)
        )
        assert len(alerts) == 1
        assert alerts[0].callsign == "BAW789"


class TestAirborneAircraft:
    """Test 5: Airborne aircraft over active runway produces no alert."""

    def test_airborne_no_alert(self):
        layout = _simple_layout()
        monitor = RunwayMonitor(layout)
        monitor.set_active_runway("09L/27R", "A")
        alerts = monitor.update_position(
            AircraftPosition("EZY999", 200.0, 5.0, 400.0, False)
        )
        assert len(alerts) == 0


class TestMultipleAircraft:
    """Test 6: Two aircraft on same active runway produce two alerts."""

    def test_two_alerts(self):
        layout = _simple_layout()
        monitor = RunwayMonitor(layout)
        monitor.set_active_runway("09L/27R", "A")
        alerts_a = monitor.update_position(
            AircraftPosition("AAL100", 200.0, 5.0, 500.0, True)
        )
        alerts_b = monitor.update_position(
            AircraftPosition("DAL200", 300.0, 5.0, 501.0, True)
        )
        assert len(alerts_a) == 1
        assert len(alerts_b) == 1
        assert alerts_a[0].callsign == "AAL100"
        assert alerts_b[0].callsign == "DAL200"


class TestComplexLayout:
    """Test 7: Multi-runway airport, only active runway triggers alerts."""

    def test_only_active_triggers(self):
        layout = _multi_layout()
        monitor = RunwayMonitor(layout)
        # Only activate 09L/27R
        monitor.set_active_runway("09L/27R", "A")
        # Position on active runway 09L/27R (y ~ 0)
        alerts = monitor.update_position(
            AircraftPosition("UPS300", 500.0, 5.0, 600.0, True)
        )
        assert len(alerts) == 1
        assert alerts[0].runway_name == "09L/27R"

    def test_inactive_runway_no_alert(self):
        layout = _multi_layout()
        monitor = RunwayMonitor(layout)
        monitor.set_active_runway("09L/27R", "A")
        # Position on inactive runway 09R/27L (y ~ 400)
        alerts = monitor.update_position(
            AircraftPosition("FDX400", 500.0, 405.0, 610.0, True)
        )
        assert len(alerts) == 0

    def test_multiple_active_runways(self):
        layout = _multi_layout()
        monitor = RunwayMonitor(layout)
        monitor.set_active_runway("09L/27R", "A")
        monitor.set_active_runway("09R/27L", "B")
        # Position on 09L/27R centerline intersection with 18/36 (x=1000, y=0)
        alerts = monitor.update_position(
            AircraftPosition("SWA500", 1000.0, 5.0, 620.0, True)
        )
        assert len(alerts) == 1
        assert alerts[0].runway_name == "09L/27R"


class TestPositionTracking:
    """Test 8: get_nearby_aircraft returns correct tracked aircraft."""

    def test_nearby_returns_tracked(self):
        layout = _simple_layout()
        monitor = RunwayMonitor(layout)
        monitor.update_position(
            AircraftPosition("NEB1", 100.0, 10.0, 100.0, True)
        )
        monitor.update_position(
            AircraftPosition("NEB2", 500.0, 15.0, 101.0, True)
        )
        # Far away aircraft
        monitor.update_position(
            AircraftPosition("FAR1", 500.0, 900.0, 102.0, True)
        )
        nearby = monitor.get_nearby_aircraft("09L/27R", 50.0)
        callsigns = {p.callsign for p in nearby}
        assert "NEB1" in callsigns
        assert "NEB2" in callsigns
        assert "FAR1" not in callsigns

    def test_active_runways_list(self):
        layout = _multi_layout()
        monitor = RunwayMonitor(layout)
        monitor.set_active_runway("09L/27R", "A")
        monitor.set_active_runway("18/36", "B")
        active = monitor.get_active_runways()
        assert set(active) == {"09L/27R", "18/36"}
