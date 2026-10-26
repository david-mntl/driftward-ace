"""The electric ball, the base rules it relies on, and electric balls inside the run.

Contract: docs/contracts/systems/drifters/electric-ball/core.md (Diagram, Interface, Rules),
docs/contracts/systems/drifters/shared/base.md (Entering, Leaving, Re-hit cooldown, Timers),
docs/contracts/systems/drifters/shared/spawner-registry-tuning.md (Spawner), docs/contracts/
systems/run.md (A playing tick, Logging). Task: docs/contracts/DRA-111/tasks/
DRA-111-03-qa-engineer.md. One test per behavior it lists.

The tuning records are built here from the GDD values below, the way `app.tuning` builds them,
never read from game/tuning/, and no expected number is imported from the code under test. The
ship against every variant is in test_collision.py, the wave files in test_wave_files.py.
"""

import copy
import logging
import math
import re
from dataclasses import replace
from fractions import Fraction

import pytest

from core.collision import Box, Circle, hitboxes_overlap
from core.drifters.base import (
    Drifter,
    DrifterType,
    DrifterTypeExtra,
    Phase,
    TickContext,
    TouchEffect,
    VariantExtra,
)
from core.drifters.electric_ball import (
    ElectricBall,
    ElectricBallTypeExtra,
    ElectricBallVariantExtra,
    check_electric_ball_variant,
    electric_ball_hitbox,
)
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
    VariantTuning,
)
from core.run import Run, add_drifters, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust, ship_hitbox

BALL_SIZE: float = 16.0
PULSE_RADIUS: float = 64.0
"""px. Source: drifters/10-electric-ball.md, ball_size, pulse_radius (guess)."""

SPEED_RATIO: float = 0.375
"""Source: drifters/10-electric-ball.md, speed_ratio (guess)."""

THRUST_SIDE: float = 0.42
DRAG_X: float = 0.94
TOP_SIDE_SPEED: float = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
"""px/tick, about 6.58. Source: 04-ship.md, derived values."""

LEVEL_ONE_SPEED: float = SPEED_RATIO * TOP_SIDE_SPEED
"""About 2.4675 px/tick. Source: drifters/10-electric-ball.md, speed (about 2.5)."""

CHARGE_TICKS: int = 120
FIRE_TICKS: int = 120
CHARGE_RAYS: int = 4
RAY_LENGTH: float = 6.0
RAY_WIDTH: float = 1.0
OUTLINE_WIDTH: float = 1.0
RIM_WIDTH: float = 2.0
FILL_OPACITY: float = 0.35
"""Source: drifters/10-electric-ball.md, Values (charge_ticks, fire_ticks, fill_opacity,
placeholder_look); drifters/03-chain-lightning.md, Values (charge_rays, ray_length)."""

WARNING_TICKS: int = 60
WARNING_HALF: float = 12.0
"""ticks, and half of the 24 px entry warning. Source: 07-drifters.md, entry_warning_ticks,
entry_warning_size (guess)."""

TELEGRAPH_MIN: int = 45
"""ticks. Source: 07-drifters.md, telegraph_min (locked)."""

GRAZE_MARGIN: float = 14.0
"""px. Source: 06-scoring.md, graze_margin (locked)."""

DRAW_MARGIN: float = 1.5
"""Px added to the pulse box's half side. Source: electric-ball/core.md, Rules, Drawn parts."""

HAZARD_SPEED: tuple[float, ...] = (1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42)
TIMER: tuple[float, ...] = (1.00, 0.94, 0.89, 0.85, 0.81, 0.77, 0.74, 0.70)
"""Source: 08-difficulty.md, the Hazard speed x and Timer x rows (Levels 1 to 8)."""

SCALED_CHARGE: tuple[int, ...] = (120, 113, 107, 102, 98, 93, 89, 84)
"""120 x each Timer x, rounded up (112.8, 106.8, 102.0, 97.2, 92.4, 88.8, 84.0)."""

