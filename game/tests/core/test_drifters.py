"""Level table, spawner, registry and meteorite tests.

Contract: docs/contracts/systems/drifters.md, Rules. Task:
docs/contracts/DRA-29/tasks/DRA-29-07-qa-engineer.md. One test per behavior it lists. The
tuning records are built here from the GDD values below, never read from game/tuning/, and
no expected number is imported from the code under test.
"""

from dataclasses import dataclass, replace
from typing import ClassVar, cast

import pytest

from core.collision import Circle
from core.drifters.base import (
    Drifter,
    DrifterType,
    Phase,
    TickContext,
    TouchEffect,
)
from core.drifters.meteorite import Meteorite
from core.drifters.registry import available_drifters, drifter_class, register_drifter
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.levels import check_level, hazard_speed_mult, level_at, timer_mult
from core.ship import Ship, spawn

THRUST_SIDE: float = 0.42
"""px/tick². Source: 04-ship.md, Values, thrust_side (guess)."""

DRAG_X: float = 0.94
"""× per tick. Source: 04-ship.md, Values, drag_x (guess)."""

TOP_SIDE_SPEED: float = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
"""px/tick, about 6.58. Source: 04-ship.md, derived values."""

SPEED_RATIO: float = 0.75
"""Level 1 speed as a multiple of the top sideways speed. Fixed test value, not the live
tuning file."""

WARNING_TICKS: int = 30
"""Fixed test value for the warning length, not the live tuning file."""

GRAZE_MARGIN: float = 14.0
"""px. Source: 06-scoring.md, graze_margin (locked)."""

SCREEN_W: int = 640
"""px. Source: 03-world-and-camera.md, screen_w (guess)."""

SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, screen_h (guess)."""

HAZARD_SPEED: tuple[float, ...] = (1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42)
"""Hazard speed × for Levels 1 to 8. Source: 08-difficulty.md, level table (locked)."""

TIMER: tuple[float, ...] = (1.00, 0.94, 0.89, 0.85, 0.81, 0.77, 0.74, 0.70)
"""Timer × for Levels 1 to 8. Source: 08-difficulty.md, level table (guess)."""

SIZES: dict[str, tuple[float, float]] = {
    "small": (20, 10),
    "medium": (28, 14),
    "big": (40, 20),
}
"""Variant name to (width, hitbox radius), px. Source: drifters/01-meteorite.md, variants
(guess)."""

START_Y: dict[str, float] = {"small": -10, "medium": -14, "big": -20}
"""Start y by variant, px: -width / 2. Source: drifters/01-meteorite.md, start_y (guess)."""


def make_tuning(*, hazard_scaling: bool = True, timer_scaling: bool = True) -> DrifterTuning:
    """Build the meteorite tuning from the GDD values above."""
    variants: dict[str, VariantTuning] = {
        name: VariantTuning(width=width, height=width, hitbox=(Circle(0, 0, radius),))
        for name, (width, radius) in SIZES.items()
    }
    return DrifterTuning(
        drifters={
            DrifterType.METEORITE: DrifterTypeTuning(
                variants=variants,
                default_variant="medium",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            )
        },
        switches=PlaytestSwitches(hazard_speed_scaling=hazard_scaling, timer_scaling=timer_scaling),
    )


TUNING: DrifterTuning = make_tuning()
CTX: TickContext = TickContext(ship=spawn())


def place(
    x: float = 300.0,
    *,
    y: float | None = None,
    variant: str | None = None,
    as_level: int | None = None,
    level: int = 1,
    tuning: DrifterTuning = TUNING,
) -> Drifter:
    """Spawn a meteorite through the spawner."""
    placement: Placement = Placement(
        DrifterType.METEORITE, x, y=y, variant=variant, as_level=as_level
    )
    return spawn_drifter(placement, level, tuning)


def advance(drifter: Drifter, ticks: int, ctx: TickContext = CTX) -> Drifter:
    """Update the drifter `ticks` times."""
    for _ in range(ticks):
        drifter = drifter.update(ctx)
    return drifter


def active(x: float = 300.0, *, y: float | None = None, variant: str | None = None) -> Drifter:
    """A meteorite that has just turned ACTIVE at (x, y)."""
    drifter: Drifter = advance(place(x, y=y, variant=variant), WARNING_TICKS)
    assert drifter.phase is Phase.ACTIVE
    return drifter


def test_level_table_matches_the_gdd() -> None:
    for level in range(1, 9):
        assert hazard_speed_mult(level) == pytest.approx(HAZARD_SPEED[level - 1])
        assert timer_mult(level) == pytest.approx(TIMER[level - 1])
        check_level(level)
    for bad in (0, 9, -1, 100):
        with pytest.raises(ValueError, match=str(bad)):
            hazard_speed_mult(bad)
        with pytest.raises(ValueError, match=str(bad)):
            timer_mult(bad)
        with pytest.raises(ValueError, match=str(bad)):
            check_level(bad)
    # Only Level 1 has a start (0 m), so every distance is Level 1.
    for meters in (0, 1, 500, 10_000, 1_000_000):
        assert level_at(meters) == 1


def test_default_placement_gets_default_variant_and_start_y() -> None:
    drifter: Drifter = place()
    assert drifter.variant == "medium"
    assert drifter.y == -14
    assert drifter.x == 300
    assert (drifter.width, drifter.height) == (28, 28)
    assert drifter.hitbox == (Circle(0, 0, 14),)
    assert drifter.uid == 0
    assert not drifter.hit_ship
    for name, (width, radius) in SIZES.items():
        sized: Drifter = place(variant=name)
        assert sized.variant == name
        assert sized.y == START_Y[name]
        assert (sized.width, sized.height) == (width, width)
        assert sized.hitbox == (Circle(0, 0, radius),)
    # A placement that sets y keeps it.
    assert place(y=123.5, variant="big").y == 123.5


def test_speed_is_ratio_times_top_side_speed_times_hazard_speed() -> None:
    level_one: float = SPEED_RATIO * TOP_SIDE_SPEED
    assert level_one == pytest.approx(4.935, abs=0.001)
    assert place().speed == pytest.approx(level_one)
    for level in range(1, 9):
        expected: float = level_one * HAZARD_SPEED[level - 1]
        assert place(level=level).speed == pytest.approx(expected)
        assert place(as_level=level).speed == pytest.approx(expected)
        # as_level beats the run's level, whichever is higher.
        assert place(level=9 - level, as_level=level).speed == pytest.approx(expected)
    assert place(level=8).speed == pytest.approx(level_one * 1.42)
    # Every variant has the same speed.
    for name in SIZES:
        assert place(variant=name, level=4).speed == pytest.approx(level_one * 1.18)
    # With the switch off, Level 1 speed at every level and every as_level.
    off: DrifterTuning = make_tuning(hazard_scaling=False)
    for level in range(1, 9):
        assert place(level=level, tuning=off).speed == pytest.approx(level_one)
        assert place(as_level=level, tuning=off).speed == pytest.approx(level_one)
        assert place(level=3, as_level=level, tuning=off).speed == pytest.approx(level_one)


def test_entry_warning_is_30_ticks_at_every_level() -> None:
    for tuning in (make_tuning(), make_tuning(timer_scaling=False)):
        for level in range(1, 9):
            assert place(level=level, tuning=tuning).warning_ticks == WARNING_TICKS
            assert place(as_level=level, tuning=tuning).warning_ticks == WARNING_TICKS
    # Playing it out: 30 updates at Level 8 and 29 still warning.
    drifter: Drifter = place(level=8)
    assert advance(drifter, WARNING_TICKS - 1).phase is Phase.WARNING
    assert advance(drifter, WARNING_TICKS).phase is Phase.ACTIVE


def test_bad_placements_raise_value_error() -> None:
    with pytest.raises(ValueError, match="huge") as unknown:
        place(variant="huge")
    assert "meteorite" in str(unknown.value)
    for bad in (0, 9, -3):
        with pytest.raises(ValueError, match=str(bad)):
            place(as_level=bad)
        with pytest.raises(ValueError, match=str(bad)):
            place(level=bad)
    with pytest.raises(ValueError, match="specialty"):
        spawn_drifter(Placement(DrifterType.METEORITE, 300, specialty_enabled=True), 1, TUNING)
    for switch in (False, None):
        drifter: Drifter = spawn_drifter(
            Placement(DrifterType.METEORITE, 300, specialty_enabled=switch), 1, TUNING
        )
        assert drifter.specialty is None


def test_new_meteorite_warns_for_30_states_then_turns_active_in_place() -> None:
    drifter: Drifter = place(250.0, y=-14.0)
    for count in range(WARNING_TICKS):
        # State after `count` updates: the born state, then the next 29.
        assert drifter.phase is Phase.WARNING
        assert drifter.ticks_in_phase == count
        assert drifter.current_hitbox() == ()
        assert drifter.graze_zone() == ()
        assert (drifter.x, drifter.y) == (250.0, -14.0)
        drifter = drifter.update(CTX)
    # The 30th update.
    assert drifter.phase is Phase.ACTIVE
    assert drifter.ticks_in_phase == 0
    assert (drifter.x, drifter.y) == (250.0, -14.0)
    assert drifter.current_hitbox() == (Circle(250.0, -14.0, 14),)
    for name, (_, radius) in SIZES.items():
        living: Drifter = advance(place(250.0, variant=name), WARNING_TICKS)
        assert living.current_hitbox() == (Circle(250.0, START_Y[name], radius),)


def test_active_meteorite_falls_straight_down_at_its_speed() -> None:
    start: Drifter = active(222.0, y=-14.0)
    speed: float = SPEED_RATIO * TOP_SIDE_SPEED
    assert start.speed == pytest.approx(speed)
    ships: list[Ship] = [
        spawn(),
        Ship(x=16.0, y=100.0, vx=-6.0, vy=0.0),
        Ship(x=600.0, y=470.0, vx=6.0, vy=5.5),
        Ship(x=222.0, y=-14.0, vx=0.0, vy=0.0),
    ]
    drifter: Drifter = start
    for n in range(1, 61):
        drifter = drifter.update(TickContext(ship=ships[n % len(ships)]))
        assert drifter.phase is Phase.ACTIVE
        assert drifter.ticks_in_phase == n
        assert drifter.x == 222.0
        assert drifter.y == pytest.approx(-14.0 + n * speed)
    # The input is never mutated.
    assert (start.y, start.ticks_in_phase) == (-14.0, 0)


def test_is_off_screen_rules() -> None:
    # WARNING: never, even far above the screen or past a side.
    for x, y in ((300.0, -1000.0), (-500.0, 200.0), (300.0, 900.0)):
        assert not place(x, y=y).is_off_screen()
    # Active, medium (28 x 28): the top edge is y - 14.
    assert not active(300.0, y=479.0).is_off_screen()
    assert not active(300.0, y=493.9).is_off_screen()
    assert active(300.0, y=494.0).is_off_screen()
    assert active(300.0, y=600.0).is_off_screen()
    # Never at the top.
    assert not active(300.0, y=-1000.0).is_off_screen()
    assert not active(300.0, y=-14.0).is_off_screen()
    # Sides: fully past a wall.
    assert not active(-13.9, y=200.0).is_off_screen()
    assert active(-14.0, y=200.0).is_off_screen()
    assert not active(SCREEN_W + 13.9, y=200.0).is_off_screen()
    assert active(SCREEN_W + 14.0, y=200.0).is_off_screen()
    # Size matters: a big rock (40) is still on at x = -19.
    assert not active(-19.0, y=200.0, variant="big").is_off_screen()
    assert active(-20.0, y=200.0, variant="big").is_off_screen()
    # It falls off the floor after a run of ticks: 103 active updates from -14 at Level 1.
    drifter: Drifter = active(300.0, y=-14.0)
    ticks: int = 0
    while not drifter.is_off_screen():
        drifter = drifter.update(CTX)
        ticks += 1
    assert ticks == 103


def test_warning_center_moves_just_inside_the_screen() -> None:
    # Above the screen: at its x, against the top edge (y = height / 2).
    assert place(300.0, y=-14.0).warning_center() == (300.0, 14.0)
    assert place(300.0, y=-1000.0).warning_center() == (300.0, 14.0)
    assert place(300.0, y=-20.0, variant="big").warning_center() == (300.0, 20.0)
    # On the screen and away from the edges: its own spot.
    assert place(300.0, y=200.0).warning_center() == (300.0, 200.0)
    # Off a side: just inside that side, in line with it.
    assert place(-50.0, y=200.0).warning_center() == (14.0, 200.0)
    assert place(SCREEN_W + 50.0, y=200.0).warning_center() == (SCREEN_W - 14.0, 200.0)
    # Off the bottom: just inside the floor.
    assert place(300.0, y=SCREEN_H + 50.0).warning_center() == (300.0, SCREEN_H - 14.0)


def test_graze_zone_is_the_hitbox_grown_by_14_and_touch_is_a_hit() -> None:
    drifter: Drifter = active(300.0, y=100.0)
    assert drifter.effect_on_touch() is TouchEffect.HIT
    assert drifter.graze_zone() == (Circle(300.0, 100.0, 14 + GRAZE_MARGIN),)
    big: Drifter = active(300.0, y=100.0, variant="big")
    assert big.graze_zone() == (Circle(300.0, 100.0, 20 + GRAZE_MARGIN),)
    assert place().effect_on_touch() is TouchEffect.HIT


def test_meteorite_hits_once() -> None:
    drifter: Drifter = place()
    assert drifter.may_hit_ship()
    assert active().may_hit_ship()
    hit: Drifter = replace(active(), hit_ship=True)
    assert not hit.may_hit_ship()
    # It keeps falling and stays a meteorite that can't hit again.
    assert not hit.update(CTX).may_hit_ship()
    assert hit.update(CTX).y > hit.y


def test_registry_holds_the_meteorite_and_refuses_duplicates_and_abstract_classes() -> None:
    assert DrifterType.METEORITE in available_drifters()
    assert drifter_class(DrifterType.METEORITE) is Meteorite
    before: frozenset[DrifterType] = available_drifters()

    @dataclass(frozen=True, slots=True, kw_only=True)
    class SecondMeteorite(Drifter):
        drifter_type: ClassVar[DrifterType] = DrifterType.METEORITE

        @classmethod
        def default_y(cls, height: float) -> float:
            return 0.0

        def update(self, ctx: TickContext) -> "SecondMeteorite":
            return self

        def effect_on_touch(self) -> TouchEffect:
            return TouchEffect.NONE

        def may_hit_ship(self) -> bool:
            return True

    with pytest.raises(ValueError, match="meteorite"):
        register_drifter(SecondMeteorite)

    @dataclass(frozen=True, slots=True, kw_only=True)
    class HalfBuilt(Drifter):
        drifter_type: ClassVar[DrifterType] = DrifterType.METEORITE

        @classmethod
        def default_y(cls, height: float) -> float:
            return 0.0

        def update(self, ctx: TickContext) -> "HalfBuilt":
            return self

        def effect_on_touch(self) -> TouchEffect:
            return TouchEffect.NONE

    with pytest.raises(TypeError):
        register_drifter(cast(type[Drifter], HalfBuilt))

    assert available_drifters() == before
    assert drifter_class(DrifterType.METEORITE) is Meteorite
