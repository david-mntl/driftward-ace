"""Debug overlay: the ship's numbers and the lines the rules use, drawn on top of the frame.

Source: docs/contracts/DRA-6/DRA-6-debug-overlay.md, Interface and Presentation;
10-ui.md, debug_overlay, debug_overlay_layout, debug_text_font, debug_overlay_color.
The view only draws. It never fills, flips, logs per frame, catches an error, changes
the ship or reads the run mode. The app decides whether to call it.
"""

import logging
from functools import cache

import pygame

from core.ship import Ship
from core.world import SCREEN_H, TOP_LINE_Y

log = logging.getLogger(__name__)

OVERLAY_COLOR: tuple[int, int, int] = (0, 255, 0)
"""Text and line color, RGB. Source: 10-ui.md, debug_overlay_color (guess)."""

OVERLAY_FONT_SIZE: int = 16
"""Text size, default font, px. Source: 10-ui.md, debug_text_font (guess)."""

OVERLAY_MARGIN: int = 4
"""Gap from the left and top edges to line 1's top-left, px.

Source: 10-ui.md, debug_overlay_layout (guess).
"""


def draw_debug_overlay(surface: pygame.Surface, ship: Ship) -> None:
    """Draw the top-line and floor lines, then the ship's x, y, vx and vy, on ``surface``.

    Lines: 1 px, full surface width, on row TOP_LINE_Y and row SCREEN_H - 1.
    Text: four lines, two decimals, line 1's top-left at (OVERLAY_MARGIN, OVERLAY_MARGIN),
    each next line one font line-height lower. Units: pixels.
    Needs ``pygame.font`` initialized; raises if it isn't.
    """
    _draw_lines(surface)
    _draw_text(surface, ship)


def _draw_lines(surface: pygame.Surface) -> None:
    """Draw the top line on row TOP_LINE_Y and the floor on row SCREEN_H - 1, full width.

    The floor is y SCREEN_H, one row past the last visible row, so it shows on the row above.
    Source: DRA-6-debug-overlay.md, Presentation and Rationale; 91-decision-log.md, row 20.
    """
    right: int = surface.get_width() - 1
    for row in (TOP_LINE_Y, SCREEN_H - 1):
        pygame.draw.line(surface, OVERLAY_COLOR, (0, row), (right, row))


def _draw_text(surface: pygame.Surface, ship: Ship) -> None:
    """Draw ``x``, ``y``, ``vx`` and ``vy`` as ``<name> <value:.2f>``, one per line, top-left.

    Source: 10-ui.md, debug_overlay_layout (guess).
    """
    font: pygame.font.Font = _overlay_font()
    readings: tuple[tuple[str, float], ...] = (
        ("x", ship.x),
        ("y", ship.y),
        ("vx", ship.vx),
        ("vy", ship.vy),
    )
    for index, (name, value) in enumerate(readings):
        line: pygame.Surface = font.render(f"{name} {value:.2f}", True, OVERLAY_COLOR)
        top: int = OVERLAY_MARGIN + index * font.get_linesize()
        surface.blit(line, (OVERLAY_MARGIN, top))


@cache
def _overlay_font() -> pygame.font.Font:
    """Return the overlay font, built on the first call and reused after.

    Default font at OVERLAY_FONT_SIZE. Built once, never per frame.
    Source: DRA-6-debug-overlay.md, Presentation; 15-tech-constraints.md, rule 5.
    """
    return pygame.font.Font(None, OVERLAY_FONT_SIZE)