SCREEN_W: float = 640.0
SCREEN_H: float = 480.0
"""px. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

REHIT_COOLDOWN: int = 180
REHIT_DIM: float = 0.75
"""Source: 05-lives-and-damage.md, rehit_cooldown, rehit_dim (guess)."""

LIVES_START: int = 3
INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

RUN_LOGGER = "core.run"
"""Logger name. Source: systems/run.md, Logging."""

NO_KEY = Thrust()

SCROLLING: Scroll = Scroll(ticks=100, scrolled_ticks=70)
"""A scroll already moving: the next step moves the world 1.1 px."""

SAFE_SHIP: Ship = Ship(x=100.0, y=463.0, vx=0.0, vy=0.0)
"""A resting ship low on the screen and far left of the ball's column (x 320, pulse reach 256 to
384), so it is never touched."""

CTX: TickContext = TickContext(ship=Ship(x=320.0, y=400.0, vx=0.0, vy=0.0))
"""A context with the ship and a world standing still. The ball reads neither."""

TYPE_EXTRA: ElectricBallTypeExtra = ElectricBallTypeExtra(
    charge_ticks=CHARGE_TICKS,
    fire_ticks=FIRE_TICKS,
    charge_rays=CHARGE_RAYS,
    ray_length=RAY_LENGTH,
    ray_width=RAY_WIDTH,
    outline_width=OUTLINE_WIDTH,
    rim_width=RIM_WIDTH,
    fill_opacity=FILL_OPACITY,
)
VARIANT_EXTRA: ElectricBallVariantExtra = ElectricBallVariantExtra(pulse_radius=PULSE_RADIUS)

PULSE_BOX_SIDE: float = 2 * (max(PULSE_RADIUS, BALL_SIZE / 2 + RAY_LENGTH) + DRAW_MARGIN)
"""2 x (64 + 1.5) = 131: the circle is wider than the rays (8 + 6 = 14)."""


def make_tuning(
    *,
    hazards: HazardRules | None = None,
    switches: PlaytestSwitches | None = None,
    variant_extra: VariantExtra | None = VARIANT_EXTRA,
    type_extra: DrifterTypeExtra | None = TYPE_EXTRA,
    charge_ticks: int | None = None,
) -> DrifterTuning:
    """Build the electric ball and meteorite tuning from the GDD values above.

    The ball's record is built the way the contract says `app.tuning` builds it: width and
    height are the ball size, the hitbox is the one pulse circle, `extra` holds the pulse radius.
    `variant_extra` and `type_extra` can be swapped for wrong ones to test the refusals;
    `charge_ticks` replaces the file's charge.
    """
    if charge_ticks is not None:
        type_extra = replace(TYPE_EXTRA, charge_ticks=charge_ticks)
    tuning: DrifterTuning = DrifterTuning(
        drifters={
            DrifterType.ELECTRIC_BALL: DrifterTypeTuning(
                variants={
                    "standard": VariantTuning(
                        width=BALL_SIZE,
                        height=BALL_SIZE,
                        hitbox=(Circle(0.0, 0.0, PULSE_RADIUS),),
                        extra=variant_extra,
                    )
                },
                default_variant="standard",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
                extra=type_extra,
            ),
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=(Circle(0, 0, 14),))},
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=WARNING_TICKS,
            ),
        },
        switches=PlaytestSwitches() if switches is None else switches,
    )
    return tuning if hazards is None else replace(tuning, hazards=hazards)


TUNING: DrifterTuning = make_tuning()
NO_SCALING: DrifterTuning = make_tuning(
    switches=PlaytestSwitches(hazard_speed_scaling=False, timer_scaling=False)
)


def ball(
    x: float | None = 320.0,
    y: float | None = None,
    *,
    invert: bool = False,
    level: int = 1,
    as_level: int | None = None,
    specialty_enabled: bool | None = None,
    speed: float | None = None,
    seed: int | None = None,
    tuning: DrifterTuning = TUNING,
) -> ElectricBall:
    """Spawn an electric ball through the spawner, in WARNING. No y: touching the top edge."""
    placement: Placement = Placement(
        DrifterType.ELECTRIC_BALL,
        x,
        y,
        as_level=as_level,
        specialty_enabled=specialty_enabled,
        invert=invert,
        speed=speed,
        seed=seed,
    )
    spawned: Drifter = spawn_drifter(placement, level, tuning)
    assert isinstance(spawned, ElectricBall)
    return spawned


def advance[T: Drifter](drifter: T, ticks: int, ctx: TickContext = CTX) -> T:
    """Update the drifter `ticks` times."""
    for _ in range(ticks):
        drifter = drifter.update(ctx)
    return drifter


def active(
    x: float = 320.0,
    y: float | None = None,
    *,
    level: int = 1,
    speed: float | None = None,
    tuning: DrifterTuning = TUNING,
) -> ElectricBall:
    """A ball that has just turned ACTIVE, on its first state (`ticks_in_phase` 0)."""
    spawned = advance(ball(x, y, level=level, speed=speed, tuning=tuning), WARNING_TICKS)
    assert spawned.phase is Phase.ACTIVE
    assert spawned.ticks_in_phase == 0
    return spawned


def states(start: ElectricBall, ticks: int, ctx: TickContext = CTX) -> list[ElectricBall]:
    """`start` and the states after each of `ticks` updates: `ticks` + 1 states."""
    found: list[ElectricBall] = [start]
    for _ in range(ticks):
        found.append(found[-1].update(ctx))
    return found


def expected_rays(cycle_tick: int, charge: int, rays: int = CHARGE_RAYS) -> int:
    """The contract's charge rays on a charging tick: 1 + cycle_tick x rays // charge."""
    return 1 + cycle_tick * rays // charge


def message(text: str) -> str:
    """A `pytest.raises` pattern that matches the whole message."""
    return f"^{re.escape(text)}$"


def scaled_ticks(ticks: int, level: int) -> int:
    """A tick count at a level's Timer x, rounded up, worked out in exact fractions."""
    return math.ceil(Fraction(ticks) * Fraction(str(TIMER[level - 1])))


def test_it_is_born_in_warning_at_its_x_against_the_top_edge_and_invert_changes_nothing() -> None:
    plain = ball(200.0)
    assert plain.phase is Phase.WARNING
    assert plain.ticks_in_phase == 0
    assert plain.drifter_type is DrifterType.ELECTRIC_BALL
    assert (plain.width, plain.height) == (BALL_SIZE, BALL_SIZE)
    assert plain.hitbox == (Circle(0.0, 0.0, PULSE_RADIUS),)
    assert plain.effect_on_touch() is TouchEffect.HIT
    # No y: the ball's box touches the top edge from above, fully off screen.
    assert (plain.x, plain.y) == (200.0, -BALL_SIZE / 2)
    assert plain.y + plain.height / 2 == 0.0
    assert not plain.ball_on_screen()
    # The shared entry warning at its x against the top edge, 12 px clear of each wall.
    assert plain.warning_center() == pytest.approx((200.0, WARNING_HALF))
    for x, wanted in ((3.0, 12.0), (12.0, 12.0), (637.0, 628.0), (320.0, 320.0)):
        assert ball(x).warning_center() == pytest.approx((wanted, WARNING_HALF)), x
    # It doesn't move or turn ACTIVE while the warning shows, and then appears where it was.
    waiting = plain
    for _ in range(WARNING_TICKS - 1):
        waiting = waiting.update(CTX)
        assert waiting.phase is Phase.WARNING
        assert (waiting.x, waiting.y) == (200.0, -8.0)
    appeared = waiting.update(CTX)
    assert appeared.phase is Phase.ACTIVE
    assert (appeared.x, appeared.y, appeared.ticks_in_phase) == (200.0, -8.0, 0)
    # x is required, with or without a y.
    for y in (None, 100.0):
        with pytest.raises(ValueError, match=message("electric_ball placement needs x")):
            ball(None, y)
    # A placed y is kept, on screen or not.
    for y in (100.0, 0.0, 479.0, -50.0):
        placed = ball(200.0, y)
        assert (placed.x, placed.y) == (200.0, y)
    assert ball(200.0, 100.0).ball_on_screen()
    # invert changes nothing: the very same ball.
    flipped = ball(200.0, invert=True)
    assert flipped == plain
    assert flipped.warning_center() == plain.warning_center()
    assert advance(flipped, 100).y == advance(plain, 100).y
    assert ball(200.0, 100.0, invert=True) == ball(200.0, 100.0)


