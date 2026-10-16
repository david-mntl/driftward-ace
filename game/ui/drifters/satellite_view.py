"""The placeholder satellite look: a white body square over a blue panel bar.

Source: docs/contracts/systems/drifters.md, Presentation, Satellite; drifters/02-satellite.md,
placeholder_look (guess). It only draws.
"""

import logging
from typing import Final

import pygame

from core.collision import Box, Hitbox
from core.drifters.base import Drifter, DrifterType
from ui.drifters.registry import dim_color, register_view
from ui.shapes import draw_shape

log = logging.getLogger(__name__)

SATELLITE_BODY_COLOR: Final[tuple[int, int, int]] = (240, 240, 240)
"""Body color, RGB. Source: drifters/02-satellite.md, placeholder_look (guess)."""

SATELLITE_PANEL_COLOR: Final[tuple[int, int, int]] = (60, 110, 220)
"""Panel bar color, RGB. Source: drifters/02-satellite.md, placeholder_look (guess)."""


@register_view(DrifterType.SATELLITE)
def render_satellite(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Draw the panel bar, then the body over it, at `center`, both upright, scaled by `scale`.

    The body is `drifter.hitbox[0]` and the bar `drifter.hitbox[1]`. Colors are times
    `brightness`. Raises TypeError when the hitbox is not exactly two boxes.
    """
    body, panel = _two_boxes(drifter)
    draw_shape(
        surface,
        dim_color(SATELLITE_PANEL_COLOR, brightness),
        _placed(panel, center, scale),
    )
    draw_shape(
        surface,
        dim_color(SATELLITE_BODY_COLOR, brightness),
        _placed(body, center, scale),
    )


def _two_boxes(drifter: Drifter) -> tuple[Box, Box]:
    """Return the body and panel boxes, or raise TypeError when the hitbox is not two boxes."""
    shapes: Hitbox = drifter.hitbox
    if len(shapes) != 2 or not isinstance(shapes[0], Box) or not isinstance(shapes[1], Box):
        raise TypeError("a satellite hitbox is two boxes: the body, then the panel bar")
    return shapes[0], shapes[1]


def _placed(box: Box, center: tuple[float, float], scale: float) -> Box:
    """Return `box` (offsets from the drifter's center) scaled and moved to `center`, screen px."""
    return Box(
        center[0] + box.cx * scale,
        center[1] + box.cy * scale,
        box.w * scale,
        box.h * scale,
    )
