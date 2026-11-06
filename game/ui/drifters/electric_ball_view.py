"""The electric ball look: a charging ball with code-drawn rays and outline, then a firing ring.

Source: docs/contracts/systems/drifters/electric-ball/view.md; drifters/10-electric-ball.md, look;
12-art-and-audio.md, rules 9 and 13. Core says what shows: `pulse_fires()` draws the firing ring
and the fire ball; otherwise the charge ball shows, its frames speeding up as the charge fills,
with `charge_ray_count()` rays and the pulse circle's outline at `outline_level()`. Frames count
game ticks, offset by uid. The rays and the outline are drawn once and cached. It only draws.
"""

import logging
from typing import Final

import pygame

from core.drifters.base import Drifter, DrifterType
from core.drifters.electric_ball import (
    ElectricBall,
    ElectricBallTypeExtra,
    ElectricBallVariantExtra,
)
from core.drifters.tuning import DrifterTuning
from ui.drifters.looks import ElectricBallLooks, StripRule
from ui.drifters.rays import blit_centered, rays_image
from ui.drifters.registry import dim_color, register_view
from ui.drifters.sprites import Sprites, eased_frame, installed_sprites, scaled_size, strip_frame

log = logging.getLogger(__name__)

_Color = tuple[int, int, int]

_RING_SALT: Final[int] = 7
"""Added to the uid for the ring's frame order, so the ring and the ball don't flicker together."""


