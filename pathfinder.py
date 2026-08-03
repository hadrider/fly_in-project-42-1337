from __future__ import annotations
import heapq
from typing import Dict, List, Optional, Tuple
from models import Graph


def shortest_path(graph: Graph, start: str, end: str) -> Optional[List[str]]:
    """
    Dijkstra shortest path from start to end using zone move costs.

    Zone costs:
      normal    -> 1 turn
      priority  -> 1 turn (preferred on tie-break)
      restricted-> 2 turns
      blocked   -> skipped entirely

    Returns list of zone names from start to end, or None if unreachable.
    Complexity: O((V + E) log V)
    """
    dist: Dict[str, float] = {z: float("inf") for z in graph.zones}
    prev: Dict[str, Optional[str]] = {z: None for z in graph.zones}

    # heap entries: (cost, priority_penalty, zone_name)
    # priority zones get penalty=0 so they win tie-breaks
    pq: List[Tuple[float, int, str]] = []
    dist[start] = 0.0
    heapq.heappush(pq, (0.0, 0, start))

    while pq:
        current_dist, _, u = heapq.heappop(pq)
        if current_dist > dist[u]:
            continue
        if u == end:
            break

        for v in graph.adjacency[u]:
            zone_v = graph.zones[v]
            if zone_v.is_blocked():
                continue

            nd = current_dist + zone_v.move_cost()
            penalty = 0 if zone_v.zone_type == "priority" else 1

            if nd < dist[v]:
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, penalty, v))

    if dist[end] == float("inf"):
        return None

    # rebuild path by walking backwards through prev
    path: List[str] = []
    cur: Optional[str] = end
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path
