"""Ship view tests. Source: docs/design/gdd/04-ship.md, look; 12-art-and-audio.md, rule 9.

The ship is a sprite that leans with its sideways speed and shows a flame jet for each held
arrow. Pixels are read from the surface with `pygame.image.tobytes`, never from the code under
test. The look never moves the hitbox, so the sprite's frame is centered on the ship.
"""

import pygame
import pytest

from core.ship import Ship, Thrust, spawn
from ui.ship_view import (
    DEFAULT_SHIP_LOOK,
    ShipLook,
    active_jets,
    draw_ship,
    lean_step,
    streak_level,
)

SURFACE_SIZE: tuple[int, int] = (640, 480)
"""Test surface. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

BLACK: tuple[int, int, int] = (0, 0, 0)

LOOK = ShipLook(lean_speed=1.0, streak_speed=1.0, streak_long_speed=4.0, flame_ticks_per_frame=4)

Box = tuple[int, int, int, int]  # left, top, right, bottom, bottom and right not included


def _drawn(ship: Ship, thrust: Thrust | None = None, tick: int = 0) -> pygame.Surface:
    surface = pygame.Surface(SURFACE_SIZE)
    surface.fill(BLACK)
    draw_ship(surface, ship, thrust, tick, LOOK)
    return surface


def _bounds(surface: pygame.Surface) -> Box | None:
    """The box round every non-black pixel, or None when the surface is empty."""
    width, height = surface.get_size()
    data = pygame.image.tobytes(surface, "RGB")
    xs: list[int] = []
    ys: list[int] = []
    for y in range(height):
        for x in range(width):
            i = (y * width + x) * 3
            if (data[i], data[i + 1], data[i + 2]) != BLACK:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def _box(surface: pygame.Surface) -> Box:
    """Like `_bounds`, but the surface must show something."""
    box = _bounds(surface)
    assert box is not None, "nothing was drawn"
    return box


def _same(a: pygame.Surface, b: pygame.Surface) -> bool:
    return pygame.image.tobytes(a, "RGB") == pygame.image.tobytes(b, "RGB")


@pytest.mark.parametrize(
    ("vx", "step"),
    [(0.0, 0), (0.99, 0), (1.0, 1), (6.6, 1), (-0.99, 0), (-1.0, -1), (-6.6, -1)],
)
def test_lean_follows_sideways_speed(vx: float, step: int) -> None:
    assert lean_step(vx, LOOK) == step


@pytest.mark.parametrize(
    ("vx", "level"),
    [(0.0, None), (0.99, None), (1.0, 0), (3.99, 0), (4.0, 1), (-0.5, None), (-1.0, 0), (-5.0, 1)],
)
def test_streaks_grow_with_sideways_speed(vx: float, level: int | None) -> None:
    assert streak_level(vx, LOOK) == level


def test_no_key_fires_no_jet() -> None:
    assert active_jets(Thrust()) == ()


def test_each_arrow_fires_its_own_jet() -> None:
    assert active_jets(Thrust(up=True)) == ("up",)
    assert active_jets(Thrust(left=True)) == ("left",)
    assert active_jets(Thrust(right=True)) == ("right",)
    assert active_jets(Thrust(down=True)) == ("down",)


def test_two_arrows_fire_both_jets() -> None:
    assert active_jets(Thrust(up=True, left=True)) == ("up", "left")


def test_opposite_arrows_cancel_like_thrust_does() -> None:
    assert active_jets(Thrust(up=True, down=True)) == ()
    assert active_jets(Thrust(left=True, right=True)) == ()
    assert active_jets(Thrust(up=True, down=True, left=True)) == ("left",)


@pytest.mark.usefixtures("pygame_headless")
def test_ship_at_spawn_is_drawn_around_its_center() -> None:
    ship = spawn()
    left, top, right, bottom = _box(_drawn(ship))

    assert left < ship.x < right
    assert top < ship.y < bottom
    assert abs((left + right) / 2 - ship.x) <= 1  # the centre pose is symmetric


@pytest.mark.usefixtures("pygame_headless")
def test_ship_covers_the_hitbox() -> None:
    """The T of 04-ship.md fits inside what is drawn: the sprite is never smaller than it."""
    left, top, right, bottom = _box(_drawn(spawn()))
    assert left <= 304  # the foot, 32 wide, runs from 304 to 336
    assert right >= 336
    assert top <= 224  # the bar, 32 tall, from 224 to 256
    assert bottom >= 256


@pytest.mark.usefixtures("pygame_headless")
def test_moving_the_ship_moves_the_sprite_by_the_same_amount() -> None:
    at = _box(_drawn(Ship(x=320.0, y=240.0, vx=0.0, vy=0.0)))
    moved = _box(_drawn(Ship(x=420.0, y=300.0, vx=0.0, vy=0.0)))

    assert moved == (at[0] + 100, at[1] + 60, at[2] + 100, at[3] + 60)


@pytest.mark.usefixtures("pygame_headless")
def test_a_ship_partly_off_the_surface_is_clipped_not_an_error() -> None:
    _box(_drawn(Ship(x=0.0, y=0.0, vx=0.0, vy=0.0)))  # the corner of the sprite still shows
    assert _bounds(_drawn(Ship(x=320.0, y=900.0, vx=0.0, vy=0.0))) is None


@pytest.mark.usefixtures("pygame_headless")
def test_a_lean_shows_a_different_frame_and_mirrors_left_to_right() -> None:
    centre = _drawn(Ship(x=320.0, y=240.0, vx=0.0, vy=0.0))
    right = _drawn(Ship(x=320.0, y=240.0, vx=5.0, vy=0.0))
    left = _drawn(Ship(x=320.0, y=240.0, vx=-5.0, vy=0.0))

    assert not _same(centre, right)
    assert not _same(right, left)
    flat, r, lf = _box(centre), _box(right), _box(left)
    assert (r[2] - r[0]) == (lf[2] - lf[0])  # the same width: a mirror
    assert (r[2] - r[0]) < (flat[2] - flat[0])  # a lean is narrower than the centre pose


@pytest.mark.usefixtures("pygame_headless")
def test_a_jet_adds_pixels_and_no_jet_changes_nothing() -> None:
    ship = spawn()
    plain = _drawn(ship)

    assert _same(plain, _drawn(ship, Thrust()))
    assert not _same(plain, _drawn(ship, Thrust(up=True)))
    assert (
        _box(_drawn(ship, Thrust(up=True)))[3] > _box(plain)[3]
    )  # the main flame hangs below the hull


@pytest.mark.usefixtures("pygame_headless")
def test_each_jet_looks_different() -> None:
    ship = spawn()
    shots = [
        pygame.image.tobytes(_drawn(ship, Thrust(**{key: True})), "RGB")
        for key in ("up", "left", "right", "down")
    ]
    assert len(set(shots)) == 4


@pytest.mark.usefixtures("pygame_headless")
def test_the_flame_flickers_every_flame_ticks_per_frame_ticks() -> None:
    ship = spawn()
    thrust = Thrust(up=True)
    first = _drawn(ship, thrust, tick=0)

    assert _same(first, _drawn(ship, thrust, tick=LOOK.flame_ticks_per_frame - 1))
    assert not _same(first, _drawn(ship, thrust, tick=LOOK.flame_ticks_per_frame))
    assert _same(first, _drawn(ship, thrust, tick=LOOK.flame_ticks_per_frame * 2))


def test_the_default_look_is_a_valid_one() -> None:
    assert DEFAULT_SHIP_LOOK.lean_speed > 0
    assert 0 < DEFAULT_SHIP_LOOK.streak_speed < DEFAULT_SHIP_LOOK.streak_long_speed
    assert DEFAULT_SHIP_LOOK.flame_ticks_per_frame >= 1


@pytest.mark.usefixtures("pygame_headless")
def test_streaks_trail_behind_a_moving_ship_and_mirror() -> None:
    flying = Thrust()
    right = _box(_drawn(Ship(x=320.0, y=240.0, vx=2.0, vy=0.0), flying))
    left = _box(_drawn(Ship(x=320.0, y=240.0, vx=-2.0, vy=0.0), flying))
    still = _box(_drawn(Ship(x=320.0, y=240.0, vx=0.0, vy=0.0), flying))

    assert right[0] < still[0]  # a ship moving right trails streaks to its left
    assert left[2] > still[2]  # a ship moving left trails them to its right


@pytest.mark.usefixtures("pygame_headless")
def test_longer_streaks_at_higher_speed() -> None:
    short = _box(_drawn(Ship(x=320.0, y=240.0, vx=2.0, vy=0.0), Thrust()))
    long = _box(_drawn(Ship(x=320.0, y=240.0, vx=5.0, vy=0.0), Thrust()))

    assert long[0] < short[0]


@pytest.mark.usefixtures("pygame_headless")
def test_no_streaks_while_the_ship_is_not_flying() -> None:
    """Paused or waiting: the app passes no thrust, so only the lean shows."""
    moving = Ship(x=320.0, y=240.0, vx=5.0, vy=0.0)

    assert _box(_drawn(moving, None))[0] > _box(_drawn(moving, Thrust()))[0]
