"""The coin look: the common or the rare strip by variant, a crystal with a turning galaxy.

Source: drifters/04-coin.md, look and hitbox; 12-art-and-audio.md, rules 9 and 13. The frame is
centered on the coin. The frames loop in game ticks, offset by uid, so a row of coins doesn't
turn together. It only draws.
"""

import logging

import pygame

from core.drifters.base import Drifter, DrifterType
from core.drifters.coin import Coin
from core.drifters.tuning import DrifterTuning
from ui.drifters.looks import StripRule
from ui.drifters.registry import register_view
from ui.drifters.sprites import Sprites, installed_sprites, scaled_size, strip_frame

log = logging.getLogger(__name__)


@register_view(DrifterType.COIN)
def render_coin(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Blit the coin's frame centered on the rounded `center`, scaled by `scale`.

    The rare coin (`glint` set by its variant) uses the rare strip, every other the common one.
    Colors are times `brightness`. Raises TypeError when `drifter` is not a Coin.
    """
    if not isinstance(drifter, Coin):
        raise TypeError("render_coin draws a Coin")
    sprites: Sprites = installed_sprites()
    rule: StripRule = _rule(sprites, drifter.glint)
    index: int = strip_frame(
        rule, sprites.seed(drifter.uid), drifter.ticks_in_phase, sprites.count(rule)
    )
    image: pygame.Surface = sprites.image(
        rule, index, sprites.level(brightness), size=scaled_size(rule, scale)
    )
    surface.blit(image, image.get_rect(center=(round(center[0]), round(center[1]))))


def warm(sprites: Sprites, tuning: DrifterTuning) -> None:
    """Build every frame of both coin strips at every warm brightness."""
    for rare in (False, True):
        rule: StripRule = _rule(sprites, rare)
        for level in sprites.warm_levels:
            for index in range(sprites.count(rule)):
                sprites.image(rule, index, level)


def _rule(sprites: Sprites, rare: bool) -> StripRule:
    """Return the rare strip for the rare coin, else the common one."""
    return sprites.looks.coin.rare if rare else sprites.looks.coin.common
