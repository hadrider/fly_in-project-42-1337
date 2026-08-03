"""Graph class representing the network of zones and connections.

Includes PEP 257 docstrings and type safety.
"""

from __future__ import annotations
from typing import Dict, Optional, Set, Tuple
from .zone import Zone
from .connection import Connection


class Graph:
    """Represents a spatial network of zones connected via links.

    Attributes:
        zones: Dictionary mapping zone name to Zone object.
        adjacency: Dictionary mapping zone name to set of adjacent zone names.
        connections: Dictionary mapping normalized connection keys
                     to Connection objects.
        start_zone: Name of the start hub, or None if not set.
        end_zone: Name of the end hub, or None if not set.
    """

    def __init__(self) -> None:
        """Initialize the Graph."""
        self.zones: Dict[str, Zone] = {}
        self.adjacency: Dict[str, Set[str]] = {}
        self.connections: Dict[Tuple[str, str], Connection] = {}
        self.start_zone: Optional[str] = None
        self.end_zone: Optional[str] = None

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the graph.

        Args:
            zone: The zone object to add.

        Raises:
            ValueError: If a zone with the same name already exists,
                        or if multiple start/end zones are defined.
        """
        if zone.name in self.zones:
            raise ValueError(f"Duplicate zone name: {zone.name}")
        self.zones[zone.name] = zone
        self.adjacency.setdefault(zone.name, set())

        if zone.role == "start_hub":
            if self.start_zone is not None:
                raise ValueError("Multiple start_hub definitions")
            self.start_zone = zone.name
        elif zone.role == "end_hub":
            if self.end_zone is not None:
                raise ValueError("Multiple end_hub definitions")
            self.end_zone = zone.name

    def add_connection(self, conn: Connection) -> None:
        """Add a connection to the graph.

        Args:
            conn: The connection object to add.

        Raises:
            ValueError: If any endpoint zone of the connection is missing,
                        or if a connection already exists.
        """
        if conn.a not in self.zones or conn.b not in self.zones:
            raise ValueError(
                f"Invalid connection: {conn.a}-{conn.b} (zone missing)"
            )
        key = conn.key()
        if key in self.connections:
            raise ValueError(f"Duplicate connection: {conn.a}-{conn.b}")
        self.connections[key] = conn
        self.adjacency[conn.a].add(conn.b)
        self.adjacency[conn.b].add(conn.a)

    def get_connection(self, z1: str, z2: str) -> Connection:
        """Retrieve the Connection object between two zones.

        Args:
            z1: Name of the first zone.
            z2: Name of the second zone.

        Returns:
            The connection object.
        """
        key = tuple(sorted((z1, z2)))
        assert len(key) == 2
        return self.connections[(key[0], key[1])]

    def __repr__(self) -> str:
        """Return the string representation of the graph."""
        return (
            f"Graph(zones={list(self.zones.keys())}, "
            f"start_zone={self.start_zone}, end_zone={self.end_zone})"
        )
