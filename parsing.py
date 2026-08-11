"""Parser for the custom Fly-in map format."""

import re
from pathlib import Path

from models import Connection, Zone, ZoneType


class MapParseError(ValueError):
    """Represent an invalid Fly-in map file."""


class DroneMap:
    """Store zones and connections parsed from a map file."""

    def __init__(self) -> None:
        """Create an empty drone map."""
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start_name: str | None = None
        self.end_name: str | None = None
        self.nb_drones: int = 0

    @classmethod
    def from_file(cls, filename: str) -> "DroneMap":
        """Read a map file and return a validated DroneMap."""
        drone_map = cls()
        lines = Path(filename).read_text(encoding="utf-8").splitlines()
        drone_map._parse_lines(lines)
        drone_map._validate_map()
        return drone_map

    def _parse_lines(self, lines: list[str]) -> None:
        """Parse every non-comment line in the input."""
        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            self._parse_line(line, line_number)

    def _parse_line(self, line: str, line_number: int) -> None:
        """Parse one line according to its record type."""
        if line.startswith("nb_drones:"):
            self._parse_drone_count(line, line_number)
        elif line.startswith("start_hub:"):
            self._parse_zone(line, line_number, True, False)
        elif line.startswith("end_hub:"):
            self._parse_zone(line, line_number, False, True)
        elif line.startswith("hub:"):
            self._parse_zone(line, line_number, False, False)
        elif line.startswith("connection:"):
            self._parse_connection(line, line_number)
        else:
            self._error(line_number, "unknown line type")

    def _parse_drone_count(self, line: str, number: int) -> None:
        """Parse and validate the number of drones."""
        value = line.split(":", 1)[1].strip()
        try:
            count = int(value)
        except ValueError as exc:
            message = f"Line {number}: nb_drones must be an integer"
            raise MapParseError(message) from exc
        if count <= 0:
            self._error(number, "nb_drones must be greater than zero")
        self.nb_drones = count

    def _parse_zone(
        self, line: str, number: int, is_start: bool, is_end: bool
    ) -> None:
        """Parse a start, end, or normal hub declaration."""
        prefix = "start_hub:" if is_start else "end_hub:" if is_end else "hub:"
        value = line[len(prefix):].strip()
        match = re.match(r"^(\S+)\s+(-?\d+)\s+(-?\d+)(?:\s+\[(.*)\])?$", value)
        if match is None:
            self._error(number, "invalid zone declaration")
        assert match is not None
        name, x_text, y_text, metadata = match.groups()
        assert name is not None and x_text is not None and y_text is not None
        self._validate_zone_name(name, number)
        if name in self.zones:
            self._error(number, f"duplicate zone '{name}'")
        zone_type, color, max_drones = self._parse_metadata(metadata, number)
        zone = Zone(
            name, int(x_text), int(y_text), zone_type, color, max_drones
        )
        self.zones[name] = zone
        self._set_start_or_end(name, is_start, is_end, number)

    def _parse_metadata(
        self, metadata: str | None, number: int
    ) -> tuple[ZoneType, str | None, int]:
        """Parse zone metadata and return validated values."""
        zone_type = ZoneType.NORMAL
        color: str | None = None
        max_drones = 1
        if metadata is None:
            return zone_type, color, max_drones
        for item in metadata.split():
            key, value = self._split_metadata(item, number)
            if key == "zone":
                zone_type = self._parse_zone_type(value, number)
            elif key == "color":
                color = value
            elif key == "max_drones":
                max_drones = self._parse_positive_int(
                    value, "max_drones", number
                )
            else:
                self._error(number, f"unknown zone metadata '{key}'")
        return zone_type, color, max_drones

    def _parse_connection(self, line: str, number: int) -> None:
        """Parse a connection and reject duplicates or unknown zones."""
        value = line[len("connection:"):].strip()

        metadata = None
        if "[" in value:
            if not value.endswith("]"):
                self._error(number, "invalid connection metadata")
            connection_text, metadata_text = value.split("[", 1)
            value = connection_text.strip()
            metadata = metadata_text[:-1].strip()

        parts = value.split("-")
        if len(parts) != 2:
            self._error(number, "invalid connection declaration")

        zone_a = parts[0].strip()
        zone_b = parts[1].strip()

        self._validate_connection_zones(zone_a, zone_b, number)

        capacity = self._parse_link_metadata(metadata, number)

        if self._is_duplicate_connection(zone_a, zone_b):
            self._error(
                number,
                f"duplicate connection '{zone_a}-{zone_b}'"
            )

        self.connections.append(
            Connection(zone_a, zone_b, capacity)
        )

    def _parse_link_metadata(self, metadata: str | None, number: int) -> int:
        """Parse the optional connection capacity."""
        if metadata is None:
            return 1
        items = metadata.split()
        if len(items) != 1:
            self._error(number, "invalid connection metadata")
        key, value = self._split_metadata(items[0], number)
        if key != "max_link_capacity":
            self._error(number, f"unknown connection metadata '{key}'")
        return self._parse_positive_int(value, "max_link_capacity", number)

    def _split_metadata(self, item: str, number: int) -> tuple[str, str]:
        """Split one metadata item into a key and value."""
        parts = item.split("=", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            self._error(number, f"invalid metadata '{item}'")
        return parts[0], parts[1]

    def _parse_zone_type(self, value: str, number: int) -> ZoneType:
        """Convert a zone type string into a ZoneType enum."""
        try:
            return ZoneType(value)
        except ValueError as exc:
            self._error(number, f"unknown zone type '{value}'")
            raise exc

    def _parse_positive_int(self, value: str, name: str, number: int) -> int:
        """Parse an integer that must be greater than zero."""
        try:
            result = int(value)
        except ValueError as exc:
            message = f"Line {number}: {name} must be an integer"
            raise MapParseError(message) from exc
        if result <= 0:
            self._error(number, f"{name} must be greater than zero")
        return result

    def _validate_zone_name(self, name: str, number: int) -> None:
        """Reject names that would make connection parsing ambiguous."""
        if "-" in name or not name:
            self._error(number, "zone names cannot contain '-'")

    def _validate_connection_zones(
        self, zone_a: str, zone_b: str, number: int
    ) -> None:
        """Check that a connection refers to two existing zones."""
        if zone_a not in self.zones:
            self._error(number, f"unknown zone '{zone_a}'")
        if zone_b not in self.zones:
            self._error(number, f"unknown zone '{zone_b}'")
        if zone_a == zone_b:
            self._error(number, "a zone cannot connect to itself")

    def _is_duplicate_connection(self, zone_a: str, zone_b: str) -> bool:
        """Return True when this connection already exists in either direction.
        """
        for connection in self.connections:
            same_direction = (
                connection.zone_a == zone_a and connection.zone_b == zone_b
            )
            reverse_direction = (
                connection.zone_a == zone_b and connection.zone_b == zone_a
            )
            if same_direction or reverse_direction:
                return True
        return False

    def _set_start_or_end(
        self, name: str, is_start: bool, is_end: bool, number: int
    ) -> None:
        """Store start and end names while enforcing uniqueness."""
        if is_start:
            if self.start_name is not None:
                self._error(number, "multiple start_hub declarations")
            self.start_name = name
        if is_end:
            if self.end_name is not None:
                self._error(number, "multiple end_hub declarations")
            self.end_name = name

    def _validate_map(self) -> None:
        """Check required global map fields after parsing."""
        if self.nb_drones <= 0:
            raise MapParseError("Missing or invalid nb_drones")
        if self.start_name is None:
            raise MapParseError("Missing start_hub")
        if self.end_name is None:
            raise MapParseError("Missing end_hub")

    @staticmethod
    def _error(number: int, message: str) -> None:
        """Raise a parsing error containing the source line number."""
        raise MapParseError(f"Line {number}: {message}")
