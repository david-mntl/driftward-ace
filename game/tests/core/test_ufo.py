"""The UFO, the base rules it relies on, the seed in the spawner, and UFOs inside the run.

Contract: docs/contracts/systems/drifters.md, Diagram (the UFO, its timeline, one ACTIVE tick,
Easing), Interface (`core/drifters/base.py`: `seeded`, the `Birth` fields `hazard_speed_mult` and
`seed`; `core/drifters/spawner.py`: `Placement.seed`, `MAX_SEED`, `placement_seed`,
`DEBUG_SPAWNS_SOURCE`; `core/drifters/ufo.py`), Rules (The base: Seeded, Entering, Leaving, Re-hit
cooldown, the `update` rule; Spawner steps 4, 5 and 8 and Placement seed; UFO); docs/contracts/
systems/run.md, Rules (steps 3, 7 and 8, Other rules: randomness) and Logging. Task:
docs/contracts/DRA-104/tasks/DRA-104-05-qa-engineer.md. One test per behavior it lists.

The tuning records are built here from the GDD values below, never read from game/tuning/, and no
expected number is imported from the code under test. The weave's picks are replayed in the file
from the contract's Pick rules (`reference_pick`), and the easing is checked by the contract's
table and by its limits (the top speed, the turn, the band, the target), not by a second copy of
the ease. The ship against every variant is in test_collision.py, the seeds of wave files in
test_wave_files.py.
"""

import copy
import logging
import math
import random
import re
from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import pairwise

import pytest

from core.collision import Box, Circle, Hitbox, hitboxes_overlap
from core.drifters.base import (
    Birth,
    Drifter,
    DrifterType,
    DrifterTypeExtra,
    GrazeState,
    Phase,
    TickContext,
    TouchEffect,
)
from core.drifters.meteorite import Meteorite
from core.drifters.planet import PlanetTypeExtra
from core.drifters.registry import available_drifters, drifter_class
from core.drifters.spawner import (
    DEBUG_SPAWNS_SOURCE,
    MAX_SEED,
    Placement,
    placement_seed,
    spawn_drifter,
)
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.drifters.ufo import (
    Ufo,
    UfoTypeExtra,
    check_ufo_variant,
    check_ufo_weave,
    weave_brake_speed,
    weave_stop_distance,
)
from core.run import Run, add_drifters, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust, ship_hitbox, spawn

DISC_W: float = 40.0
DISC_H: float = 10.0
DOME_R: float = 9.0
"""px. Source: drifters/07-ufo.md, size and hitbox (guess)."""

DOME_BOX: float = 21.0
"""The dome's drawn box side: 2 x (9 + 1.5). Source: drifters.md, Diagram (the UFO)."""

SPEED_RATIO: float = 0.3
"""Source: drifters/07-ufo.md, speed_ratio (guess)."""

THRUST_SIDE: float = 0.42
DRAG_X: float = 0.94
TOP_SIDE_SPEED: float = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
"""px/tick, about 6.58. Source: 04-ship.md, derived values."""

LEVEL_ONE_SPEED: float = SPEED_RATIO * TOP_SIDE_SPEED
"""About 1.974 px/tick. Source: drifters.md, Diagram (the UFO timeline)."""

WARNING_TICKS: int = 60
"""Source: 07-drifters.md, entry_warning_ticks (the shared value, guess)."""

TICKS_MIN: int = 60
TICKS_MAX: int = 96
STEP_MIN: float = 40.0
STEP_MAX: float = 120.0
SPEED_MAX: float = 1.6
TURN: float = 0.1
BAND_TOP: float = 188.0
BAND_BOTTOM: float = 440.0
"""Source: drifters/07-ufo.md, Values (weave_change_ticks, weave_step, weave_speed_max, weave_turn,
band; guess)."""

HAZARD_SPEED: tuple[float, ...] = (1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42)
TIMER: tuple[float, ...] = (1.00, 0.94, 0.89, 0.85, 0.81, 0.77, 0.74, 0.70)
"""Source: 08-difficulty.md, the Hazard speed x and Timer x rows (Levels 1 to 8)."""

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

SEED: int = 12345
"""A seed for the tests that need one UFO and no particular path."""

NO_KEY = Thrust()

SCROLLING: Scroll = Scroll(ticks=100, scrolled_ticks=70)
"""A scroll already moving: the next step moves the world 1.1 px."""

SAFE_SHIP: Ship = Ship(x=100.0, y=463.0, vx=0.0, vy=0.0)
"""A resting ship low on the screen and clear of the UFO: its bar's top edge is at 447, the disc's
bottom edge at 445 at the band's lowest (440 + 5). It is below the top line and clear of the walls,
so the ship logs nothing."""

ROCK_HITBOX: Hitbox = (Circle(0.0, 0.0, 14.0),)
"""The medium meteorite. Source: drifters/01-meteorite.md, variants (guess)."""

UFO_TYPE_EXTRA: UfoTypeExtra = UfoTypeExtra(
    weave_change_ticks_min=TICKS_MIN,
    weave_change_ticks_max=TICKS_MAX,
    weave_step_min=STEP_MIN,
    weave_step_max=STEP_MAX,
    weave_speed_max=SPEED_MAX,
    weave_turn=TURN,
    band_top=BAND_TOP,
    band_bottom=BAND_BOTTOM,
)

CTX: TickContext = TickContext(ship=Ship(x=320.0, y=400.0, vx=0.0, vy=0.0))
"""A context with the ship and a world standing still. The UFO reads neither."""


def make_tuning(
    *,
    switches: PlaytestSwitches | None = None,
    type_extra: DrifterTypeExtra | None = UFO_TYPE_EXTRA,
) -> DrifterTuning:
    """Build the UFO and meteorite tuning from the GDD values above.

    The UFO's records are built the way the contract says `app.tuning` builds them: width and
    height of the disc, the two-shape hitbox, `extra` None per variant, the file's `speed_ratio`
    and warning length. `type_extra` can be swapped for a wrong one to test the refusals.
    """
    return DrifterTuning(
        drifters={
            DrifterType.UFO: DrifterTypeTuning(
                variants={
                    "standard": VariantTuning(
                        width=DISC_W,
                        height=DISC_H,
                        hitbox=(Box(0.0, 0.0, DISC_W, DISC_H), Circle(0.0, -DISC_H / 2, DOME_R)),
                        extra=None,
                    )
                },
                default_variant="standard",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
                extra=type_extra,
            ),
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=ROCK_HITBOX)},
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=60,
            ),
        },
        switches=PlaytestSwitches() if switches is None else switches,
    )


TUNING: DrifterTuning = make_tuning()
NO_SCALING: DrifterTuning = make_tuning(
    switches=PlaytestSwitches(hazard_speed_scaling=False, timer_scaling=False)
)


def ufo(
    x: float | None = None,
    y: float | None = 300.0,
    *,
    seed: int | None = SEED,
    invert: bool = False,
    level: int = 1,
    as_level: int | None = None,
    speed: float | None = None,
    tuning: DrifterTuning = TUNING,
) -> Ufo:
    """Spawn a UFO through the spawner, in WARNING."""
    placement = Placement(
        DrifterType.UFO, x, y, as_level=as_level, invert=invert, speed=speed, seed=seed
    )
    spawned: Drifter = spawn_drifter(placement, level, tuning)
    assert isinstance(spawned, Ufo)
    return spawned


def active(
    x: float | None = None,
    y: float = 300.0,
    *,
    seed: int = SEED,
    invert: bool = False,
    level: int = 1,
) -> Ufo:
    """A UFO already ACTIVE at its start, at the start of its ACTIVE phase."""
    return replace(
        ufo(x, y, seed=seed, invert=invert, level=level), phase=Phase.ACTIVE, ticks_in_phase=0
    )


