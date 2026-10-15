"""The placeholder meteorite look: a grey disc as wide as the drifter.

Source: docs/contracts/systems/drifters.md, Presentation, Meteorite; drifters/01-meteorite.md,
placeholder_look (guess). It only draws.
"""

import logging
from typing import Final

import pygame

from core.drifters.base import Drifter, DrifterType
from ui.drifters.registry import register_view

log = logging.getLogger(__name__)

METEORITE_COLOR: Final[tuple[int, int, int]] = (140, 140, 140)
"""Disc color, RGB. Source: drifters/01-meteorite.md, placeholder_look (guess)."""


@register_view(DrifterType.METEORITE)
def render_meteorite(
    surface: pygame.Surface,
    drifter: Drifter,
    center: tuple[float, float],
    scale: float,
) -> None:
    """Draw a filled disc of diameter `drifter.width * scale` px at `center`, rounded to px."""
    pygame.draw.circle(
        surface,
        METEORITE_COLOR,
        (round(center[0]), round(center[1])),
        round(drifter.width * scale / 2),
    )
