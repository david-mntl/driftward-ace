"""Ship view tests. Contract: docs/contracts/systems/ship.md, Presentation.

The ship is drawn as exactly its hitbox, an inverted T: what you see is what can be hit
(Pillar 2). Pixels are read from the surface with `pygame.image.tobytes`, never from the
code under test. Every expected number is copied from the GDD below.
"""

import pygame
import pytest

from core.ship import Ship, spawn
from ui.ship_view import draw_ship

SURFACE_SIZE: tuple[int, int] = (640, 480)
"""Test surface. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

BLACK: tuple[int, int, int] = (0, 0, 0)
"""Source: 12-art-and-audio.md, placeholder_bg (guess)."""

WHITE: tuple[int, int, int] = (255, 255, 255)
"""Source: 04-ship.md, placeholder_look (guess)."""

SHIP_W: int = 32
"""Source: 04-ship.md, ship_w (guess)."""

SHIP_H: int = 32
"""Source: 04-ship.md, ship_h (guess)."""

BAR_W: int = 12
"""Source: 04-ship.md, hitbox: a bar 12 px wide (guess)."""

FOOT_H: int = 12
"""Source: 04-ship.md, hitbox: a foot 12 px tall (guess)."""

SPAWN: tuple[float, float] = (320.0, 240.0)
"""Source: 05-lives-and-damage.md, fall_respawn (locked)."""

Pixel = tuple[int, int]


def _white_pixels(ship: Ship) -> set[Pixel]:
    """Draw `ship` on a black surface and return the (x, y) of every non-black pixel."""
    surface = pygame.Surface(SURFACE_SIZE)
    surface.fill(BLACK)
    draw_ship(surface, ship)
    width, height = surface.get_size()
    data = pygame.image.tobytes(surface, "RGB")
    found: set[Pixel] = set()
    for y in range(height):
        for x in range(width):
            i = (y * width + x) * 3
            pixel = (data[i], data[i + 1], data[i + 2])
            if pixel == WHITE:
                found.add((x, y))
            else:
                assert pixel == BLACK, f"pixel ({x}, {y}) is {pixel}, neither white nor black"
    return found


def _rect(left: int, top: int, width: int, height: int) -> set[Pixel]:
    return {(x, y) for y in range(top, top + height) for x in range(left, left + width)}


@pytest.mark.usefixtures("pygame_headless")
def test_ship_at_spawn_is_drawn_as_exactly_its_hitbox() -> None:
    ship = spawn()
    assert (ship.x, ship.y) == SPAWN

    white = _white_pixels(ship)

    bar = _rect(314, 224, BAR_W, SHIP_H)  # x 314 to 325, rows 224 to 255
    foot = _rect(304, 244, SHIP_W, FOOT_H)  # x 304 to 335, rows 244 to 255
    assert white == bar | foot
    assert len(white) == 624
    # Both upper corners of the 32 x 32 square stay black.
    assert (304, 224) not in white
    assert (335, 224) not in white
    assert (313, 243) not in white
    assert (326, 243) not in white


@pytest.mark.usefixtures("pygame_headless")
@pytest.mark.parametrize(
    ("x", "y"),
    [(320.5, 240.5), (320.25, 240.75), (101.5, 99.5)],
)
def test_ship_at_a_fractional_position_keeps_the_t_joined(x: float, y: float) -> None:
    white = _white_pixels(Ship(x=x, y=y, vx=0.0, vy=0.0))

    rows: dict[int, list[int]] = {}
    for px, py in white:
        rows.setdefault(py, []).append(px)
    top, bottom = min(rows), max(rows)
    foot_top = bottom - FOOT_H + 1

    assert bottom - top + 1 == SHIP_H  # the T is as tall as the ship
    for row, columns in rows.items():
        columns.sort()
        left, right = columns[0], columns[-1]
        width = right - left + 1
        assert len(columns) == width, f"row {row} has a gap"  # no gap inside a row
        assert width == (SHIP_W if row >= foot_top else BAR_W), f"row {row} is {width} wide"
    assert sorted(rows) == list(range(top, bottom + 1))  # no empty row inside the T

    # The bar is centered on the foot, and the foot's bottom row is the bar's bottom row.
    bar_left = min(rows[top])
    foot_left = min(rows[bottom])
    assert bar_left - foot_left == (SHIP_W - BAR_W) // 2
    assert len(white) == BAR_W * (SHIP_H - FOOT_H) + SHIP_W * FOOT_H