def rock(x: float, y: float) -> Meteorite:
    """An ACTIVE meteorite that stands still where it is put."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, x, y), 1, TUNING)
    assert isinstance(spawned, Meteorite)
    return replace(spawned, phase=Phase.ACTIVE, ticks_in_phase=0, speed=0.0)


def flown(start: Ufo, ticks: int, ctx: TickContext = CTX) -> list[Ufo]:
    """The states after each of `ticks` updates, the first state `start` after one update."""
    states: list[Ufo] = []
    current = start
    for _ in range(ticks):
        current = current.update(ctx).mark_entered()
        states.append(current)
    return states


def still(x: float, y: float) -> Ufo:
    """An ACTIVE UFO that stays exactly where it is put: no speed, weaving with no pick due."""
    return replace(
        active(x, y),
        velocity_x=0.0,
        weaving=True,
        weave_ticks_left=10**9,
        weave_up=False,
        target_y=y,
    )


def resting(x: float, y: float) -> Ship:
    """A ship at rest at (x, y)."""
    return Ship(x=x, y=y, vx=0.0, vy=0.0)


def run_of(
    ship: Ship,
    *drifters: Drifter,
    scroll: Scroll = SCROLLING,
    invuln_ticks_left: int = 0,
) -> Run:
    """A run with the drifters numbered from 1, in order, and the ship where given."""
    numbered = tuple(replace(d, uid=i + 1) for i, d in enumerate(drifters))
    return Run(
        ship=ship,
        scroll=scroll,
        lives=LIVES_START,
        invuln_ticks_left=invuln_ticks_left,
        drifters=numbered,
        next_uid=len(numbered) + 1,
    )


def run_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Every line the run logged, in order."""
    return [r.getMessage() for r in caplog.records if r.name == RUN_LOGGER]


def ufos_of(run: Run) -> list[Ufo]:
    """The UFOs on the field, in order."""
    return [d for d in run.drifters if isinstance(d, Ufo)]


def message(text: str) -> str:
    """A `pytest.raises` pattern that matches the whole message."""
    return f"^{re.escape(text)}$"


def scaled_ticks(ticks: int, level: int) -> int:
    """A tick count at a level's Timer x, rounded up, worked out in exact fractions."""
    exact = Fraction(ticks) * Fraction(str(TIMER[level - 1]))
    return math.ceil(exact)


@dataclass(frozen=True)
class RefPick:
    """What the contract's Pick rules give for one pick."""

    up: bool
    ticks: int
    target: float
    seed: int


def reference_pick(
    seed: int, last_up: bool | None, y: float, ticks_min: int, ticks_max: int
) -> RefPick:
    """Replay one pick from the contract's Rules, UFO, Pick, at the file's step and band.

    Draws are `random()` for the direction on the first pick only, then `random()` for the
    interval, `random()` for the step and last `getrandbits(64)` for the next seed.
    """
    chooser = random.Random(seed)
    up = chooser.random() < 0.5 if last_up is None else not last_up
    ticks = ticks_min + math.floor(chooser.random() * (ticks_max - ticks_min + 1))
    step = STEP_MIN + chooser.random() * (STEP_MAX - STEP_MIN)
    room_up = y - BAND_TOP
    room_down = BAND_BOTTOM - y
    if (room_up if up else room_down) < STEP_MIN:
        up = not up
    target = y - min(step, room_up) if up else y + min(step, room_down)
    return RefPick(up=up, ticks=ticks, target=target, seed=chooser.getrandbits(64))


UFO_HITBOX: Hitbox = (Box(0.0, 0.0, DISC_W, DISC_H), Circle(0.0, -DISC_H / 2, DOME_R))


def birth(
    *,
    y: float = 300.0,
    seed: int | None = None,
    hazard_speed_mult: float = 1.0,
    specialty_enabled: bool | None = None,
    type_extra: DrifterTypeExtra | None = UFO_TYPE_EXTRA,
    hitbox: Hitbox = UFO_HITBOX,
) -> Birth:
    """A `Birth` for the UFO at Level 1, with the fields a test cares about changed."""
    return Birth(
        x=-20.0,
        y=y,
        variant="standard",
        width=DISC_W,
        height=DISC_H,
        hitbox=hitbox,
        speed=LEVEL_ONE_SPEED,
        warning_ticks=WARNING_TICKS,
        timer_mult=1.0,
        specialty_enabled=specialty_enabled,
        invert=False,
        variant_extra=None,
        rehit_cooldown_ticks=REHIT_COOLDOWN,
        rehit_dim=REHIT_DIM,
        type_extra=type_extra,
        telegraph_min_ticks=45,
        hazard_speed_mult=hazard_speed_mult,
        seed=seed,
    )


def test_a_ufo_is_born_in_warning_with_the_shared_warning_and_starts_just_outside_a_wall() -> None:
    base = ufo(None, 300.0)
    assert base.phase is Phase.WARNING
    assert base.ticks_in_phase == 0
    assert base.warning_ticks == WARNING_TICKS
    assert (base.x, base.y) == (-20.0, 300.0)
    assert (base.width, base.height) == (DISC_W, DISC_H)
    assert base.variant == "standard"
    assert base.hitbox == (Box(0.0, 0.0, DISC_W, DISC_H), Circle(0.0, -DISC_H / 2, DOME_R))
    assert base.current_hitbox() == ()
    assert base.uid == 0
    assert not base.has_entered
    assert base.specialty is None
    assert base.rehit_ticks_left == 0
    assert base.effect_on_touch() is TouchEffect.HIT
    assert not base.parked
    assert base.seeded
    assert not base.invert
    assert base.velocity_x == pytest.approx(LEVEL_ONE_SPEED, abs=1e-12)
    assert base.speed == pytest.approx(LEVEL_ONE_SPEED, abs=1e-12)
    # The weave has not begun: it targets the placed y and has no way yet.
    assert not base.weaving
    assert base.weave_ticks_left == 0
    assert base.weave_up is None
    assert base.target_y == 300.0
    assert base.velocity_y == 0.0
    assert base.seed == SEED
    assert base.weave_seed == SEED
    # Nothing drawn is on screen at the start: the disc's right edge is on the left wall.
    assert not base.is_partly_on_screen()
    assert not base.is_fully_on_screen()
    assert base.warning_center() == (12.0, 300.0)
    # With `invert` it starts just outside the right wall, flies left and warns at (628, y).
    mirrored = ufo(None, 300.0, invert=True)
    assert mirrored.invert
    assert (mirrored.x, mirrored.y) == (660.0, 300.0)
    assert mirrored.velocity_x == pytest.approx(-LEVEL_ONE_SPEED, abs=1e-12)
    assert mirrored.speed == pytest.approx(LEVEL_ONE_SPEED, abs=1e-12)
    assert mirrored.warning_center() == (628.0, 300.0)
    assert not mirrored.is_partly_on_screen()
    # The warning follows the placed y, and the start keeps a given x (and its y).
    for y in (BAND_TOP, 250.0, BAND_BOTTOM):
        assert ufo(None, y).warning_center() == (12.0, y)
        assert ufo(None, y, invert=True).warning_center() == (628.0, y)
    for x in (0.0, 100.0, 320.0, 640.0, -500.0):
        kept = ufo(x, 250.0)
        assert (kept.x, kept.y) == (x, 250.0)
        assert kept.phase is Phase.WARNING
        flipped = ufo(x, 250.0, invert=True)
        assert (flipped.x, flipped.y) == (x, 250.0)
        assert flipped.velocity_x < 0
    assert Ufo.start_position(None, 300.0, DISC_W, DISC_H, False) == (-20.0, 300.0)
    assert Ufo.start_position(None, 300.0, DISC_W, DISC_H, True) == (660.0, 300.0)
    assert Ufo.start_position(55.0, 300.0, DISC_W, DISC_H, True) == (55.0, 300.0)
    # Every level, every as_level and both switch sets give a UFO at the same spot, warning for
    # the same 60 ticks.
    for tuning in (TUNING, NO_SCALING):
        for level in range(1, 9):
            for other in (ufo(level=level, tuning=tuning), ufo(as_level=level, tuning=tuning)):
                assert (other.x, other.y) == (-20.0, 300.0)
                assert other.warning_ticks == WARNING_TICKS
                assert other.phase is Phase.WARNING
    # It waits 60 states in WARNING at its place, then turns ACTIVE there with 0 ticks.
    waiting = base
    for tick in range(1, WARNING_TICKS):
        waiting = waiting.update(CTX)
        assert waiting.phase is Phase.WARNING, tick
        assert waiting.ticks_in_phase == tick
        assert (waiting.x, waiting.y) == (-20.0, 300.0)
        assert waiting.current_hitbox() == ()
        assert not waiting.weaving
    waiting = waiting.update(CTX)
    assert waiting.phase is Phase.ACTIVE
    assert waiting.ticks_in_phase == 0
    assert (waiting.x, waiting.y) == (-20.0, 300.0)
    assert waiting.current_hitbox() == (
        Box(-20.0, 300.0, DISC_W, DISC_H),
        Circle(-20.0, 295.0, DOME_R),
    )
    # Added to a run it is in WARNING with its uid, and nothing else about the run changes.
    added = add_drifters(start_run(), [Placement(DrifterType.UFO, y=300.0, seed=SEED)], TUNING)
    assert len(added.drifters) == 1
    assert added.drifters[0].phase is Phase.WARNING
    assert added.drifters[0].uid == 1
    assert added.drifters[0].current_hitbox() == ()


