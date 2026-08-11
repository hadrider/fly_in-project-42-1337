"""Turn-by-turn drone movement simulation."""

from models import Connection, Drone, Zone, ZoneType
from parsing import DroneMap
from visualizer import TerminalVisualizer
from colors import color_text
import time


class Simulator:
    """Run drones through their paths while enforcing capacities."""

    def __init__(self, drone_map: DroneMap, paths: list[list[str]]) -> None:
        """Create drones and prepare simulation state."""
        self.drone_map = drone_map
        self.drones = self._create_drones(paths)
        self.turn = 0
        self.link_usage: dict[tuple[str, str], int] = {}
        self.visualizer = TerminalVisualizer(drone_map)

    def _create_drones(self, paths: list[list[str]]) -> list[Drone]:
        """Create one drone for each calculated path."""
        drones: list[Drone] = []
        start = self._start_zone()
        start.drones = len(paths)
        for index, path in enumerate(paths, start=1):
            drones.append(Drone(index, path[0], path))
        return drones

    def run(self) -> None:
        """Run turns until every drone reaches the destination."""
        while not self._all_finished():
            self.turn += 1
            self._reset_link_usage()
            self._finish_in_flight_drones()
            self._move_waiting_drones()
            self.visualizer.show(self.drones, self.turn)
            time.sleep(0.5)

    def _finish_in_flight_drones(self) -> None:
        """Complete restricted moves that started on an earlier turn."""
        for drone in self.drones:
            if drone.remaining_turns > 0:
                drone.remaining_turns -= 1
                if drone.remaining_turns == 0:
                    self._arrive(drone)

    def _move_waiting_drones(self) -> None:
        """Try to move every drone that is currently waiting."""
        for drone in self.drones:
            if drone.status != "waiting":
                continue
            if drone.is_finished():
                continue
            self._try_move(drone)

    def _try_move(self, drone: Drone) -> None:
        """Move a drone when its next zone and link have capacity."""
        next_zone_name = drone.next_zone()
        if next_zone_name is None:
            drone.status = "finished"
            return

        next_zone = self.drone_map.zones[next_zone_name]

        if next_zone_name != self._end_name():
            if not next_zone.has_space():
                return

        if not self._link_has_space(
            drone.current_position,
            next_zone_name
        ):
            return

        self._use_link(drone.current_position, next_zone_name)
        self._leave_current_zone(drone)
        self._start_move(drone, next_zone)

    def _start_move(self, drone: Drone, next_zone: Zone) -> None:
        """Start a normal or restricted move into the next zone."""
        drone.path_index += 1
        drone.destination = next_zone.name
        if next_zone.zone_type == ZoneType.RESTRICTED:
            drone.status = "in_flight"
            drone.remaining_turns = 2
            return
        self._arrive(drone)

    def _arrive(self, drone: Drone) -> None:
        """Put a drone into its destination zone."""
        if drone.destination is None:
            return
        drone.current_position = drone.destination
        drone.destination = None
        self.drone_map.zones[drone.current_position].drones += 1
        if drone.current_position == self._end_name():
            drone.status = "finished"
        else:
            drone.status = "waiting"

    def _leave_current_zone(self, drone: Drone) -> None:
        """Free the drone's old zone before filling the next zone."""
        old_zone = self.drone_map.zones[drone.current_position]
        old_zone.drones -= 1

    def _link_has_space(self, zone_a: str, zone_b: str) -> bool:
        """Return True when the connection has unused capacity this turn."""
        connection = self._find_connection(zone_a, zone_b)
        key = self._link_key(zone_a, zone_b)
        used = self.link_usage.get(key, 0)
        return used < connection.max_link_capacity

    def _use_link(self, zone_a: str, zone_b: str) -> None:
        """Record one drone using a connection this turn."""
        key = self._link_key(zone_a, zone_b)
        self.link_usage[key] = self.link_usage.get(key, 0) + 1

    def _find_connection(self, zone_a: str, zone_b: str) -> Connection:
        """Find the connection joining two zones."""
        for connection in self.drone_map.connections:
            direct = (
                connection.zone_a == zone_a and connection.zone_b == zone_b
            )
            reverse = (
                connection.zone_a == zone_b and connection.zone_b == zone_a
            )
            if direct or reverse:
                return connection
        raise ValueError(f"No connection between '{zone_a}' and '{zone_b}'")

    def _link_key(self, zone_a: str, zone_b: str) -> tuple[str, str]:
        """Return one stable key for an undirected connection."""
        if zone_a < zone_b:
            return zone_a, zone_b
        return zone_b, zone_a

    def _reset_link_usage(self) -> None:
        """Clear connection usage at the beginning of each turn."""
        self.link_usage.clear()

    def _all_finished(self) -> bool:
        """Return True when every drone has reached the end."""
        for drone in self.drones:
            if not drone.is_finished():
                return False
        return True

    def _start_zone(self) -> Zone:
        """Return the map's start zone."""
        if self.drone_map.start_name is None:
            raise ValueError("Map has no start zone")
        return self.drone_map.zones[self.drone_map.start_name]

    def _end_name(self) -> str:
        """Return the map's end zone name."""
        if self.drone_map.end_name is None:
            raise ValueError("Map has no end zone")
        return self.drone_map.end_name

    def _print_turn(self) -> None:
        """Print the visible position of every drone for this turn."""
        output: list[str] = []
        for drone in self.drones:
            output.append(self._drone_text(drone))
        print(f"Turn {self.turn}: " + " ".join(output))

    def _drone_text(self, drone: Drone) -> str:
        """Format one drone's current visible position."""
        if drone.status == "in_flight":
            text = f"D{drone.drone_id}-in-flight"
            return text
        zone = self.drone_map.zones[drone.current_position]
        text = f"D{drone.drone_id}-{zone.name}"
        return color_text(text, zone.color)
