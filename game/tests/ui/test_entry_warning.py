"""Entry warning sign. Contract: docs/contracts/systems/drifters.md, Presentation, Entry warning.

Every warning is the same plain sign, whatever the drifter, and it stays inside the warning size.
Source: 07-drifters.md, entry_warning_look, entry_warning_color, entry_warning_size (guess).
"""

import math
from types import SimpleNamespace
from typing import cast

import pygame

from core.drifters.base import ENTRY_WARNING_SIZE, Drifter
from ui.drifters import entry_warning

SIDE: int = 2 * math.ceil(ENTRY_WARNING_SIZE / 2) + 1
"""px, the image's side."""


def _distance_from_center(image: pygame.Surface, x: int, y: int) -> float:
    return math.hypot(x - image.get_width() // 2, y - image.get_height() // 2)


def test_the_sign_image_has_the_warning_size() -> None:
    assert entry_warning._sign_image().get_size() == (SIDE, SIDE)


def test_nothing_is_drawn_past_the_warning_radius() -> None:
    image: pygame.Surface = entry_warning._sign_image()
    radius: float = ENTRY_WARNING_SIZE / 2

    for x in range(image.get_width()):
        for y in range(image.get_height()):
            if image.get_at((x, y)).a > 0:
                assert _distance_from_center(image, x, y) <= radius + 0.5


def test_the_sign_is_drawn_in_the_warning_color() -> None:
    image: pygame.Surface = entry_warning._sign_image()
    opaque: list[pygame.Color] = [
        image.get_at((x, y))
        for x in range(image.get_width())
        for y in range(image.get_height())
        if image.get_at((x, y)).a == 255
    ]

    assert opaque
    for color in opaque:
        assert (color.r, color.g, color.b) == entry_warning.ENTRY_WARNING_COLOR


def test_the_mark_is_opaque_on_the_middle_column_and_the_fill_is_see_through_beside_it() -> None:
    image: pygame.Surface = entry_warning._sign_image()
    middle: int = SIDE // 2

    column: list[int] = [image.get_at((middle, y)).a for y in range(SIDE)]
    beside: int = image.get_at((middle + 4, middle + 2)).a

    assert column.count(255) >= 6
    assert 0 < beside < 255


def test_every_drifter_draws_the_same_sign_centered_on_its_warning_center() -> None:
    drifter: Drifter = cast(Drifter, SimpleNamespace(warning_center=lambda: (100.4, 12.0)))
    surface: pygame.Surface = pygame.Surface((200, 50), pygame.SRCALPHA)

    entry_warning.draw_entry_warning(surface, drifter)

    image: pygame.Surface = entry_warning._sign_image()
    left: int = 100 - SIDE // 2
    top: int = 12 - SIDE // 2
    for x in range(SIDE):
        for y in range(SIDE):
            assert surface.get_at((left + x, top + y)) == image.get_at((x, y))
