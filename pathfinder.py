"""Manual Dijkstra path finding for the drone map."""

from models import ZoneType
from parsing import DroneMap


class Pathfinder:
    """Find the lowest-cost route using a dictionary adjacency list."""

    def __init__(self, drone_map: DroneMap) -> None:
        """Build the adjacency list from the map connections."""
        self.drone_map = drone_map
        self.adjacency: dict[str, list[str]] = {}
        self._build_adjacency()

    def _build_adjacency(self) -> None:
        """Add both directions of every connection."""
        for name in self.drone_map.zones:
            self.adjacency[name] = []
        for connection in self.drone_map.connections:
            self.adjacency[connection.zone_a].append(connection.zone_b)
            self.adjacency[connection.zone_b].append(connection.zone_a)

    def find_path(self, start: str, end: str) -> list[str]:
        """Return the cheapest path from start to end."""
        distances: dict[str, int] = {}
        previous: dict[str, str | None] = {}
        unvisited: set[str] = set(self.adjacency)

        for name in self.adjacency:
            distances[name] = 10**12
            previous[name] = None
        distances[start] = 0

        while unvisited:
            current = self._closest(unvisited, distances)
            if current is None:
                break
            unvisited.remove(current)
            if current == end:
                break
            self._relax_neighbors(current, unvisited, distances, previous)

        return self._build_path(start, end, distances, previous)

    def _closest(
        self, unvisited: set[str], distances: dict[str, int]
    ) -> str | None:
        """Return the unvisited zone with the smallest known distance."""
        best_zone: str | None = None
        best_distance = 10**12
        for zone in unvisited:
            if distances[zone] < best_distance:
                best_zone = zone
                best_distance = distances[zone]
        return best_zone

    def _relax_neighbors(
        self,
        current: str,
        unvisited: set[str],
        distances: dict[str, int],
        previous: dict[str, str | None],
    ) -> None:
        """Try to improve each reachable neighbor's distance."""
        for neighbor in self.adjacency[current]:
            if neighbor not in unvisited:
                continue
            zone = self.drone_map.zones[neighbor]
            if zone.zone_type == ZoneType.BLOCKED:
                continue
            new_distance = distances[current] + zone.entry_cost()
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current

    def _build_path(
        self,
        start: str,
        end: str,
        distances: dict[str, int],
        previous: dict[str, str | None],
    ) -> list[str]:
        """Reconstruct the path from the previous-zone table."""
        if distances[end] == 10**12:
            raise ValueError(f"No path from '{start}' to '{end}'")
        path: list[str] = []
        current: str | None = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        return path
