"""Pathfinding module for the Fly-in drone simulation.

Implements a highly optimized, congestion-aware Dijkstra algorithm to find
efficient paths that minimize total turns and avoid bottlenecks.
"""

from __future__ import annotations
import heapq
from typing import Dict, List, Optional, Tuple

from models import Graph


def shortest_path(
    graph: Graph,
    start: str,
    end: str,
    zone_occupancy: Optional[Dict[str, int]] = None,
    connection_usage: Optional[Dict[Tuple[str, str], int]] = None,
) -> Optional[List[str]]:
    """Compute the shortest path from start to end zone using Dijkstra.

    Args:
        graph: The graph of zones and connections.
        start: Name of the starting zone.
        end: Name of the destination zone.
        zone_occupancy: Optional mapping of zone name to current occupancy.
        connection_usage: Optional mapping of connection keys to current usage.

    Returns:
        A list of zone names representing the path from start to end,
        or None if no path exists.
    """
    if start not in graph.zones or end not in graph.zones:
        return None

    # Priority queue entries are (total_cost, tie_break_index, current_zone)
    pq: List[Tuple[float, int, str]] = []
    dist: Dict[str, float] = {z: float("inf") for z in graph.zones}
    prev: Dict[str, Optional[str]] = {z: None for z in graph.zones}

    dist[start] = 0.0
    heapq.heappush(pq, (0.0, 0, start))
    counter = 0

    while pq:
        d, _, u = heapq.heappop(pq)

        if d > dist[u]:
            continue

        if u == end:
            break

        for v in graph.adjacency[u]:
            zone_v = graph.zones[v]
            if zone_v.is_blocked():
                continue

            # Calculate edge cost
            step_cost = float(zone_v.move_cost())

            # Add congestion penalties if maps are provided
            if (
                zone_occupancy is not None
                and v != graph.start_zone
                and v != graph.end_zone
            ):
                occ = zone_occupancy.get(v, 0)
                limit = zone_v.max_drones
                if occ >= limit:
                    step_cost += 100.0 + 50.0 * (occ - limit + 1)
                else:
                    step_cost += 2.0 * occ

            if connection_usage is not None:
                conn = graph.get_connection(u, v)
                conn_key = conn.key()
                usage = connection_usage.get(conn_key, 0)
                limit = conn.max_link_capacity
                if usage >= limit:
                    step_cost += 50.0 + 20.0 * (usage - limit + 1)
                else:
                    step_cost += 1.0 * usage

            # Prefer priority zones
            if zone_v.zone_type.value == "priority":
                step_cost -= 0.1

            nd = d + step_cost
            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                counter += 1
                heapq.heappush(pq, (nd, counter, v))

    if dist[end] == float("inf"):
        return None

    # Reconstruct the path
    path: List[str] = []
    curr: Optional[str] = end
    while curr is not None:
        path.append(curr)
        curr = prev[curr]
    path.reverse()
    return path
