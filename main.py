"""Main entry point for the Fly-in drone simulation.

Fully typesafe, handles command-line arguments, exceptions gracefully, and
provides a rich colored terminal visual representation of the simulation.
"""

from __future__ import annotations
import argparse
import sys
from typing import List

from parser import parse_file
from simulator import run_simulation


def colorize_output(line: str) -> str:
    """Apply ANSI terminal color codes to a simulation output line.

    Makes drone IDs, destination zones, transit connections, and capacity
    information clearly distinguishable to satisfy the visual feedback
    requirement.

    Args:
        line: The plain text simulation line.

    Returns:
        The colorized simulation line.
    """
    # Split between movement tokens and capacity information
    parts = line.split(" | ZONES ")
    moves_part = parts[0]
    cap_part = parts[1] if len(parts) > 1 else ""

    # Colorize movement tokens
    # e.g., "D1-corridorA D2-hub-roof1"
    colored_tokens: List[str] = []
    for token in moves_part.split():
        if not token:
            continue

        # Format is D<ID>-<zone> or D<ID>-<zone1>-<zone2>
        subparts = token.split("-")
        drone_id = subparts[0]  # D<ID>
        # Drone ID in bright cyan (\033[96m)
        colored_token = f"\033[96m{drone_id}\033[0m"

        if len(subparts) == 2:
            dest_zone = subparts[1]
            # Normal zone in bright green (\033[92m)
            colored_token += f"-\033[92m{dest_zone}\033[0m"
        elif len(subparts) == 3:
            z1, z2 = subparts[1], subparts[2]
            # In-transit connection in bright yellow (\033[93m)
            colored_token += f"-\033[93m{z1}-{z2}\033[0m"

        colored_tokens.append(colored_token)

    colored_line = " ".join(colored_tokens)

    if cap_part:
        # Colorize zone capacity info
        # e.g., "hub:0/999999, roof1:1/1"
        colored_line += " \033[1;30m|\033[0m \033[1;35mZONES\033[0m "
        zone_tokens = cap_part.split(", ")
        colored_zones = []
        for z_tok in zone_tokens:
            if ":" not in z_tok:
                colored_zones.append(z_tok)
                continue
            z_name, ratio = z_tok.split(":", 1)
            used, mx = ratio.split("/")
            used_val = int(used)
            mx_val = int(mx)

            # Color code based on utilization
            if used_val == 0:
                color_code = "\033[32m"  # Green
            elif used_val >= mx_val:
                color_code = "\033[31m"  # Red
            else:
                color_code = "\033[33m"  # Yellow

            colored_zones.append(
                f"\033[1m{z_name}\033[0m:{color_code}{used}/{mx}\033[0m"
            )
        colored_line += ", ".join(colored_zones)

    return colored_line


def main() -> int:
    """Main function executing parser and simulator with arguments."""
    parser = argparse.ArgumentParser(description="Fly-in drone simulation")
    parser.add_argument("map_file", help="Path to map file")
    parser.add_argument(
        "--capacity-info",
        action="store_true",
        help="Show capacity usage each turn"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored terminal output"
    )
    args = parser.parse_args()

    try:
        graph, nb_drones = parse_file(args.map_file)
        lines = run_simulation(
            graph, nb_drones, show_capacity=args.capacity_info
        )

        # Decide whether to use colors (tty support check)
        use_color = not args.no_color and sys.stdout.isatty()

        for line in lines:
            if use_color:
                print(colorize_output(line))
            else:
                print(line)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
