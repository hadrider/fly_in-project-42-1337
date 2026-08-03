from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class Drone:
    """Represents a single drone in the simulation."""

    drone_id: int
    current_zone: str
    finished: bool = False
    traveling_to: Optional[str] = None
    travel_time_left: int = 0

    def label(self) -> str:
        """Return the drone's display label e.g. D1, D2."""
        return f"D{self.drone_id}"
