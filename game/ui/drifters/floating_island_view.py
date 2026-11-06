"""The floating island look: the island's shape cut out of a ground image, grass on top.

Source: drifters/05-floating-islands.md, art_canvas and rule 10; 12-art-and-audio.md, rule 10.
Each island picks one ground image by its seed. The island's own size is cut from the middle of
that image (a 320 x 120 island is the whole image, the 120 x 120 box its centered crop), and the
hitbox shapes (boxes, polygons) are the mask, so what is drawn is exactly what blocks the ship.
`invert` is already in the hitbox, so it flips the shape and never the ground: the grass stays on
top. One image is built per ground, shape and size when the sprites load. It only draws.
"""

import logging

import pygame

from core.collision import Hitbox, place_hitbox
from core.drifters.base import Drifter, DrifterType
from core.drifters.floating_island import (
    INVERTIBLE_SHAPES,
    FloatingIsland,
    IslandTypeExtra,
    IslandVariantExtra,
    island_hitbox,
)
from core.drifters.tuning import DrifterTuning
from ui.drifters.registry import register_view
from ui.drifters.sprites import Sprites, installed_sprites, pick
from ui.shapes import draw_shape

log = logging.getLogger(__name__)

_WHITE: tuple[int, int, int] = (255, 255, 255)
"""The mask's color: multiplying by white keeps a pixel, by transparent clears it."""


@register_view(DrifterType.FLOATING_ISLAND)
def render_floating_island(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Blit the island's image with its top-left at the rounded `center` less half its size.

    Every pixel lies inside the hitbox shapes. Colors are times `brightness`. Raises TypeError
    when `drifter` is not a FloatingIsland, ValueError when `scale` is not 1.0.
    """
    if not isinstance(drifter, FloatingIsland):
        raise TypeError("render_floating_island draws a FloatingIsland")
    if scale != 1.0:
        raise ValueError("render_floating_island draws at full size only")
    sprites: Sprites = installed_sprites()
    image: pygame.Surface = _island_image(
        sprites,
        pick(sprites.seed(drifter.uid), sprites.ground_count()),
        drifter.hitbox,
        (drifter.width, drifter.height),
        sprites.level(brightness),
    )
    left: int = round(center[0] - drifter.width / 2)
    top: int = round(center[1] - drifter.height / 2)
    surface.blit(image, (left, top))


def warm(sprites: Sprites, tuning: DrifterTuning) -> None:
    """Build the image of every ground for every variant's shape, inverted where it may be."""
    island = tuning.drifters.get(DrifterType.FLOATING_ISLAND)
    if island is None or not isinstance(island.extra, IslandTypeExtra):
        return
    for variant in island.variants.values():
        if not isinstance(variant.extra, IslandVariantExtra):
            continue
        shape = variant.extra.shape
        for invert in (False, True) if shape in INVERTIBLE_SHAPES else (False,):
            hitbox: Hitbox = island_hitbox(
                shape, variant.width, variant.height, island.extra.arm, invert
            )
            for look in range(sprites.ground_count()):
                _island_image(sprites, look, hitbox, (variant.width, variant.height), sprites.steps)


def _island_image(
    sprites: Sprites,
    look: int,
    hitbox: Hitbox,
    size: tuple[float, float],
    level: int,
) -> pygame.Surface:
    """Return the island's image for this ground, hitbox, size and brightness, built once."""
    return sprites.built(
        ("island", look, hitbox, size, level),
        lambda: _build_image(sprites, look, hitbox, size, level),
    )


def _build_image(
    sprites: Sprites, look: int, hitbox: Hitbox, size: tuple[float, float], level: int
) -> pygame.Surface:
    """Cut the island's size from the middle of the ground, then clear everything off the shapes.

    Raises ValueError when the island is bigger than the ground image.
    """
    width, height = round(size[0]), round(size[1])
    ground: pygame.Surface = sprites.ground(look)
    ground_w, ground_h = ground.get_size()
    if width > ground_w or height > ground_h:
        raise ValueError(
            f"island {width}x{height} px is bigger than its ground image {ground_w}x{ground_h} px"
        )
    area: pygame.Rect = pygame.Rect(
        (ground_w - width) // 2, (ground_h - height) // 2, width, height
    )
    image: pygame.Surface = ground.subsurface(area).copy()
    mask: pygame.Surface = pygame.Surface((width, height), pygame.SRCALPHA)
    for shape in place_hitbox(hitbox, size[0] / 2, size[1] / 2):
        draw_shape(mask, _WHITE, shape)
    image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    if level != sprites.steps:
        value: tuple[int, int, int] = sprites.shade(_WHITE, level)
        image.fill((*value, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return image
