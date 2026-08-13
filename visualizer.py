import math
import pygame

from models import Drone, DroneMap


WIDTH = 1000
HEIGHT = 900
FPS = 60

WHITE = (255, 255, 255)
GRID = (230, 230, 230)
GRAY = (150, 150, 150)
NAVY = (10, 10, 40)

GREEN = (34, 120, 34)
YELLOW = (255, 235, 80)
BLUE = (30, 60, 220)
RED = (200, 50, 40)


class PygameVisualizer:
    """Display the drone map and moving drones."""

    def __init__(self, drone_map: DroneMap) -> None:
        """Create the Pygame window."""
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Fly-in")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("serif", 16, bold=True)
        self.drone_map = drone_map
        self.running = True

    def draw(self, drones: list[Drone]) -> None:
        """Draw one frame."""
        self._events()
        self.screen.fill(WHITE)
        self._grid()
        self._connections()
        self._zones(drones)
        pygame.display.flip()
        self.clock.tick(FPS)

    def _events(self) -> None:
        """Handle the window close button."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def _grid(self) -> None:
        """Draw the background grid."""
        for x in range(0, WIDTH, 80):
            pygame.draw.line(
                self.screen, GRID, (x, 0), (x, HEIGHT)
            )

        for y in range(0, HEIGHT, 80):
            pygame.draw.line(
                self.screen, GRID, (0, y), (WIDTH, y)
            )

    def _position(self, zone_name: str) -> tuple[int, int]:
        """Convert map coordinates into screen coordinates."""
        zone = self.drone_map.zones[zone_name]

        x = 150 + zone.x * 150
        y = 450 - zone.y * 150

        return x, y

    def _connections(self) -> None:
        """Draw all connections."""
        for connection in self.drone_map.connections:
            start = self._position(connection.zone_a)
            end = self._position(connection.zone_b)

            pygame.draw.line(
                self.screen,
                GRAY,
                start,
                end,
                6,
            )

    def _zones(self, drones: list[Drone]) -> None:
        """Draw all zones and drones."""
        for zone in self.drone_map.zones.values():
            position = self._position(zone.name)
            color = self._color(zone.name)

            radius = 55
            if zone.name != self.drone_map.start_name:
                if zone.name != self.drone_map.end_name:
                    radius = 40

            pygame.draw.circle(
                self.screen,
                color,
                position,
                radius,
            )

            pygame.draw.circle(
                self.screen,
                NAVY,
                position,
                radius,
                4,
            )

            self._label(zone.name, position)

            self._draw_drone(
                zone.name,
                position,
                drones,
            )

    def _draw_drone(
        self,
        zone_name: str,
        position: tuple[int, int],
        drones: list[Drone],
    ) -> None:
        """Draw the first drone currently at this zone."""
        for drone in drones:
            if drone.current_position == zone_name:
                text = f"D{drone.drone_id}"
                self._text(text, position)
                return

    def _label(
        self,
        name: str,
        position: tuple[int, int],
    ) -> None:
        """Draw the zone name."""
        self._text(name, position)

    def _text(
        self,
        text: str,
        position: tuple[int, int],
    ) -> None:
        """Draw centered white text."""
        surface = self.font.render(text, True, WHITE)
        rect = surface.get_rect(center=position)
        self.screen.blit(surface, rect)

    def _color(self, name: str) -> tuple[int, int, int]:
        """Choose a color based on the zone."""
        if name == self.drone_map.start_name:
            return GREEN

        if name == self.drone_map.end_name:
            return GREEN

        zone = self.drone_map.zones[name]

        if zone.zone_type.value == "restricted":
            return RED

        if zone.zone_type.value == "priority":
            return BLUE

        return YELLOW