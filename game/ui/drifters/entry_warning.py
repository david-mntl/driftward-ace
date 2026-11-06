"""The entry warning: one plain warning sign, a triangle with an exclamation mark, drawn at entry.

Source: docs/contracts/systems/drifters.md, Presentation, Entry warning; 07-drifters.md,
entry_warning values (guess). Every warning is the same sign, whatever the drifter. The image is
built once, on the first warning frame, and blitted every frame after. It only draws.
"""

from __future__ import annotations

import logging
import math
from functools import cache
from itertools import pairwise
from typing import Final

import pygame

from core.drifters.base import ENTRY_WARNING_SIZE, Drifter

log = logging.getLogger(__name__)

type _Point = tuple[float, float]

ENTRY_WARNING_COLOR: Final[tuple[int, int, int]] = (255, 158, 94)
"""Sign color, RGB, #ff9e5e, the WARNING card's orange. Source: 07-drifters.md,
entry_warning_color (guess)."""

FILL_ALPHA: Final[float] = 0.26
"""Opacity of the triangle's fill, 0..1. The outline and mark are opaque. Source: 07-drifters.md,
entry_warning_look (guess)."""

OUTLINE_WIDTH: Final[float] = 1.5
"""Triangle outline width, px. Source: 07-drifters.md, entry_warning_look (guess)."""

MARK_WIDTH: Final[float] = 1.4
"""Width of the exclamation mark's bar, px. Source: 07-drifters.md, entry_warning_look (guess)."""

MARK_BAR: Final[tuple[float, float]] = (0.32, 0.68)
"""Top and bottom of the mark's bar, as shares of the triangle's height from its apex."""

MARK_DOT: Final[tuple[float, float]] = (0.84, 0.056)
"""Center of the mark's dot and its radius, as shares of the triangle's height from its apex."""

_SUPERSAMPLE: Final[int] = 4
"""Times larger the sign is drawn before it is scaled down, so its edges are smooth."""


def draw_entry_warning(surface: pygame.Surface, drifter: Drifter) -> None:
    """Blit the warning sign centered on `drifter.warning_center()`, rounded to px."""
    image: pygame.Surface = _sign_image()
    center_x, center_y = drifter.warning_center()
    surface.blit(image, image.get_rect(center=(round(center_x), round(center_y))))


@cache
def _sign_image() -> pygame.Surface:
    """Return the sign: a point-up triangle, translucent fill, opaque outline and mark.

    Square, side 2 * ceil(R) + 1, with the warning's center on its middle pixel, where
    R = ENTRY_WARNING_SIZE / 2, px. The triangle is equilateral, centered on its middle, with its
    corners R - OUTLINE_WIDTH / 2 from the center, so its round outline never reaches past R.
    Drawn at _SUPERSAMPLE times its size and scaled down. Built once, shared by every drifter.
    """
    side: int = 2 * math.ceil(ENTRY_WARNING_SIZE / 2) + 1
    big: pygame.Surface = pygame.Surface(
        (side * _SUPERSAMPLE, side * _SUPERSAMPLE), pygame.SRCALPHA
    )
    middle: float = side * _SUPERSAMPLE / 2
    corner: float = (ENTRY_WARNING_SIZE / 2 - OUTLINE_WIDTH / 2) * _SUPERSAMPLE
    triangle: list[_Point] = [
        (middle + corner * math.cos(angle), middle - corner * math.sin(angle))
        for angle in (math.pi / 2, math.pi * 7 / 6, -math.pi / 6)
    ]
    apex: float = triangle[0][1]
    height: float = 1.5 * corner

    fill: pygame.Surface = pygame.Surface(big.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(fill, (*ENTRY_WARNING_COLOR, round(255 * FILL_ALPHA)), triangle)
    big.blit(fill, (0, 0))
    _round_line(big, [*triangle, triangle[0]], OUTLINE_WIDTH * _SUPERSAMPLE)
    _round_line(
        big,
        [(middle, apex + MARK_BAR[0] * height), (middle, apex + MARK_BAR[1] * height)],
        MARK_WIDTH * _SUPERSAMPLE,
    )
    pygame.draw.circle(
        big, ENTRY_WARNING_COLOR, (middle, apex + MARK_DOT[0] * height), MARK_DOT[1] * height
    )
    return pygame.transform.smoothscale(big, (side, side))


def _round_line(image: pygame.Surface, points: list[_Point], width: float) -> None:
    """Draw a polyline through `points` in ENTRY_WARNING_COLOR, round at every end and joint."""
    thick: int = max(round(width), 1)
    for start, end in pairwise(points):
        pygame.draw.line(image, ENTRY_WARNING_COLOR, start, end, thick)
    for point in points:
        pygame.draw.circle(image, ENTRY_WARNING_COLOR, point, thick / 2)
