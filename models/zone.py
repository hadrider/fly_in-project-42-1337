"""Zone class representing a geographic location in the simulation network.

Includes PEP 257 docstrings and type safety.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional


class ZoneType(Enum):
    """Enumeration of possible zone types."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """Represents a spatial zone in the simulation graph.

    Attributes:
        name: Unique name of the zone.
        role: Special function of the zone ('start_hub', 'end_hub', or 'hub').
        x: X-coordinate of the zone.
        y: Y-coordinate of the zone.
        zone_type: Mode of operation/movement cost category.
        color: Optional string color representation.
        max_drones: Maximum number of drones allowed simultaneously.
    """

    def __init__(
        self,
        name: str,
        role: str,
        x: int,
        y: int,
        zone_type: str = "normal",
        color: Optional[str] = None,
        max_drones: int = 1,
    ) -> None:
        """Initialize the Zone.

        Args:
            name: Name of the zone.
            role: Role of the zone (e.g. start_hub, end_hub, hub).
            x: Integer x-coordinate.
            y: Integer y-coordinate.
            zone_type: Zone type string ('normal', 'blocked' etc).
            color: Optional color name.
            max_drones: Maximum drone limit.
        """
        self.name: str = name
        self.role: str = role
        self.x: int = x
        self.y: int = y

        try:
            self.zone_type: ZoneType = ZoneType(zone_type)
        except ValueError:
            self.zone_type = ZoneType.NORMAL

        self.color: Optional[str] = color
        self.max_drones: int = max_drones

    def move_cost(self) -> int:
        """Get the cost in turns required to enter this zone.

        Returns:
            The turn cost. Restricted zones cost 2, normal/priority cost 1,
            blocked zones are inaccessible.
        """
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        if self.zone_type == ZoneType.BLOCKED:
            return 999999
        return 1

    def is_blocked(self) -> bool:
        """Check if this zone is blocked.

        Returns:
            True if the zone type is blocked, False otherwise.
        """
        return self.zone_type == ZoneType.BLOCKED

    def __repr__(self) -> str:
        """Return the string representation of the zone."""
        return (
            f"Zone(name='{self.name}', role='{self.role}', x={self.x}, "
            f"y={self.y}, zone_type={self.zone_type}, color={self.color}, "
            f"max_drones={self.max_drones})"
        )