@register_view(DrifterType.ELECTRIC_BALL)
def render_electric_ball(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Draw the firing ring and the fire ball, or the outline, the charge ball and the rays.

    Everything is centered on the rounded `center`, scaled by `scale`; colors are times
    `brightness`. Raises TypeError when `drifter` is not an ElectricBall.
    """
    if not isinstance(drifter, ElectricBall):
        raise TypeError("render_electric_ball draws an ElectricBall")
    sprites: Sprites = installed_sprites()
    looks: ElectricBallLooks = sprites.looks.electric_ball
    level: int = sprites.level(brightness)
    middle: tuple[int, int] = (round(center[0]), round(center[1]))
    if drifter.pulse_fires():
        _draw_fire(surface, sprites, drifter, middle, scale, level)
        return
    _draw_outline(surface, sprites, drifter, middle, scale, level)
    _blit(surface, sprites, looks.charge, _charge_frame(sprites, drifter), middle, scale, level)
    _draw_rays(surface, sprites, drifter, middle, scale, level)


def warm(sprites: Sprites, tuning: DrifterTuning) -> None:
    """Build the strips, the ring at every pulse radius, and the rays and outline of every count."""
    looks: ElectricBallLooks = sprites.looks.electric_ball
    for level in sprites.warm_levels:
        for rule in (looks.charge, looks.fire):
            for index in range(sprites.count(rule)):
                sprites.image(rule, index, level)
    electric = tuning.drifters.get(DrifterType.ELECTRIC_BALL)
    if electric is None or not isinstance(electric.extra, ElectricBallTypeExtra):
        return
    extra: ElectricBallTypeExtra = electric.extra
    for variant in electric.variants.values():
        if not isinstance(variant.extra, ElectricBallVariantExtra):
            continue
        size = scaled_size(looks.ring, 2 * variant.extra.pulse_radius / looks.ring.frame_w)
        for level in sprites.warm_levels:
            for index in range(sprites.count(looks.ring)):
                sprites.image(looks.ring, index, level, size=size)
            for count in range(1, extra.charge_rays + 1):
                _rays(
                    sprites,
                    (count, extra.charge_rays),
                    (variant.width, extra.ray_length, extra.ray_width),
                    1.0,
                    level,
                )
                _outline(
                    sprites,
                    round(variant.extra.pulse_radius),
                    max(1, round(extra.outline_width)),
                    count / extra.charge_rays,
                    level,
                )


def _draw_fire(
    surface: pygame.Surface,
    sprites: Sprites,
    ball: ElectricBall,
    middle: tuple[int, int],
    scale: float,
    level: int,
) -> None:
    """Blit the firing ring at twice the pulse radius, then the fire ball over it."""
    looks: ElectricBallLooks = sprites.looks.electric_ball
    ring: StripRule = looks.ring
    ring_index: int = strip_frame(
        ring, sprites.seed(ball.uid) + _RING_SALT, ball.ticks_in_phase, sprites.count(ring)
    )
    image: pygame.Surface = sprites.image(
        ring,
        ring_index,
        level,
        size=scaled_size(ring, 2 * ball.pulse_radius * scale / ring.frame_w),
    )
    surface.blit(image, image.get_rect(center=middle))
    fire: StripRule = looks.fire
    fire_index: int = strip_frame(
        fire, sprites.seed(ball.uid), ball.ticks_in_phase, sprites.count(fire)
    )
    _blit(surface, sprites, fire, fire_index, middle, scale, level)


def _charge_frame(sprites: Sprites, ball: ElectricBall) -> int:
    """Return the charge strip's frame: its speed eases up as the cycle's charge fills."""
    looks: ElectricBallLooks = sprites.looks.electric_ball
    return eased_frame(
        looks.charge,
        looks.charge_ticks_per_frame_end,
        sprites.seed(ball.uid),
        ball.cycle_tick(),
        ball.charge_ticks,
        sprites.count(looks.charge),
    )


def _blit(
    surface: pygame.Surface,
    sprites: Sprites,
    rule: StripRule,
    index: int,
    middle: tuple[int, int],
    scale: float,
    level: int,
) -> None:
    """Blit frame `index` of `rule` centered on `middle`, scaled by `scale`."""
    image: pygame.Surface = sprites.image(rule, index, level, size=scaled_size(rule, scale))
    surface.blit(image, image.get_rect(center=middle))


def _draw_outline(
    surface: pygame.Surface,
    sprites: Sprites,
    ball: ElectricBall,
    middle: tuple[int, int],
    scale: float,
    level: int,
) -> None:
    """Blit the pulse circle's charge outline at `outline_level()` of full color. None at 0."""
    share: float = ball.outline_level()
    if share <= 0:
        return
    image: pygame.Surface = _outline(
        sprites,
        round(ball.pulse_radius * scale),
        max(1, round(ball.outline_width * scale)),
        share,
        level,
    )
    blit_centered(surface, image, middle)


def _outline(sprites: Sprites, radius: int, width: int, share: float, level: int) -> pygame.Surface:
    """Return the outline circle of `radius` px in the outline color, at `share` and `level`."""
    color: _Color = dim_color(
        sprites.shade(sprites.looks.electric_ball.outline_color, level), share
    )
    return sprites.built(
        ("ball_outline", radius, width, color), lambda: _build_outline(radius, width, color)
    )


def _build_outline(radius: int, width: int, color: _Color) -> pygame.Surface:
    """Draw the outline ring on a transparent square of side 2 x radius + 1."""
    image: pygame.Surface = pygame.Surface((2 * radius + 1, 2 * radius + 1), pygame.SRCALPHA)
    pygame.draw.circle(image, color, (radius, radius), radius, width)
    return image


def _draw_rays(
    surface: pygame.Surface,
    sprites: Sprites,
    ball: ElectricBall,
    middle: tuple[int, int],
    scale: float,
    level: int,
) -> None:
    """Blit the charge rays: `charge_ray_count()` of them, evenly spread around the ball."""
    count: int = ball.charge_ray_count()
    if count == 0:
        return
    image: pygame.Surface = _rays(
        sprites,
        (count, ball.charge_rays),
        (ball.width, ball.ray_length, ball.ray_width),
        scale,
        level,
    )
    blit_centered(surface, image, middle)


def _rays(
    sprites: Sprites,
    counts: tuple[int, int],
    body: tuple[float, float, float],
    scale: float,
    level: int,
) -> pygame.Surface:
    """Return the image of `counts` = (rays shown, most rays) for a ball of `body` = (width, ray
    length, ray width), px, in the ray color at `level`."""
    return rays_image(
        sprites,
        count=counts[0],
        total=counts[1],
        edge=body[0] / 2,
        length=body[1],
        width=body[2],
        scale=scale,
        color=sprites.shade(sprites.looks.electric_ball.ray_color, level),
    )
