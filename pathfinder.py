"""Find shortest paths for drones using zone costs."""

from models import ZoneType
from parsing import DroneMap


class Pathfinder:
    """Find the cheapest paths through the drone map."""

    def __init__(self, drone_map: DroneMap) -> None:
        """Create the pathfinder and build the adjacency list."""
        self.drone_map = drone_map
        self.adjacency: dict[str, list[str]] = {}
        self._build_adjacency()

    def _build_adjacency(self) -> None:
        """Build an undirected adjacency list."""
        for name in self.drone_map.zones:
            self.adjacency[name] = []

        for connection in self.drone_map.connections:
            self.adjacency[connection.zone_a].append(connection.zone_b)
            self.adjacency[connection.zone_b].append(connection.zone_a)

    def _zone_cost(self, zone_name: str) -> float:
        """Return the cost of entering a zone."""
        zone = self.drone_map.zones[zone_name]

        if zone.zone_type == ZoneType.BLOCKED:
            return float("inf")

        if zone.zone_type == ZoneType.PRIORITY:
            return 0.9

        if zone.zone_type == ZoneType.RESTRICTED:
            return 2.0

        return 1.0

    def _shortest_distances(self, end: str) -> dict[str, float]:
        """Calculate the cheapest cost from every zone to the end."""
        distances = {name: float("inf") for name in self.drone_map.zones}

        distances[end] = 0.0
        unvisited = set(self.drone_map.zones)

        while unvisited:
            current = self._closest(unvisited, distances)

            if current is None:
                break

            unvisited.remove(current)

            for neighbor in self.adjacency[current]:
                if neighbor not in unvisited:
                    continue

                cost = self._zone_cost(current)
                if cost == float("inf"):
                    continue

                new_distance = distances[current] + cost

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance

        return distances

    def _closest(self, unvisited: set[str], distances: dict[str, float]
                 ) -> str | None:
        """Return the unvisited zone with the smallest cost."""
        best_zone = None
        best_distance = float("inf")

        for zone in unvisited:
            if distances[zone] < best_distance:
                best_zone = zone
                best_distance = distances[zone]

        return best_zone

    def find_paths(self, start: str, end: str, number_of_paths: int
                   ) -> list[list[str]]:
        """Return several cheapest paths."""
        distances = self._shortest_distances(end)

        if distances[start] == float("inf"):
            raise ValueError(f"No path from '{start}' to '{end}'")

        return self._collect_paths(start, end, distances, number_of_paths)

    def _collect_paths(self, start: str, end: str,
                       distances: dict[str, float], limit: int
                       ) -> list[list[str]]:
        """Collect cheapest paths using a simple index-based stack."""
        paths: list[list[str]] = []
        path: list[str] = [start]

        stack: list[list] = [[start, 0]]

        while stack:
            if len(paths) >= limit:
                break

            current, index = stack[-1]

            if current == end:
                paths.append(path.copy())
                path.pop()
                stack.pop()
                continue

            neighbors = self.adjacency[current]

            if index >= len(neighbors):
                path.pop()
                stack.pop()
                continue

            stack[-1][1] += 1
            neighbor = neighbors[index]

            if neighbor in path:
                continue

            cost = self._zone_cost(neighbor)
            if cost == float("inf"):
                continue

            if cost + distances[neighbor] != distances[current]:
                continue

            path.append(neighbor)
            stack.append([neighbor, 0])

        return paths