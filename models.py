"""Core data classes used by the drone simulation."""

from enum import Enum


class ZoneType(Enum):
    """Represent the four possible zone types."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    """Store the data and occupancy limit for one zone."""

    def __init__(self, name: str, x: int, y: int,
                 zone_type: ZoneType | None = None,
                 color: str | None = None, max_drones: int = 1) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = (zone_type if zone_type is not None
                          else ZoneType.NORMAL)
        self.color = color
        self.max_drones = max_drones
        self.drones = 0

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


class Connection:
    """Store an undirected connection between two zones."""

    def __init__(self, zone_a: str, zone_b: str, max_link_capacity: int = 1
                 ) -> None:
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity


class Drone:
    """Store one drone's current route and movement state."""

    def __init__(self, drone_id: int, current_position: str, path: list[str]
                 ) -> None:
        self.drone_id = drone_id
        self.current_position = current_position
        self.path = path
        self.status = "waiting"
        self.path_index = 0
        self.remaining_turns = 0
        self.destination: str | None = None

    def is_finished(self) -> bool:
        """Return True when this drone has reached the end."""
        return self.status == "finished"

    def next_zone(self) -> str | None:
        """Return the next zone in the drone's path."""
        next_index = self.path_index + 1
        if next_index >= len(self.path):
            return None
        return self.path[next_index]
