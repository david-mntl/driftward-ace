"""The meteorite look: a turning rock, one of a pool of skins, scaled to its variant.

Source: drifters/01-meteorite.md, looks; 12-art-and-audio.md, rules 9, 10 and 13. Each rock keeps
the skin its seed picks and loops its 8 turn frames in game ticks, starting at a frame set by the
seed (each rock starts at a random frame). The art was drawn for a hit circle `art_hitbox_width`
wide, so a rock is scaled by its width over that, once, when the sprites load. The art is wider
than the hit circle and has bites in it on purpose: the circle may poke out of the rock in places.
It only draws.
"""

import logging

import pygame

from core.drifters.base import Drifter, DrifterType
from core.drifters.tuning import DrifterTuning
from ui.drifters.looks import MeteoriteLooks, StripRule
from ui.drifters.registry import register_view
from ui.drifters.sprites import Sprites, installed_sprites, pick, scaled_size, strip_frame

log = logging.getLogger(__name__)


@register_view(DrifterType.METEORITE)
def render_meteorite(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Blit the rock's frame centered on the rounded `center`.

    The frame is scaled by `drifter.width * scale / art_hitbox_width`; colors are times
    `brightness`.
    """
    sprites: Sprites = installed_sprites()
    looks: MeteoriteLooks = sprites.looks.meteorite
    seed: int = sprites.seed(drifter.uid)
    rule: StripRule = looks.looks[pick(seed, len(looks.looks))]
    index: int = strip_frame(rule, seed, drifter.ticks_in_phase, sprites.count(rule))
    image: pygame.Surface = sprites.image(
        rule,
        index,
        sprites.level(brightness),
        size=scaled_size(rule, drifter.width * scale / looks.art_hitbox_width),
    )
    surface.blit(image, image.get_rect(center=(round(center[0]), round(center[1]))))


def warm(sprites: Sprites, tuning: DrifterTuning) -> None:
    """Build every frame of every skin at every variant's size and every warm brightness."""
    looks: MeteoriteLooks = sprites.looks.meteorite
    meteorite = tuning.drifters.get(DrifterType.METEORITE)
    if meteorite is None:
        return
    for variant in meteorite.variants.values():
        for rule in looks.looks:
            size = scaled_size(rule, variant.width / looks.art_hitbox_width)
            for level in sprites.warm_levels:
                for index in range(sprites.count(rule)):
                    sprites.image(rule, index, level, size=size)
