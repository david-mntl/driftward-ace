"""The placeholder meteorite look: a grey disc as wide as the object.

Source: docs/contracts/systems/objects.md, Presentation, Meteorite; objects/01-meteorite.md,
placeholder_look (guess). It only draws.
"""

import logging
from typing import Final

import pygame

from core.objects.base import GameObject, ObjectType
from ui.objects.registry import register_view

log = logging.getLogger(__name__)

METEORITE_COLOR: Final[tuple[int, int, int]] = (140, 140, 140)
"""Disc color, RGB. Source: objects/01-meteorite.md, placeholder_look (guess)."""


@register_view(ObjectType.METEORITE)
def render_meteorite(
    surface: pygame.Surface,
    obj: GameObject,
    center: tuple[float, float],
    scale: float,
) -> None:
    """Draw a filled disc of diameter `obj.width * scale` px at `center`, rounded to px."""
    pygame.draw.circle(
        surface,
        METEORITE_COLOR,
        (round(center[0]), round(center[1])),
        round(obj.width * scale / 2),
    )
