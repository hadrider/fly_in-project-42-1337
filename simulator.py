"""Turn-by-turn drone movement simulation."""

from models import Connection, Drone, Zone, ZoneType
from parsing import DroneMap
from visualizer import PygameVisualizer
from typing import Any


class Simulator:
    """Run drones through their paths while enforcing capacities."""

    def __init__(self, drone_map: DroneMap, paths: list[list[str]]) -> None:
        """Create drones and prepare simulation state."""
        self.drone_map = drone_map
        self.drones = self._create_drones(paths)
        self.turn = 0
        self.link_usage: dict[tuple[str, str], int] = {}
        self.visualizer = PygameVisualizer(drone_map)
        self.moves: list = []

    def _create_drones(self, paths: list[list[str]]) -> list[Drone]:
        """Create one drone for each calculated path."""
        drones: list[Drone] = []

        start = self._start_zone()
        start.drones = len(paths)

        for index, path in enumerate(paths, start=1):
            drones.append(Drone(index, path[0], path))

        return drones

    def run(self) -> None:
        """Run the simulation until all drones reach the goal."""
        while not self._all_finished():
            self.turn += 1
            self._reset_link_usage()

            finished = self._finish_in_flight_drones()
            moved_drones = {drone_id for drone_id, _ in finished}
            moves = finished
            moves.extend(self._move_waiting_drones(moved_drones))

            if moves:
                self.moves.append(moves)
                self._print_turn(moves)

        self.visualizer.play(self.moves)

    def _finish_in_flight_drones(self) -> list[tuple[int, str]]:
        """Finish restricted movements that started earlier."""
        moves: list[tuple[int, str]] = []

        for drone in self.drones:
            if drone.status != "in_flight":
                continue

            drone.remaining_turns -= 1

            if drone.remaining_turns == 0:
                destination = drone.destination

                if destination is None:
                    continue

                self._arrive(drone)
                moves.append((drone.drone_id,
                              f"D{drone.drone_id}-{destination}"))

        return moves

    def _move_waiting_drones(
        self,
        moved_drones: set[int],
    ) -> list[tuple[int, str]]:
        """Move waiting drones once during this turn."""
        moves: list[tuple[int, str]] = []

        for drone in self.drones:
            if drone.drone_id in moved_drones:
                continue

            if drone.status != "waiting":
                continue

            if drone.is_finished():
                continue

            move = self._try_move(drone)

            if move is not None:
                moves.append((drone.drone_id, move))

        return moves

    def _try_move(self, drone: Drone) -> str | None:
        """Try to move a drone to its next zone."""
        next_zone_name = drone.next_zone()

        if next_zone_name is None:
            drone.status = "finished"
            return None

        next_zone = self.drone_map.zones[next_zone_name]

        if next_zone_name != self._end_name():
            if not next_zone.has_space():
                return None

        if not self._link_has_space(drone.current_position,
                                    next_zone_name):
            return None

        old_position = drone.current_position

        self._use_link(old_position, next_zone_name)
        self._leave_current_zone(drone)
        self._start_move(drone, next_zone)

        if next_zone.zone_type == ZoneType.RESTRICTED:
            return (f"D{drone.drone_id}-{old_position}-{next_zone_name}")

        return f"D{drone.drone_id}-{next_zone_name}"

    def _start_move(self, drone: Drone, next_zone: Zone) -> None:
        """Start a movement into the next zone."""
        drone.path_index += 1
        drone.destination = next_zone.name

        if next_zone.zone_type == ZoneType.RESTRICTED:
            drone.status = "in_flight"
            next_zone.drones += 1
            drone.remaining_turns = 1
            return

        self._arrive(drone)

    def _arrive(self, drone: Drone) -> None:
        """Arrive at the drone's destination."""
        if drone.destination is None:
            return

        drone.current_position = drone.destination
        drone.destination = None
        zone = self.drone_map.zones[drone.current_position]

        if zone.zone_type != ZoneType.RESTRICTED:
            zone.drones += 1

        if drone.current_position == self._end_name():
            drone.status = "finished"
        else:
            drone.status = "waiting"

    def _leave_current_zone(self, drone: Drone) -> None:
        """Free the drone's current zone."""
        old_zone = self.drone_map.zones[drone.current_position]
        old_zone.drones -= 1

    def _link_has_space(self, zone_a: str, zone_b: str) -> bool:
        """Return True when the connection has capacity."""
        connection = self._find_connection(zone_a, zone_b)
        key = self._link_key(zone_a, zone_b)

        used = self.link_usage.get(key, 0)

        return used < connection.max_link_capacity

    def _use_link(self, zone_a: str, zone_b: str) -> None:
        """Record one drone using a connection this turn."""
        key = self._link_key(zone_a, zone_b)

        self.link_usage[key] = self.link_usage.get(key, 0) + 1

    def _find_connection(
        self,
        zone_a: str,
        zone_b: str,
    ) -> Connection | Any:
        """Find the connection between two zones."""
        for connection in self.drone_map.connections:
            direct = (connection.zone_a == zone_a
                      and connection.zone_b == zone_b)

            reverse = (connection.zone_a == zone_b
                       and connection.zone_b == zone_a)

            if direct or reverse:
                return connection

        raise ValueError(f"No connection between '{zone_a}' and '{zone_b}'")

    def _link_key(
        self,
        zone_a: str,
        zone_b: str,
    ) -> tuple[str, str]:
        """Return a stable key for an undirected connection."""
        if zone_a < zone_b:
            return zone_a, zone_b

        return zone_b, zone_a

    def _reset_link_usage(self) -> None:
        """Reset connection usage for the new turn."""
        self.link_usage.clear()

    def _all_finished(self) -> bool:
        """Return True when every drone reached the goal."""
        return all(drone.is_finished() for drone in self.drones)

    def _start_zone(self) -> Zone | Any:
        """Return the start zone."""
        if self.drone_map.start_name is None:
            raise ValueError("Map has no start zone")

        return self.drone_map.zones[self.drone_map.start_name]

    def _end_name(self) -> str:
        """Return the end zone name."""
        if self.drone_map.end_name is None:
            raise ValueError("Map has no end zone")

        return self.drone_map.end_name

    def _print_turn(
        self,
        moves: list[tuple[int, str]],
    ) -> None:
        """Print only drones that moved this turn."""
        print(f"Turn {self.turn}: " + " ".join(text for _, text in moves))
