"""The placeholder planet look: a purple body inside a field of 1 px rings.

Source: docs/contracts/systems/drifters.md, Presentation, Planet; drifters/08-planet.md,
placeholder_look (guess). The outer ring and the body go straight onto the surface. The inner
rings fade, so they are drawn on one reused alpha layer. It only draws: core hands over every
radius and opacity.
"""

import logging
import math
from typing import Final

import pygame

from core.drifters.base import Drifter, DrifterType
from core.drifters.planet import FieldRing, Planet
from ui.drifters.registry import dim_color, register_view

log = logging.getLogger(__name__)

PLANET_BODY_COLOR: Final[tuple[int, int, int]] = (140, 70, 200)
"""Body color, RGB. Source: drifters/08-planet.md, placeholder_look (guess)."""

PLANET_RING_COLOR: Final[tuple[int, int, int]] = (180, 120, 255)
"""Color of every field ring, RGB. Source: drifters/08-planet.md, placeholder_look (guess)."""

PLANET_RING_WIDTH: Final[int] = 1
"""Width of every field ring, px. Source: drifters/08-planet.md, placeholder_look (guess)."""

_ALPHA_MAX: Final[int] = 255
"""The most opaque alpha channel value."""

_LAYER_MARGIN: Final[int] = 1
"""Px the layer reaches past the outer ring on each side, for the ring's own line."""

_TRANSPARENT: Final[tuple[int, int, int, int]] = (0, 0, 0, 0)
"""Fully transparent RGBA, the layer's clear color."""

_LAYERS: dict[int, pygame.Surface] = {}
"""The alpha layers, one per side in px. Each is built the first time its side is drawn."""


@register_view(DrifterType.PLANET)
def render_planet(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Draw the outer ring, the inner rings, then the body over them, around the rounded `center`.

    Below full scale (the entry warning's copy) only the body is drawn. Colors are times
    `brightness`. Raises TypeError when `drifter` is not a Planet.
    """
    if not isinstance(drifter, Planet):
        raise TypeError("render_planet draws a Planet")
    cx: int = round(center[0])
    cy: int = round(center[1])
    if scale >= 1.0:
        _draw_field(surface, drifter, (cx, cy), brightness)
    pygame.draw.circle(
        surface,
        dim_color(PLANET_BODY_COLOR, brightness),
        (cx, cy),
        round(drifter.width * scale / 2),
    )


def _draw_field(
    surface: pygame.Surface, planet: Planet, center: tuple[int, int], brightness: float
) -> None:
    """Draw the opaque outer ring, then the faint inner rings over it."""
    ring_color: tuple[int, int, int] = dim_color(PLANET_RING_COLOR, brightness)
    pygame.draw.circle(surface, ring_color, center, round(planet.pull_radius), PLANET_RING_WIDTH)
    _draw_inner_rings(surface, planet, center, ring_color)


def _draw_inner_rings(
    surface: pygame.Surface,
    planet: Planet,
    center: tuple[int, int],
    ring_color: tuple[int, int, int],
) -> None:
    """Draw every inner ring on the reused alpha layer and blit it once, centered on `center`."""
    rings: tuple[FieldRing, ...] = planet.inner_rings()
    if not rings:
        return
    layer: pygame.Surface = _layer_for(round(planet.pull_radius) + _LAYER_MARGIN)
    layer.fill(_TRANSPARENT)
    middle: int = layer.get_width() // 2
    for ring in rings:
        alpha: int = math.floor(_ALPHA_MAX * ring.opacity + 0.5)
        if alpha > 0:
            pygame.draw.circle(
                layer, (*ring_color, alpha), (middle, middle), round(ring.radius), PLANET_RING_WIDTH
            )
    surface.blit(layer, (center[0] - middle, center[1] - middle))


def _layer_for(reach: int) -> pygame.Surface:
    """Return the alpha layer for a field `reach` px from the center, building it once."""
    side: int = 2 * reach + 1
    layer: pygame.Surface | None = _LAYERS.get(side)
    if layer is None:
        layer = pygame.Surface((side, side), pygame.SRCALPHA)
        _LAYERS[side] = layer
    return layer
