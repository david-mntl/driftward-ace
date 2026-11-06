"""The planet look: a turning body from a pool of looks, inside a field of code-drawn 1 px rings.

Source: drifters/08-planet.md, look and field rings; 12-art-and-audio.md, rules 9, 10 and 13. Each
planet keeps the look its seed picks and loops its turn in game ticks, offset by uid. The game
draws the field rings (core hands over every radius and opacity). A ring is one cached 8-bit
outline image per radius (an inner ring's radius is rounded to `field_ring_radius_step` px); its
fade is the image's alpha at blit time, so a ring costs one blit and no drawing. A dimmed planet
fades its rings by the same share instead. It only draws.
"""

import logging

import pygame

from core.drifters.base import Drifter, DrifterType
from core.drifters.planet import FieldRing, Planet, PlanetVariantExtra
from core.drifters.tuning import DrifterTuning
from ui.drifters.looks import StripRule
from ui.drifters.registry import register_view
from ui.drifters.sprites import Sprites, installed_sprites, pick, scaled_size, strip_frame

log = logging.getLogger(__name__)

_PALETTE_BITS: int = 8
"""Bits a pixel of a ring image takes."""

_CLEAR_INDEX: int = 0
"""Palette entry of a ring image's transparent pixels (its color key)."""

_RING_INDEX: int = 1
"""Palette entry of a ring image's ring color."""

_ALPHA_MAX: int = 255
"""The most opaque alpha channel value."""


@register_view(DrifterType.PLANET)
def render_planet(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Blit the outer ring, the inner rings, then the body's frame over them, around `center`.

    Below full scale (a small copy) only the body is drawn. The frame is centered on the rounded
    `center`; colors are times `brightness`. Raises TypeError when `drifter` is not a Planet.
    """
    if not isinstance(drifter, Planet):
        raise TypeError("render_planet draws a Planet")
    sprites: Sprites = installed_sprites()
    level: int = sprites.level(brightness)
    cx: int = round(center[0])
    cy: int = round(center[1])
    if scale >= 1.0:
        _draw_field(surface, sprites, drifter, (cx, cy), level)
    pool: tuple[StripRule, ...] = sprites.looks.planet.looks
    rule: StripRule = pool[pick(sprites.seed(drifter.uid), len(pool))]
    index: int = strip_frame(
        rule, sprites.seed(drifter.uid), drifter.ticks_in_phase, sprites.count(rule)
    )
    image: pygame.Surface = sprites.image(rule, index, level, size=scaled_size(rule, scale))
    surface.blit(image, image.get_rect(center=(cx, cy)))


def warm(sprites: Sprites, tuning: DrifterTuning) -> None:
    """Build every frame of every look, and a ring image for every radius a field ring takes."""
    for rule in sprites.looks.planet.looks:
        for level in sprites.warm_levels:
            for index in range(sprites.count(rule)):
                sprites.image(rule, index, level)
    planet = tuning.drifters.get(DrifterType.PLANET)
    if planet is None:
        return
    step: int = sprites.looks.planet.field_ring_radius_step
    for variant in planet.variants.values():
        if isinstance(variant.extra, PlanetVariantExtra):
            surface_radius: int = round(variant.width / 2)
            pull_radius: int = round(variant.extra.pull_radius)
            _ring_image(sprites, pull_radius)
            for radius in range(_stepped(surface_radius, step), pull_radius + step, step):
                _ring_image(sprites, radius)


def _draw_field(
    surface: pygame.Surface,
    sprites: Sprites,
    planet: Planet,
    center: tuple[int, int],
    level: int,
) -> None:
    """Blit the opaque outer ring, then the faint inner rings over it."""
    share: float = level / sprites.steps
    _blit_ring(surface, sprites, center, round(planet.pull_radius), _ALPHA_MAX * share)
    rings: tuple[FieldRing, ...] = planet.inner_rings()
    for ring in rings:
        alpha: float = _ALPHA_MAX * ring.opacity * share
        if alpha >= 1:
            radius: int = _stepped(round(ring.radius), sprites.looks.planet.field_ring_radius_step)
            _blit_ring(surface, sprites, center, radius, alpha)


def _blit_ring(
    surface: pygame.Surface,
    sprites: Sprites,
    center: tuple[int, int],
    radius: int,
    alpha: float,
) -> None:
    """Blit the ring image for `radius` at `alpha` (0..255), centered on `center`."""
    image: pygame.Surface = _ring_image(sprites, radius)
    image.set_alpha(round(alpha))
    surface.blit(image, (center[0] - radius, center[1] - radius))


def _stepped(radius: int, step: int) -> int:
    """Return `radius` rounded to the nearest multiple of `step`."""
    return round(radius / step) * step


def _ring_image(sprites: Sprites, radius: int) -> pygame.Surface:
    """Return the ring outline of `radius` px in the ring color, built once."""
    rings = sprites.looks.planet
    color: tuple[int, int, int] = rings.field_ring_color
    width: int = rings.field_ring_width
    return sprites.built(
        ("planet_ring", radius, width, color), lambda: _build_ring(radius, width, color)
    )


def _build_ring(radius: int, width: int, color: tuple[int, int, int]) -> pygame.Surface:
    """Draw one ring outline on an 8-bit square of side 2 x radius + 1.

    Palette entry 0 is the transparent color key and entry 1 the ring color, so the image takes
    one byte a pixel, a quarter of an RGBA one. Its fade is the surface alpha set at blit time.
    """
    image: pygame.Surface = pygame.Surface((2 * radius + 1, 2 * radius + 1), 0, _PALETTE_BITS)
    image.set_palette_at(_CLEAR_INDEX, (0, 0, 0))
    image.set_palette_at(_RING_INDEX, color)
    image.set_colorkey(_CLEAR_INDEX)
    image.fill(_CLEAR_INDEX)
    pygame.draw.circle(image, image.unmap_rgb(_RING_INDEX), (radius, radius), radius, width)
    return image
