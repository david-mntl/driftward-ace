"""Burst view tests: one white square per center, fading with the burst's opacity.

Contract: docs/contracts/systems/run.md, Interface (ui/burst_view.py, core/last_life.py) and
Presentation, Burst; Rules, Burst. The square's side, the count and the speed are stand-ins from
scope report DRA-125, Values needed (Burst); the GDD does not hold them until LD-08.

The ink is read from the drawn pixels (`pygame.image.tobytes`) on a black surface, where a white
square at alpha a leaves the gray level a. The place of each square is the center core gives
(`Burst.particle_centers`); the view's own rounding is written here from the contract.
"""

import copy

import pygame

from core.last_life import Burst
from ui.burst_view import draw_burst

SURFACE_SIZE: tuple[int, int] = (200, 160)
"""Test surface, smaller than the screen so every pixel read stays quick."""

BLACK: tuple[int, int, int] = (0, 0, 0)
"""Source: 12-art-and-audio.md, placeholder_bg (guess)."""

BURST_COUNT: int = 12
"""Squares in the burst. Source: scope report DRA-125, Values needed, Burst."""

BURST_SPEED: float = 1.0
"""Px a square moves per tick. Source: scope report DRA-125, Values needed, Burst."""

BURST_SIZE: int = 3
"""Side of a square, px. Source: scope report DRA-125, Values needed, Burst."""

LIFETIME: int = 120
"""The last-life delay, ticks. Source: 02-game-flow.md, last_life_delay (guess)."""

ORIGIN: tuple[float, float] = (100.0, 80.0)
"""Burst origin on the test surface; every square stays on it for the ages used below."""

INSIDE_AGE: int = 75
"""Last age at which every square is wholly on the test surface (reach 75 px from (100, 80))."""

BLEND_TOLERANCE: int = 1
"""SDL's alpha blend may be one level off `round(255 * opacity)`."""

Pixel = tuple[int, int]


def _burst(
    age: int,
    *,
    origin: tuple[float, float] = ORIGIN,
    count: int = BURST_COUNT,
    size: int = BURST_SIZE,
    speed: float = BURST_SPEED,
) -> Burst:
    return Burst(
        x=origin[0],
        y=origin[1],
        particle_count=count,
        speed_per_tick=speed,
        particle_size=size,
        lifetime_ticks=LIFETIME,
        age_ticks=age,
    )


def _blank(fill: tuple[int, int, int] = BLACK) -> pygame.Surface:
    surface = pygame.Surface(SURFACE_SIZE)
    surface.fill(fill)
    return surface


def _ink(surface: pygame.Surface) -> dict[Pixel, tuple[int, int, int]]:
    """Every pixel that is not black, with its color."""
    width, height = surface.get_size()
    data = pygame.image.tobytes(surface, "RGB")
    ink: dict[Pixel, tuple[int, int, int]] = {}
    for y in range(height):
        base = y * width * 3
        row = data[base : base + width * 3]
        if not any(row):
            continue
        for x in range(width):
            color = (row[x * 3], row[x * 3 + 1], row[x * 3 + 2])
            if color != BLACK:
                ink[(x, y)] = color
    return ink


def _expected_squares(burst: Burst) -> set[Pixel]:
    """The pixels of every square on the surface, written from the contract's top-left rule."""
    width, height = SURFACE_SIZE
    size = burst.particle_size
    pixels: set[Pixel] = set()
    for center_x, center_y in burst.particle_centers:
        left = round(center_x - size / 2)
        top = round(center_y - size / 2)
        for y in range(top, top + size):
            for x in range(left, left + size):
                if 0 <= x < width and 0 <= y < height:
                    pixels.add((x, y))
    return pixels


def test_burst_draws_one_square_per_center_at_the_opacity_alpha(pygame_headless: None) -> None:
    for age in (10, 20, 45, 60, 100, 119):
        burst = _burst(age)
        assert len(set(burst.particle_centers)) == BURST_COUNT, f"{age=}: squares overlap"
        surface = _blank()
        draw_burst(surface, burst)
        ink = _ink(surface)
        expected = _expected_squares(burst)
        assert set(ink) == expected, f"{age=}: ink is not the {BURST_COUNT} squares"
        if age <= INSIDE_AGE:
            assert len(expected) == BURST_COUNT * BURST_SIZE**2, f"{age=}: squares touch each other"
        alpha = round(255 * burst.opacity)
        for pixel, color in ink.items():
            assert color[0] == color[1] == color[2], f"{age=} {pixel}: not white"
            assert abs(color[0] - alpha) <= BLEND_TOLERANCE, f"{age=} {pixel}: {color} not {alpha}"


