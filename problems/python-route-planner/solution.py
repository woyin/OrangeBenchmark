class Waypoint:
    def __init__(self, name: str, lat: float, lon: float):
        self.name = name
        self.lat = lat
        self.lon = lon


class RoutePlanner:
    def add_waypoint(self, waypoint: Waypoint) -> None:
        pass

    def add_airway(self, wp1_name: str, wp2_name: str, name: str = "") -> None:
        pass

    def find_shortest_route(self, from_name: str, to_name: str) -> tuple:
        return ([], float('inf'))

    def distance_between(self, name1: str, name2: str) -> float:
        return 0.0
