"""Draws placed hitbox shapes: the shared helper for the ship view and the debug outlines.

Source: docs/contracts/systems/objects.md, ui/shapes.py. It only draws. It never fills the
background, never flips the display, never logs per frame and never catches an error.
"""

import logging

import pygame

from core.collision import Box, Circle, Hitbox, Shape

log = logging.getLogger(__name__)


def draw_shape(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    shape: Shape,
    width: int = 0,
) -> None:
    """Draw one placed shape in `color`, screen px. `width` 0 fills, 1 is a 1 px outline.

    A box is the rectangle with top-left (round(cx - w / 2), round(cy - h / 2)) and size
    round(w) by round(h). A circle has center (round(cx), round(cy)) and radius round(r).
    """
    if isinstance(shape, Circle):
        _draw_circle(surface, color, shape, width)
        return
    _draw_box(surface, color, shape, width)


def draw_hitbox(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    hitbox: Hitbox,
    width: int = 0,
) -> None:
    """Draw every shape of a placed hitbox, in order. `width` as in `draw_shape`."""
    for shape in hitbox:
        draw_shape(surface, color, shape, width)


def _draw_box(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    box: Box,
    width: int,
) -> None:
    """Draw a placed box as a rectangle."""
    left: int = round(box.cx - box.w / 2)
    top: int = round(box.cy - box.h / 2)
    rect = pygame.Rect(left, top, round(box.w), round(box.h))
    pygame.draw.rect(surface, color, rect, width)


def _draw_circle(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    circle: Circle,
    width: int,
) -> None:
    """Draw a placed circle."""
    center: tuple[int, int] = (round(circle.cx), round(circle.cy))
    pygame.draw.circle(surface, color, center, round(circle.r), width)
