import importlib.util
import math
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "route_planner_solution",
    Path(__file__).resolve().parents[1] / "solution.py",
)
solution = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(solution)
Waypoint = solution.Waypoint
RoutePlanner = solution.RoutePlanner


def _make_planner_triangle():
    p = RoutePlanner()
    p.add_waypoint(Waypoint("JFK", 40.6413, -73.7781))
    p.add_waypoint(Waypoint("LAX", 33.9425, -118.4081))
    p.add_waypoint(Waypoint("ORD", 41.9742, -87.9073))
    p.add_airway("JFK", "LAX", "J5")
    p.add_airway("JFK", "ORD", "J6")
    p.add_airway("ORD", "LAX", "J7")
    return p


def test_direct_distance():
    p = _make_planner_triangle()
    d = p.distance_between("JFK", "LAX")
    assert 2100 < d < 2200, f"Expected ~2145 NM, got {d}"


def test_shortest_route_triangle():
    p = _make_planner_triangle()
    path, dist = p.find_shortest_route("JFK", "LAX")
    assert path[0] == "JFK"
    assert path[-1] == "LAX"
    assert dist < 2200


def test_same_source_dest():
    p = _make_planner_triangle()
    path, dist = p.find_shortest_route("JFK", "JFK")
    assert path == ["JFK"]
    assert dist == 0.0


def test_no_route():
    p = RoutePlanner()
    p.add_waypoint(Waypoint("A", 0, 0))
    p.add_waypoint(Waypoint("B", 10, 10))
    path, dist = p.find_shortest_route("A", "B")
    assert path == []
    assert dist == float('inf')


def test_unknown_waypoint_raises():
    p = _make_planner_triangle()
    try:
        p.find_shortest_route("JFK", "UNKNOWN")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_bidirectional_airway():
    p = _make_planner_triangle()
    path_fwd, dist_fwd = p.find_shortest_route("LAX", "JFK")
    assert path_fwd[0] == "LAX"
    assert path_fwd[-1] == "JFK"
    assert abs(dist_fwd - p.distance_between("JFK", "LAX")) < 1


def test_long_chain():
    p = RoutePlanner()
    for i in range(20):
        p.add_waypoint(Waypoint(f"WP{i}", i * 1.0, i * 1.0))
        if i > 0:
            p.add_airway(f"WP{i-1}", f"WP{i}")
    path, dist = p.find_shortest_route("WP0", "WP19")
    assert len(path) == 20
    assert path[0] == "WP0"
    assert path[-1] == "WP19"


def test_shorter_indirect_route():
    p = RoutePlanner()
    p.add_waypoint(Waypoint("A", 0, 0))
    p.add_waypoint(Waypoint("B", 0, 10))
    p.add_waypoint(Waypoint("C", 0, 5))
    p.add_airway("A", "B")
    p.add_airway("A", "C")
    p.add_airway("C", "B")
    path, dist = p.find_shortest_route("A", "B")
    assert path == ["A", "C", "B"] or dist < p.distance_between("A", "B")
