"""The placeholder coin look: a two-tone crystal with a rim, a ring across it and a rare glint.

Source: docs/contracts/systems/drifters.md, Presentation, Coin; drifters/04-coin.md, palette and
placeholder_look (guess). Everything is drawn on whole pixels. It only draws.
"""

import logging
from typing import Final

import pygame

from core.drifters.base import Drifter, DrifterType
from core.drifters.coin import Coin
from ui.drifters.registry import dim_color, register_view

log = logging.getLogger(__name__)

type Point = tuple[int, int]
"""A whole-pixel screen point (x, y)."""

COIN_LIT_COLOR: Final[tuple[int, int, int]] = (200, 30, 90)
"""Crystal lit side, RGB. Source: drifters/04-coin.md, palette (guess)."""

COIN_SHADE_COLOR: Final[tuple[int, int, int]] = (70, 0, 60)
"""Crystal shade side, RGB. Source: drifters/04-coin.md, palette (guess)."""

COIN_RIM_COLOR: Final[tuple[int, int, int]] = (255, 80, 150)
"""Crystal rim and ring, RGB. Source: drifters/04-coin.md, palette (guess)."""

COIN_GLINT_COLOR: Final[tuple[int, int, int]] = (255, 220, 240)
"""The rare coin's glint, RGB. Source: drifters/04-coin.md, palette (guess)."""

COIN_LINE_WIDTH: Final[int] = 1
"""Rim and ring line width, px. Source: drifters/04-coin.md, placeholder_look (guess)."""


@register_view(DrifterType.COIN)
def render_coin(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
    brightness: float,
) -> None:
    """Draw the coin centered on the rounded `center`: sides, rim, ring, then the glint.

    Every pixel lies inside the crystal's and the ring's boxes. Colors are times `brightness`.
    Raises TypeError when `drifter` is not a Coin, ValueError when `scale` is not 1.0.
    """
    if not isinstance(drifter, Coin):
        raise TypeError("render_coin draws a Coin")
    if scale != 1.0:
        raise ValueError("render_coin draws at full size only")
    cx: int = round(center[0])
    cy: int = round(center[1])
    half_width: int = round(drifter.width / 2)
    half_height: int = round(drifter.height / 2)
    half_body: int = round(drifter.body_height / 2)
    _draw_sides(surface, brightness, (cx, cy), (half_width, half_height, half_body))
    _draw_rim(surface, brightness, (cx, cy), (half_width, half_height, half_body))
    _draw_ring(surface, brightness, (cx, cy), drifter)
    if drifter.glint:
        _draw_glint(surface, brightness, (cx, cy), drifter)


def _draw_sides(
    surface: pygame.Surface, brightness: float, center: Point, half: tuple[int, int, int]
) -> None:
    """Fill the lit left half and the shade right half of the crystal."""
    cx, cy = center
    half_width, half_height, half_body = half
    lit: list[Point] = [
        (cx - 1, cy - half_height),
        (cx - half_width, cy - half_body),
        (cx - half_width, cy + half_body - 1),
        (cx - 1, cy + half_height - 1),
    ]
    shade: list[Point] = [
        (cx, cy - half_height),
        (cx + half_width - 1, cy - half_body),
        (cx + half_width - 1, cy + half_body - 1),
        (cx, cy + half_height - 1),
    ]
    pygame.draw.polygon(surface, dim_color(COIN_LIT_COLOR, brightness), lit)
    pygame.draw.polygon(surface, dim_color(COIN_SHADE_COLOR, brightness), shade)


def _draw_rim(
    surface: pygame.Surface, brightness: float, center: Point, half: tuple[int, int, int]
) -> None:
    """Outline the crystal through its eight corners, clockwise from the top."""
    cx, cy = center
    half_width, half_height, half_body = half
    corners: list[Point] = [
        (cx - 1, cy - half_height),
        (cx, cy - half_height),
        (cx + half_width - 1, cy - half_body),
        (cx + half_width - 1, cy + half_body - 1),
        (cx, cy + half_height - 1),
        (cx - 1, cy + half_height - 1),
        (cx - half_width, cy + half_body - 1),
        (cx - half_width, cy - half_body),
    ]
    pygame.draw.polygon(
        surface, dim_color(COIN_RIM_COLOR, brightness), corners, width=COIN_LINE_WIDTH
    )


def _draw_ring(surface: pygame.Surface, brightness: float, center: Point, coin: Coin) -> None:
    """Draw the ring's ellipse over the crystal, centered on `center`."""
    rect: pygame.Rect = pygame.Rect(
        center[0] - coin.ring_width // 2,
        center[1] - coin.ring_height // 2,
        coin.ring_width,
        coin.ring_height,
    )
    pygame.draw.ellipse(surface, dim_color(COIN_RIM_COLOR, brightness), rect, width=COIN_LINE_WIDTH)


def _draw_glint(surface: pygame.Surface, brightness: float, center: Point, coin: Coin) -> None:
    """Fill the glint square, placed from the crystal box's top-left corner."""
    left: int = center[0] - round(coin.width / 2) + coin.glint_left
    top: int = center[1] - round(coin.height / 2) + coin.glint_top
    pygame.draw.rect(
        surface,
        dim_color(COIN_GLINT_COLOR, brightness),
        pygame.Rect(left, top, coin.glint_size, coin.glint_size),
    )
