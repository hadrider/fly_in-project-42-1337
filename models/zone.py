from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

ZONE_MOVE_COST = {
    "normal": 1,
    "priority": 1,
    "restricted": 2,
    "blocked": 999999,
}

ANSI_COLORS: dict[str, str] = {
    "red":     "\033[91m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
    "gray":    "\033[90m",
    "reset":   "\033[0m",
}


def colorize(text: str, color: Optional[str]) -> str:
    """Wrap text in ANSI color codes if color is recognized."""
    if color and color.lower() in ANSI_COLORS:
        return ANSI_COLORS[color.lower()] + text + ANSI_COLORS["reset"]
    return text


@dataclass
class Zone:
    """Represents a node in the drone network graph."""

    name: str
    role: str
    zone_type: str = "normal"
    max_drones: int = 1
    color: Optional[str] = None
    current_drones: int = field(default=0, repr=False)

    def move_cost(self) -> int:
        """Return the turn cost to enter this zone."""
        return ZONE_MOVE_COST.get(self.zone_type, 1)

    def is_blocked(self) -> bool:
        """Return True if drones cannot enter this zone."""
        return self.zone_type == "blocked"

    def display_name(self) -> str:
        """Return colorized zone name for terminal output."""
        return colorize(self.name, self.color)
