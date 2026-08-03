from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from models.zone import Zone
from models.connection import Connection


@dataclass
class Graph:
    """Adjacency-list graph holding zones and connections."""

    zones: Dict[str, Zone] = field(default_factory=dict)
    adjacency: Dict[str, Set[str]] = field(default_factory=dict)
    connections: Dict[Tuple[str, str], Connection] = field(default_factory=dict)
    start_zone: Optional[str] = None
    end_zone: Optional[str] = None

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the graph and register its role."""
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
        """Add a bidirectional connection between two zones."""
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

    def get_neighbors(self, zone_name: str) -> List[Zone]:
        """Return all Zone objects directly connected to zone_name."""
        return [self.zones[n] for n in self.adjacency[zone_name]]

    def get_connection(self, z1: str, z2: str) -> Connection:
        """Return the Connection between z1 and z2."""
        key = tuple(sorted((z1, z2)))
        return self.connections[key]  # type: ignore
