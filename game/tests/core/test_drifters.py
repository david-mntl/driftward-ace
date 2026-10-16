"""Level table, spawner, base, registry and meteorite tests.

Contract: docs/contracts/systems/drifters.md, Rules. Tasks:
docs/contracts/DRA-29/tasks/DRA-29-07-qa-engineer.md and
docs/contracts/DRA-39/tasks/DRA-39-06-qa-engineer.md. One test per behavior they list. The
tuning records are built here from the GDD values below, never read from game/tuning/, and
no expected number is imported from the code under test. The satellite is in test_satellite.py.
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
from core.drifters.satellite import Satellite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
    VariantTuning,
)
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

REHIT_COOLDOWN: int = 180
"""ticks. Source: 05-lives-and-damage.md, rehit_cooldown (guess)."""

REHIT_DIM: float = 0.75
"""× brightness while cooling. Source: 05-lives-and-damage.md, rehit_dim (guess)."""

SIZES: dict[str, tuple[float, float]] = {
    "small": (20, 10),
    "medium": (28, 14),
    "big": (40, 20),
}
"""Variant name to (width, hitbox radius), px. Source: drifters/01-meteorite.md, variants
(guess)."""

START_Y: dict[str, float] = {"small": -10, "medium": -14, "big": -20}
"""Start y by variant, px: -width / 2. Source: drifters/01-meteorite.md, start_y (guess)."""


def make_tuning(
    *,
    hazard_scaling: bool = True,
    timer_scaling: bool = True,
    hazards: HazardRules | None = None,
) -> DrifterTuning:
    """Build the meteorite tuning from the GDD values above.

    `hazards` None leaves the field out, so the tuning holds the default hazard rules.
    """
    variants: dict[str, VariantTuning] = {
        name: VariantTuning(width=width, height=width, hitbox=(Circle(0, 0, radius),))
        for name, (width, radius) in SIZES.items()
    }
    tuning: DrifterTuning = DrifterTuning(
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
    return tuning if hazards is None else replace(tuning, hazards=hazards)


TUNING: DrifterTuning = make_tuning()
CTX: TickContext = TickContext(ship=spawn())


def place(
    x: float | None = 300.0,
    *,
    y: float | None = None,
    variant: str | None = None,
    as_level: int | None = None,
    level: int = 1,
    tuning: DrifterTuning = TUNING,
    speed: float | None = None,
) -> Drifter:
    """Spawn a meteorite through the spawner."""
    placement: Placement = Placement(
        DrifterType.METEORITE, x, y=y, variant=variant, as_level=as_level, speed=speed
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
    for name, (width, radius) in SIZES.items():
        sized: Drifter = place(variant=name)
        assert sized.variant == name
        assert sized.y == START_Y[name]
        assert (sized.width, sized.height) == (width, width)
        assert sized.hitbox == (Circle(0, 0, radius),)
    # A placement that sets y keeps it, and so does y = 0.
    assert place(y=123.5, variant="big").y == 123.5
    assert place(y=0.0).y == 0.0
    # A meteorite placement without x raises, naming x.
    for variant in (None, "small", "big"):
        with pytest.raises(ValueError, match="x") as missing:
            place(None, y=50.0, variant=variant)
        assert "meteorite placement needs x" in str(missing.value)
    with pytest.raises(ValueError, match="needs x"):
        place(None)


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


def test_placement_speed_replaces_the_default_level_one_speed() -> None:
    given: float = 3.0
    assert place(speed=given).speed == pytest.approx(given)
    # The level's hazard speed multiplier applies on top, through `level` and through `as_level`.
    for level in range(1, 9):
        expected: float = given * HAZARD_SPEED[level - 1]
        assert place(speed=given, level=level).speed == pytest.approx(expected)
        assert place(speed=given, as_level=level).speed == pytest.approx(expected)
        assert place(speed=given, level=9 - level, as_level=level).speed == pytest.approx(expected)
    # Not the ratio: the default is not used when a speed is set.
    assert place(speed=given).speed != pytest.approx(SPEED_RATIO * TOP_SIDE_SPEED)
    # With hazard_speed_scaling off it is used as given, at every level and as_level.
    off: DrifterTuning = make_tuning(hazard_scaling=False)
    for level in range(1, 9):
        assert place(speed=given, level=level, tuning=off).speed == pytest.approx(given)
        assert place(speed=given, as_level=level, tuning=off).speed == pytest.approx(given)
    # A speed of 0.0 counts as set: it does not fall back to the default.
    for level in (1, 8):
        assert place(speed=0.0, level=level).speed == 0.0
        assert place(speed=0.0, level=level, tuning=off).speed == 0.0
    still: Drifter = advance(place(y=100.0, speed=0.0), WARNING_TICKS)
    assert advance(still, 10).y == 100.0


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
    # The meteorite has no invert: True raises, False is the default and is fine.
    with pytest.raises(ValueError, match="invert"):
        spawn_drifter(Placement(DrifterType.METEORITE, 300, invert=True), 1, TUNING)
    assert spawn_drifter(Placement(DrifterType.METEORITE, 300, invert=False), 1, TUNING).x == 300
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


def test_new_drifter_gets_rehit_values_from_the_hazard_rules() -> None:
    # `hazards` left out: the defaults of 05-lives-and-damage.md.
    drifter: Drifter = place()
    assert drifter.rehit_cooldown_ticks == REHIT_COOLDOWN
    assert drifter.rehit_dim == REHIT_DIM
    assert drifter.rehit_ticks_left == 0
    assert not drifter.has_entered
    # A field left out of HazardRules keeps its own default.
    assert HazardRules().rehit_cooldown_ticks == REHIT_COOLDOWN
    assert HazardRules().rehit_dim == REHIT_DIM
    only_dim: Drifter = place(tuning=make_tuning(hazards=HazardRules(rehit_dim=0.4)))
    assert (only_dim.rehit_cooldown_ticks, only_dim.rehit_dim) == (REHIT_COOLDOWN, 0.4)
    # Values that are set reach the drifter, and never scale with the level or the switches.
    given: HazardRules = HazardRules(rehit_cooldown_ticks=90, rehit_dim=0.5)
    for tuning in (make_tuning(hazards=given), make_tuning(hazards=given, hazard_scaling=False)):
        for level in (1, 8):
            born: Drifter = place(level=level, tuning=tuning)
            assert (born.rehit_cooldown_ticks, born.rehit_dim) == (90, 0.5)
            assert born.rehit_ticks_left == 0
            assert not born.has_entered
        assert place(as_level=5, tuning=tuning).rehit_cooldown_ticks == 90
    zero: Drifter = place(tuning=make_tuning(hazards=HazardRules(rehit_cooldown_ticks=0)))
    assert zero.rehit_cooldown_ticks == 0
    # Updating never changes them.
    played: Drifter = advance(place(tuning=make_tuning(hazards=given)), WARNING_TICKS + 20)
    assert (played.rehit_cooldown_ticks, played.rehit_dim, played.rehit_ticks_left) == (90, 0.5, 0)


def test_may_hit_ship_and_brightness_follow_the_rehit_counter() -> None:
    for drifter in (place(), active(), active(300.0, y=100.0, variant="big")):
        assert drifter.rehit_ticks_left == 0
        assert drifter.may_hit_ship()
        assert drifter.brightness() == 1.0
        for left in (1, 2, 90, REHIT_COOLDOWN - 1, REHIT_COOLDOWN, 1000):
            cooling: Drifter = replace(drifter, rehit_ticks_left=left)
            assert not cooling.may_hit_ship()
            assert cooling.brightness() == REHIT_DIM
        # The counter reaching 0 makes it ready and bright again.
        ready: Drifter = replace(replace(drifter, rehit_ticks_left=1), rehit_ticks_left=0)
        assert ready.may_hit_ship()
        assert ready.brightness() == 1.0
    # The dim is the drifter's own value, from the hazard rules.
    dim_half: Drifter = place(tuning=make_tuning(hazards=HazardRules(rehit_dim=0.5)))
    assert dim_half.brightness() == 1.0
    assert replace(dim_half, rehit_ticks_left=5).brightness() == 0.5
    # A meteorite that is cooling keeps falling as normal, and can hit once the counter is 0.
    cooling_rock: Drifter = replace(active(300.0, y=100.0), rehit_ticks_left=3)
    moved: Drifter = cooling_rock.update(CTX)
    assert moved.y > cooling_rock.y
    assert moved.rehit_ticks_left == 3
    assert not moved.may_hit_ship()


def test_mark_entered_sets_has_entered_only_for_an_active_drifter_partly_on_screen() -> None:
    # Medium rock, 28 x 28: the footprint reaches 14 px from its center.
    cases: list[tuple[float, float, bool]] = [
        (300.0, 200.0, True),
        (300.0, -14.0, False),  # bottom edge on the top edge: touching from outside
        (300.0, -13.9, True),
        (300.0, -1000.0, False),
        (-14.0, 200.0, False),  # right edge on the left wall
        (-13.9, 200.0, True),
        (SCREEN_W + 14.0, 200.0, False),  # left edge on the right wall
        (SCREEN_W + 13.9, 200.0, True),
        (300.0, SCREEN_H + 14.0, False),  # top edge on the floor
        (300.0, SCREEN_H + 13.9, True),
        (-14.0, -14.0, False),  # a corner, touching only at a point
        (-13.9, -13.9, True),
        (-500.0, 900.0, False),
    ]
    for x, y, expected in cases:
        rock: Drifter = active(x, y=y)
        assert not rock.has_entered
        assert rock.mark_entered().has_entered is expected, (x, y)
        assert rock.mark_entered().phase is Phase.ACTIVE
    # The footprint is the variant's width x height: a big rock (40) is on at x = -19.
    assert active(-19.0, y=200.0, variant="big").mark_entered().has_entered
    assert not active(-20.0, y=200.0, variant="big").mark_entered().has_entered
    # Never in WARNING, however well placed.
    warning: Drifter = place(300.0, y=200.0)
    assert warning.phase is Phase.WARNING
    assert not warning.mark_entered().has_entered
    assert not advance(place(300.0, y=200.0), WARNING_TICKS - 1).mark_entered().has_entered
    # Never in GONE.
    gone: Drifter = replace(active(300.0, y=200.0), phase=Phase.GONE)
    assert not gone.mark_entered().has_entered
    # It never clears: once set it stays, wherever the drifter goes.
    entered: Drifter = active(300.0, y=200.0).mark_entered()
    assert entered.has_entered
    for x, y in ((300.0, 200.0), (-500.0, 200.0), (300.0, 900.0), (300.0, -900.0)):
        assert replace(entered, x=x, y=y).mark_entered().has_entered
    assert entered.mark_entered().mark_entered().has_entered
    # Nothing else changes.
    assert replace(entered.mark_entered(), has_entered=False) == replace(entered, has_entered=False)


def test_is_off_screen_rules() -> None:
    def entered(x: float, y: float, variant: str | None = None) -> Drifter:
        """An ACTIVE rock that has already been on screen, put at (x, y)."""
        return replace(active(x, y=y, variant=variant), has_entered=True)

    # WARNING: never, even far above the screen or past a side, and even once entered.
    for x, y in ((300.0, -1000.0), (-500.0, 200.0), (300.0, 900.0)):
        assert not place(x, y=y).is_off_screen()
        assert not replace(place(x, y=y), has_entered=True).is_off_screen()
    # GONE: never.
    assert not replace(entered(300.0, 600.0), phase=Phase.GONE).is_off_screen()
    # A rock that has not entered is never off screen, wherever it is.
    for x, y in ((300.0, 600.0), (300.0, 494.0), (-50.0, 200.0), (700.0, 200.0), (-14.0, 200.0)):
        assert not active(x, y=y).is_off_screen()
    # Entered, medium (28 x 28): the top edge is y - 14.
    assert not entered(300.0, 479.0).is_off_screen()
    assert not entered(300.0, 493.9).is_off_screen()
    assert entered(300.0, 494.0).is_off_screen()
    assert entered(300.0, 600.0).is_off_screen()
    # Never at the top.
    assert not entered(300.0, -1000.0).is_off_screen()
    assert not entered(300.0, -14.0).is_off_screen()
    # Sides: fully past a wall.
    assert not entered(-13.9, 200.0).is_off_screen()
    assert entered(-14.0, 200.0).is_off_screen()
    assert not entered(SCREEN_W + 13.9, 200.0).is_off_screen()
    assert entered(SCREEN_W + 14.0, 200.0).is_off_screen()
    # Size matters: a big rock (40) is still on at x = -19.
    assert not entered(-19.0, 200.0, "big").is_off_screen()
    assert entered(-20.0, 200.0, "big").is_off_screen()
    # It falls off the floor after a run of ticks: 103 active updates from -14, run order
    # (update, then mark_entered). It is never removed before it has entered.
    drifter: Drifter = active(300.0, y=-14.0)
    assert not drifter.is_off_screen()
    ticks: int = 0
    while not drifter.is_off_screen():
        drifter = drifter.update(CTX).mark_entered()
        ticks += 1
        assert ticks <= 103
    assert ticks == 103
    assert drifter.has_entered


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


def test_registry_holds_both_drifters_and_refuses_duplicates_and_abstract_classes() -> None:
    assert {DrifterType.METEORITE, DrifterType.SATELLITE} <= available_drifters()
    assert drifter_class(DrifterType.METEORITE) is Meteorite
    assert drifter_class(DrifterType.SATELLITE) is Satellite
    before: frozenset[DrifterType] = available_drifters()

    @dataclass(frozen=True, slots=True, kw_only=True)
    class SecondMeteorite(Drifter):
        drifter_type: ClassVar[DrifterType] = DrifterType.METEORITE

        @classmethod
        def start_position(
            cls, x: float | None, y: float | None, width: float, height: float, invert: bool
        ) -> tuple[float, float]:
            return (0.0, 0.0)

        def update(self, ctx: TickContext) -> "SecondMeteorite":
            return self

        def effect_on_touch(self) -> TouchEffect:
            return TouchEffect.NONE

    with pytest.raises(ValueError, match="meteorite"):
        register_drifter(SecondMeteorite)

    @dataclass(frozen=True, slots=True, kw_only=True)
    class SecondSatellite(Drifter):
        drifter_type: ClassVar[DrifterType] = DrifterType.SATELLITE

        @classmethod
        def start_position(
            cls, x: float | None, y: float | None, width: float, height: float, invert: bool
        ) -> tuple[float, float]:
            return (0.0, 0.0)

        def update(self, ctx: TickContext) -> "SecondSatellite":
            return self

        def effect_on_touch(self) -> TouchEffect:
            return TouchEffect.NONE

    with pytest.raises(ValueError, match="satellite"):
        register_drifter(SecondSatellite)

    @dataclass(frozen=True, slots=True, kw_only=True)
    class NoStart(Drifter):
        drifter_type: ClassVar[DrifterType] = DrifterType.METEORITE

        def update(self, ctx: TickContext) -> "NoStart":
            return self

        def effect_on_touch(self) -> TouchEffect:
            return TouchEffect.NONE

    # No start_position: still abstract, so it is refused.
    with pytest.raises(TypeError):
        register_drifter(cast(type[Drifter], NoStart))

    assert available_drifters() == before
    assert drifter_class(DrifterType.METEORITE) is Meteorite
    assert drifter_class(DrifterType.SATELLITE) is Satellite