def test_a_ufo_refuses_a_missing_y_or_seed_a_band_miss_a_specialty_and_wrong_tuning_in_order() -> (
    None
):
    wrong_type = DrifterTypeExtra()
    other_type = PlanetTypeExtra(
        field_ring_trip=120, field_ring_gap=60, field_ring_fade=50.0, field_ring_count=2
    )
    # No y: refused first, before anything the UFO checks at birth.
    with pytest.raises(ValueError, match=message("ufo placement needs y")):
        spawn_drifter(Placement(DrifterType.UFO, seed=None, specialty_enabled=True), 1, TUNING)
    with pytest.raises(ValueError, match=message("ufo placement needs y")):
        Ufo.start_position(None, None, DISC_W, DISC_H, False)
    with pytest.raises(ValueError, match=message("ufo placement needs y")):
        Ufo.start_position(10.0, None, DISC_W, DISC_H, True)
    # Then a specialty, even with the tuning wrong, no seed and a y outside the band.
    for tuning in (make_tuning(type_extra=None), TUNING):
        with pytest.raises(ValueError, match=message("ufo has no specialty")):
            spawn_drifter(Placement(DrifterType.UFO, y=100.0, specialty_enabled=True), 1, tuning)
    # A specialty switched off, or left out, is fine.
    for switch in (False, None):
        placed = spawn_drifter(
            Placement(DrifterType.UFO, y=300.0, seed=1, specialty_enabled=switch), 1, TUNING
        )
        assert placed.phase is Phase.WARNING
    # Then tuning with no UFO type values: none, an empty base, another drifter's. No seed and a
    # y outside the band don't change the message.
    for bad in (None, wrong_type, other_type):
        tuning = make_tuning(type_extra=bad)
        for seed, y in ((SEED, 300.0), (None, 300.0), (None, 100.0), (SEED, 100.0)):
            with pytest.raises(ValueError, match=message("ufo tuning has no type values")):
                spawn_drifter(Placement(DrifterType.UFO, y=y, seed=seed), 1, tuning)
    # Then a missing seed, whatever the y.
    for y in (300.0, 100.0, 0.0):
        with pytest.raises(ValueError, match=message("ufo placement needs seed")):
            spawn_drifter(Placement(DrifterType.UFO, y=y), 1, TUNING)
    # Seed 0 is a seed.
    assert ufo(seed=0).seed == 0
    assert ufo(seed=MAX_SEED).seed == MAX_SEED
    # Then a y outside the band, both ends allowed, the numbers in `g` format.
    misses = (
        (100.0, "ufo placement y 100 is outside its band 188 to 440"),
        (187.5, "ufo placement y 187.5 is outside its band 188 to 440"),
        (187.999, "ufo placement y 187.999 is outside its band 188 to 440"),
        (440.001, "ufo placement y 440.001 is outside its band 188 to 440"),
        (441.0, "ufo placement y 441 is outside its band 188 to 440"),
        (0.0, "ufo placement y 0 is outside its band 188 to 440"),
        (480.0, "ufo placement y 480 is outside its band 188 to 440"),
        (-12.5, "ufo placement y -12.5 is outside its band 188 to 440"),
    )
    for y, text in misses:
        with pytest.raises(ValueError, match=message(text)):
            spawn_drifter(Placement(DrifterType.UFO, y=y, seed=SEED), 1, TUNING)
        with pytest.raises(ValueError, match=message(text)):
            spawn_drifter(
                Placement(DrifterType.UFO, x=100.0, y=y, seed=SEED, invert=True), 8, TUNING
            )
        run = start_run()
        with pytest.raises(ValueError, match=message(text)):
            add_drifters(run, [Placement(DrifterType.UFO, y=y, seed=SEED)], TUNING)
        assert run.drifters == ()
    for y in (BAND_TOP, BAND_TOP + 0.001, 300.0, BAND_BOTTOM - 0.001, BAND_BOTTOM):
        assert ufo(None, y).y == y
        assert ufo(None, y, invert=True).y == y
    # The band is the file's: a different band moves the edges and the numbers in the message.
    narrow = make_tuning(type_extra=replace(UFO_TYPE_EXTRA, band_top=200.0, band_bottom=430.5))
    assert ufo(None, 200.0, tuning=narrow).y == 200.0
    with pytest.raises(
        ValueError, match=message("ufo placement y 199 is outside its band 200 to 430.5")
    ):
        ufo(None, 199.0, tuning=narrow)
    # Born, called directly, refuses in the same order.
    with pytest.raises(ValueError, match=message("ufo has no specialty")):
        Ufo.born(birth(specialty_enabled=True, type_extra=None, seed=None, y=1.0))
    with pytest.raises(ValueError, match=message("ufo tuning has no type values")):
        Ufo.born(birth(type_extra=None, seed=None, y=1.0))
    with pytest.raises(ValueError, match=message("ufo placement needs seed")):
        Ufo.born(birth(seed=None, y=1.0))
    with pytest.raises(
        ValueError, match=message("ufo placement y 1 is outside its band 188 to 440")
    ):
        Ufo.born(birth(seed=3, y=1.0))
    # `invert` and `speed` are not refused.
    assert ufo(invert=True).invert
    assert ufo(speed=2.0).phase is Phase.WARNING


def test_a_seed_is_refused_on_any_other_drifter_and_birth_carries_the_seed_and_the_multiplier() -> (
    None
):
    # Only the UFO is seeded, of every drifter the game registers.
    assert available_drifters() >= {DrifterType.UFO, DrifterType.METEORITE}
    for drifter_type in available_drifters():
        assert drifter_class(drifter_type).seeded is (drifter_type is DrifterType.UFO), drifter_type
    # A seed on any other drifter is refused, 0 included, before born's own refusals.
    for seed in (0, 1, MAX_SEED):
        with pytest.raises(ValueError, match=message("meteorite has no seed")):
            spawn_drifter(Placement(DrifterType.METEORITE, x=100.0, seed=seed), 1, TUNING)
    with pytest.raises(ValueError, match=message("meteorite has no seed")):
        spawn_drifter(
            Placement(DrifterType.METEORITE, x=100.0, seed=5, invert=True, specialty_enabled=True),
            1,
            TUNING,
        )
    run = start_run()
    with pytest.raises(ValueError, match=message("meteorite has no seed")):
        add_drifters(run, [Placement(DrifterType.METEORITE, x=100.0, seed=5)], TUNING)
    assert run.drifters == ()
    # With no seed the meteorite is spawned as always, and the new Birth fields have defaults.
    plain = spawn_drifter(Placement(DrifterType.METEORITE, x=100.0), 8, TUNING)
    assert plain.phase is Phase.WARNING
    assert plain.speed == pytest.approx(0.375 * TOP_SIDE_SPEED * HAZARD_SPEED[7], abs=1e-9)
    defaults = Birth(
        x=-20.0,
        y=300.0,
        variant="standard",
        width=DISC_W,
        height=DISC_H,
        hitbox=UFO_HITBOX,
        speed=LEVEL_ONE_SPEED,
        warning_ticks=WARNING_TICKS,
        timer_mult=1.0,
        specialty_enabled=None,
        invert=False,
        variant_extra=None,
        rehit_cooldown_ticks=REHIT_COOLDOWN,
        rehit_dim=REHIT_DIM,
        type_extra=UFO_TYPE_EXTRA,
        telegraph_min_ticks=45,
    )
    assert defaults.seed is None
    assert defaults.hazard_speed_mult == 1.0
    # `Birth.seed` and `Birth.hazard_speed_mult` reach the UFO's born.
    born = Ufo.born(birth(seed=77, hazard_speed_mult=1.42))
    assert born.seed == 77
    assert born.weave_seed == 77
    assert born.weave_speed_max == pytest.approx(SPEED_MAX * 1.42, abs=1e-12)
    assert born.weave_turn == pytest.approx(TURN * 1.42, abs=1e-12)
    assert Ufo.born(birth(seed=0)).seed == 0
    unscaled = Ufo.born(birth(seed=77))
    assert unscaled.weave_speed_max == SPEED_MAX
    assert unscaled.weave_turn == TURN
    # Through the spawner they carry the placement's seed and the level's hazard speed x, or
    # Level 1's with the switch off.
    for level in (1, 5, 8):
        spawned = ufo(seed=424242, level=level)
        assert spawned.seed == 424242
        assert spawned.weave_seed == 424242
        assert spawned.weave_speed_max == pytest.approx(
            SPEED_MAX * HAZARD_SPEED[level - 1], abs=1e-12
        )
        flat = ufo(seed=424242, level=level, tuning=NO_SCALING)
        assert flat.weave_speed_max == SPEED_MAX
        assert flat.weave_turn == TURN
    # No other drifter changes: the meteorite is the same with or without a seed and a
    # multiplier on its Birth.
    base_rock = birth(seed=None, hazard_speed_mult=1.0, hitbox=ROCK_HITBOX, type_extra=None)
    seeded_rock = replace(base_rock, seed=99, hazard_speed_mult=1.42)
    assert Meteorite.born(seeded_rock) == Meteorite.born(base_rock)
    assert Meteorite.born(base_rock).phase is Phase.WARNING