def test_burst_square_sits_on_the_rounded_top_left_for_any_size_and_origin(
    pygame_headless: None,
) -> None:
    cases = (
        (1, (100.0, 80.0)),
        (2, (100.0, 80.0)),
        (3, (100.0, 80.0)),
        (3, (100.4, 80.6)),
        (3, (60.5, 50.5)),
        (4, (60.5, 50.5)),
        (5, (150.0, 40.25)),
        (8, (30.0, 120.0)),
    )
    for size, origin in cases:
        burst = _burst(0, origin=origin, count=1, size=size)
        surface = _blank()
        draw_burst(surface, burst)
        ink = _ink(surface)
        left = round(origin[0] - size / 2)
        top = round(origin[1] - size / 2)
        assert set(ink) == {
            (x, y) for x in range(left, left + size) for y in range(top, top + size)
        }, f"{size=} {origin=}: square not at ({left}, {top})"
        assert all(color == (255, 255, 255) for color in ink.values()), (
            f"{size=} {origin=}: opacity 1.0 is not full white"
        )


def test_burst_draws_nothing_at_opacity_zero(pygame_headless: None) -> None:
    for age in (LIFETIME, LIFETIME + 1, LIFETIME + 50):
        burst = _burst(age)
        assert burst.opacity == 0.0
        black = _blank()
        draw_burst(black, burst)
        assert not _ink(black), f"{age=}: ink at opacity 0"
        gray = _blank((90, 120, 150))
        before = pygame.image.tobytes(gray, "RGB")
        draw_burst(gray, burst)
        assert pygame.image.tobytes(gray, "RGB") == before, f"{age=}: the surface changed"


def test_burst_squares_off_the_surface_are_clipped(pygame_headless: None) -> None:
    width, height = SURFACE_SIZE
    origins = (
        (0.0, 0.0),
        (float(width), float(height)),
        (1.0, 80.0),
        (float(width) - 1.0, 5.0),
        (100.0, float(height)),
    )
    for origin in origins:
        burst = _burst(30, origin=origin, size=5)
        surface = _blank()
        draw_burst(surface, burst)
        ink = _ink(surface)
        expected = _expected_squares(burst)
        assert expected, f"{origin=}: the case shows nothing, so it clips nothing"
        assert set(ink) == expected, f"{origin=}: ink is not the clipped squares"
    # Squares wholly off the surface draw nothing and raise nothing.
    for origin in ((-50.0, -50.0), (500.0, 80.0), (100.0, 400.0)):
        surface = _blank()
        draw_burst(surface, _burst(0, origin=origin, count=1, size=3))
        assert not _ink(surface), f"{origin=}: ink from a square off the surface"
    # One square on the edge shows only its part on the surface.
    surface = _blank()
    draw_burst(surface, _burst(0, origin=(1.0, 80.0), count=1, size=5))
    left, top = round(1.0 - 2.5), round(80.0 - 2.5)
    assert set(_ink(surface)) == {(x, y) for x in range(left + 5) for y in range(top, top + 5)}


def test_burst_view_changes_nothing_it_is_given(pygame_headless: None) -> None:
    for age in (0, 1, 60, 119, LIFETIME):
        burst = _burst(age)
        before = copy.deepcopy(burst)
        centers = burst.particle_centers
        opacity = burst.opacity
        first = _blank()
        second = _blank()
        draw_burst(first, burst)
        draw_burst(second, burst)
        assert burst == before, f"{age=}: the burst changed"
        assert burst.particle_centers == centers
        assert burst.opacity == opacity
        assert pygame.image.tobytes(first, "RGB") == pygame.image.tobytes(second, "RGB"), (
            f"{age=}: the same burst drew two different pictures"
        )
