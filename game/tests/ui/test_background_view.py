"""Background view tests: the same time draws the same frame, the sway and river loop, planets fall.

Source: 12-art-and-audio.md, Background. Sprites here are flat colors, so a test reads the
pixels it expects.
"""

import dataclasses

import pygame
import pytest

from core.world import SCREEN_H, SCREEN_W
from ui.background_view import BackgroundArt, BackgroundRules, build_background, draw_background

RULES: BackgroundRules = BackgroundRules(
    sway_loop_ticks=40,
    planet_count=1,
    planet_speed=1.0,
    planet_scale=1.0,
    river_light_count=10,
    river_light_loop_ticks=100,
    river_light_strength=1.0,
    swirl_count=4,
    swirl_loop_ticks=60,
    glow_height=20,
    glow_strength=1.0,
)
PAINTING_COLOR: tuple[int, int, int] = (10, 10, 30)
SWAY_COLORS: tuple[tuple[int, int, int], ...] = (
    (10, 10, 30),
    (30, 10, 10),
    (10, 30, 10),
    (30, 30, 30),
)
PLANET_COLOR: tuple[int, int, int] = (200, 200, 200)
PLANET_SIZE: int = 80


def _frames(*colors: tuple[int, int, int]) -> tuple[pygame.Surface, ...]:
    frames: list[pygame.Surface] = []
    for color in colors:
        frame: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H))
        frame.fill(color)
        frames.append(frame)
    return tuple(frames)


def _art(
    rules: BackgroundRules = RULES, sway: tuple[pygame.Surface, ...] | None = None
) -> BackgroundArt:
    planet: pygame.Surface = pygame.Surface((PLANET_SIZE, PLANET_SIZE))
    planet.fill(PLANET_COLOR)
    return build_background(sway or _frames(PAINTING_COLOR), (planet,), rules)


def _frame(art: BackgroundArt, ticks: float) -> bytes:
    surface: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_background(surface, art, ticks)
    return pygame.image.tobytes(surface, "RGB")


def _nothing_moving() -> BackgroundRules:
    return dataclasses.replace(
        RULES, planet_count=0, river_light_count=0, swirl_count=0, glow_height=0
    )


def test_the_same_time_draws_the_same_frame() -> None:
    art: BackgroundArt = _art()
    assert _frame(art, 123.5) == _frame(art, 123.5)


def test_river_light_loops_after_its_loop_length() -> None:
    rules: BackgroundRules = dataclasses.replace(RULES, planet_count=0, swirl_count=0)
    art: BackgroundArt = _art(rules)
    assert _frame(art, 10.0) == _frame(art, 10.0 + rules.river_light_loop_ticks)


def test_river_light_moves_between_two_times() -> None:
    rules: BackgroundRules = dataclasses.replace(RULES, planet_count=0, swirl_count=0)
    art: BackgroundArt = _art(rules)
    assert _frame(art, 10.0) != _frame(art, 20.0)


def test_with_everything_off_the_painting_shows_unchanged() -> None:
    art: BackgroundArt = _art(_nothing_moving())
    surface: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_background(surface, art, 50.0)
    assert surface.get_at((300, 200))[:3] == PAINTING_COLOR


def test_a_planet_slides_down_by_planet_speed_a_tick() -> None:
    art: BackgroundArt = _art(dataclasses.replace(_nothing_moving(), planet_count=1))
    surface: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H))
    # The one planet starts at x = -50 on trip 0, so column 10 is inside it. Its top edge is at
    # planet_speed * ticks - PLANET_SIZE, and its bottom edge PLANET_SIZE lower.
    draw_background(surface, art, 40.0)
    assert surface.get_at((10, 30))[:3] == PLANET_COLOR
    assert surface.get_at((10, 45))[:3] == PAINTING_COLOR
    draw_background(surface, art, 60.0)
    assert surface.get_at((10, 50))[:3] == PLANET_COLOR


def test_bottom_glow_is_brightest_at_the_bottom_edge_and_none_above_it() -> None:
    art: BackgroundArt = _art(dataclasses.replace(_nothing_moving(), glow_height=20))
    surface: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_background(surface, art, 0.0)
    bottom: pygame.Color = surface.get_at((300, SCREEN_H - 1))
    higher: pygame.Color = surface.get_at((300, SCREEN_H - 10))
    above: pygame.Color = surface.get_at((300, SCREEN_H - 21))
    assert bottom.r > higher.r > above.r
    assert above[:3] == PAINTING_COLOR


def _swayed(rules: BackgroundRules = RULES) -> BackgroundArt:
    return _art(dataclasses.replace(rules, **_nothing_moving_fields()), _frames(*SWAY_COLORS))


def _nothing_moving_fields() -> dict[str, int]:
    return {"planet_count": 0, "river_light_count": 0, "swirl_count": 0, "glow_height": 0}


def _center(art: BackgroundArt, ticks: float) -> tuple[int, int, int]:
    surface: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_background(surface, art, ticks)
    red, green, blue = surface.get_at((300, 200))[:3]
    return (red, green, blue)


def test_the_painting_shows_each_sway_frame_in_turn() -> None:
    art: BackgroundArt = _swayed()
    step: float = RULES.sway_loop_ticks / len(SWAY_COLORS)
    assert [_center(art, step * index) for index in range(len(SWAY_COLORS))] == list(SWAY_COLORS)


def test_the_painting_fades_between_two_frames() -> None:
    art: BackgroundArt = _swayed()
    halfway: tuple[int, int, int] = _center(art, RULES.sway_loop_ticks / len(SWAY_COLORS) / 2)
    assert halfway[0] in range(19, 22)
    assert halfway[1] == 10
    assert halfway[2] in range(19, 22)


def test_the_last_sway_frame_fades_back_into_the_first() -> None:
    art: BackgroundArt = _swayed()
    near_end: tuple[int, int, int] = _center(art, RULES.sway_loop_ticks * 0.99)
    assert all(abs(got - want) <= 2 for got, want in zip(near_end, SWAY_COLORS[0], strict=True))


def test_the_sway_loops_after_its_loop_length() -> None:
    art: BackgroundArt = _swayed()
    assert _center(art, 7.0) == _center(art, 7.0 + RULES.sway_loop_ticks)


def test_building_with_no_planet_sprite_raises() -> None:
    with pytest.raises(ValueError, match="planet"):
        build_background(_frames(PAINTING_COLOR), (), RULES)


def test_building_with_no_painting_frame_raises() -> None:
    planet: pygame.Surface = pygame.Surface((PLANET_SIZE, PLANET_SIZE))
    with pytest.raises(ValueError, match="painting"):
        build_background((), (planet,), RULES)
