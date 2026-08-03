from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Connection:
    """Represents a bidirectional edge between two zones."""

    a: str
    b: str
    max_link_capacity: int = 1

    def key(self) -> Tuple[str, str]:
        """Return a normalized key for this connection (order-independent)."""
        return tuple(sorted((self.a, self.b)))  # type: ignore
