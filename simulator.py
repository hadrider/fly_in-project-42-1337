"""Turn-by-turn drone movement simulation."""

from models import Connection, Drone, ZoneType
from parsing import DroneMap
from visualizer import PygameVisualizer


class Simulator:
    """Run drones through their paths while enforcing capacities."""

    def __init__(self, drone_map: DroneMap, paths: list[list[str]]) -> None:
        """Create drones and set up simulation state."""
        self.drone_map = drone_map

        self.drones = []
        start_zone = self.drone_map.zones[self.drone_map.start_name]
        start_zone.drones = len(paths)

        drone_id = 1
        for path in paths:
            new_drone = Drone(drone_id, path[0], path)
            self.drones.append(new_drone)
            drone_id += 1

        self.turn = 0
        self.link_usage: dict = {}
        self.moves: list = []
        self.visualizer = PygameVisualizer(drone_map)

    def run(self) -> None:
        """Run the simulation turn by turn until every drone finishes."""
        while not self._all_finished():
            self.turn += 1
            self.link_usage = {}

            moves = []
            drones_moved = []

            for drone in self.drones:
                if drone.status == "in_flight":
                    drone.remaining_turns -= 1

                    if (drone.remaining_turns == 0 and
                            drone.destination is not None):
                        where_it_landed = drone.destination
                        self._arrive(drone)

                        move_text = f"D{drone.drone_id}-{where_it_landed}"
                        moves.append((drone.drone_id, move_text))
                        drones_moved.append(drone.drone_id)

            for drone in self.drones:
                if drone.drone_id in drones_moved:
                    continue

                if drone.status != "waiting":
                    continue

                move_result = self._try_move(drone)

                if move_result is not None:
                    moves.append((drone.drone_id, move_result))

            if len(moves) > 0:
                self.moves.append(moves)

                text = f"Turn {self.turn}: "
                for _, move_text in moves:
                    text += move_text + " "
                print(text)

        self.visualizer.play(self.moves)

    def _all_finished(self) -> bool:
        """Return True once every drone has reached the goal."""
        return all(drone.is_finished() for drone in self.drones)

    def _try_move(self, drone: Drone) -> str | None:
        """Try to move a drone into its next zone, if there's room."""
        next_zone_name = drone.next_zone()

        if next_zone_name is None:
            drone.status = "finished"
            return None

        next_zone = self.drone_map.zones[next_zone_name]

        if next_zone_name != self.drone_map.end_name:
            if not next_zone.has_space():
                return None

        old_position = drone.current_position
        connection = self._find_connection(old_position, next_zone_name)

        link_key = (old_position, next_zone_name)

        if link_key in self.link_usage:
            times_used = self.link_usage[link_key]
        else:
            times_used = 0

        if times_used >= connection.max_link_capacity:
            return None

        self.link_usage[link_key] = times_used + 1

        old_zone = self.drone_map.zones[old_position]
        old_zone.drones -= 1

        drone.path_index += 1
        drone.destination = next_zone_name

        if next_zone.zone_type == ZoneType.RESTRICTED:
            drone.status = "in_flight"
            drone.remaining_turns = 1
            next_zone.drones += 1
            return f"D{drone.drone_id}-{old_position}-{next_zone_name}"

        self._arrive(drone)
        return f"D{drone.drone_id}-{next_zone_name}"

    def _arrive(self, drone: Drone) -> None:
        """Move a drone onto its destination zone and update its status."""
        if drone.destination is None:
            raise ValueError("Drone has no destination to arrive at")

        drone.current_position = drone.destination
        drone.destination = None

        zone = self.drone_map.zones[drone.current_position]
        if zone.zone_type != ZoneType.RESTRICTED:
            zone.drones += 1

        if drone.current_position == self.drone_map.end_name:
            drone.status = "finished"
        else:
            drone.status = "waiting"

    def _find_connection(self, zone_a: str, zone_b: str) -> Connection:
        """Find the connection between two zones, in either direction."""
        for connection in self.drone_map.connections:
            match: Connection = connection

            if match.zone_a == zone_a and match.zone_b == zone_b:
                return match
            if match.zone_a == zone_b and match.zone_b == zone_a:
                return match

        raise ValueError(f"No connection between '{zone_a}' and '{zone_b}'")
