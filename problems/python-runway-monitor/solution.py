"""Runway incursion detection system for airport ground monitoring."""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Runway:
    """A runway defined by two endpoints and a width."""

    name: str
    endpoint_a: tuple[float, float]
    endpoint_b: tuple[float, float]
    width: float


@dataclass
class Taxiway:
    """A taxiway defined by a polyline path and a width."""

    name: str
    points: list[tuple[float, float]]
    width: float


@dataclass
class AirportLayout:
    """Airport layout containing runways, taxiways, and crossing definitions."""

    runways: list[Runway]
    taxiways: list[Taxiway]
    crossings: list[dict]  # {"taxiway": str, "runway": str, "point": (x, y)}


@dataclass
class AircraftPosition:
    """Aircraft position update."""

    callsign: str
    x: float
    y: float
    timestamp: float
    on_ground: bool


@dataclass
class Alert:
    """Alert generated when a runway incursion is detected."""

    alert_type: str
    callsign: str
    runway_name: str
    position: tuple[float, float]
    timestamp: float
    message: str


def _point_to_segment_distance(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> float:
    """Compute the perpendicular distance from point (px, py) to segment (ax, ay)-(bx, by)."""
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def _project_t(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> float:
    """Project point onto segment, returning parameter t in [0, 1]."""
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return 0.0
    return max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))


class RunwayMonitor:
    """Monitors aircraft positions and detects runway incursions."""

    def __init__(self, layout: AirportLayout) -> None:
        self._layout = layout
        self._runway_map: dict[str, Runway] = {r.name: r for r in layout.runways}
        self._active_runways: dict[str, str] = {}  # runway_name -> direction
        self._active_crossings: set[tuple[str, str]] = set()  # (taxiway, runway)
        self._positions: dict[str, AircraftPosition] = {}

    def set_active_runway(self, runway_name: str, direction: str) -> None:
        """Set a runway as active with a given direction ('A' or 'B')."""
        self._active_runways[runway_name] = direction

    def set_crossing_active(
        self, taxiway_name: str, runway_name: str, active: bool
    ) -> None:
        """Activate or deactivate a taxiway crossing on a runway."""
        key = (taxiway_name, runway_name)
        if active:
            self._active_crossings.add(key)
        else:
            self._active_crossings.discard(key)

    def update_position(self, pos: AircraftPosition) -> list[Alert]:
        """Process an aircraft position update and return any incursion alerts."""
        self._positions[pos.callsign] = pos
        if not pos.on_ground:
            return []

        alerts: list[Alert] = []
        for runway_name in self._active_runways:
            if not self.is_in_runway_zone(pos.x, pos.y, runway_name):
                continue
            if self._is_authorized(pos, runway_name):
                continue
            alerts.append(
                Alert(
                    alert_type="RUNWAY_INCURSION",
                    callsign=pos.callsign,
                    runway_name=runway_name,
                    position=(pos.x, pos.y),
                    timestamp=pos.timestamp,
                    message=(
                        f"Aircraft {pos.callsign} incursion on runway {runway_name} "
                        f"at ({pos.x:.1f}, {pos.y:.1f})"
                    ),
                )
            )
        return alerts

    def get_active_runways(self) -> list[str]:
        """Return names of currently active runways."""
        return list(self._active_runways.keys())

    def is_in_runway_zone(self, x: float, y: float, runway_name: str) -> bool:
        """Check if a point is within the runway zone rectangle."""
        runway = self._runway_map.get(runway_name)
        if runway is None:
            return False
        ax, ay = runway.endpoint_a
        bx, by = runway.endpoint_b
        dist = _point_to_segment_distance(x, y, ax, ay, bx, by)
        if dist > runway.width / 2:
            return False
        t = _project_t(x, y, ax, ay, bx, by)
        return 0.0 <= t <= 1.0

    def get_nearby_aircraft(
        self, runway_name: str, radius: float
    ) -> list[AircraftPosition]:
        """Return all tracked aircraft within radius of the runway centerline."""
        runway = self._runway_map.get(runway_name)
        if runway is None:
            return []
        ax, ay = runway.endpoint_a
        bx, by = runway.endpoint_b
        result: list[AircraftPosition] = []
        for pos in self._positions.values():
            dist = _point_to_segment_distance(pos.x, pos.y, ax, ay, bx, by)
            if dist <= radius:
                result.append(pos)
        return result

    def _is_authorized(self, pos: AircraftPosition, runway_name: str) -> bool:
        """Check if the aircraft is on an active authorized crossing."""
        for crossing in self._layout.crossings:
            if crossing["runway"] != runway_name:
                continue
            taxiway_name = crossing["taxiway"]
            if (taxiway_name, runway_name) not in self._active_crossings:
                continue
            cx, cy = crossing["point"]
            dist = math.hypot(pos.x - cx, pos.y - cy)
            taxiway = self._find_taxiway(taxiway_name)
            if taxiway is not None:
                if dist <= taxiway.width / 2:
                    return True
            elif dist <= 5.0:
                return True
        return False

    def _find_taxiway(self, name: str) -> Taxiway | None:
        """Look up a taxiway by name."""
        for tw in self._layout.taxiways:
            if tw.name == name:
                return tw
        return None