def test_placement_seed_is_the_same_for_a_source_and_index_and_lies_in_range() -> None:
    assert MAX_SEED == 4_294_967_295
    assert DEBUG_SPAWNS_SOURCE == "debug_spawns"
    # The contract's formula, written out, and two values worked out from it.
    assert placement_seed("l1_a", 0) == random.Random("l1_a#0").getrandbits(32)
    assert placement_seed("l1_a", 0) == 3_644_637_674
    assert placement_seed("l1_a", 1) == 2_868_672_573
    assert placement_seed("wave_0", 0) == 293_031_380
    assert placement_seed("wave_0", 1) == 2_630_326_367
    assert placement_seed(DEBUG_SPAWNS_SOURCE, 3) == 2_528_993_570
    # The same source and index give the same seed on every call.
    for source, index in (("l1_a", 0), ("wave_0", 1), (DEBUG_SPAWNS_SOURCE, 3)):
        assert placement_seed(source, index) == placement_seed(source, index)
    # The contract's examples differ: another index, another wave, the debug list.
    assert placement_seed("l1_a", 0) != placement_seed("l1_a", 1)
    assert placement_seed("l1_a", 0) != placement_seed("wave_0", 0)
    assert placement_seed("wave_0", 0) != placement_seed(DEBUG_SPAWNS_SOURCE, 0)
    assert placement_seed("wave_0", 0) != placement_seed("wave_0", 1)
    # Two UFOs in one wave never share a path: no repeat over a long list.
    seeds = [placement_seed("l1_a", index) for index in range(500)]
    assert len(set(seeds)) == len(seeds)
    # Every seed lies from 0 to MAX_SEED, whatever the source.
    for source in ("l1_a", "wave_0", DEBUG_SPAWNS_SOURCE, "", "a#b", "wave with spaces"):
        for index in range(60):
            assert 0 <= placement_seed(source, index) <= MAX_SEED
    # A default seed makes a UFO the spawner takes.
    assert ufo(seed=placement_seed("l1_a", 0)).seed == 3_644_637_674


def test_a_ufo_crosses_at_its_speed_and_flies_level_until_it_is_fully_on_screen() -> None:
    ships = [spawn(), resting(0.0, 0.0), resting(500.0, 400.0), resting(318.0, 100.0)]
    steps = [0.0, 1.1, 3.7, 0.0, 1.87]
    for invert in (False, True):
        sign = -1.0 if invert else 1.0
        start = -20.0 if not invert else 660.0
        moving = active(invert=invert)
        plain = moving
        for n in range(1, 361):
            ctx = TickContext(ship=ships[n % len(ships)], scroll_step_px=steps[n % len(steps)])
            before_x = moving.x
            moving = moving.update(ctx)
            plain = plain.update(CTX)
            # The ship and the scroll never matter: the same UFO tick for tick.
            assert moving == plain, (invert, n)
            assert moving.ticks_in_phase == n
            assert moving.phase is Phase.ACTIVE
            # It crosses at its speed every tick, never stops, never turns back.
            assert moving.x == pytest.approx(start + sign * n * LEVEL_ONE_SPEED, abs=1e-9)
            assert (moving.x - before_x) * sign == pytest.approx(LEVEL_ONE_SPEED, abs=1e-12)
            # Level at its placed y until fully on screen: n 20 and before, the first pick on n 21.
            if n <= 20:
                assert not moving.weaving, (invert, n)
                assert (moving.y, moving.target_y, moving.velocity_y) == (300.0, 300.0, 0.0)
                assert moving.weave_ticks_left == 0
                assert moving.weave_up is None
                assert moving.weave_seed == SEED
            else:
                assert moving.weaving, (invert, n)
        # The pick is on n 21: the first state weaving, and it has already taken its first step.
        first = flown(active(invert=invert), 21)[-1]
        assert first.weaving
        assert first.weave_up is not None
        assert TICKS_MIN <= first.weave_ticks_left <= TICKS_MAX
        assert abs(first.velocity_y) == pytest.approx(TURN, abs=1e-12)
        assert (first.velocity_y < 0) == first.weave_up
        assert first.y == pytest.approx(300.0 + first.velocity_y, abs=1e-12)
        assert first.weave_seed != SEED
        assert not flown(active(invert=invert), 20)[-1].weaving
    # The Diagram's x values: -20.00, -18.03 (n 1), 19.48 (n 20), 21.45 (n 21), 659.06 (n 344).
    states = flown(active(), 345)
    assert round(states[0].x, 2) == -18.03
    assert round(states[19].x, 2) == 19.48
    assert round(states[20].x, 2) == 21.45
    assert round(states[343].x, 2) == 659.06
    assert round(states[344].x, 2) == 661.03
    # A UFO placed fully on screen weaves on its first tick; a placed x is still level until then.
    on_screen = flown(active(320.0), 1)[0]
    assert on_screen.weaving
    assert on_screen.x == pytest.approx(320.0 + LEVEL_ONE_SPEED, abs=1e-12)
    off = flown(active(-100.0), 40)
    assert [s.weaving for s in off] == [False] * 40
    assert all(s.y == 300.0 for s in off)
    # The limit is inclusive: a disc whose left edge lands on x 0 is fully on screen.
    edge = replace(active(18.0), velocity_x=2.0)
    assert edge.update(CTX).x == 20.0
    assert edge.update(CTX).weaving
    assert not replace(active(17.99), velocity_x=2.0).update(CTX).weaving
    right = replace(active(622.0, invert=True), velocity_x=-2.0)
    assert right.update(CTX).x == 620.0
    assert right.update(CTX).weaving
    assert not replace(active(622.01, invert=True), velocity_x=-2.0).update(CTX).weaving
    # Judged on everything drawn, vertically too: the dome's box reaches 10.5 above the disc's
    # top edge and 5.5 below the disc's center.
    for y, expected in ((15.4, False), (15.5, True), (474.5, True), (474.6, False)):
        assert replace(active(320.0), y=y).is_fully_on_screen() is expected, y
    assert replace(active(320.0), x=20.0).is_fully_on_screen()
    assert not replace(active(320.0), x=19.9).is_fully_on_screen()
    assert replace(active(320.0), x=620.0).is_fully_on_screen()
    assert not replace(active(320.0), x=620.1).is_fully_on_screen()
    # Once weaving it never stops, even as the UFO leaves: still weaving past the far wall.
    leaving = flown(active(), 420)
    assert all(s.weaving for s in leaving[20:])
    assert not leaving[-1].is_fully_on_screen()
    # A GONE UFO is left as it is.
    gone = replace(active(), phase=Phase.GONE)
    assert gone.update(CTX) == gone


