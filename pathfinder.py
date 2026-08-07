from __future__ import annotations
import heapq
from typing import List, Optional, Tuple
from models import Graph


def k_shortest_paths(
    graph: Graph,
    start: str,
    end: str,
    k: int,
) -> List[List[str]]:
    """
    Return up to k shortest simple paths from start to end.

    Paths are ordered by total move cost, with a small priority-zone tie-break.
    """
    if k <= 0:
        return []

    # heap entries: (cost, penalty, path_as_tuple)
    pq: List[Tuple[float, int, Tuple[str, ...]]] = [(0.0, 0, (start,))]
    out: List[List[str]] = []
    expansions = 0
    max_expansions = 10000

    while pq and len(out) < k and expansions < max_expansions:
        cost, penalty, path_tuple = heapq.heappop(pq)
        expansions += 1
        u = path_tuple[-1]

        if u == end:
            out.append(list(path_tuple))
            continue

        for v in graph.adjacency[u]:
            if v in path_tuple:
                continue
            zone_v = graph.zones[v]
            if zone_v.is_blocked():
                continue
            nd = cost + zone_v.move_cost()
            np = penalty + (0 if zone_v.zone_type == "priority" else 1)
            heapq.heappush(pq, (nd, np, path_tuple + (v,)))

    return out


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
    paths = k_shortest_paths(graph, start, end, 1)
    if not paths:
        return None
    return paths[0]
