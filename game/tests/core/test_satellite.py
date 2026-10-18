"""Satellite tests, and the warning tilt of the drifters that have one.

Contract: docs/contracts/systems/drifters.md, Rules: Satellite, The base. Task:
docs/contracts/DRA-39/tasks/DRA-39-06-qa-engineer.md. One test per behavior it lists. The
tuning records are built here from the GDD values below, never read from game/tuning/, and
no expected number is imported from the code under test.
"""

import math
from dataclasses import replace

import pytest

from core.collision import Box, Circle
from core.drifters.base import (
    Drifter,
    DrifterType,
    Phase,
    TickContext,
    TouchEffect,
    VariantExtra,
)
from core.drifters.satellite import SatelliteVariantExtra
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
    VariantTuning,
)
from core.ship import Ship, spawn

THRUST_SIDE: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_side (guess)."""

DRAG_X: float = 0.94
"""× per tick. Source: 04-ship.md, Values, drag_x (guess)."""

TOP_SIDE_SPEED: float = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
"""px/tick, about 6.58. Source: 04-ship.md, derived values."""

SPEED_RATIO: float = 0.375
"""Level 1 speed as a multiple of the top sideways speed. Source: drifters/02-satellite.md,
speed_ratio (guess)."""

LEVEL_ONE_SPEED: float = SPEED_RATIO * TOP_SIDE_SPEED
"""px/tick along the path, about 2.4675. Source: drifters/02-satellite.md, speed."""

WARNING_TICKS: int = 60
"""ticks. Source: 07-drifters.md, entry_warning_ticks (guess)."""

GRAZE_MARGIN: float = 14.0
"""px. Source: 06-scoring.md, graze_margin (locked)."""

SCREEN_W: int = 640
"""px. Source: 03-world-and-camera.md, screen_w (guess)."""

SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, screen_h (guess)."""

WIDTH: float = 36.0
HEIGHT: float = 12.0
"""px. Source: drifters/02-satellite.md, size (guess)."""

ANGLE: float = 20.0
"""degrees below level for the angled variant. Source: drifters/02-satellite.md, variants."""

HAZARD_SPEED: tuple[float, ...] = (1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42)
"""Hazard speed × for Levels 1 to 8. Source: 08-difficulty.md, level table (locked)."""

BODY: tuple[float, float] = (12.0, 12.0)
PANEL: tuple[float, float] = (36.0, 6.0)
"""Box sizes, px, body then panel bar, both centered. Source: drifters/02-satellite.md, hitbox
(guess)."""

REHIT_COOLDOWN: int = 180
REHIT_DIM: float = 0.75
"""Source: 05-lives-and-damage.md, rehit_cooldown, rehit_dim (guess)."""

OFFSET_HITBOX = (Box(0, 0, *BODY), Box(0, 0, *PANEL))


