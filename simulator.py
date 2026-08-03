"""Simulation engine for the Fly-in drone routing system.

Adheres to PEP 257 docstrings, type hints, and strict object-oriented design.
Tracks zone occupancy, connection capacity, restricted zones, and runs
congestion-aware pathfinding.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from models import Graph, Drone
from pathfinder import shortest_path


def run_simulation(
    graph: Graph, nb_drones: int, show_capacity: bool = False
) -> List[str]:
    """Run the step-by-step drone simulation from start_hub to end_hub.

    Args:
        graph: The fully parsed simulation graph.
        nb_drones: Total number of drones to route.
        show_capacity: If True, prints additional capacity context.

    Returns:
        A list of formatted output strings, one per simulation turn.

    Raises:
        ValueError: If no valid path exists between start and end hubs.
    """
    start = graph.start_zone
    end = graph.end_zone
    if start is None or end is None:
        raise ValueError("Graph must have a start_hub and an end_hub.")

    # Validate that at least one path exists initially
    initial_path = shortest_path(graph, start, end)
    if initial_path is None:
        raise ValueError("No valid path exists from start_hub to end_hub")

    # Create drones starting at the start_hub
    drones: List[Drone] = [
        Drone(drone_id=i + 1, current_zone=start) for i in range(nb_drones)
    ]

    output_lines: List[str] = []

    # Track how long each drone has been waiting to move
    wait_time: Dict[int, int] = {d.drone_id: 0 for d in drones}

    while not all(d.finished for d in drones):
        moved_tokens: List[str] = []
        arrived_this_turn: Set[int] = set()

        # Step 1: Advance any drones currently in transit (restricted zones)
        for d in drones:
            if d.traveling_to is not None:
                d.travel_time_left -= 1
                if d.travel_time_left <= 0:
                    # Drone successfully arrives at the destination zone
                    dest = d.traveling_to
                    d.current_zone = dest
                    d.traveling_to = None
                    arrived_this_turn.add(d.drone_id)

                    if dest == end:
                        d.finished = True
                    else:
                        moved_tokens.append(f"D{d.drone_id}-{dest}")

        # Step 2: Dynamically schedule moves for eligible drones
        drones_moved_this_turn: Set[int] = set()
        links_used_this_turn: Dict[Tuple[str, str], int] = defaultdict(int)

        # We repeatedly evaluate moves in multiple passes to resolve chains
        while True:
            # Build current occupancies and connection usage for this pass
            zone_occupancy: Dict[str, int] = defaultdict(int)
            connection_usage: Dict[Tuple[str, str], int] = defaultdict(int)

            # 1. Account for currently stationary active drones
            for d in drones:
                if not d.finished and d.traveling_to is None:
                    zone_occupancy[d.current_zone] += 1

            # 2. Account for drones still in transit across this turn
            for d in drones:
                if d.traveling_to is not None:
                    # In transit, occupies the link
                    conn = graph.get_connection(
                        d.current_zone, d.traveling_to
                    )
                    connection_usage[conn.key()] += 1
                    # Also reserve space in target zone
                    zone_occupancy[d.traveling_to] += 1

            # 3. Account for connections already traversed on this turn
            for key, val in links_used_this_turn.items():
                connection_usage[key] += val

            # Find candidates that haven't moved yet on this turn
            candidates = [
                d for d in drones
                if not d.finished
                and d.traveling_to is None
                and d.drone_id not in drones_moved_this_turn
                and d.drone_id not in arrived_this_turn
                and d.current_zone != end
            ]

            if not candidates:
                break

            # Sort candidates to prioritize those with shorter path distance,
            # and breaking ties by wait time and then drone ID.
            def candidate_sort_key(d: Drone) -> Tuple[int, int, int]:
                p = shortest_path(
                    graph,
                    d.current_zone,
                    end,
                    zone_occupancy,
                    connection_usage
                )
                p_len = len(p) if p is not None else 999999
                # Prioritize shorter path, longer wait, then lower drone ID
                return (p_len, -wait_time[d.drone_id], d.drone_id)

            candidates.sort(key=candidate_sort_key)

            move_made = False
            for d in candidates:
                # Find the congestion-aware best path for this drone
                p = shortest_path(
                    graph,
                    d.current_zone,
                    end,
                    zone_occupancy,
                    connection_usage
                )
                if not p or len(p) < 2:
                    continue

                nxt = p[1]
                conn = graph.get_connection(d.current_zone, nxt)
                conn_key = conn.key()

                # Check connection capacity
                if connection_usage[conn_key] >= conn.max_link_capacity:
                    continue

                # Check destination zone capacity
                nxt_zone = graph.zones[nxt]
                if nxt != start and nxt != end:
                    if zone_occupancy[nxt] >= nxt_zone.max_drones:
                        continue

                # Move is valid! Schedule it.
                drones_moved_this_turn.add(d.drone_id)
                links_used_this_turn[conn_key] += 1
                wait_time[d.drone_id] = 0  # Reset waiting count

                if nxt_zone.zone_type.value == "restricted":
                    # Moves onto connection towards restricted zone
                    d.traveling_to = nxt
                    d.travel_time_left = 1  # Will arrive next turn
                    moved_tokens.append(
                        f"D{d.drone_id}-{d.current_zone}-{nxt}"
                    )
                else:
                    # Normal or priority zone, enters immediately
                    d.current_zone = nxt
                    if nxt == end:
                        d.finished = True
                    moved_tokens.append(f"D{d.drone_id}-{nxt}")

                move_made = True
                break  # Recalculate occupancy/paths in a new pass

            if not move_made:
                break

        # Increment wait time for any active stationary drone that did not move
        for d in drones:
            if not d.finished and d.traveling_to is None:
                if (
                    d.drone_id not in drones_moved_this_turn
                    and d.drone_id not in arrived_this_turn
                ):
                    wait_time[d.drone_id] += 1

        # Format output if at least one movement/arrival occurred
        if moved_tokens:
            # Sort tokens by drone ID for deterministic output
            def get_token_id(t: str) -> int:
                # Token format is D<ID>-<rest>
                return int(t.split("-", 1)[0][1:])

            moved_tokens.sort(key=get_token_id)
            line = " ".join(moved_tokens)

            if show_capacity:
                # Include capacity-info helper context
                # Re-calculate final zone occupancy at end of turn
                final_zo: Dict[str, int] = defaultdict(int)
                for d in drones:
                    if not d.finished and d.traveling_to is None:
                        final_zo[d.current_zone] += 1

                zone_parts = []
                for z_name, z in graph.zones.items():
                    used = final_zo[z_name]
                    zone_parts.append(f"{z_name}:{used}/{z.max_drones}")

                line += " | ZONES " + ", ".join(zone_parts)
            output_lines.append(line)

    return output_lines
