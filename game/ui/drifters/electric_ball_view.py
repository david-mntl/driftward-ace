"""The placeholder electric ball look: a purple ball, charge rays and outline, a firing circle.

Source: docs/contracts/systems/drifters/electric-ball/view.md;
drifters/10-electric-ball.md, placeholder_look (guess). It only draws.
"""

import logging
import math
from typing import Final

import pygame

from core.drifters.base import Drifter, DrifterType
from core.drifters.electric_ball import ElectricBall
from ui.drifters.registry import dim_color, register_view

log = logging.getLogger(__name__)

ELECTRIC_BALL_COLOR: Final[tuple[int, int, int]] = (170, 80, 255)
"""Ball color, RGB. Source: drifters/10-electric-ball.md, placeholder_look, ball (guess)."""

ELECTRIC_CHARGE_COLOR: Final[tuple[int, int, int]] = (200, 150, 255)
"""Charge rays and outline color, RGB. Source: drifters/10-electric-ball.md, placeholder_look,
Charge (guess)."""

ELECTRIC_FILL_COLOR: Final[tuple[int, int, int]] = (200, 160, 255)
"""Firing circle fill color, RGB. Source: drifters/10-electric-ball.md, placeholder_look, Fire
(guess)."""

ELECTRIC_RIM_COLOR: Final[tuple[int, int, int]] = (240, 220, 255)
"""Firing circle rim color, RGB. Source: drifters/10-electric-ball.md, placeholder_look, Fire
(guess)."""

FIRST_RAY_DEGREES: Final[float] = 45.0
"""Angle of the first ray, degrees counterclockwise on screen from pointing right.

Source: drifters/03-chain-lightning.md, ray_length (guess), reused for the electric ball.
"""

FULL_TURN_DEGREES: Final[float] = 360.0
"""Degrees in a full turn, to spread the rays evenly."""

MAX_ALPHA: Final[int] = 255
"""Opaque alpha, the scale `fill_opacity` multiplies."""

_Color = tuple[int, int, int]
_Key = tuple[int, int, int, _Color, _Color]

_IMAGES: dict[_Key, pygame.Surface] = {}
"""Built firing-circle images, keyed by (radius, rim px, alpha, fill color, rim color). The image
depends only on its key, so an entry is never stale."""


@register_view(DrifterType.ELECTRIC_BALL)
def render_electric_ball(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Draw the firing circle, the charge outline, the ball, then the rays, around `center`.

    Colors are times `brightness`. Raises TypeError when `drifter` is not an ElectricBall.
    """
    if not isinstance(drifter, ElectricBall):
        raise TypeError("render_electric_ball draws an ElectricBall")
    cx: int = round(center[0])
    cy: int = round(center[1])
    if drifter.pulse_fires():
        _draw_fire(surface, drifter, (cx, cy), scale, brightness)
    _draw_outline(surface, drifter, (cx, cy), scale, brightness)
    _draw_ball(surface, drifter, (cx, cy), scale, brightness)
    _draw_rays(surface, drifter, (cx, cy), scale, brightness)


def _draw_fire(
    surface: pygame.Surface,
    ball: ElectricBall,
    center: tuple[int, int],
    scale: float,
    brightness: float,
) -> None:
    """Blit the translucent firing circle with its rim, centered on `center`."""
    image: pygame.Surface = _fire_image(
        round(ball.pulse_radius * scale),
        max(1, round(ball.rim_width * scale)),
        round(MAX_ALPHA * ball.fill_opacity),
        dim_color(ELECTRIC_FILL_COLOR, brightness),
        dim_color(ELECTRIC_RIM_COLOR, brightness),
    )
    surface.blit(image, image.get_rect(center=center))


def _fire_image(
    radius: int, rim: int, alpha: int, fill_color: _Color, rim_color: _Color
) -> pygame.Surface:
    """Return the firing-circle image for these values, building it the first time."""
    key: _Key = (radius, rim, alpha, fill_color, rim_color)
    image: pygame.Surface | None = _IMAGES.get(key)
    if image is None:
        image = _build_fire_image(key)
        _IMAGES[key] = image
    return image


def _build_fire_image(key: _Key) -> pygame.Surface:
    """Draw the filled circle at `alpha`, then the opaque rim ring inside the same circle."""
    radius, rim, alpha, fill_color, rim_color = key
    image = pygame.Surface((2 * radius + 1, 2 * radius + 1), pygame.SRCALPHA)
    middle: tuple[int, int] = (radius, radius)
    pygame.draw.circle(image, (*fill_color, alpha), middle, radius)
    pygame.draw.circle(image, rim_color, middle, radius, rim)
    return image


def _draw_outline(
    surface: pygame.Surface,
    ball: ElectricBall,
    center: tuple[int, int],
    scale: float,
    brightness: float,
) -> None:
    """Draw the pulse circle's charge outline at `outline_level()` of full color. None at 0."""
    level: float = ball.outline_level()
    if level <= 0:
        return
    color: _Color = dim_color(ELECTRIC_CHARGE_COLOR, brightness * level)
    width: int = max(1, round(ball.outline_width * scale))
    pygame.draw.circle(surface, color, center, round(ball.pulse_radius * scale), width)


def _draw_ball(
    surface: pygame.Surface,
    ball: ElectricBall,
    center: tuple[int, int],
    scale: float,
    brightness: float,
) -> None:
    """Fill the ball, a disc `width` across."""
    color: _Color = dim_color(ELECTRIC_BALL_COLOR, brightness)
    pygame.draw.circle(surface, color, center, round(ball.width * scale / 2))


def _draw_rays(
    surface: pygame.Surface,
    ball: ElectricBall,
    center: tuple[int, int],
    scale: float,
    brightness: float,
) -> None:
    """Draw the charge rays: `charge_ray_count()` of them, evenly spread around the ball."""
    color: _Color = dim_color(ELECTRIC_CHARGE_COLOR, brightness)
    width: int = max(1, round(ball.ray_width * scale))
    edge: float = ball.width / 2 * scale
    tip: float = (ball.width / 2 + ball.ray_length) * scale
    for k in range(ball.charge_ray_count()):
        angle: float = math.radians(FIRST_RAY_DEGREES + k * FULL_TURN_DEGREES / ball.charge_rays)
        dx: float = math.cos(angle)
        dy: float = -math.sin(angle)
        start: tuple[float, float] = (center[0] + dx * edge, center[1] + dy * edge)
        end: tuple[float, float] = (center[0] + dx * tip, center[1] + dy * tip)
        pygame.draw.line(surface, color, start, end, width)