def test_each_pick_follows_the_contract_from_its_seed() -> None:
    first_ups: set[bool] = set()
    picks_seen = 0
    for level in (1, 8):
        low = scaled_ticks(TICKS_MIN, level)
        high = scaled_ticks(TICKS_MAX, level)
        for invert in (False, True):
            for seed in range(25):
                y0 = (BAND_TOP, 200.0, 300.0, 400.0, BAND_BOTTOM)[seed % 5]
                current = active(y=y0, seed=seed, invert=invert, level=level)
                assert (current.weave_change_ticks_min, current.weave_change_ticks_max) == (
                    low,
                    high,
                )
                last_pick_up: bool | None = None
                for n in range(1, 361):
                    before = current
                    current = before.update(CTX)
                    picked = current.weaving and (
                        not before.weaving or before.weave_ticks_left == 1
                    )
                    if not picked:
                        if before.weaving:
                            assert current.weave_ticks_left == before.weave_ticks_left - 1
                            assert current.weave_up == before.weave_up
                            assert current.weave_seed == before.weave_seed
                            assert current.target_y == before.target_y
                        continue
                    picks_seen += 1
                    ref = reference_pick(before.weave_seed, before.weave_up, before.y, low, high)
                    assert current.weave_up is ref.up, (level, invert, seed, n)
                    assert current.weave_ticks_left == ref.ticks, (level, invert, seed, n)
                    assert current.target_y == pytest.approx(ref.target, abs=1e-9)
                    assert current.weave_seed == ref.seed, (level, invert, seed, n)
                    # The interval is a whole number from the scaled min to the scaled max.
                    assert isinstance(current.weave_ticks_left, int)
                    assert low <= current.weave_ticks_left <= high
                    # The new height: `step` away, or the band's edge; the other way when the room
                    # in the turn's direction is under the step minimum.
                    way_up = current.target_y < before.y
                    distance = abs(current.target_y - before.y)
                    assert current.weave_up is way_up
                    edge = BAND_TOP if way_up else BAND_BOTTOM
                    assert STEP_MIN <= distance <= STEP_MAX or current.target_y == edge
                    assert BAND_TOP <= current.target_y <= BAND_BOTTOM
                    if last_pick_up is None:
                        wanted = random.Random(before.weave_seed).random() < 0.5
                        first_ups.add(wanted)
                    else:
                        wanted = not last_pick_up
                    room = before.y - BAND_TOP if wanted else BAND_BOTTOM - before.y
                    assert way_up is (wanted if room >= STEP_MIN else not wanted)
                    last_pick_up = way_up
    assert first_ups == {True, False}
    assert picks_seen > 25 * 4 * 4
    # The picks are the weave_ticks_left apart: a pick, then the next one that many ticks later.
    states = flown(active(seed=3), 400)
    pick_ticks = [
        n + 1
        for n, (a, b) in enumerate(zip([active(seed=3), *states], states, strict=False))
        if b.weaving and (not a.weaving or a.weave_ticks_left == 1)
    ]
    assert pick_ticks[0] == 21
    for earlier, later in pairwise(pick_ticks):
        assert TICKS_MIN <= later - earlier <= TICKS_MAX
    # The contract's examples. At y 210 a pick that says up has 22 px of room: it goes down.
    # At y 400 a pick that says down has 40 px of room, not less than 40: it goes down to 440.
    # Each row is (y, the way the last pick went, the way this pick goes): the pick says the
    # opposite of the last.
    rows = (
        (210.0, False, False),
        (227.9, False, False),
        (228.0, False, True),
        (400.0, True, False),
        (400.1, True, True),
        (401.0, True, True),
        (250.0, False, True),
        (380.0, True, False),
    )
    for seed in range(30):
        for y, last_up, expected_up in rows:
            state = replace(
                active(y=y, seed=seed),
                weaving=True,
                weave_ticks_left=1,
                weave_up=last_up,
                target_y=y,
            )
            after = state.update(CTX)
            assert after.weave_up is expected_up, (seed, y)
            assert (after.target_y < y) is expected_up
            assert BAND_TOP <= after.target_y <= BAND_BOTTOM
            ref = reference_pick(seed, last_up, y, TICKS_MIN, TICKS_MAX)
            assert after.target_y == pytest.approx(ref.target, abs=1e-9)
            assert after.weave_ticks_left == ref.ticks
            if y == 210.0:
                assert STEP_MIN <= after.target_y - 210.0 <= STEP_MAX
            if y == 400.0:
                assert after.target_y == BAND_BOTTOM
            if y == 228.0:
                assert after.target_y == BAND_TOP


@pytest.mark.smoke
def test_over_many_seeds_the_weave_keeps_the_band_the_speed_limit_and_the_turn_limit() -> None:
    swings_landed = 0
    for level in (1, 8):
        speed_max = SPEED_MAX * HAZARD_SPEED[level - 1]
        turn = TURN * HAZARD_SPEED[level - 1]
        for invert in (False, True):
            for seed in range(70):
                y0 = (BAND_TOP, 200.0, 300.0, 400.0, BAND_BOTTOM, 188.5, 439.5)[seed % 7]
                current = active(y=y0, seed=seed, invert=invert, level=level)
                assert current.weave_speed_max == pytest.approx(speed_max, abs=1e-12)
                assert current.weave_turn == pytest.approx(turn, abs=1e-12)
                for n in range(1, 346):
                    before = current
                    current = before.update(CTX)
                    where = (level, invert, seed, n)
                    # The band holds on every tick, and so does every target.
                    assert BAND_TOP <= current.y <= BAND_BOTTOM, where
                    assert BAND_TOP <= current.target_y <= BAND_BOTTOM, where
                    # The speed never passes the top, and never changes by more than the turn.
                    assert abs(current.velocity_y) <= speed_max + 1e-9, where
                    assert abs(current.velocity_y - before.velocity_y) <= turn + 1e-9, where
                    # It never passes its target: it lands on it or is still short of it.
                    target = current.target_y
                    crossed = (before.y - target > 1e-9 and current.y - target < -1e-9) or (
                        before.y - target < -1e-9 and current.y - target > 1e-9
                    )
                    assert not crossed, where
                    # It lands on its target and then flies level until the next pick.
                    if (
                        before.weaving
                        and before.y == before.target_y
                        and current.target_y == before.target_y
                    ):
                        assert current.y == before.y, where
                        assert abs(current.velocity_y) < 1e-9, where
                    if current.weaving and current.y == target and before.y != target:
                        swings_landed += 1
                    # Before it weaves it is level at its placed y.
                    if not current.weaving:
                        assert current.y == y0, where
    assert swings_landed > 500


def test_the_easing_table_tick_for_tick() -> None:
    # Level 1, level at y 300, a pick has just chosen target_y 220 (80 px up): the Diagram's table.
    # The swing is set up as a weaving UFO with a long count, so tick 1 is the first ease step.
    up_swing = replace(
        active(y=300.0),
        velocity_x=0.0,
        weaving=True,
        weave_ticks_left=10**9,
        weave_up=True,
        target_y=220.0,
    )
    table = {
        1: (-0.10, 299.90),
        2: (-0.20, 299.70),
        16: (-1.60, 286.40),
        17: (-1.60, 284.80),
        50: (-1.60, 232.00),
        51: (-1.50, 230.50),
        52: (-1.40, 229.10),
        64: (-0.20, 220.10),
        65: (-0.10, 220.00),
        66: (0.00, 220.00),
    }
    down_swing = replace(up_swing, target_y=380.0)
    for swing, flip, goal in ((up_swing, 1.0, 220.0), (down_swing, -1.0, 380.0)):
        states = flown(swing, 90)
        for tick, (velocity, y) in table.items():
            state = states[tick - 1]
            assert state.velocity_y == pytest.approx(velocity * flip, abs=1e-9), tick
            assert state.y == pytest.approx(300.0 + (y - 300.0) * flip, abs=1e-9), tick
        # Every tick of it: up to speed by 0.1 a tick for 16 ticks, cruise at 1.6, brake by
        # exactly 0.1 a tick from tick 51, land on tick 65 and flat from tick 66.
        for tick in range(1, 91):
            state = states[tick - 1]
            if tick <= 16:
                expected = -0.1 * tick
            elif tick <= 50:
                expected = -1.6
            elif tick <= 65:
                expected = -(1.6 - 0.1 * (tick - 50))
            else:
                expected = 0.0
            assert state.velocity_y == pytest.approx(expected * flip, abs=1e-9), tick
            if tick >= 65:
                assert state.y == goal, tick
            assert state.target_y == goal
            assert state.x == swing.x
    # Braking starts where the brake speed drops below 1.6: 12 px out it is 1.5.
    assert weave_brake_speed(12.0, 0.1) == pytest.approx(1.5, abs=1e-9)
    # A short swing of 5 px from rest: speeds up, brakes, lands exactly and stays.
    short = replace(up_swing, target_y=295.0)
    travelled = flown(short, 40)
    assert travelled[-1].y == 295.0
    assert travelled[-1].velocity_y == 0.0
    assert all(s.y >= 295.0 for s in travelled)
    # Already at the target and at rest: nothing moves.
    resting_ufo = replace(up_swing, target_y=300.0)
    assert all(s.y == 300.0 and s.velocity_y == 0.0 for s in flown(resting_ufo, 20))
    # A pick the other way while it still moves brakes it at 0.1 a tick, then turns it: the speed
    # goes -1.6, -1.5, ... through 0 to the other way, never changing by more than 0.1.
    turning = replace(up_swing, y=250.0, velocity_y=-1.6, target_y=300.0)
    speeds = [s.velocity_y for s in flown(turning, 40)]
    assert speeds[0] == pytest.approx(-1.5, abs=1e-9)
    assert max(speeds) > 0
    for earlier, later in zip([-1.6, *speeds], speeds, strict=False):
        assert abs(later - earlier) <= TURN + 1e-9


