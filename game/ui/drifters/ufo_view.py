"""The UFO look: one strip from a pool, picked per UFO, the disc and dome sitting on the hitbox.

Source: drifters/07-ufo.md, look and hitbox; 12-art-and-audio.md, rules 9, 10 and 13. Each UFO
keeps the look its seed picks. The frames play in the strip's order (a loop, or a random order that
never repeats a frame twice in a row), counted in game ticks and offset by uid. The art is a disc
in its bottom rows with the dome above; a UFO flying left (`invert`) is mirrored. It only draws.
"""

import logging

import pygame

from core.collision import Box, Circle, Hitbox
from core.drifters.base import Drifter, DrifterType
from core.drifters.tuning import DrifterTuning
from core.drifters.ufo import Ufo
from ui.drifters.looks import StripRule
from ui.drifters.registry import register_view
from ui.drifters.sprites import Sprites, installed_sprites, pick, scaled_size, strip_frame

log = logging.getLogger(__name__)


@register_view(DrifterType.UFO)
def render_ufo(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Blit the UFO's frame so its disc fills `drifter.hitbox[0]` and the dome sits above it.

    The frame's bottom edge is the disc's bottom edge and its middle column is the disc's middle,
    so the 40 x 20 art lands on the 40 x 10 disc and the dome circle. Scaled by `scale`, dimmed
    to `brightness`. Raises TypeError when `drifter` is not a Ufo or its hitbox is not a box then
    a circle.
    """
    if not isinstance(drifter, Ufo):
        raise TypeError("render_ufo draws a Ufo")
    disc: Box = _disc(drifter)
    sprites: Sprites = installed_sprites()
    pool: tuple[StripRule, ...] = sprites.looks.ufo.looks
    rule: StripRule = pool[pick(sprites.seed(drifter.uid), len(pool))]
    index: int = strip_frame(
        rule, sprites.seed(drifter.uid), drifter.ticks_in_phase, sprites.count(rule)
    )
    image: pygame.Surface = sprites.image(
        rule,
        index,
        sprites.level(brightness),
        mirror=drifter.invert,
        size=scaled_size(rule, scale),
    )
    left: int = round(center[0] + disc.cx * scale - image.get_width() / 2)
    top: int = round(center[1] + disc.cy * scale + disc.h * scale / 2 - image.get_height())
    surface.blit(image, (left, top))


def warm(sprites: Sprites, tuning: DrifterTuning) -> None:
    """Build every frame of every UFO look, both ways round, at every warm brightness."""
    for rule in sprites.looks.ufo.looks:
        for level in sprites.warm_levels:
            for index in range(sprites.count(rule)):
                for mirror in (False, True):
                    sprites.image(rule, index, level, mirror=mirror)


def _disc(drifter: Drifter) -> Box:
    """Return the disc box, or raise TypeError when the hitbox is not a box then a circle."""
    shapes: Hitbox = drifter.hitbox
    if len(shapes) != 2 or not isinstance(shapes[0], Box) or not isinstance(shapes[1], Circle):
        raise TypeError("render_ufo draws a box then a circle, disc then dome")
    return shapes[0]
