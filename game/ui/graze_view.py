"""Graze ring view: the ring a paid graze shows around the ship, growing and fading.

Source: docs/contracts/systems/run.md, Interface (DRA-117) and Presentation, Graze ring. The view
reads only the ring and the ship it is given. It never fills, flips, logs per frame, catches an
error, changes the ring or the ship, or reads the run mode or a key. The app draws each ring in
``run.graze_rings``, in order, after the ship's place in the draw order.
"""

import logging
from functools import cache
from typing import Final

import pygame

from core.graze import GrazeRing
from core.ship import Ship

log = logging.getLogger(__name__)

GRAZE_RING_COLOR: Final[tuple[int, int, int]] = (255, 255, 255)
"""Graze ring color, RGB. 06-scoring.md, graze_ring_color (guess)."""

MAX_ALPHA: Final[int] = 255
"""Alpha of a fully opaque ring, 0..255. The ring's opacity (0..1) scales it."""


def draw_graze_ring(surface: pygame.Surface, ring: GrazeRing, ship: Ship) -> None:
    """Blit the ring's outline centered on ``(round(ship.x), round(ship.y))``. Units: pixels.

    Radius is ``round(ring.diameter / 2)``, line width ``ring.line_width``, alpha
    ``round(255 * ring.opacity)``. The place comes from the ship; nothing is stored here.
    """
    radius: int = round(ring.diameter / 2)
    alpha: int = round(MAX_ALPHA * ring.opacity)
    image: pygame.Surface = _ring_image(radius, ring.line_width, alpha)
    center: tuple[int, int] = (round(ship.x), round(ship.y))
    surface.blit(image, image.get_rect(center=center))


@cache
def _ring_image(radius: int, line_width: int, alpha: int) -> pygame.Surface:
    """Return the ring outline on a transparent surface, built once per key and kept.

    The surface is ``2 * radius + 1`` px square with the circle centered on its middle pixel.
    Source: run.md, Presentation, Graze ring, Cache; 15-tech-constraints.md, rule 5.
    """
    side: int = 2 * radius + 1
    image: pygame.Surface = pygame.Surface((side, side), pygame.SRCALPHA)
    color: tuple[int, int, int, int] = (*GRAZE_RING_COLOR, alpha)
    pygame.draw.circle(image, color, (radius, radius), radius, line_width)
    return image
