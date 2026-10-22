"""The placeholder UFO look: a green dome over a grey disc, the disc drawn on top of the dome.

Source: docs/contracts/systems/drifters.md, Presentation, UFO; drifters/07-ufo.md,
placeholder_look (guess). It only draws.
"""

import logging
from typing import Final

import pygame

from core.collision import Box, Circle, Hitbox
from core.drifters.base import Drifter, DrifterType
from ui.drifters.registry import dim_color, register_view
from ui.shapes import draw_shape

log = logging.getLogger(__name__)

UFO_DISC_COLOR: Final[tuple[int, int, int]] = (170, 170, 185)
"""Disc color, RGB. Source: drifters/07-ufo.md, placeholder_look (guess)."""

UFO_DOME_COLOR: Final[tuple[int, int, int]] = (90, 220, 110)
"""Dome color, RGB. Source: drifters/07-ufo.md, placeholder_look (guess)."""


@register_view(DrifterType.UFO)
def render_ufo(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Draw the dome, then the disc over its lower half, at `center`, scaled by `scale`.

    The disc is `drifter.hitbox[0]` and the dome `drifter.hitbox[1]`. Colors are times
    `brightness`. Raises TypeError when the hitbox is not exactly a box then a circle.
    """
    disc, dome = _disc_and_dome(drifter)
    draw_shape(
        surface,
        dim_color(UFO_DOME_COLOR, brightness),
        Circle(
            center[0] + dome.cx * scale,
            center[1] + dome.cy * scale,
            dome.r * scale,
        ),
    )
    draw_shape(
        surface,
        dim_color(UFO_DISC_COLOR, brightness),
        Box(
            center[0] + disc.cx * scale,
            center[1] + disc.cy * scale,
            disc.w * scale,
            disc.h * scale,
        ),
    )


def _disc_and_dome(drifter: Drifter) -> tuple[Box, Circle]:
    """Return the disc box and the dome circle, or raise TypeError when the hitbox is not them."""
    shapes: Hitbox = drifter.hitbox
    if len(shapes) != 2 or not isinstance(shapes[0], Box) or not isinstance(shapes[1], Circle):
        raise TypeError("render_ufo draws a box then a circle, disc then dome")
    return shapes[0], shapes[1]
