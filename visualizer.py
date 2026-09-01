"""Simple and fast Pygame visualization for Fly-in."""

from parsing import DroneMap
import pygame


WIDTH = 1280
HEIGHT = 720

ZOOM_MIN = 0.4
ZOOM_MAX = 3.0
ZOOM_STEP = 0.1

FPS = 60
MOVE_DELAY = 500


class PygameVisualizer:
    """Display the drone map and replay drone movements."""

    def __init__(self, drone_map: DroneMap) -> None:
        """Create the Pygame window."""
        pygame.init()

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT),
            pygame.RESIZABLE,
        )
        pygame.display.set_caption("لعبة الطيارة حلال")
        self.original_image = pygame.image.load("image.png").convert_alpha()
        self.image = pygame.transform.scale(self.original_image,
                                            (WIDTH, HEIGHT))

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 12, bold=True)
        self.drone_font = pygame.font.SysFont("arial", 9, bold=True)

        self.drone_map = drone_map
        self.running = True
        self.started = False
        self.finished = False

        self.zoom = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        self.dragging = False
        self.last_mouse = (0, 0)

        self.positions: dict = {}

        self.moves: list = []
        self.current_turn = 0
        self.last_move_time = 0

        self.background = (220, 220, 220)
        self.connection_color = (17, 17, 17)
        self.border_color = (0, 0, 0)
        self.drone_color = (255, 255, 255)

        self.zone_positions: dict[str, tuple[int, int]] = {}
        self._prepare_map()

    def _prepare_map(self) -> None:
        """Prepare static map information."""
        for zone in self.drone_map.zones.values():
            self.zone_positions[zone.name] = self._position(zone.name)

    def play(self, moves: list[tuple[int, str]]) -> None:
        """
        Display the map and wait for SPACE before starting
        the simulation.
        """
        start = self.drone_map.start_name

        self.moves = moves
        self.positions = {
            drone_id: start
            for drone_id in range(1, self.drone_map.nb_drones + 1)
        }

        self.current_turn = 0
        self.started = False
        self.finished = False

        while self.running:
            self._events()

            if not self.running:
                break

            if self.started and not self.finished:
                self._update_simulation()

            self._draw()
            self.clock.tick(FPS)

        pygame.quit()

    def _update_simulation(self) -> None:
        """Advance the simulation at a fixed speed."""
        current_time = pygame.time.get_ticks()

        if current_time - self.last_move_time < MOVE_DELAY:
            return

        if self.current_turn >= len(self.moves):
            self.finished = True
            return

        turn = self.moves[self.current_turn]

        for drone_id, movement in turn:
            if "-" not in movement:
                continue

            parts = movement.split("-")

            if len(parts) == 3:
                zone1 = parts[1]
                zone2 = parts[2]
                self.positions[drone_id] = (zone1, zone2)
            else:
                self.positions[drone_id] = parts[1]

        self.current_turn += 1
        self.last_move_time = current_time

        if self.current_turn >= len(self.moves):
            self.finished = True

    def _draw(self) -> None:
        """Draw the complete visualization."""
        self.screen.fill(self.background)
        self.screen.blit(self.image, (0, 0))

        self._connections()
        self._zones()
        self._drones()

        pygame.display.flip()

    def _events(self) -> None:
        """Handle user input."""
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:
                    self._start_simulation()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._mouse_down(event)

            elif event.type == pygame.MOUSEBUTTONUP:
                self._mouse_up(event)

            elif event.type == pygame.MOUSEMOTION:
                self._mouse_move(event)

            elif event.type == pygame.MOUSEWHEEL:
                self._zoom(event.y)

            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(event.size,
                                                      pygame.RESIZABLE)
                self.image = pygame.transform.scale(
                    self.original_image, event.size
                )

    def _start_simulation(self) -> None:
        """Start or restart the simulation."""
        start = self.drone_map.start_name

        if start is None:
            return

        self.positions = {
            drone_id: start
            for drone_id in range(1, self.drone_map.nb_drones + 1)
        }

        self.current_turn = 0
        self.finished = False
        self.started = True
        self.last_move_time = pygame.time.get_ticks()

    def _mouse_down(self, event: pygame.event.Event) -> None:
        """Start dragging the map."""
        if event.button == 1:
            self.dragging = True
            self.last_mouse = event.pos

    def _mouse_up(self, event: pygame.event.Event) -> None:
        """Stop dragging the map."""
        if event.button == 1:
            self.dragging = False

    def _mouse_move(self, event: pygame.event.Event) -> None:
        """Move the map while dragging."""
        if not self.dragging:
            return

        dx = event.pos[0] - self.last_mouse[0]
        dy = event.pos[1] - self.last_mouse[1]

        self.offset_x += dx
        self.offset_y += dy

        self.last_mouse = event.pos
        self._update_zone_positions()

    def _zoom(self, direction: int) -> None:
        """Zoom the map."""
        old_zoom = self.zoom

        self.zoom += direction * ZOOM_STEP
        self.zoom = max(ZOOM_MIN, min(ZOOM_MAX, self.zoom))

        if self.zoom != old_zoom:
            self._update_zone_positions()

    def _update_zone_positions(self) -> None:
        """Update cached screen positions."""
        for zone in self.drone_map.zones.values():
            self.zone_positions[zone.name] = self._position(zone.name)

    def _position(self, zone_name: str) -> tuple[int, int]:
        """Convert map coordinates into screen coordinates."""
        zone = self.drone_map.zones[zone_name]

        x = 150 + zone.x * 150.0
        y = 450 + zone.y * 150.0

        x = x * self.zoom + self.offset_x
        y = y * self.zoom + self.offset_y

        return int(x), int(y)

    def _connections(self) -> None:
        """Draw all map connections."""
        width = max(1, int(4 * self.zoom))

        for connection in self.drone_map.connections:
            start = self.zone_positions[connection.zone_a]
            end = self.zone_positions[connection.zone_b]

            pygame.draw.line(self.screen, self.connection_color, start, end,
                             width)

    def _zones(self) -> None:
        """Draw all zones."""
        for zone in self.drone_map.zones.values():
            position = self.zone_positions[zone.name]

            color = self._zone_color(zone.color)

            radius = 40.0

            if (zone.name == self.drone_map.start_name
                    or zone.name == self.drone_map.end_name):
                radius = 50.0

            radius *= self.zoom

            pygame.draw.circle(self.screen, color, position, radius)
            pygame.draw.circle(self.screen, self.border_color, position,
                               radius, max(1, int(3 * self.zoom)))

            label_position = (position[0], position[1] + radius + 12)
            self._text(zone.name, label_position)

    def _drones(self) -> None:
        """Draw all drones."""
        radius = 20 * self.zoom

        for drone_id, location in self.positions.items():
            position = None

            if isinstance(location, tuple):
                zone1, zone2 = location
                pos1 = self.zone_positions.get(zone1)
                pos2 = self.zone_positions.get(zone2)

                if pos1 is None or pos2 is None:
                    continue

                position = (int((pos1[0] + pos2[0]) / 2),
                            int((pos1[1] + pos2[1]) / 2))
            else:
                position = self.zone_positions.get(location)

            if position is None:
                continue

            pygame.draw.circle(self.screen, self.drone_color, position, radius)
            pygame.draw.circle(self.screen, self.border_color, position,
                               radius, 1)

            self._text(f"D{drone_id}", position)

    def _zone_color(self, color: str | None) -> str:
        """Convert map colors into simple visualization colors."""
        if color is None:
            return "silver"

        if color == "rainbow":
            return "red"

        return color

    def _text(self, text: str, position: tuple[float, float]) -> None:
        """Draw centered zone text."""
        surface = self.font.render(text, True, "black")
        rect = surface.get_rect(center=position)
        self.screen.blit(surface, rect)
