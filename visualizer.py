from __future__ import annotations
import os
from typing import Dict, List, Sequence, Tuple

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from models import Drone, Graph, Zone

_BACKGROUND = pygame.Color("white")
_EDGE_COLOR = pygame.Color("gray55")
_TEXT_DARK = pygame.Color("black")
_TEXT_LIGHT = pygame.Color("white")


def _to_color(raw: object) -> pygame.Color:
    """Parse a color value using pygame.Color where possible."""
    if isinstance(raw, pygame.Color):
        return pygame.Color(raw)
    if isinstance(raw, str):
        value = raw.strip()
        if value and value[0] in "([" and value[-1] in ")]":
            parts = [p.strip() for p in value[1:-1].split(",") if p.strip()]
            if len(parts) in (3, 4):
                return pygame.Color(*[int(v) for v in parts])
        return pygame.Color(value)
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        values = list(raw)
        if len(values) in (3, 4):
            return pygame.Color(*[int(v) for v in values])
    raise ValueError(f"Unsupported color value: {raw!r}")


def _fallback_color(zone_name: str) -> pygame.Color:
    """Generate a stable readable fallback color from zone name."""
    color = pygame.Color(0)
    hue = sum(ord(ch) for ch in zone_name) % 360
    color.hsva = (hue, 55, 85, 100)
    return color


def _zone_color(zone: Zone) -> pygame.Color:
    """Resolve a zone fill color from data or deterministic fallback."""
    try:
        if zone.color is not None:
            return _to_color(zone.color)
    except (ValueError, TypeError):
        pass
    return _fallback_color(zone.name)


def _label_color(fill: pygame.Color) -> pygame.Color:
    """Pick black/white text for best contrast against fill color."""
    luminance = (0.299 * fill.r) + (0.587 * fill.g) + (0.114 * fill.b)
    return _TEXT_DARK if luminance > 160 else _TEXT_LIGHT


class _PygameVisualizer:
    def __init__(self, graph: Graph) -> None:
        pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        self.graph = graph
        self.node_radius = 24
        self.margin = 60
        self.scale = 80
        self.tick_ms = 350
        self.positions = self._compute_positions()
        width, height = self._window_size()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Fly-in Simulation")
        self.font = pygame.font.SysFont(None, 20)
        self.small_font = pygame.font.SysFont(None, 16)
        self.clock = pygame.time.Clock()
        self.closed = False

    def _compute_positions(self) -> Dict[str, Tuple[int, int]]:
        xs = [z.x for z in self.graph.zones.values()]
        ys = [z.y for z in self.graph.zones.values()]
        min_x, min_y = min(xs), min(ys)
        positions: Dict[str, Tuple[int, int]] = {}
        for name, zone in self.graph.zones.items():
            px = self.margin + (zone.x - min_x) * self.scale
            py = self.margin + (zone.y - min_y) * self.scale
            positions[name] = (px, py)
        return positions

    def _window_size(self) -> Tuple[int, int]:
        points = list(self.positions.values())
        max_x = max(x for x, _ in points) + self.margin
        max_y = max(y for _, y in points) + self.margin
        return max(max_x, 640), max(max_y, 480)

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.closed = True

    def _draw_arrow(self, src: Tuple[int, int], dst: Tuple[int, int]) -> None:
        if src == dst:
            return
        dx = dst[0] - src[0]
        dy = dst[1] - src[1]
        dist = (dx * dx + dy * dy) ** 0.5
        if dist == 0:
            return
        ux = dx / dist
        uy = dy / dist
        sx = src[0] + ux * self.node_radius
        sy = src[1] + uy * self.node_radius
        ex = dst[0] - ux * self.node_radius
        ey = dst[1] - uy * self.node_radius
        perp_x = -uy * 4
        perp_y = ux * 4
        start = (sx + perp_x, sy + perp_y)
        end = (ex + perp_x, ey + perp_y)
        pygame.draw.line(self.screen, _EDGE_COLOR, start, end, 2)

        arrow_len = 10
        arrow_w = 6
        left = (
            end[0] - ux * arrow_len + uy * arrow_w,
            end[1] - uy * arrow_len - ux * arrow_w,
        )
        right = (
            end[0] - ux * arrow_len - uy * arrow_w,
            end[1] - uy * arrow_len + ux * arrow_w,
        )
        pygame.draw.polygon(self.screen, _EDGE_COLOR, [end, left, right])

    def draw_turn(
        self,
        turn: int,
        drones: List[Drone],
        zone_occupancy: Dict[str, int],
    ) -> None:
        self._process_events()
        if self.closed:
            return

        self.screen.fill(_BACKGROUND)

        for conn in self.graph.connections.values():
            a = self.positions[conn.a]
            b = self.positions[conn.b]
            self._draw_arrow(a, b)
            self._draw_arrow(b, a)

        for name, zone in self.graph.zones.items():
            center = self.positions[name]
            fill = _zone_color(zone)
            pygame.draw.circle(self.screen, fill, center, self.node_radius)
            pygame.draw.circle(
                self.screen, _TEXT_DARK, center, self.node_radius, 2
            )

            label = self.font.render(name, True, _label_color(fill))
            label_rect = label.get_rect(center=center)
            self.screen.blit(label, label_rect)

            used = zone_occupancy.get(name, 0)
            drones_here = [
                d.label() for d in drones
                if (
                    d.current_zone == name
                    and not d.finished
                    and d.traveling_to is None
                )
            ]
            info_text = f"{used}/{zone.max_drones}"
            if drones_here:
                info_text += " " + ",".join(drones_here)
            info = self.small_font.render(info_text, True, _TEXT_DARK)
            info_rect = info.get_rect(
                midtop=(center[0], center[1] + self.node_radius + 4)
            )
            self.screen.blit(info, info_rect)

        title = self.font.render(f"Turn {turn}", True, _TEXT_DARK)
        self.screen.blit(title, (16, 12))
        pygame.display.flip()
        pygame.time.wait(self.tick_ms)
        self.clock.tick(60)

    def draw_summary(self, total_turns: int, nb_drones: int) -> None:
        self._process_events()
        if self.closed:
            return

        summary = self.font.render(
            f"Complete: {nb_drones} drones in {total_turns} turns",
            True,
            _TEXT_DARK,
        )
        rect = summary.get_rect()
        rect.bottomleft = (16, self.screen.get_height() - 16)
        self.screen.blit(summary, rect)
        pygame.display.flip()


_VISUALIZER: _PygameVisualizer | None = None


def _get_visualizer(graph: Graph) -> _PygameVisualizer:
    global _VISUALIZER
    if _VISUALIZER is None:
        _VISUALIZER = _PygameVisualizer(graph)
    return _VISUALIZER


def render_turn(
    turn: int,
    graph: Graph,
    drones: List[Drone],
    moved_tokens: List[str],
    zone_occupancy: Dict[str, int],
    link_usage: Dict[Tuple[str, str], int],
) -> None:
    del moved_tokens, link_usage
    _get_visualizer(graph).draw_turn(turn, drones, zone_occupancy)


def render_summary(total_turns: int, nb_drones: int) -> None:
    global _VISUALIZER
    if _VISUALIZER is None:
        return
    _VISUALIZER.draw_summary(total_turns, nb_drones)
    pygame.quit()
    _VISUALIZER = None
