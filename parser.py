"""Parser module for the Fly-in simulation network.

Includes PEP 257 docstrings, full type safety, and handles all coordinate and
metadata parsing rules.
"""

from __future__ import annotations
from typing import Dict, Tuple

from models import Graph, Zone, Connection


def _parse_metadata(meta_text: str, line_no: int) -> Dict[str, str]:
    """Parse a metadata block enclosed in brackets.

    E.g. '[zone=restricted color=red]'.

    Args:
        meta_text: The string containing the metadata.
        line_no: The current line number for error reporting.

    Returns:
        A dictionary of the key-value metadata.

    Raises:
        ValueError: If the metadata format is invalid.
    """
    meta_text = meta_text.strip()
    if not meta_text:
        return {}

    if not meta_text.startswith("[") or not meta_text.endswith("]"):
        raise ValueError(
            f"Line {line_no}: Metadata block must be "
            f"enclosed in brackets '[...]'."
        )

    content = meta_text[1:-1].strip()
    if not content:
        return {}

    out: Dict[str, str] = {}
    tokens = content.split()
    for token in tokens:
        if "=" not in token:
            raise ValueError(
                f"Line {line_no}: Invalid metadata token '{token}'"
            )
        k, v = token.split("=", 1)
        k = k.strip()
        v = v.strip()
        if not k or not v:
            raise ValueError(
                f"Line {line_no}: Empty key/value in metadata '{token}'"
            )
        out[k] = v
    return out


def parse_file(path: str) -> Tuple[Graph, int]:
    """Parse the Fly-in map file and return the Graph and drone count.

    Args:
        path: Path to the map configuration file.

    Returns:
        A tuple of (Graph object, number of drones).

    Raises:
        ValueError: On any parsing, capacity, or duplicate error.
    """
    graph = Graph()
    nb_drones = None

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line_no, raw in enumerate(lines, start=1):
        line = raw.strip()

        # Strip comments
        if "#" in line:
            line = line.split("#", 1)[0].strip()

        # Ignore empty lines
        if not line:
            continue

        # Enforce that the very first active line is nb_drones
        if nb_drones is None:
            if not line.startswith("nb_drones:"):
                raise ValueError(
                    f"Line {line_no}: First active line "
                    f"must define 'nb_drones'"
                )
            right = line.split(":", 1)[1].strip()
            if not right.isdigit() or int(right) <= 0:
                raise ValueError(
                    f"Line {line_no}: 'nb_drones' must be a positive integer"
                )
            nb_drones = int(right)
            continue

        # If nb_drones is already defined but we see another nb_drones line
        if line.startswith("nb_drones:"):
            raise ValueError(
                f"Line {line_no}: Duplicate 'nb_drones' definition"
            )

        # Parse zone definitions: start_hub:, end_hub:, hub:
        if (
            line.startswith("start_hub:")
            or line.startswith("end_hub:")
            or line.startswith("hub:")
        ):
            role, rest = line.split(":", 1)
            role = role.strip()
            rest = rest.strip()
            if not rest:
                raise ValueError(f"Line {line_no}: Empty zone definition")

            # Split metadata block if present
            meta_dict: Dict[str, str] = {}
            if "[" in rest:
                start_bracket = rest.index("[")
                meta_part = rest[start_bracket:].strip()
                main_part = rest[:start_bracket].strip()
                meta_dict = _parse_metadata(meta_part, line_no)
            else:
                main_part = rest

            parts = main_part.split()
            if len(parts) != 3:
                raise ValueError(
                    f"Line {line_no}: Zone must define exactly name, "
                    f"x-coordinate, and y-coordinate"
                )

            zone_name, x_str, y_str = parts[0], parts[1], parts[2]

            # Validate name has no dashes or spaces
            if "-" in zone_name:
                raise ValueError(
                    f"Line {line_no}: Zone name '{zone_name}' "
                    f"cannot contain dashes"
                )

            # Validate coordinates are valid integers
            try:
                x = int(x_str)
            except ValueError:
                raise ValueError(
                    f"Line {line_no}: X-coordinate '{x_str}' "
                    f"must be an integer"
                )
            try:
                y = int(y_str)
            except ValueError:
                raise ValueError(
                    f"Line {line_no}: Y-coordinate '{y_str}' "
                    f"must be an integer"
                )

            # Parse zone type
            zone_type = meta_dict.get("zone", "normal")
            if zone_type not in {
                "normal", "blocked", "restricted", "priority"
            }:
                raise ValueError(
                    f"Line {line_no}: Invalid zone type '{zone_type}'"
                )

            # Parse and validate capacity max_drones
            if role in {"start_hub", "end_hub"}:
                # max_drones metadata is ignored for start_hub/end_hub
                max_drones = 999999
            else:
                max_drones_str = meta_dict.get("max_drones", "1")
                try:
                    max_drones = int(max_drones_str)
                    if max_drones <= 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError(
                        f"Line {line_no}: max_drones capacity "
                        f"'{max_drones_str}' must be a positive integer"
                    )

            color = meta_dict.get("color")

            zone = Zone(
                name=zone_name,
                role=role,
                x=x,
                y=y,
                zone_type=zone_type,
                color=color,
                max_drones=max_drones
            )

            try:
                graph.add_zone(zone)
            except ValueError as e:
                raise ValueError(f"Line {line_no}: {e}")
            continue

        # Parse connections
        if line.startswith("connection:"):
            rest = line.split(":", 1)[1].strip()
            if not rest:
                raise ValueError(
                    f"Line {line_no}: Empty connection"
                )

            meta_dict = {}
            if "[" in rest:
                start_bracket = rest.index("[")
                meta_part = rest[start_bracket:].strip()
                main_part = rest[:start_bracket].strip()
                meta_dict = _parse_metadata(meta_part, line_no)
            else:
                main_part = rest

            edge = main_part.strip()
            if "-" not in edge:
                raise ValueError(
                    f"Line {line_no}: Connection must be in "
                    f"format <zone1>-<zone2>"
                )

            parts = edge.split("-")
            if len(parts) != 2:
                raise ValueError(
                    f"Line {line_no}: Connection format must "
                    f"be exactly <zone1>-<zone2>"
                )

            a, b = parts[0].strip(), parts[1].strip()
            if not a or not b:
                raise ValueError(
                    f"Line {line_no}: Connection endpoints cannot be empty"
                )

            max_link_capacity_str = meta_dict.get("max_link_capacity", "1")
            try:
                max_link_capacity = int(max_link_capacity_str)
                if max_link_capacity <= 0:
                    raise ValueError()
            except ValueError:
                raise ValueError(
                    f"Line {line_no}: max_link_capacity "
                    f"'{max_link_capacity_str}' must be a positive integer"
                )

            try:
                conn = Connection(
                    a=a, b=b, max_link_capacity=max_link_capacity
                )
                graph.add_connection(conn)
            except ValueError as e:
                raise ValueError(f"Line {line_no}: {e}")
            continue

        raise ValueError(f"Line {line_no}: Unknown line format '{line}'")

    # Verify we got start and end zones
    if nb_drones is None:
        raise ValueError("Parsing Error: Missing 'nb_drones'")
    if graph.start_zone is None:
        raise ValueError("Parsing Error: Missing 'start_hub' zone")
    if graph.end_zone is None:
        raise ValueError("Parsing Error: Missing 'end_hub' zone")

    return graph, nb_drones
