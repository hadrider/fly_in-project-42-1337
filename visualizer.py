from __future__ import annotations
from typing import Dict, List, Set
from models import Graph, Drone
from models.zone import colorize, ANSI_COLORS

BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


def _drone_labels(drones: List[Drone], zone_name: str) -> str:
    """Return comma-separated drone labels currently in a zone."""
    labels = [d.label() for d in drones
              if d.current_zone == zone_name and not d.finished
              and d.traveling_to is None]
    if not labels:
        return ""
    return ANSI_COLORS.get("cyan", "") + ",".join(labels) + RESET


def render_turn(
    turn: int,
    graph: Graph,
    drones: List[Drone],
    moved_tokens: List[str],
    zone_occupancy: Dict[str, int],
    link_usage: Dict[tuple, int],
) -> None:
    """
    Print a rich colored summary of one simulation turn.

    Shows:
      - turn number
      - movement tokens (D1-zone format)
      - zone states with occupancy and drone positions
      - connection usage
    """
    sep = DIM + "─" * 60 + RESET

    print(sep)
    print(f"{BOLD}Turn {turn}{RESET}  " + "  ".join(moved_tokens))
    print()

    # zone states
    zone_parts: List[str] = []
    for name, zone in graph.zones.items():
        used = zone_occupancy.get(name, 0)
        capacity = zone.max_drones
        drone_str = _drone_labels(drones, name)

        # color zone name by its own color attribute
        colored_name = zone.display_name()

        # occupancy indicator
        if name in {graph.start_zone, graph.end_zone}:
            occ = ""
        elif used >= capacity:
            occ = ANSI_COLORS.get("red", "") + f"[{used}/{capacity}]" + RESET
        else:
            occ = DIM + f"[{used}/{capacity}]" + RESET

        entry = colored_name + occ
        if drone_str:
            entry += "(" + drone_str + ")"
        zone_parts.append(entry)

    print("  Zones : " + "  ".join(zone_parts))

    # connection usage
    conn_parts: List[str] = []
    for key, conn in graph.connections.items():
        used = link_usage.get(key, 0)
        cap = conn.max_link_capacity
        color = "red" if used >= cap else ""
        text = f"{conn.a}-{conn.b}:{used}/{cap}"
        conn_parts.append(colorize(text, color) if color else DIM + text + RESET)

    print("  Links : " + "  ".join(conn_parts))
    print()


def render_summary(total_turns: int, nb_drones: int) -> None:
    """Print final simulation summary."""
    sep = ANSI_COLORS.get("green", "") + "═" * 60 + RESET
    print(sep)
    print(f"{BOLD}Simulation complete{RESET}")
    print(f"  Drones delivered : {nb_drones}")
    print(f"  Total turns      : {total_turns}")
    avg = round(total_turns / nb_drones, 2) if nb_drones else 0
    print(f"  Avg turns/drone  : {avg}")
    print(sep)
