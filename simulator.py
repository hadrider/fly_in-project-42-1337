from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Tuple
from models import Graph, Drone
from pathfinder import shortest_path
from visualizer import render_turn, render_summary


def run_simulation(
    graph: Graph,
    nb_drones: int,
    visual: bool = True,
    show_capacity: bool = False,
) -> List[str]:
    """
    Run the full drone simulation turn by turn.

    Args:
        graph: the parsed zone/connection graph
        nb_drones: number of drones starting at start_zone
        visual: if True, print colored turn-by-turn display
        show_capacity: if True, append capacity info to log lines

    Returns:
        List of output strings, one per turn (D<ID>-<zone> format).
    """
    start = graph.start_zone
    end = graph.end_zone
    assert start is not None and end is not None

    base_path = shortest_path(graph, start, end)
    if base_path is None:
        raise ValueError("No valid path from start_hub to end_hub")

    drones: List[Drone] = [
        Drone(drone_id=i + 1, current_zone=start) for i in range(nb_drones)
    ]
    path_index: Dict[int, int] = {d.drone_id: 0 for d in drones}
    output_lines: List[str] = []
    turn = 0

    while not all(d.finished for d in drones):
        turn += 1

        # snapshot occupancy before moves
        zone_occupancy: Dict[str, int] = defaultdict(int)
        for d in drones:
            if not d.finished and d.traveling_to is None:
                zone_occupancy[d.current_zone] += 1

        link_usage: Dict[Tuple[str, str], int] = defaultdict(int)
        moved_tokens: List[str] = []

        for d in drones:
            if d.finished:
                continue

            # drone is mid-transit toward a restricted zone
            if d.traveling_to is not None:
                d.travel_time_left -= 1
                if d.travel_time_left <= 0:
                    d.current_zone = d.traveling_to
                    d.traveling_to = None
                    if d.current_zone == end:
                        d.finished = True
                    else:
                        moved_tokens.append(f"D{d.drone_id}-{d.current_zone}")
                continue

            if d.current_zone == end:
                d.finished = True
                continue

            idx = path_index[d.drone_id]
            if idx + 1 >= len(base_path):
                d.finished = True
                continue

            nxt = base_path[idx + 1]
            conn = graph.get_connection(d.current_zone, nxt)
            conn_key = conn.key()

            # check connection capacity
            if link_usage[conn_key] >= conn.max_link_capacity:
                continue

            # check zone capacity (start and end are unlimited)
            nxt_zone = graph.zones[nxt]
            if nxt not in {start, end}:
                if zone_occupancy[nxt] >= nxt_zone.max_drones:
                    continue

            # move approved
            link_usage[conn_key] += 1
            zone_occupancy[d.current_zone] -= 1

            if nxt_zone.zone_type == "restricted":
                # restricted zone takes 2 turns — drone goes into transit
                d.traveling_to = nxt
                d.travel_time_left = 2
                path_index[d.drone_id] += 1
                moved_tokens.append(f"D{d.drone_id}-{d.current_zone}-{nxt}")
            else:
                d.current_zone = nxt
                path_index[d.drone_id] += 1
                zone_occupancy[nxt] += 1
                moved_tokens.append(f"D{d.drone_id}-{nxt}")
                if d.current_zone == end:
                    d.finished = True

        if not moved_tokens:
            continue

        # build log line
        line = " ".join(moved_tokens)
        if show_capacity:
            zone_parts = [
                f"{n}:{zone_occupancy[n]}/{z.max_drones}"
                for n, z in graph.zones.items()
            ]
            conn_parts = [
                f"{c.a}-{c.b}:{link_usage[k]}/{c.max_link_capacity}"
                for k, c in graph.connections.items()
            ]
            line += (
                " | ZONES " + ", ".join(zone_parts)
                + " | LINKS " + ", ".join(conn_parts)
            )
        output_lines.append(line)

        # visual display
        if visual:
            render_turn(
                turn=turn,
                graph=graph,
                drones=drones,
                moved_tokens=moved_tokens,
                zone_occupancy=zone_occupancy,
                link_usage=link_usage,
            )

    if visual:
        render_summary(turn, nb_drones)

    return output_lines
