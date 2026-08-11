"""Core data classes used by the drone simulation."""

from dataclasses import dataclass, field
from enum import Enum


class ZoneType(Enum):
    """Represent the four possible zone types."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


@dataclass
class Zone:
    """Store the data and occupancy limit for one zone."""

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1
    drones: int = field(default=0, init=False)

    def is_blocked(self) -> bool:
        """Return True when drones cannot enter this zone."""
        return self.zone_type == ZoneType.BLOCKED

    def entry_cost(self) -> int:
        """Return the number of turns needed to enter this zone."""
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    def has_space(self) -> bool:
        """Return True when another drone can occupy this zone."""
        return self.drones < self.max_drones


@dataclass(frozen=True)
class Connection:
    """Store an undirected connection between two zones."""

    zone_a: str
    zone_b: str
    max_link_capacity: int = 1


@dataclass
class Drone:
    """Store one drone's current route and movement state."""

    drone_id: int
    current_position: str
    path: list[str]
    status: str = "waiting"
    path_index: int = 0
    remaining_turns: int = 0
    destination: str | None = None

    def is_finished(self) -> bool:
        """Return True when this drone has reached the end."""
        return self.status == "finished"

    def next_zone(self) -> str | None:
        """Return the next zone in the drone's path."""
        next_index = self.path_index + 1
        if next_index >= len(self.path):
            return None
        return self.path[next_index]
