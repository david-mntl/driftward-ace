"""The fireball look: one strip, its head on the hitbox's head, the small variant scaled down.

Source: drifters/06-fireball.md, look and hitbox; 12-art-and-audio.md, rules 9 and 13. The art
flies down and to the right, head at `art_head_center`, tail behind it up and to the left. A
fireball flying the other way (`invert`) is mirrored, so its head center lands on the mirrored
point. The art is drawn for the head width `art_head_width`; a smaller head scales the whole
frame by head width over that, once, when the sprites load. The frames loop in game ticks,
offset by uid. It only draws.
"""

import logging

import pygame

from core.collision import Circle, Hitbox
from core.drifters.base import Drifter, DrifterType
from core.drifters.fireball import Fireball
from core.drifters.tuning import DrifterTuning
from ui.drifters.looks import FireballLooks, StripRule
from ui.drifters.registry import register_view
from ui.drifters.sprites import Sprites, installed_sprites, scaled_size, strip_frame

log = logging.getLogger(__name__)


@register_view(DrifterType.FIREBALL)
def render_fireball(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Blit the fireball's frame so the art's head center lands on the head circle's center.

    The head is `drifter.hitbox[0]`. The frame is scaled by head width over `art_head_width`,
    times `scale`. Mirrored with `invert`: the head center is then `frame width - art x`. Colors
    are times `brightness`. Raises TypeError when `drifter` is not a Fireball or its hitbox is
    not exactly two circles.
    """
    if not isinstance(drifter, Fireball):
        raise TypeError("render_fireball draws a Fireball")
    head: Circle = _head_of(drifter.hitbox)
    sprites: Sprites = installed_sprites()
    looks: FireballLooks = sprites.looks.fireball
    rule: StripRule = looks.strip
    factor: float = 2 * head.r * scale / looks.art_head_width
    index: int = strip_frame(
        rule, sprites.seed(drifter.uid), drifter.ticks_in_phase, sprites.count(rule)
    )
    image: pygame.Surface = sprites.image(
        rule,
        index,
        sprites.level(brightness),
        mirror=drifter.invert,
        size=scaled_size(rule, factor),
    )
    anchor_x: float = looks.art_head_center[0] * image.get_width() / rule.frame_w
    anchor_y: float = looks.art_head_center[1] * image.get_height() / rule.frame_h
    if drifter.invert:
        anchor_x = image.get_width() - anchor_x
    surface.blit(
        image,
        (
            round(center[0] + head.cx * scale - anchor_x),
            round(center[1] + head.cy * scale - anchor_y),
        ),
    )


def warm(sprites: Sprites, tuning: DrifterTuning) -> None:
    """Build every frame for every variant's head width, both ways round, at every warm level."""
    looks: FireballLooks = sprites.looks.fireball
    fireball = tuning.drifters.get(DrifterType.FIREBALL)
    if fireball is None:
        return
    for variant in fireball.variants.values():
        head: Circle = _head_of(variant.hitbox)
        size = scaled_size(looks.strip, 2 * head.r / looks.art_head_width)
        for level in sprites.warm_levels:
            for index in range(sprites.count(looks.strip)):
                for mirror in (False, True):
                    sprites.image(looks.strip, index, level, mirror=mirror, size=size)


def _head_of(hitbox: Hitbox) -> Circle:
    """Return the first circle of a head-then-tail hitbox. Raises TypeError for any other shape."""
    if len(hitbox) != 2 or not isinstance(hitbox[0], Circle) or not isinstance(hitbox[1], Circle):
        raise TypeError("render_fireball draws two circles, head then tail")
    return hitbox[0]