def test_weave_brake_speed_and_stop_distance_at_the_contracts_examples() -> None:
    # Braking v, v - a, ... covers exactly the distance and stops; the last step is at most a.
    for turn in (0.1, 0.142):
        for distance in (0.01, 0.05, 0.1, 0.3, 1.0, 12.0, 37.3, 80.0, 120.0, 252.0):
            speed = weave_brake_speed(distance, turn)
            covered = 0.0
            step = speed
            while step > 1e-9:
                covered += step
                step -= turn
            assert covered == pytest.approx(distance, abs=1e-9), (turn, distance)
            assert speed > 0
    assert weave_brake_speed(0.0, 0.1) == 0.0
    assert weave_brake_speed(0.0, 0.142) == 0.0
    # Under one step it is the distance itself (k = 0), the Diagram's k = 14 row at 12 px is 1.5.
    assert weave_brake_speed(0.05, 0.1) == pytest.approx(0.05, abs=1e-12)
    assert weave_brake_speed(0.1, 0.1) == pytest.approx(0.1, abs=1e-12)
    assert weave_brake_speed(0.3, 0.1) == pytest.approx(0.2, abs=1e-9)
    assert weave_brake_speed(12.0, 0.1) == pytest.approx(0.8 + 0.7, abs=1e-9)
    # The speed is never more than a swing can brake from, and grows with the distance.
    previous = 0.0
    for tenths in range(1, 2000):
        speed = weave_brake_speed(tenths / 10, 0.1)
        assert speed >= previous - 1e-12
        previous = speed
    # Stopping distance: turn x k x (k + 1) / 2 with k = ceil(speed / turn).
    assert weave_stop_distance(1.6, 0.1) == pytest.approx(13.6, abs=1e-9)
    assert weave_stop_distance(1.6 * 1.42, 0.1 * 1.42) == pytest.approx(19.312, abs=1e-9)
    assert weave_stop_distance(0.0, 0.1) == 0.0
    assert weave_stop_distance(0.25, 0.1) == pytest.approx(0.6, abs=1e-9)
    assert weave_stop_distance(0.3, 0.1) == pytest.approx(0.6, abs=1e-9)
    assert weave_stop_distance(0.1, 0.1) == pytest.approx(0.1, abs=1e-9)
    assert weave_stop_distance(0.11, 0.1) == pytest.approx(0.3, abs=1e-9)


def test_the_tuning_checks_accept_the_gdd_values_and_refuse_each_broken_rule_in_order() -> None:
    # The GDD values pass.
    check_ufo_variant(DISC_W, DISC_H, DOME_R)
    check_ufo_weave(UFO_TYPE_EXTRA)
    # The dome's drawn box (2 x (radius + 1.5)) must fit the disc: 40 at most.
    check_ufo_variant(40.0, 10.0, 18.5)
    check_ufo_variant(21.0, 4.0, 9.0)
    with pytest.raises(
        ValueError,
        match=message(
            "dome_radius is too wide for the disc: 2 × (dome_radius + 1.5) must be at most "
            "disc_width (41 > 40)"
        ),
    ):
        check_ufo_variant(40.0, 10.0, 19.0)
    with pytest.raises(
        ValueError,
        match=message(
            "dome_radius is too wide for the disc: 2 × (dome_radius + 1.5) must be at most "
            "disc_width (21 > 20)"
        ),
    ):
        check_ufo_variant(20.0, 10.0, 9.0)
    # The weave: each rule on its own, with its message.
    cases = (
        (
            replace(UFO_TYPE_EXTRA, weave_change_ticks_max=59),
            "weave_change_ticks_max must be at least weave_change_ticks_min",
        ),
        (
            replace(UFO_TYPE_EXTRA, weave_step_max=39.0),
            "weave_step_max must be at least weave_step_min",
        ),
        (
            replace(UFO_TYPE_EXTRA, band_bottom=188.0),
            "band_bottom must be more than band_top",
        ),
        (
            replace(UFO_TYPE_EXTRA, band_bottom=150.0),
            "band_bottom must be more than band_top",
        ),
        (
            replace(UFO_TYPE_EXTRA, band_bottom=481.0),
            "band_bottom must be at most the screen height (480)",
        ),
        (
            replace(UFO_TYPE_EXTRA, band_bottom=260.0),
            "the band must be at least 2 × weave_step_min tall (72 < 80)",
        ),
        (
            replace(UFO_TYPE_EXTRA, weave_step_min=19.0, weave_step_max=120.0),
            "weave_step_min must be at least the stopping distance at the top hazard speed × "
            "(19 < 19.312)",
        ),
    )
    for extra, text in cases:
        with pytest.raises(ValueError, match=message(text)):
            check_ufo_weave(extra)
    # The edges that pass: a tick count equal, a step equal, a band of exactly 2 x step_min, a band
    # ending on the floor, a step minimum above the stopping distance.
    check_ufo_weave(replace(UFO_TYPE_EXTRA, weave_change_ticks_max=60))
    check_ufo_weave(replace(UFO_TYPE_EXTRA, weave_step_max=40.0))
    check_ufo_weave(replace(UFO_TYPE_EXTRA, band_bottom=268.0))
    check_ufo_weave(replace(UFO_TYPE_EXTRA, band_bottom=480.0))
    check_ufo_weave(replace(UFO_TYPE_EXTRA, weave_step_min=20.0))
    # In order: with every rule broken at once the first is named; fixing each reveals the next.
    broken = replace(
        UFO_TYPE_EXTRA,
        weave_change_ticks_max=10,
        weave_step_min=19.0,
        weave_step_max=10.0,
        band_top=300.0,
        band_bottom=500.0,
    )
    with pytest.raises(
        ValueError, match=message("weave_change_ticks_max must be at least weave_change_ticks_min")
    ):
        check_ufo_weave(broken)
    broken = replace(broken, weave_change_ticks_max=96)
    with pytest.raises(ValueError, match=message("weave_step_max must be at least weave_step_min")):
        check_ufo_weave(broken)
    broken = replace(broken, weave_step_max=120.0, band_top=500.0)
    with pytest.raises(ValueError, match=message("band_bottom must be more than band_top")):
        check_ufo_weave(broken)
    broken = replace(broken, band_top=300.0)
    with pytest.raises(
        ValueError, match=message("band_bottom must be at most the screen height (480)")
    ):
        check_ufo_weave(broken)
    broken = replace(broken, band_bottom=330.0)
    with pytest.raises(
        ValueError, match=message("the band must be at least 2 × weave_step_min tall (30 < 38)")
    ):
        check_ufo_weave(broken)
    broken = replace(broken, band_bottom=400.0)
    with pytest.raises(
        ValueError,
        match=message(
            "weave_step_min must be at least the stopping distance at the top hazard speed × "
            "(19 < 19.312)"
        ),
    ):
        check_ufo_weave(broken)
    check_ufo_weave(replace(broken, weave_step_min=20.0))


