"""The charge rays of the electric ball and the chain lightning node: code-drawn, drawn once.

Rays point out from a round body at evenly spread angles, the first at 45 degrees counterclockwise
from pointing right. How many show is the core's `charge_ray_count()`. One image holds all the
rays for one count, in one color, and is blitted centered on the body. Source:
drifters/03-chain-lightning.md, ray_length; 10-electric-ball.md. It only draws.
"""

import logging
import math
from typing import Final

import pygame

from ui.drifters.sprites import Sprites

log = logging.getLogger(__name__)

FIRST_RAY_DEGREES: Final[float] = 45.0
"""Angle of the first ray, degrees counterclockwise on screen from pointing right.

Source: drifters/03-chain-lightning.md, ray_length (guess), shared with the electric ball.
"""

FULL_TURN_DEGREES: Final[float] = 360.0
"""Degrees in a full turn, to spread the rays evenly."""

_SCALE_STEPS: Final[int] = 1000
"""A scale is kept in the cache key as thousandths, so the key is a whole number."""


def rays_image(
    sprites: Sprites,
    *,
    count: int,
    total: int,
    edge: float,
    length: float,
    width: float,
    scale: float,
    color: tuple[int, int, int],
) -> pygame.Surface:
    """Return an image of `count` of `total` rays, centered on its middle pixel, built once.

    Each ray runs from `edge` px out from the center to `length` px past it, `width` px thick, all
    times `scale`. The image is square with an odd side, so its middle pixel is the body's center.
    """
    key: tuple[object, ...] = (
        "rays",
        count,
        total,
        edge,
        length,
        width,
        round(scale * _SCALE_STEPS),
        color,
    )
    return sprites.built(
        key,
        lambda: _build(count, total, edge * scale, (edge + length) * scale, width * scale, color),
    )


def _build(
    count: int,
    total: int,
    edge: float,
    tip: float,
    width: float,
    color: tuple[int, int, int],
) -> pygame.Surface:
    """Draw `count` of `total` evenly spread rays from `edge` to `tip` px, `width` px thick."""
    thick: int = max(1, round(width))
    middle: int = math.ceil(tip) + thick
    image: pygame.Surface = pygame.Surface((2 * middle + 1, 2 * middle + 1), pygame.SRCALPHA)
    for k in range(count):
        angle: float = math.radians(FIRST_RAY_DEGREES + k * FULL_TURN_DEGREES / total)
        dx: float = math.cos(angle)
        dy: float = -math.sin(angle)
        start: tuple[float, float] = (middle + dx * edge, middle + dy * edge)
        end: tuple[float, float] = (middle + dx * tip, middle + dy * tip)
        pygame.draw.line(image, color, start, end, thick)
    return image


def blit_centered(surface: pygame.Surface, image: pygame.Surface, center: tuple[int, int]) -> None:
    """Blit an odd-sided `image` so its middle pixel lands on `center`."""
    surface.blit(image, (center[0] - image.get_width() // 2, center[1] - image.get_height() // 2))
