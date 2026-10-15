"""Debug overlay: the ship's numbers, the lines the rules use, hitboxes and labels.

`draw_debug_overlay` draws the lines and the four text lines. `draw_debug_hitboxes` outlines
every hitbox and graze zone and labels every object. Both draw on top of the frame.

Source: docs/contracts/systems/debug-overlay.md, Interface and Presentation;
10-ui.md, debug_overlay, debug_overlay_layout, debug_text_font, debug_overlay_color.
The view only draws. It never fills, flips, logs per frame, catches an error, changes
the ship or reads the run mode. The app decides whether to call it.
"""

import logging
from functools import cache

import pygame

from core.objects.base import GameObject
from core.run import Run
from core.ship import Ship, ship_hitbox
from core.world import SCREEN_H, TOP_LINE_Y
from ui.shapes import draw_hitbox

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


def overlay_text_bottom() -> int:
    """Return the first screen row below every pixel the four text lines can cover. Draws nothing.

    Value: OVERLAY_MARGIN + 3 * linesize + max(linesize, font height), from the overlay's own
    cached font. Units: pixels. Needs ``pygame.font`` initialized.
    Source: docs/contracts/systems/debug-overlay.md, Interface and Presentation (DRA-13).
    """
    font: pygame.font.Font = _overlay_font()
    linesize: int = font.get_linesize()
    return OVERLAY_MARGIN + 3 * linesize + max(linesize, font.get_height())


def draw_debug_hitboxes(surface: pygame.Surface, run: Run) -> None:
    """Outline every hitbox and graze zone and label every object, on ``surface``.

    Order: every graze zone, the ship's hitbox, every object's hitbox, then every label.
    Outlines are 1 px in OVERLAY_COLOR. The ship's hitbox is drawn even while it blinks.
    Needs ``pygame.font`` initialized. Source: systems/debug-overlay.md, Presentation (DRA-29).
    """
    for obj in run.objects:
        draw_hitbox(surface, OVERLAY_COLOR, obj.graze_zone(), 1)
    draw_hitbox(surface, OVERLAY_COLOR, ship_hitbox(run.ship), 1)
    for obj in run.objects:
        draw_hitbox(surface, OVERLAY_COLOR, obj.current_hitbox(), 1)
    for obj in run.objects:
        _draw_label(surface, obj)


def _draw_label(surface: pygame.Surface, obj: GameObject) -> None:
    """Draw ``<type> <variant> x <x> y <y> <phase>`` under the object's footprint.

    Numbers use ``z.2f``. The label stays fully on the surface.
    Source: systems/debug-overlay.md, Presentation, label place (DRA-29).
    """
    font: pygame.font.Font = _overlay_font()
    text: str = (
        f"{obj.object_type.value} {obj.variant} x {obj.x:z.2f} y {obj.y:z.2f} {obj.phase.value}"
    )
    label: pygame.Surface = font.render(text, True, OVERLAY_COLOR)
    wanted: tuple[int, int] = (
        round(obj.x - obj.width / 2),
        round(obj.y + obj.height / 2),
    )
    surface.blit(label, _clamp_inside(surface, label, wanted))


def _clamp_inside(
    surface: pygame.Surface,
    label: pygame.Surface,
    top_left: tuple[int, int],
) -> tuple[int, int]:
    """Move ``top_left`` just enough for ``label`` to lie on ``surface``; 0 if it is bigger."""
    left: int = max(0, min(top_left[0], surface.get_width() - label.get_width()))
    top: int = max(0, min(top_left[1], surface.get_height() - label.get_height()))
    return left, top


def _draw_lines(surface: pygame.Surface) -> None:
    """Draw the top line on row TOP_LINE_Y and the floor on row SCREEN_H - 1, full width.

    The floor is y SCREEN_H, one row past the last visible row, so it shows on the row above.
    Source: systems/debug-overlay.md, Presentation and Rationale; 91-decision-log.md, row 20.
    """
    right: int = surface.get_width() - 1
    for row in (TOP_LINE_Y, SCREEN_H - 1):
        pygame.draw.line(surface, OVERLAY_COLOR, (0, row), (right, row))


def _draw_text(surface: pygame.Surface, ship: Ship) -> None:
    """Draw ``x``, ``y``, ``vx`` and ``vy`` as ``<name> <value:z.2f>``, one per line, top-left.

    The ``z`` option turns a value that rounds to zero into ``0.00``, never ``-0.00``.
    Source: 10-ui.md, debug_overlay_layout (guess); DRA-19 scope report, item 3.
    """
    font: pygame.font.Font = _overlay_font()
    readings: tuple[tuple[str, float], ...] = (
        ("x", ship.x),
        ("y", ship.y),
        ("vx", ship.vx),
        ("vy", ship.vy),
    )
    for index, (name, value) in enumerate(readings):
        line: pygame.Surface = font.render(f"{name} {value:z.2f}", True, OVERLAY_COLOR)
        top: int = OVERLAY_MARGIN + index * font.get_linesize()
        surface.blit(line, (OVERLAY_MARGIN, top))


@cache
def _overlay_font() -> pygame.font.Font:
    """Return the overlay font, built on the first call and reused after.

    Default font at OVERLAY_FONT_SIZE. Built once, never per frame.
    Source: systems/debug-overlay.md, Presentation; 15-tech-constraints.md, rule 5.
    """
    return pygame.font.Font(None, OVERLAY_FONT_SIZE)
