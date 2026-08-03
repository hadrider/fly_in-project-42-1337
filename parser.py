from __future__ import annotations
from typing import Dict, Tuple
from models import Graph, Zone, Connection


def _parse_kv_items(part: str) -> Dict[str, str]:
    """
    Parse a metadata string like 'zone=restricted color=red max_drones=2'
    into a dict: {'zone': 'restricted', 'color': 'red', 'max_drones': '2'}.
    Brackets are stripped before parsing.
    """
    out: Dict[str, str] = {}
    part = part.replace("[", "").replace("]", "")
    for token in part.strip().split():
        if "=" not in token:
            continue
        k, v = token.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def parse_file(path: str) -> Tuple[Graph, int]:
    """
    Parse a map file and return a fully built Graph and drone count.

    Raises ValueError with line number on any format error.
    """
    graph = Graph()
    nb_drones = None

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line_no, raw in enumerate(lines, start=1):
        line = raw.strip()

        # skip comments and blank lines
        if not line or line.startswith("#"):
            continue

        # nb_drones line
        if line.startswith("nb_drones:"):
            if nb_drones is not None:
                raise ValueError(f"Line {line_no}: duplicate nb_drones")
            right = line.split(":", 1)[1].strip()
            if not right.isdigit() or int(right) <= 0:
                raise ValueError(f"Line {line_no}: nb_drones must be a positive integer")
            nb_drones = int(right)
            continue

        # zone lines
        if (line.startswith("start_hub:")
                or line.startswith("end_hub:")
                or line.startswith("hub:")):
            role, rest = line.split(":", 1)
            rest = rest.strip()
            if not rest:
                raise ValueError(f"Line {line_no}: empty zone definition")

            parts = rest.split(maxsplit=1)
            zone_name = parts[0]
            meta_text = parts[1] if len(parts) > 1 else ""
            meta = _parse_kv_items(meta_text)

            zone_type = meta.get("zone", "normal")
            if zone_type not in {"normal", "restricted", "priority", "blocked"}:
                raise ValueError(
                    f"Line {line_no}: invalid zone type '{zone_type}'"
                )

            max_drones_str = meta.get("max_drones", "1")
            if not max_drones_str.isdigit() or int(max_drones_str) <= 0:
                raise ValueError(f"Line {line_no}: max_drones must be a positive integer")
            max_drones = int(max_drones_str)

            color = meta.get("color")

            graph.add_zone(Zone(
                name=zone_name,
                role=role,
                zone_type=zone_type,
                max_drones=max_drones,
                color=color,
            ))
            continue

        # connection lines
        if line.startswith("connection:"):
            rest = line.split(":", 1)[1].strip()
            if not rest:
                raise ValueError(f"Line {line_no}: empty connection definition")

            parts = rest.split(maxsplit=1)
            edge = parts[0]
            meta_text = parts[1] if len(parts) > 1 else ""
            meta = _parse_kv_items(meta_text)

            if "-" not in edge:
                raise ValueError(f"Line {line_no}: connection must use format a-b")
            a, b = edge.split("-", 1)
            a = a.strip()
            b = b.strip()
            if not a or not b:
                raise ValueError(f"Line {line_no}: invalid connection nodes")
            if a == b:
                raise ValueError(f"Line {line_no}: cannot connect a zone to itself")

            cap_str = meta.get("max_link_capacity", "1")
            if not cap_str.isdigit() or int(cap_str) <= 0:
                raise ValueError(
                    f"Line {line_no}: max_link_capacity must be a positive integer"
                )

            graph.add_connection(Connection(
                a=a,
                b=b,
                max_link_capacity=int(cap_str),
            ))
            continue

        raise ValueError(f"Line {line_no}: unknown line format: '{line}'")

    if nb_drones is None:
        raise ValueError("Missing nb_drones declaration")
    if graph.start_zone is None:
        raise ValueError("Missing start_hub declaration")
    if graph.end_zone is None:
        raise ValueError("Missing end_hub declaration")

    return graph, nb_drones
