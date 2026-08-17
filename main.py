"""Command-line entry point for the Fly-in simulation."""

try:
    from parsing import DroneMap, MapParseError
    from pathfinder import Pathfinder
    from simulator import Simulator
    import sys

except Exception as error:
    print(f"\nError: {error}")
    sys.exit()


class PathBuilder:
    """Find paths and assign them to the drones."""

    def __init__(self, drone_map: DroneMap) -> None:
        """Initialize the path builder."""
        self.drone_map = drone_map
        self.pathfinder = Pathfinder(drone_map)

    def build(self) -> list[list[str]]:
        """Find two shortest paths and assign them to the drones."""
        if self.drone_map.start_name is None:
            raise ValueError("Map has no start zone")

        if self.drone_map.end_name is None:
            raise ValueError("Map has no end zone")

        paths = self.pathfinder.find_paths(self.drone_map.start_name,
                                           self.drone_map.end_name, 2)
        if not paths:
            raise ValueError("No path found")

        return [paths[index % len(paths)]
                for index in range(self.drone_map.nb_drones)]


if __name__ == "__main__":
    """Run the Fly-in simulation."""
    filename = sys.argv[1] if len(sys.argv) > 1 else "maps/map.txt"

    try:
        drone_map = DroneMap()
        drone_map.from_file(filename)

        path_builder = PathBuilder(drone_map)
        paths = path_builder.build()

        Simulator(drone_map, paths).run()

    except (OSError, MapParseError, KeyboardInterrupt) as error:
        print(f"\nError: {error}")