@pytest.mark.determinism
def test_the_same_seed_gives_the_same_path_another_seed_another_and_update_never_mutates() -> None:
    for invert in (False, True):
        one = flown(active(seed=2024, invert=invert), 400)
        two = flown(active(seed=2024, invert=invert), 400)
        assert one == two
        # Spawned again from the same placement, warning included: the same states.
        first = ufo(seed=2024, invert=invert)
        second = ufo(seed=2024, invert=invert)
        assert first == second
        assert flown(first, WARNING_TICKS + 400) == flown(second, WARNING_TICKS + 400)
        # Another seed, another path.
        other = flown(active(seed=2025, invert=invert), 400)
        assert [s.y for s in one] != [s.y for s in other]
        assert [s.weave_seed for s in one] != [s.weave_seed for s in other]
        # The x path is the same for every seed: only the weave comes from it.
        assert [s.x for s in one] == [s.x for s in other]
    paths = {tuple(round(s.y, 6) for s in flown(active(seed=seed), 200)) for seed in range(30)}
    assert len(paths) == 30
    # The same UFO and context give the same UFO, a call never changes what it was given, and a
    # call in between changes nothing.
    for start in (ufo(seed=9), active(seed=9), flown(active(seed=9), 70)[-1]):
        snapshot = copy.deepcopy(start)
        result = start.update(CTX)
        assert start == snapshot
        assert result is not start
        assert start.update(CTX) == result
        assert start == snapshot
        assert result.update(CTX) == result.update(CTX)
    # A UFO that picks does not change the one it came from.
    picking = replace(active(seed=9), weaving=True, weave_ticks_left=1, weave_up=True)
    snapshot = copy.deepcopy(picking)
    assert picking.update(CTX).weave_ticks_left >= TICKS_MIN
    assert picking == snapshot
    # In the run: the same placement added twice flies the same, state for state.
    placement = Placement(DrifterType.UFO, y=300.0, seed=31, invert=True)
    runs = [
        add_drifters(replace(start_run(), scroll=SCROLLING), [placement], TUNING) for _ in range(2)
    ]
    for _ in range(WARNING_TICKS + 120):
        runs = [step_run(replace(run, ship=SAFE_SHIP), NO_KEY) for run in runs]
    assert ufos_of(runs[0]) == ufos_of(runs[1])
    assert ufos_of(runs[0])[0].weaving


def test_level_scaling_speed_weave_speed_and_turn_by_hazard_speed_and_intervals_by_timer() -> None:
    for tuning in (TUNING, NO_SCALING):
        scaling = tuning is TUNING
        for level in range(1, 9):
            index = level - 1 if scaling else 0
            hazard = HAZARD_SPEED[index]
            timer_level = level if scaling else 1
            for built in (
                ufo(level=level, tuning=tuning),
                ufo(as_level=level, level=1, tuning=tuning),
                ufo(as_level=level, level=8, tuning=tuning),
            ):
                where = (scaling, level)
                assert built.speed == pytest.approx(LEVEL_ONE_SPEED * hazard, abs=1e-9), where
                assert built.velocity_x == pytest.approx(LEVEL_ONE_SPEED * hazard, abs=1e-9), where
                assert built.weave_speed_max == pytest.approx(SPEED_MAX * hazard, abs=1e-9), where
                assert built.weave_turn == pytest.approx(TURN * hazard, abs=1e-9), where
                # Both ends of the interval: Timer x, rounded up to a whole tick.
                assert built.weave_change_ticks_min == scaled_ticks(TICKS_MIN, timer_level), where
                assert built.weave_change_ticks_max == scaled_ticks(TICKS_MAX, timer_level), where
                assert isinstance(built.weave_change_ticks_min, int)
                # The step, the band and the warning never scale.
                assert built.weave_step_min == STEP_MIN
                assert built.weave_step_max == STEP_MAX
                assert built.band_top == BAND_TOP
                assert built.band_bottom == BAND_BOTTOM
                assert built.warning_ticks == WARNING_TICKS
                assert built.rehit_cooldown_ticks == REHIT_COOLDOWN
    # The contract's two rows: Level 1 and Level 8.
    one = ufo(level=1)
    assert (one.weave_change_ticks_min, one.weave_change_ticks_max) == (60, 96)
    eight = ufo(level=8)
    assert (eight.weave_change_ticks_min, eight.weave_change_ticks_max) == (42, 68)
    assert eight.speed == pytest.approx(2.8031, abs=1e-4)
    assert eight.weave_speed_max == pytest.approx(2.272, abs=1e-9)
    assert eight.weave_turn == pytest.approx(0.142, abs=1e-9)
    # Level 8 starts weaving on n 15 and is dropped on n 243.
    states = flown(active(level=8), 260)
    weaving_from = next(n for n, s in enumerate(states, 1) if s.weaving)
    dropped_on = next(n for n, s in enumerate(states, 1) if s.is_off_screen())
    assert (weaving_from, dropped_on) == (15, 243)
    states = flown(active(), 400)
    assert next(n for n, s in enumerate(states, 1) if s.weaving) == 21
    assert next(n for n, s in enumerate(states, 1) if s.is_off_screen()) == 345
    # `speed` from the placement is a Level 1 speed along the path: hazard speed x still applies,
    # and the weave keeps the file's values.
    for level in (1, 8):
        for invert in (False, True):
            plain = ufo(level=level, invert=invert)
            fast = ufo(level=level, invert=invert, speed=3.0)
            hazard = HAZARD_SPEED[level - 1]
            expected = 3.0 * hazard
            assert fast.speed == pytest.approx(expected, abs=1e-9)
            assert abs(fast.velocity_x) == pytest.approx(expected, abs=1e-9)
            assert (fast.velocity_x < 0) is invert
            assert fast.weave_speed_max == plain.weave_speed_max
            assert fast.weave_turn == plain.weave_turn
            assert fast.weave_change_ticks_min == plain.weave_change_ticks_min
            assert fast.weave_change_ticks_max == plain.weave_change_ticks_max
            assert replace(fast, speed=plain.speed, velocity_x=plain.velocity_x) == plain
    assert ufo(level=8, speed=3.0, tuning=NO_SCALING).speed == 3.0


@pytest.mark.parametrize("invert", [False, True], ids=["from_the_left", "from_the_right"])
def test_a_ufo_has_its_drawn_boxes_and_timeline_from_both_sides(invert: bool) -> None:
    sign = -1.0 if invert else 1.0
    start = 660.0 if invert else -20.0
    warning_at = (628.0, 300.0) if invert else (12.0, 300.0)
    assert ufo(None, 300.0, invert=invert).drawn_parts() == (
        Box(start, 300.0, DISC_W, DISC_H),
        Box(start, 295.0, DOME_BOX, DOME_BOX),
    )
    # The standalone timeline: warning 60 states, then n counts the ACTIVE ticks.
    chain = flown(ufo(None, 300.0, invert=invert), WARNING_TICKS + 400)
    for tick, state in enumerate(chain, 1):
        n = tick - WARNING_TICKS
        if n < 0:
            assert state.phase is Phase.WARNING
            assert state.warning_center() == warning_at
            assert not state.has_entered
            assert not state.is_off_screen()
            continue
        assert state.phase is Phase.ACTIVE
        assert state.ticks_in_phase == n
        assert state.x == pytest.approx(start + sign * n * LEVEL_ONE_SPEED, abs=1e-9)
        assert state.drawn_parts() == (
            Box(state.x, state.y, DISC_W, DISC_H),
            Box(state.x, state.y - 5.0, DOME_BOX, DOME_BOX),
        )
        # Entered on n 1; at n 0 the disc's edge is on the wall: nothing drawn is on screen.
        assert state.has_entered is (n >= 1), n
        assert state.is_partly_on_screen() is (n >= 1 and n <= 344), n
        # It starts weaving on n 21 and is dropped on n 345, never before it has entered.
        assert state.weaving is (n >= 21), n
        assert state.is_off_screen() is (n >= 345), n
        assert state.current_hitbox() == (
            Box(state.x, state.y, DISC_W, DISC_H),
            Circle(state.x, state.y - 5.0, DOME_R),
        )
    weave_start = chain[WARNING_TICKS + 21 - 1]
    assert round(weave_start.x, 2) == (618.55 if invert else 21.45)
    last_kept = chain[WARNING_TICKS + 344 - 1]
    dropped = chain[WARNING_TICKS + 345 - 1]
    assert round(dropped.x, 2) == (-21.03 if invert else 661.03)
    assert round(last_kept.x, 2) == (-19.06 if invert else 659.06)
    # The same timeline inside the run, with the world scrolling and the ship put back far off.
    run = add_drifters(
        replace(start_run(), scroll=SCROLLING),
        [Placement(DrifterType.UFO, y=300.0, invert=invert, seed=SEED)],
        TUNING,
    )
    dropped_tick = 0
    for tick in range(1, WARNING_TICKS + 346):
        run = step_run(replace(run, ship=SAFE_SHIP), NO_KEY)
        n = tick - WARNING_TICKS
        if n >= 345:
            assert run.drifters == (), tick
            dropped_tick = tick
            break
        (only,) = ufos_of(run)
        assert replace(only, uid=0) == replace(chain[tick - 1], uid=0), tick
        assert only.has_entered is (n >= 1), tick
        assert only.weaving is (n >= 21), tick
        assert run.lives == LIVES_START
    assert dropped_tick == WARNING_TICKS + 345
    # Never dropped before it has entered: a UFO that starts fully past the far wall, or far outside
    # its own wall, is kept for as long as the run goes on.
    for x, flying_invert in ((700.0, False), (-100.0, True), (1000.0, False)):
        away = add_drifters(
            replace(start_run(), scroll=SCROLLING),
            [Placement(DrifterType.UFO, x=x, y=300.0, invert=flying_invert, seed=SEED)],
            TUNING,
        )
        for _ in range(WARNING_TICKS + 60):
            away = step_run(replace(away, ship=SAFE_SHIP), NO_KEY)
            assert len(away.drifters) == 1
        (still_there,) = ufos_of(away)
        assert not still_there.has_entered
        assert not still_there.is_off_screen()
    # The leaving rule is the base's, on both boxes: the disc's left edge at or past x 640 (its
    # right edge at or past 0 with invert); the dome's narrower box is past it by then.
    assert not replace(active(659.9), has_entered=True).is_off_screen()
    assert replace(active(660.0), has_entered=True).is_off_screen()
    assert not replace(active(-19.9, invert=True), has_entered=True).is_off_screen()
    assert replace(active(-20.0, invert=True), has_entered=True).is_off_screen()
    assert not active(660.0).is_off_screen()
    assert not active(-20.0, invert=True).is_off_screen()