def make_tuning(*, hazards: HazardRules | None = None) -> DrifterTuning:
    """Build the satellite and meteorite tuning from the GDD values above."""
    extra: dict[str, VariantExtra | None] = {
        "flat": SatelliteVariantExtra(angle_degrees=0.0),
        "angled": SatelliteVariantExtra(angle_degrees=ANGLE),
        "bare": None,
        "plain": VariantExtra(),
    }
    satellite_variants: dict[str, VariantTuning] = {
        name: VariantTuning(width=WIDTH, height=HEIGHT, hitbox=OFFSET_HITBOX, extra=value)
        for name, value in extra.items()
    }
    meteorite_variants: dict[str, VariantTuning] = {
        "medium": VariantTuning(width=28, height=28, hitbox=(Circle(0, 0, 14),))
    }
    tuning: DrifterTuning = DrifterTuning(
        drifters={
            DrifterType.SATELLITE: DrifterTypeTuning(
                variants=satellite_variants,
                default_variant="flat",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
            DrifterType.METEORITE: DrifterTypeTuning(
                variants=meteorite_variants,
                default_variant="medium",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
        },
        switches=PlaytestSwitches(),
    )
    return tuning if hazards is None else replace(tuning, hazards=hazards)


TUNING: DrifterTuning = make_tuning()
CTX: TickContext = TickContext(ship=spawn())


def place(
    x: float | None = None,
    y: float | None = 300.0,
    *,
    variant: str | None = None,
    invert: bool = False,
    level: int = 1,
    as_level: int | None = None,
    speed: float | None = None,
    specialty_enabled: bool | None = None,
    tuning: DrifterTuning = TUNING,
) -> Drifter:
    """Spawn a satellite through the spawner."""
    placement: Placement = Placement(
        DrifterType.SATELLITE,
        x,
        y,
        variant=variant,
        as_level=as_level,
        specialty_enabled=specialty_enabled,
        invert=invert,
        speed=speed,
    )
    return spawn_drifter(placement, level, tuning)


def advance(drifter: Drifter, ticks: int, ctx: TickContext = CTX) -> Drifter:
    """Update the drifter `ticks` times."""
    for _ in range(ticks):
        drifter = drifter.update(ctx)
    return drifter


def active(
    x: float | None = None,
    y: float | None = 300.0,
    *,
    variant: str | None = None,
    invert: bool = False,
) -> Drifter:
    """A satellite that has just turned ACTIVE."""
    drifter: Drifter = advance(place(x, y, variant=variant, invert=invert), WARNING_TICKS)
    assert drifter.phase is Phase.ACTIVE
    return drifter


def test_satellite_placement_needs_y_and_defaults_x_to_just_outside_its_wall() -> None:
    for variant in (None, "flat", "angled"):
        for invert in (False, True):
            with pytest.raises(ValueError, match="y") as missing:
                place(None, None, variant=variant, invert=invert)
            assert "satellite placement needs y" in str(missing.value)
            with pytest.raises(ValueError, match="needs y"):
                place(123.0, None, variant=variant, invert=invert)
    # x defaults to -width / 2 (touching the left wall), or SCREEN_W + width / 2 with invert.
    assert place().x == -18.0
    assert place(invert=True).x == SCREEN_W + 18.0 == 658.0
    assert place(variant="angled").x == -18.0
    assert place(variant="angled", invert=True).x == 658.0
    # y is kept as set, including 0.
    assert place(y=300.0).y == 300.0
    assert place(y=0.0).y == 0.0
    assert place(y=-50.0, invert=True).y == -50.0
    # An x the placement sets is kept, with and without invert, including 0.
    for invert in (False, True):
        for x in (0.0, 100.5, 320.0, -200.0, 700.0):
            drifter: Drifter = place(x, 200.0, invert=invert)
            assert (drifter.x, drifter.y) == (x, 200.0)
    assert (place().width, place().height) == (WIDTH, HEIGHT)
    assert place().variant == "flat"


def test_satellite_refuses_a_specialty_and_a_variant_without_an_angle() -> None:
    with pytest.raises(ValueError, match="specialty"):
        place(specialty_enabled=True)
    with pytest.raises(ValueError, match="specialty"):
        place(specialty_enabled=True, variant="angled", invert=True)
    for switch in (False, None):
        assert place(specialty_enabled=switch).specialty is None
    # A variant with no extra, or with an extra of the wrong kind, has no angle.
    for variant in ("bare", "plain"):
        with pytest.raises(ValueError, match="angle") as no_angle:
            place(variant=variant)
        assert variant in str(no_angle.value)
        with pytest.raises(ValueError, match="angle"):
            place(variant=variant, invert=True)
    # The good variants are fine, with an invert too.
    for variant in ("flat", "angled"):
        assert place(variant=variant, invert=True).x == 658.0


def test_satellite_new_drifter_gets_rehit_values_from_the_hazard_rules() -> None:
    drifter: Drifter = place()
    assert (drifter.rehit_cooldown_ticks, drifter.rehit_dim) == (REHIT_COOLDOWN, REHIT_DIM)
    assert (drifter.rehit_ticks_left, drifter.has_entered) == (0, False)
    given: HazardRules = HazardRules(rehit_cooldown_ticks=45, rehit_dim=0.6)
    set_values: Drifter = place(tuning=make_tuning(hazards=given), level=8)
    assert (set_values.rehit_cooldown_ticks, set_values.rehit_dim) == (45, 0.6)
    assert (set_values.rehit_ticks_left, set_values.has_entered) == (0, False)
    assert set_values.may_hit_ship()
    assert replace(set_values, rehit_ticks_left=2).brightness() == 0.6


def test_satellite_shows_its_warning_for_60_states_then_turns_active_in_place() -> None:
    for invert, wall_x, warn_x in ((False, -18.0, 12.0), (True, 658.0, 628.0)):
        for variant in ("flat", "angled"):
            drifter: Drifter = place(y=300.0, variant=variant, invert=invert)
            for count in range(WARNING_TICKS):
                # The born state, then the next 59 updates.
                assert drifter.phase is Phase.WARNING
                assert drifter.ticks_in_phase == count
                assert drifter.current_hitbox() == ()
                assert drifter.graze_zone() == ()
                assert (drifter.x, drifter.y) == (wall_x, 300.0)
                assert drifter.warning_center() == (warn_x, 300.0)
                drifter = drifter.update(CTX)
            # The 60th update: ACTIVE in place, its two boxes placed.
            assert drifter.phase is Phase.ACTIVE
            assert drifter.ticks_in_phase == 0
            assert (drifter.x, drifter.y) == (wall_x, 300.0)
            assert drifter.current_hitbox() == (
                Box(wall_x, 300.0, *BODY),
                Box(wall_x, 300.0, *PANEL),
            )
            assert not drifter.has_entered
    # The warning is clamped to the screen at any y: against the wall, the whole warning inside.
    assert place(y=-100.0).warning_center() == (12.0, 12.0)
    assert place(y=900.0, invert=True).warning_center() == (628.0, 468.0)
    # Not scaled by the level.
    assert place(level=8).warning_ticks == WARNING_TICKS
    assert advance(place(level=8), WARNING_TICKS - 1).phase is Phase.WARNING


def test_active_satellite_moves_by_the_same_step_every_update() -> None:
    ships: list[Ship] = [
        spawn(),
        Ship(x=16.0, y=100.0, vx=-6.0, vy=0.0),
        Ship(x=600.0, y=470.0, vx=6.0, vy=5.5),
        Ship(x=-18.0, y=300.0, vx=0.0, vy=0.0),
    ]
    cos: float = math.cos(math.radians(ANGLE))
    sin: float = math.sin(math.radians(ANGLE))
    assert pytest.approx(2.4675) == LEVEL_ONE_SPEED
    cases: list[tuple[str, bool, float, float]] = [
        ("flat", False, LEVEL_ONE_SPEED, 0.0),
        ("flat", True, -LEVEL_ONE_SPEED, 0.0),
        ("angled", False, LEVEL_ONE_SPEED * cos, LEVEL_ONE_SPEED * sin),
        ("angled", True, -LEVEL_ONE_SPEED * cos, LEVEL_ONE_SPEED * sin),
    ]
    assert LEVEL_ONE_SPEED * cos == pytest.approx(2.3187, abs=0.0001)
    assert LEVEL_ONE_SPEED * sin == pytest.approx(0.8439, abs=0.0001)
    for variant, invert, step_x, step_y in cases:
        start: Drifter = active(y=100.0, variant=variant, invert=invert)
        start_x: float = start.x
        drifter: Drifter = start
        for n in range(1, 61):
            drifter = drifter.update(TickContext(ship=ships[n % len(ships)]))
            assert drifter.phase is Phase.ACTIVE
            assert drifter.ticks_in_phase == n
            assert drifter.x == pytest.approx(start.x + n * step_x)
            assert drifter.y == pytest.approx(start.y + n * step_y)
        # The input is never mutated.
        assert (start.x, start.y, start.ticks_in_phase) == (start_x, 100.0, 0)
    # The level's hazard speed multiplier scales the step along the path; the angle never scales.
    for level in (1, 4, 8):
        fast: Drifter = advance(place(variant="angled", level=level), WARNING_TICKS)
        moved: Drifter = fast.update(CTX)
        path: float = LEVEL_ONE_SPEED * HAZARD_SPEED[level - 1]
        assert moved.x - fast.x == pytest.approx(path * cos)
        assert moved.y - fast.y == pytest.approx(path * sin)
    # A placement speed is a Level 1 speed along the path.
    given: Drifter = advance(place(variant="angled", speed=4.0, as_level=3), WARNING_TICKS)
    stepped: Drifter = given.update(CTX)
    assert stepped.x - given.x == pytest.approx(4.0 * 1.12 * cos)
    assert stepped.y - given.y == pytest.approx(4.0 * 1.12 * sin)
    # The ship in the context is never read: it moves the same with no ship near and on top.
    for variant in ("flat", "angled"):
        on_top: Drifter = active(y=300.0, variant=variant)
        near: Drifter = on_top.update(TickContext(ship=Ship(x=on_top.x, y=300.0, vx=0, vy=0)))
        far: Drifter = on_top.update(TickContext(ship=Ship(x=600.0, y=20.0, vx=5.0, vy=-5.0)))
        assert near == far
    # Whole crossing at Level 1, run order (update, mark_entered), from the contract timeline.
    for variant, y, expected in (
        ("flat", 300.0, 274),
        ("angled", 200.0, 292),
        ("angled", 300.0, 221),
    ):
        crossing: Drifter = active(y=y, variant=variant)
        ticks: int = 0
        while not crossing.is_off_screen():
            crossing = crossing.update(CTX).mark_entered()
            ticks += 1
            assert ticks <= 400
        assert ticks == expected, (variant, y)


def test_satellite_touch_is_a_hit_and_its_graze_zone_is_both_boxes_grown_by_14() -> None:
    for variant in ("flat", "angled"):
        for invert in (False, True):
            warning: Drifter = place(variant=variant, invert=invert)
            assert warning.effect_on_touch() is TouchEffect.HIT
            assert warning.graze_zone() == ()
            drifter: Drifter = active(x=200.0, y=100.0, variant=variant, invert=invert)
            assert drifter.effect_on_touch() is TouchEffect.HIT
            assert drifter.graze_zone() == (
                Box(200.0, 100.0, BODY[0] + 2 * GRAZE_MARGIN, BODY[1] + 2 * GRAZE_MARGIN),
                Box(200.0, 100.0, PANEL[0] + 2 * GRAZE_MARGIN, PANEL[1] + 2 * GRAZE_MARGIN),
            )
            assert len(drifter.graze_zone()) == len(drifter.current_hitbox()) == 2


def test_warning_tilt_is_zero_for_the_meteorite_and_the_flat_satellite() -> None:
    meteorite: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, 300.0), 1, TUNING)
    assert meteorite.warning_tilt_degrees() == 0.0
    assert advance(meteorite, WARNING_TICKS).warning_tilt_degrees() == 0.0
    for invert in (False, True):
        flat: Drifter = place(variant="flat", invert=invert)
        assert flat.warning_tilt_degrees() == 0.0
        assert advance(flat, WARNING_TICKS).warning_tilt_degrees() == 0.0
    # The angled one points the way it will fly: -20 down to the right, +20 down to the left.
    assert place(variant="angled").warning_tilt_degrees() == -ANGLE
    assert place(variant="angled", invert=True).warning_tilt_degrees() == ANGLE
    assert active(variant="angled").warning_tilt_degrees() == -ANGLE
    assert active(variant="angled", invert=True).warning_tilt_degrees() == ANGLE
    # The level never changes the angle.
    assert place(variant="angled", level=8).warning_tilt_degrees() == -ANGLE
