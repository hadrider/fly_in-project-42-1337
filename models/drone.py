"""Drone class representing an autonomous flying drone in the simulation.

Following PEP 257 and type annotations for complete type safety.
"""

from __future__ import annotations
from typing import Optional


class Drone:
    """Represents a drone that moves between zones.

    Attributes:
        drone_id: Unique integer identifier for the drone.
        current_zone: Name of the zone where the drone currently resides.
        finished: A boolean flag indicating whether the drone reached
                  the end hub.
        traveling_to: Name of the destination zone if drone is in transit,
                      else None.
        travel_time_left: Number of simulation turns left to arrive.
    """

    def __init__(self, drone_id: int, current_zone: str) -> None:
        """Initialize the drone.

        Args:
            drone_id: The unique drone identifier.
            current_zone: The starting zone of the drone.
        """
        self.drone_id: int = drone_id
        self.current_zone: str = current_zone
        self.finished: bool = False
        self.traveling_to: Optional[str] = None
        self.travel_time_left: int = 0

    def __repr__(self) -> str:
        """Return the string representation of the drone."""
        return (
            f"Drone(drone_id={self.drone_id}, "
            f"current_zone='{self.current_zone}', "
            f"finished={self.finished}, "
            f"traveling_to={self.traveling_to}, "
            f"travel_time_left={self.travel_time_left})"
        )
