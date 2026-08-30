"""Parser for the custom Fly-in map format."""

from models import Connection, Zone, ZoneType
from webcolors import name_to_rgb


class MapParseError(ValueError):
    """Represent an invalid Fly-in map file."""


class DroneMap:
    """Store zones and connections parsed from a map file."""

    def __init__(self) -> None:
        """Create an empty drone map."""
        self.zones: dict = {}
        self.coords: list = []
        self.connections: list = []
        self.start_name = ""
        self.end_name = ""
        self.nb_drones = 0
        self._nb_drones_parsed = False  # false cuz we need to see nb of droens only apperad once

    def from_file(self, filename: str) -> "DroneMap":
        """Read a map file and return a validated DroneMap."""
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        for i, raw in enumerate(lines, 1):
            line = raw.split("#", 1)[0].strip()#strip the line fom comments an take what comes befor the #
            if not line:
                continue#skip empty lines 
            self._parse_line(line, i)

        self._validate_map()
        return self

    def _parse_line(self, line: str, num: int) -> None:
        """Parse one line."""
        if line.startswith("nb_drones:"):
            self._parse_drones(line, num)
        elif line.startswith(("start_hub:", "end_hub:", "hub:")):
            self._parse_zone(line, num)
        elif line.startswith("connection:"):
            self._parse_connection(line, num)
        else:
            self._error(num, "unknown line type")

    def _parse_drones(self, line: str, num: int) -> None:
        """Parse number of drones."""
        if self._nb_drones_parsed:
            self._error(num, "nb_drones can only appear once")
        self._nb_drones_parsed = True

        try:
            count = int(line.split(":", 1)[1].strip())
        except ValueError:
            self._error(num, "nb_drones must be an integer")#parse nub of drones line and take number chack if its a num or no 

        if count <= 0:
            self._error(num, "nb_drones must be greater than zero")
        self.nb_drones = count

    def _parse_zone(self, line: str, num: int) -> None:
        """Parse zone declaration."""
        if not self._nb_drones_parsed:
            self._error(num, "nb_drones must be the first line")

        if line.startswith("start_hub:"):
            prefix, is_start, is_end = "start_hub:", True, False
        elif line.startswith("end_hub:"):
            prefix, is_start, is_end = "end_hub:", False, True
        else:
            prefix, is_start, is_end = "hub:", False, False

        value = line[len(prefix):].strip()
        metadata = None
        if value.endswith("]"):
            bracket = value.rfind("[")
            if bracket == -1:
                self._error(num, "invalid metadata")

            metadata = value[bracket+1:-1].strip()
            value = value[:bracket].strip()
            if not value:
                self._error(num, "missing zone name")

        parts = value.split()
        if len(parts) < 3:
            self._error(num, "invalid zone declaration")
        if len(parts) > 3:
            self._error(num, "invalid structure")

        name, zone_x, zone_y = parts[0], parts[1], parts[2]
        if "-" in name or not name:
            self._error(num, "zone names cannot contain '-'")
        if name in self.zones:
            self._error(num, f"duplicate zone '{name}'")

        try:
            x, y = int(zone_x), int(zone_y)
        except ValueError:
            self._error(num, "invalid coordinates")

        if (x, y) in self.coords:
            self._error(num, "duplicate coordinates")
        self.coords.append((x, y))

        zone_type, color, max_drones = ZoneType.NORMAL, None, 1

        if metadata:
            for item in metadata.split():
                if "=" not in item:
                    self._error(num, f"invalid metadata '{item}'")
                key, val = item.split("=", 1)
                if key == "zone":
                    try:
                        zone_type = ZoneType(val)
                    except ValueError:
                        self._error(num, f"unknown zone type '{val}'")
                    if (prefix == "start_hub:" and
                            zone_type == ZoneType.BLOCKED):
                        self._error(num,
                                    "start_hub zone type can't be blocked")
                elif key == "color":
                    if val != "rainbow":
                        try:
                            name_to_rgb(val)
                        except ValueError:
                            self._error(num,
                                        f"invalid or unkonwn color '{val}'")
                    color = val
                elif key == "max_drones":
                    try:
                        max_drones = int(val)
                    except ValueError:
                        self._error(num, "max_drones must be integer")
                    if max_drones <= 0:
                        self._error(num, "max_drones must be positive")
                else:
                    self._error(num, f"unknown zone metadata '{key}'")

        self.zones[name] = Zone(name, x, y, zone_type, color, max_drones)

        if is_start:
            if self.start_name:
                self._error(num, "multiple start_hub declarations")
            self.start_name = name
        if is_end:
            if self.end_name:
                self._error(num, "multiple end_hub declarations")
            self.end_name = name

    def _parse_connection(self, line: str, num: int) -> None:
        """Parse connection."""
        if not self._nb_drones_parsed:
            self._error(num, "nb_drones must be the first line")

        value = line[len("connection:"):].strip()
        capacity = 1

        metadata = None
        if value.endswith("]"):
            bracket = value.rfind("[")
            if bracket == -1:
                self._error(num, "invalid metadata")
            metadata = value[bracket+1:-1].strip()
            value = value[:bracket].strip()
            if not value:
                self._error(num, "missing connection")

        if " " in value:
            self._error(num, "invalid connection declaration")

        zones = value.split("-")
        if len(zones) != 2:
            self._error(num, "invalid connection declaration")

        zone_a, zone_b = zones[0].strip(), zones[1].strip()
        if not zone_a or not zone_b:
            self._error(num, "invalid connection declaration")

        if metadata:
            if metadata:
                if "=" not in metadata:
                    self._error(num, "invalid connection metadata")
            key, val = metadata.split("=", 1)
            if key != "max_link_capacity":
                self._error(num, f"unknown connection metadata '{key}'")
            try:
                capacity = int(val)
            except ValueError:
                self._error(num, "max_link_capacity must be integer")
            if capacity <= 0:
                self._error(num, "max_link_capacity must be positive")

        if zone_a not in self.zones:
            self._error(num, f"unknown zone '{zone_a}'")
        if zone_b not in self.zones:
            self._error(num, f"unknown zone '{zone_b}'")
        if zone_a == zone_b:
            self._error(num, "zone cannot connect to itself")

        for conn in self.connections:
            if ((conn.zone_a == zone_a and conn.zone_b == zone_b) or
                    (conn.zone_a == zone_b and conn.zone_b == zone_a)):
                self._error(num, f"duplicate connection '{zone_a}-{zone_b}'")

        self.connections.append(Connection(zone_a, zone_b, capacity))

    def _validate_map(self) -> None:
        """Check required fields."""
        if not self._nb_drones_parsed:
            raise MapParseError("Missing nb_drones")
        if not self.start_name:
            raise MapParseError("Missing start_hub")
        if not self.end_name:
            raise MapParseError("Missing end_hub")

    def _error(self, num: int, msg: str) -> None:
        """Raise parse error."""
        raise MapParseError(f"Line {num}: {msg}")