def test_a_specialty_a_seed_and_the_wrong_extras_are_refused_in_the_contracts_order() -> None:
    no_specialty = message("electric_ball has no specialty")
    no_seed = message("electric_ball has no seed")
    no_pulse = message("electric_ball variant 'standard' has no pulse_radius")
    no_type_values = message("electric_ball tuning has no type values")
    # Each alone.
    with pytest.raises(ValueError, match=no_specialty):
        ball(specialty_enabled=True)
    with pytest.raises(ValueError, match=no_seed):
        ball(seed=0)
    with pytest.raises(ValueError, match=no_seed):
        ball(seed=4_294_967_295)
    for wrong_variant in (None, VariantExtra()):
        with pytest.raises(ValueError, match=no_pulse):
            ball(tuning=make_tuning(variant_extra=wrong_variant))
    for wrong_type in (None, DrifterTypeExtra()):
        with pytest.raises(ValueError, match=no_type_values):
            ball(tuning=make_tuning(type_extra=wrong_type))
    # Specialty off and left out are fine, and so are invert, as_level and a speed.
    assert ball(specialty_enabled=False).specialty is None
    assert ball(specialty_enabled=None).specialty is None
    ball(invert=True, as_level=3, speed=2.0, y=100.0)
    # The order: the missing x first (the start), then the seed (the spawner), then in `born` the
    # specialty, the variant's extra and the type's.
    both_wrong = make_tuning(variant_extra=None, type_extra=None)
    with pytest.raises(ValueError, match=message("electric_ball placement needs x")):
        ball(None, seed=1, specialty_enabled=True, tuning=both_wrong)
    with pytest.raises(ValueError, match=no_seed):
        ball(seed=1, specialty_enabled=True, tuning=both_wrong)
    with pytest.raises(ValueError, match=no_specialty):
        ball(specialty_enabled=True, tuning=both_wrong)
    with pytest.raises(ValueError, match=no_pulse):
        ball(tuning=both_wrong)
    with pytest.raises(ValueError, match=no_type_values):
        ball(tuning=make_tuning(type_extra=None))


def test_it_falls_by_its_speed_on_every_active_tick_and_reads_neither_ship_nor_scroll() -> None:
    contexts: tuple[TickContext, ...] = (
        CTX,
        TickContext(ship=Ship(x=320.0, y=10.0, vx=5.0, vy=-3.0), scroll_step_px=1.1),
        TickContext(ship=Ship(x=0.0, y=480.0, vx=-6.0, vy=9.0), scroll_step_px=40.0),
    )
    start = active(250.0, 100.0)
    assert start.speed == pytest.approx(LEVEL_ONE_SPEED)
    runs: list[list[ElectricBall]] = [states(start, 100, ctx) for ctx in contexts]
    for n in range(101):
        for run in runs:
            state = run[n]
            assert state.phase is Phase.ACTIVE
            assert state.ticks_in_phase == n
            assert state.x == 250.0
            assert state.y == pytest.approx(100.0 + n * LEVEL_ONE_SPEED, abs=1e-9)
        # The three contexts give the very same state.
        assert runs[0][n] == runs[1][n] == runs[2][n]
    # In WARNING it does not move: 59 updates keep it, whatever the context.
    waiting = ball(250.0, 100.0)
    for ctx in contexts:
        held = advance(waiting, WARNING_TICKS - 1, ctx)
        assert held.phase is Phase.WARNING
        assert (held.x, held.y) == (250.0, 100.0)
    # From the top it is the same fall: -8 + n x speed.
    from_top = active(250.0)
    after = advance(from_top, 40, contexts[1])
    assert after.y == pytest.approx(-8.0 + 40 * LEVEL_ONE_SPEED, abs=1e-9)
    assert after.x == 250.0


@pytest.mark.parametrize("level", [1, 8])
def test_the_cycle_runs_charge_then_fire_tick_for_tick_over_two_whole_cycles(level: int) -> None:
    charge = SCALED_CHARGE[level - 1]
    cycle = charge + FIRE_TICKS
    start = active(320.0, 100.0, level=level, speed=0.5)
    assert start.charge_ticks == charge
    assert start.fire_ticks == FIRE_TICKS
    found = states(start, 2 * cycle)
    assert all(state.ball_on_screen() for state in found)
    for n, state in enumerate(found):
        c = n % cycle
        assert state.ticks_in_phase == n
        assert state.is_charging() is (c < charge), n
        assert state.is_firing() is (c >= charge), n
        assert state.pulse_fires() is (c >= charge), n
    # Run lengths: charge for exactly `charge` states from the state it appears, fire for exactly
    # `FIRE_TICKS`, then charge again, twice over.
    runs: list[tuple[str, int]] = []
    for state in found[: 2 * cycle]:
        kind = "charge" if state.is_charging() else "fire"
        if runs and runs[-1][0] == kind:
            runs[-1] = (kind, runs[-1][1] + 1)
        else:
            runs.append((kind, 1))
    assert runs == [("charge", charge), ("fire", FIRE_TICKS)] * 2
    assert found[0].is_charging()
    assert found[2 * cycle].is_charging()
    # Neither flag holds outside ACTIVE.
    waiting = ball(320.0, 100.0, level=level)
    assert not waiting.is_charging()
    assert not waiting.is_firing()
    assert not replace(found[10], phase=Phase.GONE).is_charging()
    assert not replace(found[charge + 5], phase=Phase.GONE).is_firing()


