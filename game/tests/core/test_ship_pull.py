"""The planet's pull on the ship. Contract: docs/contracts/systems/ship.md, Rules.

Task: docs/contracts/DRA-96/tasks/DRA-96-05-qa-engineer.md. One test per behavior it lists.

Every expected number is worked out here from the GDD values below and the contract's Diagram
(Planet pull). Every `GravityWell` is built by hand. No `game/tuning/` file is read and no expected
number comes from the code under test.
"""

import logging
import math
from dataclasses import replace
from typing import Literal

import pytest

import core.ship as ship_module
from core.collision import Box, place_hitbox
from core.ship import (
    NO_GROUND,
    NO_WELLS,
    GravityWell,
    Ground,
    Ship,
    Thrust,
    block_ship,
    check_escapable_pull,
    step,
    well_pull,
)

GRAVITY: float = 0.16
"""px/tick². Source: 04-ship.md, Values, gravity (guess)."""

THRUST_SIDE: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_side (guess)."""

THRUST_UP: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_up (guess)."""

THRUST_DOWN: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_down (guess)."""

DRAG_X: float = 0.94
"""× per tick. Source: 04-ship.md, Values, drag_x (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

HALF: float = 16.0
"""Half of the ship's 32 x 32 square, px. Source: 04-ship.md, ship_w, ship_h (guess)."""

SCREEN_W: float = 640.0
"""px. Source: 03-world-and-camera.md, Values, screen_w (guess)."""

TOP_LINE_Y: float = 168.0
"""Screen y of the top line: round(480 * 0.35). Source: 03-world-and-camera.md, rule 2."""

PULL_RADIUS: float = 150.0
"""px from the planet's center. Source: drifters/08-planet.md, pull_radius (guess)."""

PULL_MAX: float = 0.2
"""px/tick². Source: drifters/08-planet.md, pull_max (guess)."""

SURFACE: float = 32.0
"""px from the planet's center. Source: drifters/08-planet.md, pull_shape (locked): the surface."""

SHIP_LOGGER: str = "core.ship"
NO_KEY: Thrust = Thrust()

CX: float = 320.0
CY: float = 400.0
"""The field's center: the Diagram's planet pull, (320, 400). Clear of the walls and the top line,
with the whole field on screen."""

WELL: GravityWell = GravityWell(CX, CY, SURFACE, PULL_RADIUS, PULL_MAX)

ANGLES: list[float] = [math.radians(degrees) for degrees in range(0, 360, 30)] + [
    math.radians(degrees) for degrees in (7.5, 100.0, 213.0)
]
"""Directions from the field's center to the ship, rad. Right angles and slanted ones."""

# Offsets (dx, dy) whose length is exactly 150 or 160 (3-4-5 triples), in every quadrant and on
# every axis, so "on the edge" is exact and not a rounding of cos and sin.
EDGE_OFFSETS: list[tuple[float, float]] = [
    (150.0, 0.0),
    (-150.0, 0.0),
    (0.0, 150.0),
    (0.0, -150.0),
    (90.0, 120.0),
    (-90.0, 120.0),
    (90.0, -120.0),
    (-90.0, -120.0),
    (120.0, 90.0),
    (-120.0, -90.0),
]
OUTSIDE_OFFSETS: list[tuple[float, float]] = [
    (160.0, 0.0),
    (0.0, -160.0),
    (96.0, 128.0),
    (-96.0, -128.0),
    (-96.0, 128.0),
    (300.0, 0.0),
]


def expected_strength(distance: float) -> float:
    """The pull at `distance` px from the center, from the GDD's pull_shape, worked out here."""
    if distance >= PULL_RADIUS or distance <= 0.0:
        return 0.0
    if distance <= SURFACE:
        return PULL_MAX
    return PULL_MAX * (PULL_RADIUS - distance) / (PULL_RADIUS - SURFACE)


def at_distance(distance: float, angle: float, well: GravityWell = WELL) -> Ship:
    """A ship at rest `distance` px from the well's center, in the direction `angle` from it."""
    return Ship(
        well.x + distance * math.cos(angle),
        well.y + distance * math.sin(angle),
        0.0,
        0.0,
    )


def assert_pull(got: tuple[float, float], want: tuple[float, float]) -> None:
    assert got[0] == pytest.approx(want[0], abs=1e-12)
    assert got[1] == pytest.approx(want[1], abs=1e-12)


def toward_center(distance: float, angle: float) -> tuple[float, float]:
    """The pull a ship `distance` px from the center, at `angle`, feels: toward the center."""
    strength = expected_strength(distance)
    return (-strength * math.cos(angle), -strength * math.sin(angle))


@pytest.mark.parametrize("offset", EDGE_OFFSETS + OUTSIDE_OFFSETS)
def test_no_pull_outside_the_field_or_on_its_edge(offset: tuple[float, float]) -> None:
    ship = Ship(CX + offset[0], CY + offset[1], 0.0, 0.0)

    assert well_pull(ship, (WELL,)) == (0.0, 0.0)


@pytest.mark.parametrize("angle", ANGLES)
@pytest.mark.parametrize(
    "distance",
    [149.0, 149.999, 120.0, 91.0, 60.0, 33.0, 32.0],
    ids=[
        "just-in",
        "hair-in",
        "ramp-120",
        "mid-field",
        "ramp-60",
        "just-out-of-surface",
        "surface",
    ],
)
def test_the_pull_follows_the_straight_line_toward_the_center(
    distance: float, angle: float
) -> None:
    ship = at_distance(distance, angle)

    got = well_pull(ship, (WELL,))

    assert_pull(got, toward_center(distance, angle))
    assert math.hypot(*got) == pytest.approx(expected_strength(distance), abs=1e-12)


def test_the_pull_at_the_diagram_distances() -> None:
    # Diagram, Planet pull: d 120, 91 (mid-field), 32 (surface), straight above the center.
    for y, want in [(280.0, 0.2 * 30 / 118), (309.0, 0.1), (368.0, 0.2)]:
        pull_x, pull_y = well_pull(Ship(CX, y, 0.0, 0.0), (WELL,))
        assert pull_x == 0.0
        assert pull_y == pytest.approx(want, abs=1e-12)


@pytest.mark.parametrize("angle", ANGLES)
@pytest.mark.parametrize("distance", [31.999, 20.0, 10.0, 1.0, 0.5])
def test_inside_the_surface_the_pull_stays_at_pull_max(distance: float, angle: float) -> None:
    got = well_pull(at_distance(distance, angle), (WELL,))

    assert_pull(got, toward_center(distance, angle))
    assert math.hypot(*got) == pytest.approx(PULL_MAX, abs=1e-12)


def test_the_pull_is_never_more_than_pull_max() -> None:
    biggest = 0.0
    for tenth in range(1600):
        distance = tenth / 10
        for angle in ANGLES:
            biggest = max(biggest, math.hypot(*well_pull(at_distance(distance, angle), (WELL,))))

    assert biggest <= PULL_MAX + 1e-12


def test_at_the_exact_center_there_is_no_pull() -> None:
    assert well_pull(Ship(CX, CY, 0.0, 0.0), (WELL,)) == (0.0, 0.0)


def test_pull_depends_on_the_ship_center_only() -> None:
    # A moving ship's speed and flags change nothing: only its center counts.
    still = Ship(CX, 309.0, 0.0, 0.0)
    moving = Ship(CX, 309.0, 5.0, -3.0, wall="left", at_top_line=True, against_island=True)

    assert well_pull(moving, (WELL,)) == well_pull(still, (WELL,))


def test_two_overlapping_fields_add_up() -> None:
    # Diagram: fields at (320, 391) and (411, 300), ship at (320, 300), d 91 to each.
    first = GravityWell(320.0, 391.0, SURFACE, PULL_RADIUS, PULL_MAX)
    second = GravityWell(411.0, 300.0, SURFACE, PULL_RADIUS, PULL_MAX)
    ship = Ship(320.0, 300.0, 0.0, 0.0)

    assert_pull(well_pull(ship, (first, second)), (0.1, 0.1))
    assert_pull(well_pull(ship, (second, first)), (0.1, 0.1))
    result = step(ship, NO_KEY, NO_GROUND, (first, second))
    assert result.vx == pytest.approx(0.1 * DRAG_X, abs=1e-12)
    assert result.vy == pytest.approx(GRAVITY + 0.1, abs=1e-12)


def test_the_sum_of_fields_of_different_size_is_the_sum_of_each() -> None:
    small = GravityWell(260.0, 330.0, 20.0, 80.0, 0.1)
    big = GravityWell(380.0, 280.0, 40.0, 200.0, 0.25)
    ship = Ship(320.0, 300.0, 0.0, 0.0)
    want_x = want_y = 0.0
    for well in (small, big):
        dx, dy = well.x - ship.x, well.y - ship.y
        distance = math.hypot(dx, dy)
        if distance >= well.pull_radius:
            continue
        if distance <= well.surface_radius:
            strength = well.pull_max
        else:
            strength = (
                well.pull_max
                * (well.pull_radius - distance)
                / (well.pull_radius - well.surface_radius)
            )
        want_x += strength * dx / distance
        want_y += strength * dy / distance

    assert want_x != 0.0
    assert_pull(well_pull(ship, (small, big)), (want_x, want_y))


def test_a_field_that_does_not_hold_the_ship_adds_nothing() -> None:
    near = GravityWell(320.0, 391.0, SURFACE, PULL_RADIUS, PULL_MAX)
    far = GravityWell(320.0, 600.0, SURFACE, PULL_RADIUS, PULL_MAX)
    on_the_edge = GravityWell(320.0 + 90.0, 300.0 + 120.0, SURFACE, PULL_RADIUS, PULL_MAX)
    ship = Ship(320.0, 300.0, 0.0, 0.0)
    alone = well_pull(ship, (near,))

    assert alone[1] > 0.0
    assert well_pull(ship, (near, far)) == alone
    assert well_pull(ship, (far, near, on_the_edge)) == alone
    assert well_pull(ship, (far, on_the_edge)) == (0.0, 0.0)
    assert well_pull(ship, NO_WELLS) == (0.0, 0.0)
    assert NO_WELLS == ()


# The step, from the Diagram's Planet pull table: (x, y, vx after the tick, vy after the tick).
DIAGRAM_STEPS: list[tuple[float, float, float, float]] = [
    (320.0, 240.0, 0.0, GRAVITY),
    (320.0, 250.0, 0.0, GRAVITY),
    (320.0, 280.0, 0.0, GRAVITY + 0.2 * 30 / 118),
    (320.0, 309.0, 0.0, GRAVITY + 0.1),
    (320.0, 368.0, 0.0, GRAVITY + 0.2),
    (320.0, 390.0, 0.0, GRAVITY + 0.2),
    (320.0, 400.0, 0.0, GRAVITY),
    (229.0, 400.0, 0.1 * DRAG_X, GRAVITY),
]


@pytest.mark.parametrize(("x", "y", "vx", "vy"), DIAGRAM_STEPS)
def test_the_step_gives_the_diagrams_speed_after_the_tick(
    x: float, y: float, vx: float, vy: float
) -> None:
    result = step(Ship(x, y, 0.0, 0.0), NO_KEY, NO_GROUND, (WELL,))

    assert result.vx == pytest.approx(vx, abs=1e-12)
    assert result.vy == pytest.approx(vy, abs=1e-12)
    assert result.x == pytest.approx(x + vx, abs=1e-12)
    assert result.y == pytest.approx(y + vy, abs=1e-12)


def test_the_pull_is_measured_from_the_position_before_the_move() -> None:
    # Fast down, just outside the field: it ends the move inside, but felt no pull this tick.
    entering = step(Ship(CX, 249.0, 0.0, 5.0), NO_KEY, NO_GROUND, (WELL,))
    # Fast up, just inside: it ends the move outside, but did feel the pull this tick.
    leaving = step(Ship(CX, 251.0, 0.0, -5.0), NO_KEY, NO_GROUND, (WELL,))

    assert entering.vy == pytest.approx(5.0 + GRAVITY, abs=1e-12)
    assert entering.y == pytest.approx(249.0 + 5.0 + GRAVITY, abs=1e-12)
    assert leaving.vy == pytest.approx(-5.0 + GRAVITY + expected_strength(149.0), abs=1e-12)
    assert leaving.y == pytest.approx(251.0 + leaving.vy, abs=1e-12)


def test_the_pull_comes_right_after_gravity_and_before_drag() -> None:
    # Thrust right, gravity and a sideways pull: drag multiplies all of vx, the pull included.
    ship = Ship(229.0, 400.0, 1.0, 0.0)
    result = step(ship, Thrust(right=True), NO_GROUND, (WELL,))

    assert result.vx == pytest.approx((1.0 + THRUST_SIDE + 0.1) * DRAG_X, abs=1e-12)
    assert result.vy == pytest.approx(GRAVITY, abs=1e-12)
    # No drag on the y part of the pull.
    below = step(Ship(CX, 309.0, 0.0, 2.0), Thrust(up=True), NO_GROUND, (WELL,))
    assert below.vy == pytest.approx(2.0 - THRUST_UP + GRAVITY + 0.1, abs=1e-12)


def test_the_fall_cap_acts_on_the_speed_with_the_pull_in() -> None:
    # 5.45 + 0.16 + 0.2 = 5.81 is past the cap: the cap comes after the pull, so it is 5.5, not
    # 5.5 + 0.2.
    result = step(Ship(CX, 368.0, 0.0, 5.45), NO_KEY, NO_GROUND, (WELL,))

    assert result.vy == FALL_CAP
    assert result.y == pytest.approx(368.0 + FALL_CAP, abs=1e-12)
    # The cap is only a ceiling for falling: an upward pull is never cut.
    up = step(Ship(CX, 420.0, 0.0, -5.0), NO_KEY, NO_GROUND, (WELL,))
    assert up.vy == pytest.approx(-5.0 + GRAVITY - PULL_MAX, abs=1e-12)


def test_the_step_pulls_a_ship_toward_the_center_from_any_side() -> None:
    for angle in ANGLES:
        distance = 60.0
        ship = at_distance(distance, angle)
        pull = toward_center(distance, angle)

        result = step(ship, NO_KEY, NO_GROUND, (WELL,))

        assert result.vx == pytest.approx(pull[0] * DRAG_X, abs=1e-12)
        assert result.vy == pytest.approx(GRAVITY + pull[1], abs=1e-12)


# What `step` gave before DRA-96, written out: thrust, gravity, drag, fall cap, move, side walls,
# the ground, the top line.


def expected_step(ship: Ship, thrust: Thrust, ground: Ground = NO_GROUND) -> Ship:
    vx, vy = ship.vx, ship.vy
    if thrust.left:
        vx -= THRUST_SIDE
    if thrust.right:
        vx += THRUST_SIDE
    if thrust.up:
        vy -= THRUST_UP
    if thrust.down:
        vy += THRUST_DOWN
    vy += GRAVITY
    vx *= DRAG_X
    vy = min(vy, FALL_CAP)
    x, y = ship.x + vx, ship.y + vy
    wall: Literal["left", "right"] | None = None
    if x - HALF < 0:
        x, vx, wall = HALF, 0.0, "left"
    elif x + HALF > SCREEN_W:
        x, vx, wall = SCREEN_W - HALF, 0.0, "right"
    walled = Ship(x, y, vx, vy, wall, ship.at_top_line, ship.against_island)
    blocked = block_ship(walled, ground)
    y, vy, at_top_line = blocked.y, blocked.vy, False
    if y - HALF < TOP_LINE_Y:
        y, vy, at_top_line = TOP_LINE_Y + HALF, 0.0, True
    return replace(blocked, y=y, vy=vy, at_top_line=at_top_line)


STATES: list[Ship] = [
    Ship(x, y, vx, vy)
    for (x, y) in [(320.0, 240.0), (20.0, 300.0), (620.0, 300.0), (320.0, 190.0), (320.0, 470.0)]
    for (vx, vy) in [(0.0, 0.0), (3.0, -2.0), (-9.0, 4.0), (9.0, -9.0), (0.0, 5.5), (0.0, 7.0)]
]
THRUSTS: list[Thrust] = [
    Thrust(),
    Thrust(up=True),
    Thrust(down=True),
    Thrust(left=True),
    Thrust(right=True),
    Thrust(up=True, left=True),
    Thrust(down=True, right=True),
]
# Ground: one in the way of the spawn, one that holds the ship at (320, 470) low down, one far off.
GROUNDS: list[Ground] = [
    NO_GROUND,
    Ground(),
    Ground(place_hitbox((Box(0.0, 0.0, 120.0, 120.0),), 320.0, 300.0), 0.0, 1.1),
    Ground(place_hitbox((Box(0.0, 0.0, 200.0, 40.0),), 320.0, 500.0), 0.0, 1.1),
    Ground(place_hitbox((Box(0.0, 0.0, 50.0, 50.0),), 100.0, 100.0), 0.5, 1.1),
]


def test_with_no_wells_the_step_is_the_step_before_the_pull() -> None:
    for ground in GROUNDS:
        for ship in STATES:
            for thrust in THRUSTS:
                want = expected_step(ship, thrust, ground)
                for got in (
                    step(ship, thrust, ground),
                    step(ship, thrust, ground, NO_WELLS),
                    step(ship, thrust, ground, ()),
                    step(ship, thrust, ground, wells=()),
                ):
                    assert got.x == pytest.approx(want.x, abs=1e-9)
                    assert got.y == pytest.approx(want.y, abs=1e-9)
                    assert got.vx == pytest.approx(want.vx, abs=1e-9)
                    assert got.vy == pytest.approx(want.vy, abs=1e-9)
                    assert got.wall == want.wall
                    assert got.at_top_line == want.at_top_line
                    assert got.against_island == want.against_island
    # The calls the older tests make, with two or three arguments.
    assert step(STATES[0], NO_KEY) == step(STATES[0], NO_KEY, NO_GROUND, NO_WELLS)


def test_a_field_that_holds_nothing_leaves_the_step_as_it_was() -> None:
    far = GravityWell(100.0, 900.0, SURFACE, PULL_RADIUS, PULL_MAX)
    for ground in GROUNDS:
        for ship in STATES:
            for thrust in THRUSTS:
                assert step(ship, thrust, ground, (far,)) == step(ship, thrust, ground)


def distance_to_center(ship: Ship) -> float:
    return math.hypot(ship.x - CX, ship.y - CY)


def fly_away(ship: Ship, thrust: Thrust) -> int:
    """Step with `thrust` until the ship's center is out of the field. Every tick must take it
    farther from the center. Returns the ticks it took."""
    ticks = 0
    while distance_to_center(ship) < PULL_RADIUS:
        before = distance_to_center(ship)
        ship = step(ship, thrust, NO_GROUND, (WELL,))
        ticks += 1
        assert distance_to_center(ship) > before, f"tick {ticks}: {ship}"
        assert ship.wall is None
        assert not ship.at_top_line
        assert ticks < 1000, "the ship never left the field"
    return ticks


def test_up_held_from_just_above_the_planet_leaves_the_field() -> None:
    ship = Ship(CX, CY - SURFACE, 0.0, 0.0)

    first = step(ship, Thrust(up=True), NO_GROUND, (WELL,))

    # Diagram: vy = -0.42 + 0.16 + 0.2 = -0.06, it still climbs.
    assert first.vy == pytest.approx(-0.06, abs=1e-12)
    assert first.y < ship.y
    assert fly_away(ship, Thrust(up=True)) > 1


@pytest.mark.parametrize("side", ["left", "right"])
def test_a_side_key_held_from_beside_the_planet_leaves_the_field(side: str) -> None:
    sign = -1.0 if side == "left" else 1.0
    ship = Ship(CX + sign * SURFACE, CY, 0.0, 0.0)
    thrust = Thrust(left=side == "left", right=side == "right")

    first = step(ship, thrust, NO_GROUND, (WELL,))

    # Diagram: vx = (-0.42 + 0.2) * 0.94 = -0.2068 for the left key.
    assert first.vx == pytest.approx(sign * (THRUST_SIDE - PULL_MAX) * DRAG_X, abs=1e-12)
    assert abs(first.x - CX) > SURFACE
    assert fly_away(ship, thrust) > 1


@pytest.mark.parametrize("side", ["left", "right"])
def test_a_side_key_held_inside_the_surface_still_leaves_the_field(side: str) -> None:
    # The pull is never more than pull_max inside the surface, so the escape still holds there.
    sign = -1.0 if side == "left" else 1.0
    ship = Ship(CX + sign * 5.0, CY, 0.0, 0.0)
    thrust = Thrust(left=side == "left", right=side == "right")

    assert fly_away(ship, thrust) > 1


def test_check_escapable_pull_accepts_todays_pull_max() -> None:
    check_escapable_pull(PULL_MAX)
    check_escapable_pull(0.25)
    check_escapable_pull(0.01)


def test_check_escapable_pull_refuses_a_pull_that_ties_or_passes_thrust_up() -> None:
    # 0.26 + 0.16 reaches thrust_up, 0.42: refused (strict "below").
    for pull_max, shown in [(THRUST_UP - GRAVITY, "0.26"), (0.3, "0.3"), (0.5, "0.5")]:
        with pytest.raises(ValueError, match=r"pull_max is too strong") as error:
            check_escapable_pull(pull_max)
        assert str(error.value) == (
            "pull_max is too strong: pull_max + gravity must stay below thrust_up "
            f"({shown} + 0.16 >= 0.42)"
        )


def test_check_escapable_pull_ties_with_thrust_up_are_refused_in_exact_numbers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Binary-exact values, so the tie is a true tie: 0.25 + 0.25 is 0.5.
    monkeypatch.setattr(ship_module, "GRAVITY", 0.25)
    monkeypatch.setattr(ship_module, "THRUST_UP", 0.5)
    monkeypatch.setattr(ship_module, "THRUST_SIDE", 4.0)

    with pytest.raises(ValueError, match="too strong") as error:
        check_escapable_pull(0.25)
    assert str(error.value) == (
        "pull_max is too strong: pull_max + gravity must stay below thrust_up (0.25 + 0.25 >= 0.5)"
    )
    check_escapable_pull(0.125)


def test_check_escapable_pull_refuses_a_pull_at_or_past_thrust_side(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Today thrust_side equals thrust_up, so the first rule always speaks first. Lower the side
    # thrust: the check reads it when it is called.
    monkeypatch.setattr(ship_module, "THRUST_SIDE", 0.2)

    for pull_max, shown in [(0.2, "0.2"), (0.25, "0.25"), (0.3, "0.3")]:
        if pull_max + GRAVITY >= THRUST_UP:
            continue
        with pytest.raises(ValueError, match="too strong") as error:
            check_escapable_pull(pull_max)
        assert str(error.value) == (
            f"pull_max is too strong: pull_max must stay below thrust_side ({shown} >= 0.2)"
        )
    check_escapable_pull(0.19)


def test_check_escapable_pull_names_thrust_up_first_when_both_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ship_module, "THRUST_SIDE", 0.2)

    with pytest.raises(ValueError, match="must stay below thrust_up"):
        check_escapable_pull(0.5)


def test_check_escapable_pull_reads_gravity_and_thrust_up_when_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="must stay below thrust_up"):
        check_escapable_pull(0.3)
    monkeypatch.setattr(ship_module, "THRUST_UP", 0.8)
    monkeypatch.setattr(ship_module, "THRUST_SIDE", 0.8)

    check_escapable_pull(0.3)
    monkeypatch.setattr(ship_module, "GRAVITY", 0.6)
    with pytest.raises(ValueError, match="must stay below thrust_up"):
        check_escapable_pull(0.3)


def test_the_pull_and_its_check_log_nothing(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=SHIP_LOGGER)
    ship = Ship(CX, 309.0, 0.0, 0.0)

    well_pull(ship, (WELL,))
    well_pull(Ship(CX, CY, 0.0, 0.0), (WELL,))
    well_pull(Ship(CX, 100.0, 0.0, 0.0), (WELL,))
    check_escapable_pull(PULL_MAX)
    with pytest.raises(ValueError, match="too strong"):
        check_escapable_pull(0.5)
    # A pulled step through the field, in and out of it, touching nothing.
    pulled = ship
    for _ in range(20):
        pulled = step(pulled, Thrust(up=True), NO_GROUND, (WELL,))
    pulled = step(Ship(CX, 250.0, 0.0, 0.0), NO_KEY, NO_GROUND, (WELL,))

    assert [r for r in caplog.records if r.name.startswith("core")] == []
    assert pulled.vy > 0.0
