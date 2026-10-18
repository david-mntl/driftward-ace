"""The placeholder fireball look: a dark yellow tail disc behind an orange head disc.

Source: docs/contracts/systems/drifters.md, Presentation, Fireball; drifters/06-fireball.md,
placeholder_look (guess). It only draws.
"""

import logging
from typing import Final

import pygame

from core.collision import Circle, Hitbox
from core.drifters.base import Drifter, DrifterType
from ui.drifters.registry import dim_color, register_view
from ui.shapes import draw_shape

log = logging.getLogger(__name__)

FIREBALL_HEAD_COLOR: Final[tuple[int, int, int]] = (255, 140, 0)
"""Head color, RGB. Source: drifters/06-fireball.md, placeholder_look (guess)."""

FIREBALL_TAIL_COLOR: Final[tuple[int, int, int]] = (200, 160, 0)
"""Tail color, RGB. Source: drifters/06-fireball.md, placeholder_look (guess)."""


@register_view(DrifterType.FIREBALL)
def render_fireball(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Draw the tail, then the head over it, at `center`, scaled by `scale`.

    The head is `drifter.hitbox[0]` and the tail `drifter.hitbox[1]`. Colors are times
    `brightness`. Raises TypeError when the hitbox is not exactly two circles.
    """
    head, tail = _two_circles(drifter)
    draw_shape(
        surface,
        dim_color(FIREBALL_TAIL_COLOR, brightness),
        _placed(tail, center, scale),
    )
    draw_shape(
        surface,
        dim_color(FIREBALL_HEAD_COLOR, brightness),
        _placed(head, center, scale),
    )


def _two_circles(drifter: Drifter) -> tuple[Circle, Circle]:
    """Return the head and tail circles, or raise TypeError when the hitbox is not two circles."""
    shapes: Hitbox = drifter.hitbox
    if len(shapes) != 2 or not isinstance(shapes[0], Circle) or not isinstance(shapes[1], Circle):
        raise TypeError("render_fireball draws two circles, head then tail")
    return shapes[0], shapes[1]


def _placed(circle: Circle, center: tuple[float, float], scale: float) -> Circle:
    """Return `circle` (offsets from the drifter's center) scaled and moved to `center`, px."""
    return Circle(center[0] + circle.cx * scale, center[1] + circle.cy * scale, circle.r * scale)
