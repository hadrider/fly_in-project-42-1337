"""Command-line entry point for the Fly-in simulation."""

import sys

from parsing import DroneMap, MapParseError
from pathfinder import Pathfinder
from simulator import Simulator


def build_paths(drone_map: DroneMap) -> list[list[str]]:
    """Calculate one shortest path for every drone."""
    if drone_map.start_name is None or drone_map.end_name is None:
        raise ValueError("Map has no start or end zone")
    pathfinder = Pathfinder(drone_map)
    paths: list[list[str]] = []
    for _ in range(drone_map.nb_drones):
        path = pathfinder.find_path(drone_map.start_name, drone_map.end_name)
        paths.append(path)
    return paths


def main() -> int:
    """Parse the map, calculate paths, and run the simulation."""
    filename = sys.argv[1] if len(sys.argv) > 1 else "maps/sample_map.txt"
    try:
        drone_map = DroneMap.from_file(filename)
        paths = build_paths(drone_map)
        Simulator(drone_map, paths).run()
    except (OSError, MapParseError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
