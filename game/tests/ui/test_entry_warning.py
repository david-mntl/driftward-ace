"""Entry warning size. Contract: docs/contracts/systems/drifters.md, Presentation, Entry warning.

Every warning is the same size, whatever the drifter, and its copy sits inside the glow.
Source: 07-drifters.md, entry_warning_size (guess).
"""

import math
from types import SimpleNamespace
from typing import cast

import pygame
import pytest

from core.collision import Box, Circle
from core.drifters.base import ENTRY_WARNING_SIZE, Drifter, DrifterType
from ui.drifters import entry_warning
from ui.drifters.registry import _view_for

GLOW_RADIUS: float = entry_warning.GLOW_RATIO * ENTRY_WARNING_SIZE / 2
"""px, from the glow's constants."""

SATELLITE_BLUE: tuple[int, int, int] = (60, 110, 220)
SATELLITE_WHITE: tuple[int, int, int] = (240, 240, 240)
METEORITE_GREY: tuple[int, int, int] = (140, 140, 140)


def _drifter(drifter_type: DrifterType, width: float, height: float, tilt: float) -> Drifter:
    """Return a stand-in with the fields the warning reads."""
    hitbox: tuple[Box | Circle, ...] = (
        (Box(0, 0, 12, 12), Box(0, 0, width, 6))
        if drifter_type is DrifterType.SATELLITE
        else (Circle(0, 0, width / 2),)
    )
    stand_in: SimpleNamespace = SimpleNamespace(
        uid=7,
        drifter_type=drifter_type,
        variant="test",
        width=width,
        height=height,
        hitbox=hitbox,
        warning_tilt_degrees=lambda: tilt,
        warning_copy=lambda: stand_in,
    )
    return cast(Drifter, stand_in)


CASES: list[tuple[DrifterType, float, float, float]] = [
    (DrifterType.METEORITE, 20, 20, 0.0),
    (DrifterType.METEORITE, 28, 28, 0.0),
    (DrifterType.METEORITE, 40, 40, 0.0),
    (DrifterType.SATELLITE, 36, 12, 0.0),
    (DrifterType.SATELLITE, 36, 12, 20.0),
    (DrifterType.SATELLITE, 36, 12, -20.0),
]


def _image(case: tuple[DrifterType, float, float, float]) -> pygame.Surface:
    drifter_type, width, height, tilt = case
    drifter: Drifter = _drifter(drifter_type, width, height, tilt)
    return entry_warning._build_image(drifter, _view_for(drifter_type))


def _distance_from_center(image: pygame.Surface, x: int, y: int) -> float:
    return math.hypot(x - image.get_width() // 2, y - image.get_height() // 2)


@pytest.mark.parametrize("case", CASES)
def test_every_warning_image_is_the_same_size(
    case: tuple[DrifterType, float, float, float],
) -> None:
    side: int = 2 * math.ceil(ENTRY_WARNING_SIZE / 2) + 1

    assert _image(case).get_size() == (side, side)


@pytest.mark.parametrize("case", CASES)
def test_nothing_is_drawn_past_the_warning_radius(
    case: tuple[DrifterType, float, float, float],
) -> None:
    image: pygame.Surface = _image(case)
    radius: float = ENTRY_WARNING_SIZE / 2

    for x in range(image.get_width()):
        for y in range(image.get_height()):
            if image.get_at((x, y)).a > 0:
                assert _distance_from_center(image, x, y) <= radius + 0.5


@pytest.mark.parametrize("case", CASES)
def test_the_copy_sits_inside_the_glow(case: tuple[DrifterType, float, float, float]) -> None:
    image: pygame.Surface = _image(case)
    copy_colors: set[tuple[int, int, int]] = {SATELLITE_BLUE, SATELLITE_WHITE, METEORITE_GREY}

    for x in range(image.get_width()):
        for y in range(image.get_height()):
            color: pygame.Color = image.get_at((x, y))
            if (color.r, color.g, color.b) in copy_colors:
                assert _distance_from_center(image, x, y) <= GLOW_RADIUS