def test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds() -> None:
    # A still UFO at (320, 300): the disc spans x 300 to 340, y 295 to 305; the dome is a circle of
    # radius 9 centered on (320, 295), reaching up to y 286. The ship's bar is 12 wide and 32 tall,
    # its foot 32 wide and 12 tall at the bottom: its bottom edge is 16 px under its center.
    base = still(320.0, 300.0)
    disc_only = resting(285.0, 290.0)
    dome_only = resting(320.0, 274.0)
    clear = resting(320.0, 262.0)
    disc, dome = base.current_hitbox()
    for ship, on_disc, on_dome in ((disc_only, True, False), (dome_only, False, True)):
        assert hitboxes_overlap(ship_hitbox(ship), (disc,)) is on_disc
        assert hitboxes_overlap(ship_hitbox(ship), (dome,)) is on_dome
    assert not hitboxes_overlap(ship_hitbox(clear), base.current_hitbox())
    for name, ship in (("disc", disc_only), ("dome", dome_only)):
        run = step_run(run_of(ship, base), NO_KEY)
        assert run.lives == LIVES_START - 1, name
        assert run.invuln_ticks_left == INVULN_TICKS, name
        (hit,) = ufos_of(run)
        assert hit.rehit_ticks_left == REHIT_COOLDOWN, name
        assert hit.brightness() == REHIT_DIM
        assert hit.phase is Phase.ACTIVE
        assert (hit.x, hit.y) == (320.0, 300.0)
        assert not run.game_over
    # A ship clear of both shapes: no hit, no cooldown.
    nothing = step_run(run_of(clear, base), NO_KEY)
    assert nothing.lives == LIVES_START
    assert ufos_of(nothing)[0].rehit_ticks_left == 0
    assert ufos_of(nothing)[0].brightness() == 1.0
    # While the ship is invulnerable the UFO passes through it: no hit, no cooldown, and it still
    # flies. Protection counts the state going into the tick: 5 ticks left means 5 protected ticks.
    run = run_of(dome_only, base, invuln_ticks_left=5)
    for tick in range(1, 6):
        run = step_run(replace(run, ship=dome_only), NO_KEY)
        assert run.lives == LIVES_START, tick
        assert ufos_of(run)[0].rehit_ticks_left == 0, tick
    run = step_run(replace(run, ship=dome_only), NO_KEY)
    assert run.lives == LIVES_START - 1
    assert run.invuln_ticks_left == INVULN_TICKS
    assert ufos_of(run)[0].rehit_ticks_left == REHIT_COOLDOWN
    # A hit while the UFO flies and weaves: the ship is put on its disc every tick, so it touches
    # all the time. One hit on tick 1, the cooldown counting 180 down, no second hit on ticks 2 to
    # 181 (the invulnerable blink ends on its own after 30), a second on tick 182.
    flying = replace(active(300.0, 300.0))
    run = run_of(resting(300.0, 290.0), flying)
    twin = flying
    for tick in range(1, REHIT_COOLDOWN + 3):
        (current,) = ufos_of(run)
        run = step_run(replace(run, ship=resting(current.x, current.y - 10.0)), NO_KEY)
        twin = twin.update(CTX).mark_entered()
        (after,) = ufos_of(run)
        # It keeps flying and weaving exactly as one that was never touched, but for its graze
        # state: a touch ends the hazard's graze for good (SPENT, DRA-117, run.md step 5b item 3).
        assert after.graze_state is GrazeState.SPENT, tick
        spent = replace(after, rehit_ticks_left=0, uid=0, graze_state=twin.graze_state)
        assert spent == replace(twin, uid=0), tick
        assert after.weaving
        if tick == 1:
            assert run.lives == LIVES_START - 1
            assert after.rehit_ticks_left == REHIT_COOLDOWN
            assert after.brightness() == REHIT_DIM
            assert run.invuln_ticks_left == INVULN_TICKS
        elif tick <= REHIT_COOLDOWN + 1:
            assert run.lives == LIVES_START - 1, tick
            assert after.rehit_ticks_left == REHIT_COOLDOWN - (tick - 1), tick
            assert after.brightness() == (REHIT_DIM if after.rehit_ticks_left > 0 else 1.0)
            if tick == 31:
                assert run.invuln_ticks_left == 0
            assert hitboxes_overlap(ship_hitbox(run.ship), after.current_hitbox()), tick
        else:
            # Tick 182: the cooldown is over and the ship is still on it: the second hit.
            assert run.lives == LIVES_START - 2
            assert after.rehit_ticks_left == REHIT_COOLDOWN
            assert run.invuln_ticks_left == INVULN_TICKS
    assert not run.game_over


def test_a_ufo_logs_spawn_active_each_hit_and_gone_and_nothing_from_core_drifters(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    placement = Placement(DrifterType.UFO, y=300.0, seed=SEED)
    run = add_drifters(replace(start_run(), scroll=SCROLLING), [placement], TUNING)
    twin = ufo(None, 300.0, seed=SEED)
    twin_states = flown(twin, WARNING_TICKS + 345)
    for tick in range(1, WARNING_TICKS + 346):
        ship = SAFE_SHIP
        if tick in (100, 101):
            # Put the ship on the UFO for two ticks: one hit, and the cooldown stops a second.
            (current,) = ufos_of(run)
            ship = resting(current.x, current.y - 10.0)
        run = step_run(replace(run, ship=ship), NO_KEY)
    assert run.drifters == ()
    assert run.lives == LIVES_START - 1
    last = twin_states[-1]
    lines = run_lines(caplog)
    assert lines == [
        "drifter spawn id=1 type=ufo variant=standard x=-20.00 y=300.00 speed=1.97 level=1",
        "drifter active id=1 type=ufo x=-20.00 y=300.00",
        "drifter touch id=1 type=ufo effect=hit",
        "life lost lives=2",
        "invulnerable end",
        f"drifter gone id=1 type=ufo x={last.x:.2f} y={last.y:.2f}",
    ]
    # Every record is the run's: the UFO, the spawner and the collision logged nothing themselves.
    assert {r.name for r in caplog.records} == {RUN_LOGGER}
    assert not [r for r in caplog.records if r.name.startswith("core.drifters")]
    # From the right wall too, and a UFO that never enters logs no `drifter gone`.
    caplog.clear()
    mirrored = add_drifters(
        replace(start_run(), scroll=SCROLLING),
        [
            Placement(DrifterType.UFO, x=700.0, y=250.0, seed=3),
            Placement(DrifterType.UFO, y=250.0, seed=4, invert=True),
        ],
        TUNING,
    )
    for _ in range(WARNING_TICKS + 5):
        mirrored = step_run(replace(mirrored, ship=SAFE_SHIP), NO_KEY)
    assert [line for line in run_lines(caplog) if "gone" in line] == []
    assert [line for line in run_lines(caplog) if "touch" in line] == []
    assert len([line for line in run_lines(caplog) if "active" in line]) == 2
