"""Burst view: the squares the ship bursts into on the last life, flying out and fading.

Source: docs/contracts/systems/run.md, Interface (DRA-125) and Presentation, Burst. The view reads
only the burst it is given. It never fills, flips, logs per frame, catches an error, changes the
burst, or reads the run mode or a key. The app draws it only on frames where the run is in its
last life, in the ship's place in the draw order. A stand-in until LD-08 sets the look.
"""

import logging
from functools import cache
from typing import Final

import pygame

from core.last_life import Burst

log = logging.getLogger(__name__)

BURST_COLOR: Final[tuple[int, int, int]] = (255, 255, 255)
"""Burst square color, RGB. Scope report DRA-125, Values needed, Burst: white (stand-in until
LD-08)."""

MAX_ALPHA: Final[int] = 255
"""Alpha of a fully opaque square, 0..255. The burst's opacity (0..1) scales it."""


def draw_burst(surface: pygame.Surface, burst: Burst) -> None:
    """Blit one square per particle center, each ``burst.particle_size`` px on a side. Units: px.

    The top-left is ``(round(cx - size / 2), round(cy - size / 2))`` for the center ``(cx, cy)``.
    Alpha is ``round(255 * burst.opacity)``. Squares off the surface are clipped by pygame.
    """
    size: int = burst.particle_size
    alpha: int = round(MAX_ALPHA * burst.opacity)
    image: pygame.Surface = _square_image(size, alpha)
    for center_x, center_y in burst.particle_centers:
        surface.blit(image, (round(center_x - size / 2), round(center_y - size / 2)))


@cache
def _square_image(size: int, alpha: int) -> pygame.Surface:
    """Return a filled square on a transparent surface, built once per key and kept.

    Source: run.md, Presentation, Burst, Cache; 15-tech-constraints.md, rule 5.
    """
    image: pygame.Surface = pygame.Surface((size, size), pygame.SRCALPHA)
    image.fill((*BURST_COLOR, alpha))
    return image
