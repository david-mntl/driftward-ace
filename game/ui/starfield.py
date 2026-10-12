"""Starfield view: dim dots that drift down with the world scroll.

Source: docs/contracts/systems/scroll.md, Interface and Presentation. The view only
draws. It never fills the background, never flips the display, never logs per frame, never
catches an error and never changes the scroll.
"""

import logging
import random

import pygame

from core.scroll import Scroll
from core.world import SCREEN_H, SCREEN_W

log = logging.getLogger(__name__)

STAR_COUNT: int = 50
"""Number of stars. Scope report DRA-13, temporary stand-in approved by the Director, not in
the GDD."""

STAR_COLOR: tuple[int, int, int] = (90, 100, 140)
"""Star fill, RGB. Scope report DRA-13, temporary stand-in approved by the Director, not in
the GDD."""

STAR_SIZES: tuple[int, ...] = (1, 2)
"""Star square sizes, px. Scope report DRA-13, temporary stand-in approved by the Director,
not in the GDD."""

STAR_SEED: int = 1301
"""Fixed seed, so the layout is the same every run. No design meaning."""

Star = tuple[int, int, int]
"""One star: (x, base_y, size), screen px."""


def _build_stars() -> tuple[Star, ...]:
    """Return STAR_COUNT stars from STAR_SEED, each as (x, base_y, size)."""
    rng: random.Random = random.Random(STAR_SEED)
    stars: list[Star] = []
    for _ in range(STAR_COUNT):
        x: int = rng.randrange(SCREEN_W)
        base_y: int = rng.randrange(SCREEN_H)
        size: int = rng.choice(STAR_SIZES)
        stars.append((x, base_y, size))
    return tuple(stars)


STARS: tuple[Star, ...] = _build_stars()
"""The star layout, built once at import."""


def draw_starfield(surface: pygame.Surface, scroll: Scroll) -> None:
    """Draw every star as a filled square in STAR_COLOR, moved down by the scroll distance.

    The top-left of each star is (x, int((base_y + scroll.distance_px) % SCREEN_H)), so stars
    fall at the scroll speed and wrap from the bottom to the top. Reads only
    scroll.distance_px. Units: pixels. Source: systems/scroll.md, Presentation.
    """
    distance_px: float = scroll.distance_px
    for x, base_y, size in STARS:
        y: int = int((base_y + distance_px) % SCREEN_H)
        pygame.draw.rect(surface, STAR_COLOR, pygame.Rect(x, y, size, size))
