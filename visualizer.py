"""Simple ANSI terminal visualization for the drone simulation."""

import os
import time

from colors import ANSI_COLORS, RESET
from models import Drone
from parsing import DroneMap


class TerminalVisualizer:
    """Draw the drone map as a simple terminal graph."""

    def __init__(self, drone_map: DroneMap) -> None:
        """Store the map used by the visualizer."""
        self.drone_map = drone_map
        self.width = 7
        self.height = 3

    def show(self, drones: list[Drone], turn: int) -> None:
        """Clear the terminal and draw the current simulation state."""
        self._clear_screen()
        print(f"Turn {turn}")
        print()
        grid = self._create_grid()
        self._draw_connections(grid)
        self._draw_zones(grid, drones)
        self._print_grid(grid)

    def _create_grid(self) -> list[list[str]]:
        """Create an empty character grid."""
        min_x, max_x, min_y, max_y = self._map_bounds()
        width = (max_x - min_x) * self.width + 1
        height = (max_y - min_y) * self.height + 1
        grid: list[list[str]] = []

        for _ in range(height):
            row = [" "] * width
            grid.append(row)

        return grid

    def _map_bounds(self) -> tuple[int, int, int, int]:
        """Return the smallest rectangle containing every zone."""
        zones = list(self.drone_map.zones.values())
        min_x = min(zone.x for zone in zones)
        max_x = max(zone.x for zone in zones)
        min_y = min(zone.y for zone in zones)
        max_y = max(zone.y for zone in zones)
        return min_x, max_x, min_y, max_y

    def _position(self, x: int, y: int) -> tuple[int, int]:
        """Convert map coordinates into terminal coordinates."""
        min_x, _, _, max_y = self._map_bounds()
        column = (x - min_x) * self.width
        row = (max_y - y) * self.height
        return row, column

    def _draw_connections(self, grid: list[list[str]]) -> None:
        """Draw every connection using simple terminal characters."""
        for connection in self.drone_map.connections:
            zone_a = self.drone_map.zones[connection.zone_a]
            zone_b = self.drone_map.zones[connection.zone_b]
            self._draw_connection(grid, zone_a.x, zone_a.y, zone_b.x, zone_b.y)

    def _draw_connection(
        self,
        grid: list[list[str]],
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ) -> None:
        """Draw one horizontal, vertical, or diagonal connection."""
        row1, col1 = self._position(x1, y1)
        row2, col2 = self._position(x2, y2)

        if row1 == row2:
            self._draw_horizontal(grid, row1, col1, col2)
        elif col1 == col2:
            self._draw_vertical(grid, row1, row2, col1)
        else:
            self._draw_diagonal(grid, row1, col1, row2, col2)

    def _draw_horizontal(
        self,
        grid: list[list[str]],
        row: int,
        col1: int,
        col2: int,
    ) -> None:
        """Draw a horizontal connection."""
        start = min(col1, col2)
        end = max(col1, col2)

        for column in range(start + 1, end):
            grid[row][column] = "-"

    def _draw_vertical(
        self,
        grid: list[list[str]],
        row1: int,
        row2: int,
        column: int,
    ) -> None:
        """Draw a vertical connection."""
        start = min(row1, row2)
        end = max(row1, row2)

        for row in range(start + 1, end):
            grid[row][column] = "|"

    def _draw_diagonal(
        self,
        grid: list[list[str]],
        row1: int,
        col1: int,
        row2: int,
        col2: int,
    ) -> None:
        """Draw a diagonal connection with slash characters."""
        step_row = 1 if row2 > row1 else -1
        step_col = 1 if col2 > col1 else -1
        row = row1 + step_row
        column = col1 + step_col

        while row != row2 and column != col2:
            if step_row == step_col:
                grid[row][column] = "\\"
            else:
                grid[row][column] = "/"
            row += step_row
            column += step_col

    def _draw_zones(
        self,
        grid: list[list[str]],
        drones: list[Drone],
    ) -> None:
        """Draw colored dots for zones and drones."""
        for zone in self.drone_map.zones.values():
            row, column = self._position(zone.x, zone.y)
            drone = self._drone_at_zone(zone.name, drones)

            if drone is not None:
                text = f"D{drone.drone_id}"
                self._put_text(grid, row, column, text, zone.color)
            else:
                self._put_text(grid, row, column, ".", zone.color)

    def _drone_at_zone(
        self,
        zone_name: str,
        drones: list[Drone],
    ) -> Drone | None:
        """Return the first drone currently visible at a zone."""
        for drone in drones:
            if drone.current_position == zone_name:
                return drone
        return None

    def _put_text(
        self,
        grid: list[list[str]],
        row: int,
        column: int,
        text: str,
        color: str | None,
    ) -> None:
        """Put colored text into the terminal grid."""
        if color in ANSI_COLORS:
            colored = f"{ANSI_COLORS[color]}{text}{RESET}"
        else:
            colored = text

        if column < len(grid[row]):
            grid[row][column] = colored

    def _print_grid(self, grid: list[list[str]]) -> None:
        """Print every row of the terminal grid."""
        for row in grid:
            print("".join(row).rstrip())

    def _clear_screen(self) -> None:
        """Clear the terminal using ANSI escape sequences."""
        print("\033[2J\033[H", end="")