def test_rays_and_outline_level_step_up_with_the_charge_and_end_full_at_levels_1_and_8() -> None:
    named: dict[int, dict[int, int]] = {
        1: {0: 1, 29: 1, 30: 2, 59: 2, 60: 3, 89: 3, 90: 4, 119: 4},
        8: {0: 1, 20: 1, 21: 2, 41: 2, 42: 3, 62: 3, 63: 4, 83: 4},
    }
    for level, rows in named.items():
        charge = SCALED_CHARGE[level - 1]
        cycle = charge + FIRE_TICKS
        found = states(active(320.0, 100.0, level=level, speed=0.5), cycle + 1)
        for n, state in enumerate(found[:cycle]):
            if n < charge:
                rays = expected_rays(n, charge)
                assert state.charge_ray_count() == rays, (level, n)
                assert state.outline_level() == pytest.approx(rays / CHARGE_RAYS), (level, n)
                assert 1 <= rays <= CHARGE_RAYS
            else:
                assert state.charge_ray_count() == 0, (level, n)
                assert state.outline_level() == 0.0, (level, n)
        for n, rays in rows.items():
            assert found[n].charge_ray_count() == rays, (level, n)
            assert found[n].outline_level() == pytest.approx(rays / CHARGE_RAYS), (level, n)
        # All of them for the last part, and the next cycle starts with one again.
        assert found[charge - 1].charge_ray_count() == CHARGE_RAYS
        assert found[charge - 1].outline_level() == 1.0
        assert found[cycle].charge_ray_count() == 1
        assert found[cycle].outline_level() == pytest.approx(1 / CHARGE_RAYS)
    # A charge held at telegraph_min (45): the steps follow it, the last one shows all rays.
    short = states(active(320.0, 100.0, speed=0.5, tuning=make_tuning(charge_ticks=45)), 44)
    for n, state in enumerate(short):
        assert state.charge_ray_count() == 1 + n * CHARGE_RAYS // 45, n
        assert state.charge_ray_count() <= CHARGE_RAYS
    assert short[44].charge_ray_count() == CHARGE_RAYS
    # A different count of rays: never past it, and full on the last tick.
    three = replace(TYPE_EXTRA, charge_rays=3, charge_ticks=100)
    few = states(active(320.0, 100.0, speed=0.5, tuning=make_tuning(type_extra=three)), 99)
    for n, state in enumerate(few):
        assert state.charge_ray_count() == 1 + n * 3 // 100, n
        assert state.outline_level() == pytest.approx((1 + n * 3 // 100) / 3)
    assert few[99].charge_ray_count() == 3
    assert few[99].outline_level() == 1.0


def test_ball_on_screen_is_the_strict_box_test_at_each_of_the_four_edges() -> None:
    base = active(320.0, 240.0)
    half = BALL_SIZE / 2

    def shows(x: float, y: float) -> bool:
        return replace(base, x=x, y=y).ball_on_screen()

    # Top: the box's bottom edge touching y 0 does not count; a hair over does.
    assert not shows(320.0, -half)
    assert shows(320.0, -half + 0.5)
    assert not shows(320.0, -half - 0.5)
    # Bottom: the box's top edge on the floor does not count; a hair over does.
    assert not shows(320.0, SCREEN_H + half)
    assert shows(320.0, SCREEN_H + half - 0.5)
    assert not shows(320.0, SCREEN_H + half + 0.5)
    # Left and right walls.
    assert not shows(-half, 240.0)
    assert shows(-half + 0.5, 240.0)
    assert not shows(-half - 0.5, 240.0)
    assert not shows(SCREEN_W + half, 240.0)
    assert shows(SCREEN_W + half - 0.5, 240.0)
    assert not shows(SCREEN_W + half + 0.5, 240.0)
    # Part of the box is enough, and both axes count: a corner past two edges is off.
    assert shows(0.0, 0.0)
    assert shows(SCREEN_W, SCREEN_H)
    assert not shows(-half, -half)
    assert not shows(SCREEN_W + half, SCREEN_H + half)
    assert not shows(320.0, 1000.0)
    assert not shows(-1000.0, 240.0)


def test_off_screen_the_cycle_keeps_counting_but_nothing_shows_or_fires() -> None:
    cycle = CHARGE_TICKS + FIRE_TICKS
    still = replace(active(320.0), speed=0.0)
    assert (still.x, still.y) == (320.0, -8.0)
    found = states(still, 2 * cycle)
    for n, state in enumerate(found):
        c = n % cycle
        assert not state.ball_on_screen()
        # The cycle counts on.
        assert state.ticks_in_phase == n
        assert state.is_charging() is (c < CHARGE_TICKS), n
        assert state.is_firing() is (c >= CHARGE_TICKS), n
        # Nothing shows and nothing fires.
        assert state.charge_ray_count() == 0, n
        assert state.outline_level() == 0.0, n
        assert not state.pulse_fires(), n
        assert state.current_hitbox() == (), n
        assert state.graze_zone() == (), n
        # The same state with the ball on screen does show it.
        shown = replace(state, y=100.0)
        if c < CHARGE_TICKS:
            assert shown.charge_ray_count() == expected_rays(c, CHARGE_TICKS), n
            assert shown.outline_level() > 0.0
            assert not shown.pulse_fires()
        else:
            assert shown.charge_ray_count() == 0
            assert shown.pulse_fires(), n
    # The ball leaves the screen while firing: the circle stops at once, and it is still the fire
    # part of the cycle.
    leaving = replace(active(320.0), speed=2.0, y=486.0, ticks_in_phase=130)
    assert leaving.is_firing()
    assert leaving.pulse_fires()
    gone_by = leaving.update(CTX)
    assert (gone_by.y, gone_by.ticks_in_phase) == (488.0, 131)
    assert not gone_by.ball_on_screen()
    assert gone_by.is_firing()
    assert not gone_by.pulse_fires()
    assert gone_by.current_hitbox() == ()
    # It comes in firing: it fires on the first state the ball shows.
    entering = replace(active(320.0), speed=2.0, y=-9.0, ticks_in_phase=130)
    assert not entering.pulse_fires()
    assert entering.update(CTX).pulse_fires()


def test_the_hitbox_is_the_pulse_circle_only_while_it_fires_with_the_ball_on_screen() -> None:
    waiting = ball(320.0, 240.0)
    assert waiting.current_hitbox() == ()
    assert waiting.graze_zone() == ()
    live = active(320.0, 240.0, speed=0.5)
    cycle = CHARGE_TICKS + FIRE_TICKS
    for n, state in enumerate(states(live, 2 * cycle)):
        c = n % cycle
        if c < CHARGE_TICKS:
            assert state.current_hitbox() == (), n
            assert state.graze_zone() == (), n
        else:
            assert state.current_hitbox() == (Circle(320.0, state.y, PULSE_RADIUS),), n
            # The graze zone exists only while it fires: the circle grown by the margin.
            assert state.graze_zone() == (Circle(320.0, state.y, PULSE_RADIUS + GRAZE_MARGIN),), n
        assert state.hitbox == (Circle(0.0, 0.0, PULSE_RADIUS),)
    # GONE has none, even on a firing tick.
    firing = states(live, CHARGE_TICKS)[-1]
    assert firing.is_firing()
    assert firing.current_hitbox() != ()
    dead = replace(firing, phase=Phase.GONE)
    assert dead.current_hitbox() == ()
    assert dead.graze_zone() == ()
    # The first firing state with the ball off screen has none.
    off = replace(live, y=-8.0, ticks_in_phase=CHARGE_TICKS)
    assert off.is_firing()
    assert off.current_hitbox() == ()
    assert off.graze_zone() == ()
    below = replace(live, y=SCREEN_H + 8.0, ticks_in_phase=CHARGE_TICKS)
    assert below.current_hitbox() == ()
    # The circle is placed on the ball: it moves with it, off the center line too.
    side = replace(live, x=100.0, y=300.0, ticks_in_phase=CHARGE_TICKS)
    assert side.current_hitbox() == (Circle(100.0, 300.0, PULSE_RADIUS),)


def test_the_drawn_parts_are_the_ball_alone_off_screen_and_the_ball_and_pulse_box_on_screen() -> (
    None
):
    top = active(320.0)
    assert top.drawn_parts() == (Box(320.0, -8.0, BALL_SIZE, BALL_SIZE),)
    assert ball(320.0).drawn_parts() == (Box(320.0, -8.0, BALL_SIZE, BALL_SIZE),)
    assert PULSE_BOX_SIDE == 131.0
    for x, y in ((320.0, 100.0), (100.0, 479.0), (320.0, -7.5), (639.5, 240.0)):
        on = replace(top, x=x, y=y)
        assert on.drawn_parts() == (
            Box(x, y, BALL_SIZE, BALL_SIZE),
            Box(x, y, PULSE_BOX_SIDE, PULSE_BOX_SIDE),
        ), (x, y)
    # The parts follow the ball's own state: off screen below and past the sides is the ball alone.
    for x, y in ((320.0, 488.0), (320.0, 600.0), (-8.0, 240.0), (648.0, 240.0)):
        off = replace(top, x=x, y=y)
        assert off.drawn_parts() == (Box(x, y, BALL_SIZE, BALL_SIZE),), (x, y)
    # The pulse box is as wide as the rays when they reach farther than the circle.
    long_rays = replace(top, y=100.0, ray_length=100.0)
    assert long_rays.drawn_parts()[1].w == 2 * (BALL_SIZE / 2 + 100.0 + DRAW_MARGIN)
    # It is the one change of what is drawn: the parts never depend on the cycle.
    cycle = CHARGE_TICKS + FIRE_TICKS
    on_screen = states(active(320.0, 100.0, speed=0.5), cycle)
    for state in on_screen:
        assert len(state.drawn_parts()) == 2
        assert state.drawn_parts()[1].w == PULSE_BOX_SIDE
        assert state.drawn_parts()[1].h == PULSE_BOX_SIDE


def run_with_ship(ship: Ship, *placements: Placement, tuning: DrifterTuning = TUNING) -> Run:
    """A fresh run with the ship put where the test wants it, and the placements added."""
    return add_drifters(replace(start_run(), ship=ship), list(placements), tuning)


def ball_of(run: Run) -> ElectricBall:
    """The single electric ball on the field."""
    assert len(run.drifters) == 1
    found = run.drifters[0]
    assert isinstance(found, ElectricBall)
    return found


def lines_starting(caplog: pytest.LogCaptureFixture, prefix: str) -> list[str]:
    """The lines the run logged that start with `prefix`."""
    return [
        r.getMessage()
        for r in caplog.records
        if r.name == RUN_LOGGER and r.getMessage().startswith(prefix)
    ]


def test_the_top_timeline_at_level_1_enters_fires_once_mid_screen_and_is_dropped_when_below(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    run = run_with_ship(SAFE_SHIP, Placement(DrifterType.ELECTRIC_BALL, x=320.0))
    fire_states: list[tuple[int, float]] = []
    last: ElectricBall | None = None
    for state in range(1, 262):
        run = step_run(replace(run, ship=SAFE_SHIP), NO_KEY)
        current = ball_of(run)
        if state < WARNING_TICKS:
            assert current.phase is Phase.WARNING
            assert not current.has_entered
            assert not current.is_off_screen()
            assert (current.x, current.y) == (320.0, -8.0)
            last = current
            continue
        n = state - WARNING_TICKS
        assert current.phase is Phase.ACTIVE
        assert current.ticks_in_phase == n
        assert current.x == 320.0
        assert current.y == pytest.approx(-8.0 + n * LEVEL_ONE_SPEED, abs=1e-9)
        if n == 0:
            # It appears touching the top edge: not on screen yet, not entered, no charge shown.
            assert not current.ball_on_screen()
            assert not current.has_entered
            assert current.is_charging()
            assert current.charge_ray_count() == 0
            assert current.outline_level() == 0.0
        else:
            # On screen from the next state, with its charge: one ray at the first.
            assert current.ball_on_screen()
            assert current.has_entered
            if n < CHARGE_TICKS:
                assert current.charge_ray_count() == expected_rays(n, CHARGE_TICKS)
        if n == 1:
            assert current.charge_ray_count() == 1
            assert current.outline_level() == pytest.approx(0.25)
        assert not current.is_off_screen(), state
        if current.pulse_fires():
            fire_states.append((n, current.y))
            assert current.current_hitbox() == (Circle(320.0, current.y, PULSE_RADIUS),)
        else:
            assert current.current_hitbox() == ()
        assert lines_starting(caplog, "drifter gone") == [], state
        last = current
    # It fired once, on one unbroken run of states from mid-screen to the drop.
    first_n, first_y = fire_states[0]
    assert first_n == CHARGE_TICKS
    assert first_y == pytest.approx(-8.0 + 120 * LEVEL_ONE_SPEED, abs=1e-9)
    assert SCREEN_H / 4 < first_y < 3 * SCREEN_H / 4
    assert [n for n, _ in fire_states] == list(range(CHARGE_TICKS, 202))
    # The last state still on screen is firing, its box top just above the floor.
    assert last is not None
    assert last.ticks_in_phase == 201
    assert last.is_firing()
    assert last.y - BALL_SIZE / 2 < SCREEN_H
    # The next tick, n 202: the ball is fully below the floor and the run drops it.
    previous = last
    run = step_run(replace(run, ship=SAFE_SHIP), NO_KEY)
    assert run.drifters == ()
    assert run.lives == LIVES_START
    dropped = previous.update(CTX)
    assert dropped.ticks_in_phase == 202
    assert dropped.y - BALL_SIZE / 2 >= SCREEN_H
    assert dropped.y == pytest.approx(-8.0 + 202 * LEVEL_ONE_SPEED, abs=1e-9)
    assert previous.y - BALL_SIZE / 2 < SCREEN_H
    assert lines_starting(caplog, "drifter gone") == [
        f"drifter gone id=1 type=electric_ball x=320.00 y={dropped.y:.2f}"
    ]
    assert lines_starting(caplog, "drifter touch") == []
    assert len(lines_starting(caplog, "drifter spawn")) == 1
    assert len(lines_starting(caplog, "drifter active")) == 1
    # Never dropped before it has entered: far below the floor, ACTIVE, not entered, it stays.
    unentered = replace(active(320.0, 600.0), has_entered=False)
    assert not unentered.is_off_screen()
    assert not replace(unentered, y=-50.0).is_off_screen()
    entered = replace(unentered, has_entered=True)
    assert entered.is_off_screen()
    # In WARNING it is never off screen, even with has_entered forced on.
    assert not replace(ball(320.0, 600.0), has_entered=True).is_off_screen()


def test_the_level_scales_the_speed_and_the_charge_alone() -> None:
    for level in range(1, 9):
        scaled = ball(320.0, 100.0, level=level)
        wanted = SCALED_CHARGE[level - 1]
        assert wanted == scaled_ticks(CHARGE_TICKS, level)
        assert scaled.speed == pytest.approx(LEVEL_ONE_SPEED * HAZARD_SPEED[level - 1]), level
        assert scaled.charge_ticks == wanted, level
        # Everything else is the Level 1 value.
        assert scaled.fire_ticks == FIRE_TICKS
        assert scaled.pulse_radius == PULSE_RADIUS
        assert (scaled.width, scaled.height) == (BALL_SIZE, BALL_SIZE)
        assert scaled.hitbox == (Circle(0.0, 0.0, PULSE_RADIUS),)
        assert scaled.charge_rays == CHARGE_RAYS
        assert scaled.ray_length == RAY_LENGTH
        assert scaled.ray_width == RAY_WIDTH
        assert scaled.outline_width == OUTLINE_WIDTH
        assert scaled.rim_width == RIM_WIDTH
        assert scaled.fill_opacity == FILL_OPACITY
        assert scaled.warning_ticks == WARNING_TICKS
        # as_level at Level 1 is the same ball as that level.
        assert replace(ball(320.0, 100.0, as_level=level)) == scaled, level
    # A tuning charge under telegraph_min is raised to it at every level.
    low = make_tuning(charge_ticks=30)
    for level in range(1, 9):
        assert ball(320.0, 100.0, level=level, tuning=low).charge_ticks == TELEGRAPH_MIN, level
    # A charge of 60 scales to 56.4 -> 57 at Level 2 and to 42 at Level 8, which the floor holds.
    sixty = make_tuning(charge_ticks=60)
    assert ball(320.0, 100.0, level=1, tuning=sixty).charge_ticks == 60
    assert ball(320.0, 100.0, level=2, tuning=sixty).charge_ticks == 57
    assert ball(320.0, 100.0, level=8, tuning=sixty).charge_ticks == TELEGRAPH_MIN
    # A floor set in HazardRules is the floor: 100 beats the scaled 84 at Level 8, not 120 at 1.
    floored = make_tuning(hazards=HazardRules(telegraph_min_ticks=100))
    assert ball(320.0, 100.0, level=8, tuning=floored).charge_ticks == 100
    assert ball(320.0, 100.0, level=1, tuning=floored).charge_ticks == 120
    # With the playtest switches off, Level 1 values at any level.
    for level in (1, 4, 8):
        flat = ball(320.0, 100.0, level=level, tuning=NO_SCALING)
        assert flat.speed == pytest.approx(LEVEL_ONE_SPEED)
        assert flat.charge_ticks == CHARGE_TICKS
        assert ball(320.0, 100.0, as_level=8, level=level, tuning=NO_SCALING).charge_ticks == 120
    only_speed_off = make_tuning(switches=PlaytestSwitches(hazard_speed_scaling=False))
    assert ball(level=8, tuning=only_speed_off).speed == pytest.approx(LEVEL_ONE_SPEED)
    assert ball(level=8, tuning=only_speed_off).charge_ticks == 84
    only_timer_off = make_tuning(switches=PlaytestSwitches(timer_scaling=False))
    assert ball(level=8, tuning=only_timer_off).speed == pytest.approx(LEVEL_ONE_SPEED * 1.42)
    assert ball(level=8, tuning=only_timer_off).charge_ticks == 120
    # A placement speed changes only the speed (the level's hazard speed x still applies).
    for level in (1, 8):
        fast = ball(320.0, 100.0, level=level, speed=2.0)
        plain = ball(320.0, 100.0, level=level)
        assert fast.speed == pytest.approx(2.0 * HAZARD_SPEED[level - 1])
        assert replace(fast, speed=plain.speed) == plain
    assert ball(320.0, 100.0, speed=2.0, as_level=8).speed == pytest.approx(2.0 * 1.42)


def test_telegraph_ticks_is_the_types_charge_and_none_without_its_type_values() -> None:
    assert ElectricBall.telegraph_ticks(TYPE_EXTRA) == CHARGE_TICKS
    assert ElectricBall.telegraph_ticks(replace(TYPE_EXTRA, charge_ticks=77)) == 77
    assert ElectricBall.telegraph_ticks(None) is None
    assert ElectricBall.telegraph_ticks(DrifterTypeExtra()) is None
    # It reads the type's own value, not a scaled one: the telegraph check scales it itself.
    assert ball(level=8).charge_ticks == 84
    assert ElectricBall.telegraph_ticks(TUNING.drifters[DrifterType.ELECTRIC_BALL].extra) == 120


def test_the_hitbox_is_one_circle_on_the_center_and_the_variant_check_refuses_a_small_pulse() -> (
    None
):
    for radius in (64.0, 12.5, 100.0):
        assert electric_ball_hitbox(radius) == (Circle(0.0, 0.0, radius),)
    # The GDD values are accepted, and so is anything past half the ball.
    check_electric_ball_variant(BALL_SIZE, PULSE_RADIUS)
    check_electric_ball_variant(BALL_SIZE, 8.5)
    check_electric_ball_variant(15.0, 7.75)
    # At or below half the ball is refused, with the numbers in g format.
    refused: tuple[tuple[float, float, str], ...] = (
        (16.0, 8.0, "pulse_radius must be more than ball_size / 2 (8 <= 8)"),
        (16.0, 7.0, "pulse_radius must be more than ball_size / 2 (7 <= 8)"),
        (16.0, 7.25, "pulse_radius must be more than ball_size / 2 (7.25 <= 8)"),
        (15.0, 7.5, "pulse_radius must be more than ball_size / 2 (7.5 <= 7.5)"),
        (16.0, 0.0, "pulse_radius must be more than ball_size / 2 (0 <= 8)"),
        (16.0, -3.0, "pulse_radius must be more than ball_size / 2 (-3 <= 8)"),
    )
    for ball_size, pulse_radius, text in refused:
        with pytest.raises(ValueError, match=message(text)):
            check_electric_ball_variant(ball_size, pulse_radius)


def ball_run(ball_state: ElectricBall, ship: Ship, *, invuln: int = 0) -> Run:
    """A run with one ACTIVE ball, uid 1, that has entered, and the ship where given."""
    return Run(
        ship=ship,
        scroll=Scroll(ticks=200, scrolled_ticks=170),
        invuln_ticks_left=invuln,
        drifters=(replace(ball_state, uid=1, has_entered=True),),
        next_uid=2,
    )


def tick(run: Run, ship: Ship, *, clear_invuln: bool = True) -> Run:
    """One tick with the ship put back first, and invulnerability cleared so only the cooldown
    can stop a hit."""
    run = replace(run, ship=ship)
    return step_run(replace(run, invuln_ticks_left=0) if clear_invuln else run, NO_KEY)


def resting(x: float, y: float) -> Ship:
    """A ship at rest at (x, y)."""
    return Ship(x=x, y=y, vx=0.0, vy=0.0)


def test_in_the_run_a_hit_on_the_first_firing_state_costs_one_life_and_the_cooldown_holds() -> None:
    ship = resting(320.0, 240.0)
    # A very slow ball keeps the ship in the circle for the whole time.
    crawl = 0.02
    sitting = active(320.0, 240.0, speed=crawl)
    run = ball_run(sitting, ship)
    assert hitboxes_overlap(ship_hitbox(ship), (Circle(320.0, 240.0, PULSE_RADIUS),))
    # The ship sits on the ball while it charges: not hit on any charging tick.
    for n in range(1, CHARGE_TICKS):
        run = tick(run, ship)
        current = ball_of(run)
        assert current.ticks_in_phase == n
        assert current.is_charging()
        assert current.current_hitbox() == ()
        assert run.lives == LIVES_START, n
        assert current.rehit_ticks_left == 0
    # The first firing state: the ship is inside the circle and is hit, once.
    run = tick(run, ship)
    first = ball_of(run)
    assert first.ticks_in_phase == CHARGE_TICKS
    assert first.is_firing()
    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert not run.game_over
    assert first.rehit_ticks_left == REHIT_COOLDOWN
    assert first.brightness() == REHIT_DIM
    # It keeps falling and keeps its cycle, dim, with no second hit until the cooldown ends.
    cycle = CHARGE_TICKS + FIRE_TICKS
    for after in range(1, REHIT_COOLDOWN + 1):
        run = tick(run, ship)
        current = ball_of(run)
        n = CHARGE_TICKS + after
        assert current.ticks_in_phase == n
        assert current.y == pytest.approx(first.y + after * crawl, abs=1e-9)
        assert current.x == 320.0
        assert current.is_firing() is (n % cycle >= CHARGE_TICKS), n
        if current.is_firing():
            assert hitboxes_overlap(ship_hitbox(ship), current.current_hitbox()), n
        assert run.lives == LIVES_START - 1, n
        assert current.rehit_ticks_left == REHIT_COOLDOWN - after
        assert current.brightness() == (REHIT_DIM if after < REHIT_COOLDOWN else 1.0), n
    # The cooldown ended in a charge: no hit then, and the next fire hits again on its first state.
    assert ball_of(run).is_charging()
    for after in range(REHIT_COOLDOWN + 1, cycle):
        run = tick(run, ship)
        assert run.lives == LIVES_START - 1, after
    run = tick(run, ship)
    again = ball_of(run)
    assert again.ticks_in_phase == cycle + CHARGE_TICKS
    assert again.is_firing()
    assert run.lives == LIVES_START - 2
    assert run.invuln_ticks_left == INVULN_TICKS
    assert again.rehit_ticks_left == REHIT_COOLDOWN
    # A ship clear of the circle is never hit.
    clear = resting(320.0 + PULSE_RADIUS + 60.0, 240.0)
    away = ball_run(sitting, clear)
    for _ in range(CHARGE_TICKS + 5):
        away = tick(away, clear)
        assert away.lives == LIVES_START
        assert ball_of(away).rehit_ticks_left == 0


def test_in_the_run_an_invulnerable_ship_is_not_hit_and_the_circle_keeps_firing() -> None:
    ship = resting(320.0, 240.0)
    crawl = 0.02
    firing_next = replace(active(320.0, 240.0, speed=crawl), ticks_in_phase=CHARGE_TICKS - 1)
    run = ball_run(firing_next, ship, invuln=INVULN_TICKS)
    for left in range(INVULN_TICKS - 1, -1, -1):
        run = tick(run, ship, clear_invuln=False)
        current = ball_of(run)
        assert current.pulse_fires()
        assert hitboxes_overlap(ship_hitbox(ship), current.current_hitbox())
        assert run.lives == LIVES_START
        assert run.invuln_ticks_left == left
        assert current.rehit_ticks_left == 0
        assert current.brightness() == 1.0
    # Still inside the circle when invulnerability ends: hit on the first tick after it.
    run = tick(run, ship, clear_invuln=False)
    assert ball_of(run).pulse_fires()
    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert ball_of(run).rehit_ticks_left == REHIT_COOLDOWN
    # A ship invulnerable from a hit is not hit again while the cooldown runs, even when the
    # protection ends first (30 ticks against 180).
    for _ in range(INVULN_TICKS + 20):
        run = tick(run, ship, clear_invuln=False)
        assert run.lives == LIVES_START - 1


def test_the_run_logs_spawn_active_touch_and_gone_and_the_ball_logs_nothing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    ship = resting(320.0, 330.0)
    run = run_with_ship(
        ship, Placement(DrifterType.ELECTRIC_BALL, x=320.0, y=200.0, speed=1.0), tuning=TUNING
    )
    # Exercise the drifter's own methods too: none may log.
    probe = ball_of(run)
    for state in states(replace(probe, phase=Phase.ACTIVE), 5):
        state.drawn_parts()
        state.current_hitbox()
        state.graze_zone()
        state.charge_ray_count()
        state.outline_level()
    ticks = 0
    while run.drifters:
        run = step_run(replace(run, ship=ship), NO_KEY)
        ticks += 1
        assert ticks < 1000
    # Ball at 200, 1 px/tick: warning 60 ticks, hit on the first firing tick (n 120, y 320),
    # dropped at n 288 (y 488, box top on the floor), before the cooldown ends.
    assert ticks == WARNING_TICKS + 288
    assert run.lives == LIVES_START - 1
    run_lines = [r.getMessage() for r in caplog.records if r.name == RUN_LOGGER]
    drifter_lines = [line for line in run_lines if line.startswith("drifter")]
    assert drifter_lines == [
        "drifter spawn id=1 type=electric_ball variant=standard x=320.00 y=200.00"
        " speed=1.00 level=1",
        "drifter active id=1 type=electric_ball x=320.00 y=200.00",
        "drifter touch id=1 type=electric_ball effect=hit",
        "drifter gone id=1 type=electric_ball x=320.00 y=488.00",
    ]
    assert "life lost lives=2" in run_lines
    # The ball's own module and the base log nothing.
    assert [r.name for r in caplog.records if r.name.startswith("core.drifters")] == []


@pytest.mark.determinism
def test_update_never_mutates_its_input_and_the_same_state_gives_the_same_result() -> None:
    cycle = CHARGE_TICKS + FIRE_TICKS
    start = active(250.0, 100.0, speed=0.5)
    inputs: list[ElectricBall] = [
        ball(250.0),
        ball(250.0, 100.0),
        start,
        states(start, 10)[-1],
        states(start, CHARGE_TICKS)[-1],
        states(start, cycle + 3)[-1],
        replace(start, phase=Phase.GONE),
    ]
    contexts: tuple[TickContext, ...] = (
        CTX,
        TickContext(ship=Ship(x=10.0, y=20.0, vx=1.0, vy=-1.0), scroll_step_px=1.1),
    )
    for state in inputs:
        for ctx in contexts:
            frozen = copy.deepcopy(state)
            first = state.update(ctx)
            second = state.update(ctx)
            assert state == frozen
            assert first == second
            assert first is not state or state.phase is Phase.GONE
    # GONE stays exactly as it is.
    gone = replace(start, phase=Phase.GONE)
    assert gone.update(CTX) == gone
    # The same placements and ticks twice give the same run.
    placements = (
        Placement(DrifterType.ELECTRIC_BALL, x=320.0),
        Placement(DrifterType.ELECTRIC_BALL, x=200.0, y=100.0, speed=0.5, as_level=5),
    )
    finals: list[Run] = []
    for _ in range(2):
        run = run_with_ship(SAFE_SHIP, *placements)
        for _ in range(300):
            run = step_run(replace(run, ship=SAFE_SHIP), NO_KEY)
        finals.append(run)
    assert finals[0] == finals[1]
    assert len(finals[0].drifters) == 1
