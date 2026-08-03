from __future__ import annotations
import argparse
import sys

from parser import parse_file
from simulator import run_simulation


def main() -> int:
    """Entry point for the fly-in drone routing simulation."""
    arg_parser = argparse.ArgumentParser(
        description="Fly-in: route drones through a zone network"
    )
    arg_parser.add_argument("map_file", help="Path to the map file")
    arg_parser.add_argument(
        "--no-visual",
        action="store_true",
        help="Disable colored visual output, print log lines only",
    )
    arg_parser.add_argument(
        "--capacity-info",
        action="store_true",
        help="Append zone and link capacity info to each log line",
    )
    args = arg_parser.parse_args()

    try:
        graph, nb_drones = parse_file(args.map_file)
        lines = run_simulation(
            graph,
            nb_drones,
            visual=not args.no_visual,
            show_capacity=args.capacity_info,
        )
        if args.no_visual:
            for line in lines:
                print(line)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
