"""Connection class representing a link in the simulation network.

Includes PEP 257 docstrings and type safety.
"""

from __future__ import annotations
from typing import Tuple


class Connection:
    """Represents a bidirectional edge/connection between two zones.

    Attributes:
        a: Name of the first zone.
        b: Name of the second zone.
        max_link_capacity: Maximum number of drones allowed to
                           traverse simultaneously.
    """

    def __init__(self, a: str, b: str, max_link_capacity: int = 1) -> None:
        """Initialize the connection.

        Args:
            a: Zone name of first endpoint.
            b: Zone name of second endpoint.
            max_link_capacity: Link capacity limit.
        """
        self.a: str = a
        self.b: str = b
        self.max_link_capacity: int = max_link_capacity

    def key(self) -> Tuple[str, str]:
        """Normalize the link direction for sorted key tracking.

        Returns:
            A sorted tuple of the two zone names.
        """
        first, second = sorted((self.a, self.b))
        return (first, second)

    def __repr__(self) -> str:
        """Return the representation of the connection."""
        return (
            f"Connection(a='{self.a}', b='{self.b}', "
            f"max_link_capacity={self.max_link_capacity})"
        )
