"""The floating island, the base rules it relies on, and islands inside the run.

Contract: docs/contracts/systems/drifters.md, Diagram (the island timeline), Interface
(`core/drifters/floating_island.py`), Rules (The base: Phase, Parked and moving, Block; Spawner,
step 4 Parked; Floating island); docs/contracts/systems/run.md, Interface (`island_ground`),
Rules (steps 4, 5a, 6 and 7, Other rules) and Logging; docs/contracts/systems/waves.md (the
unknown-type message, tested in test_wave_files.py). Task:
docs/contracts/DRA-86/tasks/DRA-86-09-qa-engineer.md. One test per behavior it lists.

The tuning records are built here from the GDD values below, never read from game/tuning/, and
no expected number is imported from the code under test. The expected shapes are written out
from the contract's Diagram, never taken from `island_hitbox`. The ship against the island's
shapes alone is in test_collision.py and test_ship_islands.py.
"""

import logging
from dataclasses import replace

import pytest

from core.collision import Box, Circle, Hitbox, Polygon, deeply_overlaps, hitboxes_overlap
from core.drifters.base import Drifter, DrifterType, Phase, TickContext, TouchEffect
from core.drifters.coin import Coin, CoinTypeExtra, CoinVariantExtra
from core.drifters.floating_island import (
    FloatingIsland,
    IslandShape,
    IslandTypeExtra,
    IslandVariantExtra,
)
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.run import Run, add_drifters, island_ground, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust, ship_hitbox, spawn

ARM: float = 40.0
"""The L's and the T's arm, px. Source: drifters/05-floating-islands.md, Values (arm, guess)."""

SIZES: dict[str, tuple[float, float, IslandShape]] = {
    "rectangle": (320.0, 120.0, IslandShape.RECTANGLE),
    "box": (120.0, 120.0, IslandShape.RECTANGLE),
    "l_shape": (320.0, 120.0, IslandShape.L_SHAPE),
    "t_shape": (320.0, 120.0, IslandShape.T_SHAPE),
    "triangle": (320.0, 120.0, IslandShape.TRIANGLE),
}
"""Width, height and shape kind of each variant. Source: drifters/05-floating-islands.md, Values
and Shapes (guess); drifters.md, Rules, Floating island (Variants)."""

VARIANTS: tuple[str, ...] = tuple(SIZES)
INVERTIBLE: frozenset[str] = frozenset({"l_shape", "t_shape", "triangle"})
"""Variants whose shape takes `invert`. Source: drifters/05-floating-islands.md, rule 9."""

HEIGHT: float = 120.0
"""Every variant is 120 tall. Source: same."""

SCROLL_SPEED: float = 1.1
"""px/tick at Level 1. Source: 03-world-and-camera.md, scroll_base (guess)."""

SCROLL_START_DELAY: int = 30
"""Ticks. Source: 03-world-and-camera.md, scroll_start_delay (guess)."""

SCREEN_H: float = 480.0
"""px. Source: 03-world-and-camera.md, screen_h (guess)."""

SHIP_HALF: float = 16.0
"""Half of the ship's 32 x 32 square. Source: 04-ship.md, ship_w, ship_h (guess)."""

GRAVITY: float = 0.16
FALL_CAP: float = 5.5
"""px/tick², px/tick. Source: 04-ship.md, Values, gravity, fall_cap (guess)."""

LIVES_START: int = 3
INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

SPAWN_X: float = 320.0
SPAWN_Y: float = 240.0
"""Source: 05-lives-and-damage.md, fall_respawn (locked)."""

TOP_LINE_Y: float = 168.0
"""round(480 * 0.35). Source: 03-world-and-camera.md, rule 2."""

RUN_LOGGER = "core.run"
SHIP_LOGGER = "core.ship"
"""Logger names. Source: systems/run.md and systems/ship.md, Logging."""

NO_KEY = Thrust()

SCROLLING: Scroll = Scroll(ticks=100, scrolled_ticks=70)
"""A scroll already moving: the next step moves the world 1.1 px."""

STILL: Scroll = Scroll()
"""A scroll at tick 0: the next 30 steps leave the world standing still."""

FAR_LEFT: Ship = Ship(x=40.0, y=240.0, vx=0.0, vy=0.0)
FAR_RIGHT: Ship = Ship(x=600.0, y=240.0, vx=0.0, vy=0.0)
"""Resting ships clear of an island 320 wide centered at x 320 (left) or at x 0 (right)."""


def upright_hitbox(variant: str) -> Hitbox:
    """The un-inverted shapes of a variant, offsets from its center, from the Diagram."""
    return diagram_hitbox(variant, invert=False)


def diagram_hitbox(variant: str, *, invert: bool) -> Hitbox:
    """The shapes of a variant at its file sizes, offsets from the center, written out from the
    contract's Diagram (Floating island). `invert` mirrors the shape top to bottom.
    """
    width, height, shape = SIZES[variant]
    sign = -1.0 if invert else 1.0
    match shape:
        case IslandShape.RECTANGLE:
            return (Box(0.0, 0.0, width, height),)
        case IslandShape.L_SHAPE:
            return (Box(0.0, sign * 40.0, 320.0, 40.0), Box(-140.0, 0.0, 40.0, 120.0))
        case IslandShape.T_SHAPE:
            return (Box(0.0, -sign * 40.0, 320.0, 40.0), Box(0.0, 0.0, 40.0, 120.0))
        case IslandShape.TRIANGLE:
            return (Polygon(((-160.0, -sign * 60.0), (160.0, sign * 60.0), (-160.0, sign * 60.0))),)


ROCK_HITBOX: Hitbox = (Circle(0.0, 0.0, 14.0),)
"""The medium meteorite. Source: drifters/01-meteorite.md, variants (guess)."""

COIN_HITBOX: Hitbox = (Box(0.0, 0.0, 12.0, 10.0),)
"""The coin's one box, the crystal's middle. Source: drifters.md, Rules, Coin (Size and hitbox)."""


def make_tuning(*, switches: PlaytestSwitches | None = None) -> DrifterTuning:
    """Build the island, meteorite and coin tuning from the GDD values above.

    The island's records are built the way the contract says `app.tuning` builds them: the
    un-inverted shapes, `speed_ratio` 0.0 and no entry warning.
    """
    islands: dict[str, VariantTuning] = {
        name: VariantTuning(
            width=width,
            height=height,
            hitbox=upright_hitbox(name),
            extra=IslandVariantExtra(shape=shape),
        )
        for name, (width, height, shape) in SIZES.items()
    }
    coin_extra = CoinTypeExtra(
        body_height=10,
        ring_width=22,
        ring_height=8,
        glint_size=2,
        glint_left=3,
        glint_top=3,
        popup_ticks=60,
        popup_rise_per_tick=0.5,
    )
    return DrifterTuning(
        drifters={
            DrifterType.FLOATING_ISLAND: DrifterTypeTuning(
                variants=islands,
                default_variant="rectangle",
                speed_ratio=0.0,
                entry_warning_ticks=0,
                extra=IslandTypeExtra(arm=ARM),
            ),
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=ROCK_HITBOX)},
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=60,
            ),
            DrifterType.COIN: DrifterTypeTuning(
                variants={
                    "common": VariantTuning(
                        width=12,
                        height=20,
                        hitbox=COIN_HITBOX,
                        extra=CoinVariantExtra(points=50, glint=False),
                    )
                },
                default_variant="common",
                speed_ratio=0.0,
                entry_warning_ticks=0,
                extra=coin_extra,
            ),
        },
        switches=PlaytestSwitches() if switches is None else switches,
    )


TUNING: DrifterTuning = make_tuning()
NO_SCALING: DrifterTuning = make_tuning(
    switches=PlaytestSwitches(hazard_speed_scaling=False, timer_scaling=False)
)


def island(
    variant: str | None = None,
    x: float | None = 320.0,
    y: float | None = None,
    *,
    invert: bool = False,
    as_level: int | None = None,
    level: int = 1,
    tuning: DrifterTuning = TUNING,
) -> FloatingIsland:
    """Spawn an island through the spawner. y None: its bottom edge on the top edge."""
    placement = Placement(
        DrifterType.FLOATING_ISLAND, x, y, variant=variant, as_level=as_level, invert=invert
    )
    spawned: Drifter = spawn_drifter(placement, level, tuning)
    assert isinstance(spawned, FloatingIsland)
    return spawned


def rock(x: float, y: float) -> Meteorite:
    """An ACTIVE meteorite that stands still where it is put."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, x, y), 1, TUNING)
    assert isinstance(spawned, Meteorite)
    return replace(spawned, phase=Phase.ACTIVE, ticks_in_phase=0, speed=0.0)


def coin(x: float, y: float) -> Coin:
    """A coin put where given."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.COIN, x, y), 1, TUNING)
    assert isinstance(spawned, Coin)
    return spawned


def resting(x: float, y: float) -> Ship:
    """A ship at rest at (x, y)."""
    return Ship(x=x, y=y, vx=0.0, vy=0.0)


def run_of(
    ship: Ship,
    *drifters: Drifter,
    scroll: Scroll = SCROLLING,
    lives: int = LIVES_START,
    waiting: bool = False,
    invuln_ticks_left: int = 0,
) -> Run:
    """A run with the drifters numbered from 1, in order, and the ship where given."""
    numbered = tuple(replace(d, uid=i + 1) for i, d in enumerate(drifters))
    return Run(
        ship=ship,
        scroll=scroll,
        lives=lives,
        waiting=waiting,
        invuln_ticks_left=invuln_ticks_left,
        drifters=numbered,
        next_uid=len(numbered) + 1,
    )


def run_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Every line the run logged, in order."""
    return [r.getMessage() for r in caplog.records if r.name == RUN_LOGGER]


def islands_of(run: Run) -> list[FloatingIsland]:
    """The islands on the field, in order."""
    return [d for d in run.drifters if isinstance(d, FloatingIsland)]


def test_an_island_is_born_active_with_no_warning_and_speed_0_at_every_level() -> None:
    for variant in VARIANTS:
        inverts = (False, True) if variant in INVERTIBLE else (False,)
        for invert in inverts:
            where = (variant, invert)
            width, height, shape = SIZES[variant]
            base = island(variant, 320.0, None, invert=invert)
            assert base.phase is Phase.ACTIVE, where
            assert base.ticks_in_phase == 0
            assert base.warning_ticks == 0
            assert base.speed == 0.0
            assert (base.x, base.y) == (320.0, -HEIGHT / 2)
            assert (base.width, base.height) == (width, height)
            assert base.variant == variant
            assert base.shape is shape
            assert base.invert is invert
            assert base.arm == ARM
            assert base.uid == 0
            assert not base.has_entered
            assert base.specialty is None
            assert base.rehit_ticks_left == 0
            assert base.parked
            assert base.effect_on_touch() is TouchEffect.BLOCK
            # Its hitbox is there on the state it is born on: there is no WARNING state to wait.
            expected = diagram_hitbox(variant, invert=invert)
            assert base.hitbox == expected
            assert base.current_hitbox() == tuple(_placed(expected, 320.0, -HEIGHT / 2))
            # Its first update keeps it ACTIVE.
            first = base.update(TickContext(ship=spawn()))
            assert first.phase is Phase.ACTIVE
            assert first.ticks_in_phase == 1
            # Every level, every as_level and both switch sets give the very same island.
            for tuning in (TUNING, NO_SCALING):
                for level in range(1, 9):
                    by_level = island(
                        variant, 320.0, None, invert=invert, level=level, tuning=tuning
                    )
                    by_as_level = island(
                        variant, 320.0, None, invert=invert, as_level=level, tuning=tuning
                    )
                    assert by_level == base, (where, level)
                    assert by_as_level == base, (where, level)
    # Added to a run, it is ACTIVE at once, with its uid, and logs no `drifter active` later.
    added = add_drifters(start_run(), [Placement(DrifterType.FLOATING_ISLAND, x=320.0)], TUNING)
    assert len(added.drifters) == 1
    assert added.drifters[0].phase is Phase.ACTIVE
    assert added.drifters[0].uid == 1
    assert added.drifters[0].current_hitbox() != ()


def _placed(shapes: Hitbox, x: float, y: float) -> list[Box | Polygon]:
    """The shapes moved to (x, y), written out here for boxes and polygons."""
    out: list[Box | Polygon] = []
    for shape in shapes:
        if isinstance(shape, Box):
            out.append(Box(shape.cx + x, shape.cy + y, shape.w, shape.h))
        else:
            assert isinstance(shape, Polygon)
            out.append(Polygon(tuple((px + x, py + y) for px, py in shape.points)))
    return out


def test_an_island_starts_at_the_x_given_and_the_y_given_or_just_above_the_top_edge() -> None:
    for variant in VARIANTS:
        top = island(variant, 320.0, None)
        assert (top.x, top.y) == (320.0, -HEIGHT / 2), variant
        # Its bottom edge is on the top edge: fully off screen.
        assert top.y + top.height / 2 == 0.0
        spot = island(variant, 440.0, 210.0)
        assert (spot.x, spot.y) == (440.0, 210.0)
        assert spot.phase is Phase.ACTIVE
        assert spot.current_hitbox() == tuple(_placed(upright_hitbox(variant), 440.0, 210.0))
        # An x of 0 is an x, and so is a y of 0.
        zero = island(variant, 0.0, 0.0)
        assert (zero.x, zero.y) == (0.0, 0.0)
    # No variant given: the rectangle, the default.
    assert island(None).variant == "rectangle"
    for invert in (False, True):
        assert FloatingIsland.start_position(55.0, None, 120.0, 120.0, invert) == (55.0, -60.0)
        assert FloatingIsland.start_position(55.0, 7.0, 120.0, 120.0, invert) == (55.0, 7.0)
    # A placement without x is refused, with or without y; the run is left as it was.
    for placement in (
        Placement(DrifterType.FLOATING_ISLAND),
        Placement(DrifterType.FLOATING_ISLAND, y=100.0),
    ):
        with pytest.raises(ValueError, match="floating_island placement needs x"):
            spawn_drifter(placement, 1, TUNING)
        with pytest.raises(ValueError, match="floating_island placement needs x"):
            add_drifters(start_run(), [placement], TUNING)
    with pytest.raises(ValueError, match="floating_island placement needs x"):
        FloatingIsland.start_position(None, 10.0, 120.0, 120.0, False)


def test_an_island_moves_only_by_the_scroll_step_and_stands_still_before_the_scroll() -> None:
    steps = [0.0, 0.0, 1.1, 1.1, 3.7, 0.0, 1.87, 1.1]
    ships = [spawn(), resting(0.0, 0.0), resting(500.0, 400.0), resting(318.0, 100.0)]
    for variant in VARIANTS:
        for tuning in (TUNING, NO_SCALING):
            for level in (1, 8):
                where = (variant, tuning is NO_SCALING, level)
                moving = island(variant, 123.0, 50.0, as_level=level, tuning=tuning)
                assert moving.speed == 0.0, where
                y = 50.0
                for index, step in enumerate(steps * 3):
                    ship = ships[index % len(ships)]
                    moving = moving.update(TickContext(ship=ship, scroll_step_px=step))
                    y += step
                    assert moving.y == pytest.approx(y, abs=1e-9), (where, index)
                    assert moving.x == 123.0
                    assert moving.ticks_in_phase == index + 1
                    assert moving.phase is Phase.ACTIVE
                # A TickContext built with the ship alone is a world standing still.
                still = moving.update(TickContext(ship=spawn()))
                assert still.y == moving.y
                assert still.x == moving.x
        # In WARNING and GONE it is left as it is, whatever the step.
        for phase in (Phase.WARNING, Phase.GONE):
            held = replace(island(variant, 123.0, 50.0), phase=phase)
            assert held.update(TickContext(ship=spawn(), scroll_step_px=1.1)) == held
    # In a run: still on the states after ticks 1 to 30, first moves on tick 31, then 1.1 a tick.
    run = add_drifters(start_run(), [Placement(DrifterType.FLOATING_ISLAND, x=100.0)], TUNING)
    for tick in range(1, 71):
        run = step_run(replace(run, ship=FAR_RIGHT), NO_KEY)
        (only,) = islands_of(run)
        assert only.x == 100.0
        assert only.speed == 0.0
        if tick <= SCROLL_START_DELAY:
            assert only.y == -HEIGHT / 2, tick
        else:
            expected = -HEIGHT / 2 + (tick - SCROLL_START_DELAY) * SCROLL_SPEED
            assert only.y == pytest.approx(expected, abs=1e-9), tick


def test_invert_is_taken_by_the_l_the_t_and_the_triangle_and_refused_by_the_rectangle_and_box() -> (
    None
):
    for variant in VARIANTS:
        placement = Placement(DrifterType.FLOATING_ISLAND, x=320.0, variant=variant, invert=True)
        if variant in INVERTIBLE:
            turned = island(variant, 320.0, None, invert=True)
            assert turned.invert
            assert turned.hitbox == diagram_hitbox(variant, invert=True)
            assert turned.hitbox != diagram_hitbox(variant, invert=False)
            # Everything but the shape and the flag is the upright island's.
            upright = island(variant, 320.0, None)
            assert replace(turned, hitbox=upright.hitbox, invert=False) == upright
            added = add_drifters(start_run(), [placement], TUNING)
            assert islands_of(added)[0].invert
        else:
            message = f"floating_island variant '{variant}' has no invert"
            with pytest.raises(ValueError, match=message):
                spawn_drifter(placement, 1, TUNING)
            run = start_run()
            with pytest.raises(ValueError, match=message):
                add_drifters(run, [placement], TUNING)
            assert run.drifters == ()
            # Off, it is accepted.
            assert not island(variant, 320.0, None, invert=False).invert
    # A speed is refused whatever it is, at any level, for every variant.
    for variant in VARIANTS:
        for speed in (0.0, 1.0, 4.5):
            placement = Placement(
                DrifterType.FLOATING_ISLAND, x=320.0, variant=variant, speed=speed
            )
            with pytest.raises(ValueError, match="floating_island has no speed"):
                spawn_drifter(placement, 1, TUNING)
            with pytest.raises(ValueError, match="floating_island has no speed"):
                add_drifters(start_run(), [placement], TUNING)
    # A specialty switched on is refused, for every variant.
    for variant in VARIANTS:
        placement = Placement(
            DrifterType.FLOATING_ISLAND, x=320.0, variant=variant, specialty_enabled=True
        )
        with pytest.raises(ValueError, match="floating_island has no specialty"):
            spawn_drifter(placement, 1, TUNING)
        with pytest.raises(ValueError, match="floating_island has no specialty"):
            add_drifters(start_run(), [placement], TUNING)


def test_an_island_enters_on_its_first_state_on_screen_and_is_dropped_at_the_floor(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    ctx = TickContext(ship=spawn(), scroll_step_px=SCROLL_SPEED)
    for variant in VARIANTS:
        inverts = (False, True) if variant in INVERTIBLE else (False,)
        for invert in inverts:
            where = (variant, invert)
            # The drifter alone. At T its bottom edge is on the top edge: not on screen yet.
            moving = island(variant, 320.0, None, invert=invert)
            assert not moving.is_partly_on_screen(), where
            assert not moving.mark_entered().has_entered, where
            assert not moving.is_off_screen(), where
            for n in range(1, 547):
                moving = moving.update(ctx).mark_entered()
                assert moving.has_entered, (where, n)
                assert moving.y == pytest.approx(-60.0 + n * SCROLL_SPEED, abs=1e-9)
                # Its top edge is at 479.50 on T+545 (kept) and 480.60 on T+546 (dropped).
                assert moving.is_off_screen() == (n >= 546), (where, n)
    # In a run, with the world scrolling, the same timeline and the drop's log line.
    caplog.clear()
    run = replace(start_run(), scroll=SCROLLING)
    run = add_drifters(run, [Placement(DrifterType.FLOATING_ISLAND, x=320.0)], TUNING)
    for n in range(1, 547):
        run = step_run(replace(run, ship=FAR_LEFT), NO_KEY)
        if n < 546:
            (only,) = islands_of(run)
            assert only.has_entered
            assert only.y == pytest.approx(-60.0 + n * SCROLL_SPEED, abs=1e-9)
        else:
            assert run.drifters == ()
    assert [line for line in run_lines(caplog) if "gone" in line] == [
        "drifter gone id=1 type=floating_island x=320.00 y=540.60"
    ]
    # Placed on screen it shows there at once, and enters on its first update.
    spot = island("rectangle", 320.0, 240.0)
    assert spot.is_partly_on_screen()
    assert spot.update(ctx).mark_entered().has_entered
    # Placed half past a side wall it never leaves by the side: it never moves sideways. It goes
    # only below the floor, once its top edge is at or below it (y >= 540).
    for x in (0.0, 640.0):
        edge = island("rectangle", x, 240.0)
        for n in range(1, 400):
            edge = edge.update(ctx).mark_entered()
            assert edge.x == x
            assert edge.has_entered
            assert edge.is_off_screen() == (edge.y - HEIGHT / 2 >= SCREEN_H), (x, n)
    # Never before it has entered: fully past a side from the start, or already below the floor,
    # it is not off screen on any state and the run never drops it.
    for x, y in ((-1000.0, 240.0), (1640.0, 240.0), (320.0, 700.0)):
        outside = island("rectangle", x, y)
        for n in range(1, 300):
            outside = outside.update(ctx).mark_entered()
            assert not outside.has_entered, (x, y, n)
            assert not outside.is_off_screen(), (x, y, n)
        parked = add_drifters(
            replace(start_run(), scroll=SCROLLING),
            [Placement(DrifterType.FLOATING_ISLAND, x=x, y=y)],
            TUNING,
        )
        for _ in range(300):
            parked = step_run(replace(parked, ship=FAR_LEFT), NO_KEY)
        assert len(parked.drifters) == 1


def _first_resting_tick(states: list[Run]) -> int:
    """The index of the first state with the ship against an island."""
    return next(i for i, state in enumerate(states) if state.ship.against_island)


def test_a_ship_falls_onto_an_island_stands_and_rides_down_and_falls_when_it_leaves(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    # A 320 x 120 island at (320, 300), its top edge at 240 and moving 1.1 a tick. The ship
    # falls from rest at (320, 200), its bottom edge at 216.
    run = run_of(resting(320.0, 200.0), island("rectangle", 320.0, 300.0))
    states: list[Run] = []
    for _ in range(260):
        run = step_run(run, NO_KEY)
        states.append(run)
    # State k (1-based) is after tick k. The island's top edge is 240 + 1.1 k. It is dropped on
    # the state where y >= 540: 300 + 1.1 k >= 540 first at k = 219.
    landed = _first_resting_tick(states)
    assert 5 <= landed < 30
    for index in range(landed):
        # Falling: gravity every tick, no cap reached, no contact.
        assert states[index].ship.vy == pytest.approx(GRAVITY * (index + 1), abs=1e-9)
        assert not states[index].ship.against_island
    for index in range(landed, 218):
        state = states[index]
        k = index + 1
        assert len(islands_of(state)) == 1, k
        assert state.ship.against_island, k
        assert state.ship.y + SHIP_HALF == pytest.approx(240.0 + SCROLL_SPEED * k, abs=1e-9), k
        assert state.ship.x == 320.0
        assert state.ship.vy == pytest.approx(SCROLL_SPEED, abs=1e-9), k
        assert state.lives == LIVES_START
        assert not state.waiting
    # State 219: the island is dropped, the ship still stands where it rode to.
    last = states[218]
    assert islands_of(last) == []
    assert last.ship.y + SHIP_HALF == pytest.approx(240.0 + SCROLL_SPEED * 219, abs=1e-9)
    assert last.lives == LIVES_START
    # Then it falls from there at 1.1 px/tick: the top edge reaches the floor (y >= 496) after
    # m more ticks where 464.9 + 1.1 m + 0.08 m (m + 1) first reaches 496, m = 14.
    for m in range(1, 14):
        state = states[218 + m]
        fall_y = 464.9 + SCROLL_SPEED * m + GRAVITY * m * (m + 1) / 2
        assert state.ship.y == pytest.approx(fall_y, abs=1e-6), m
        assert state.lives == LIVES_START, m
        assert not state.ship.against_island
    fell = states[218 + 14]
    assert fell.lives == LIVES_START - 1
    assert fell.waiting
    assert fell.invuln_ticks_left == INVULN_TICKS
    assert fell.ship == spawn()
    assert "life lost lives=2" in run_lines(caplog)
    assert not any(line.startswith("respawn clear") for line in run_lines(caplog))
    assert not any(line.startswith("drifter touch") for line in run_lines(caplog))


def test_an_island_never_hits_and_never_pays_invulnerable_or_not(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    for variant in VARIANTS:
        for protected in (False, True):
            caplog.clear()
            where = (variant, protected)
            # The ship is put in the middle of the island: the worst overlap. 40 ticks: a ship
            # pushed out below an island falls off the floor after that, which costs a fall.
            start = INVULN_TICKS if protected else 0
            run = run_of(
                resting(320.0, 300.0),
                island(variant, 320.0, 300.0),
                invuln_ticks_left=start,
            )
            blocked_once = False
            for tick in range(1, 41):
                run = step_run(run, NO_KEY)
                assert run.lives == LIVES_START, (where, tick)
                assert not run.game_over
                assert run.coin_points == 0
                assert run.popups == ()
                assert run.score == run.scroll.meters
                assert run.invuln_ticks_left == max(start - tick, 0), (where, tick)
                (only,) = islands_of(run)
                assert only.rehit_ticks_left == 0
                assert only.phase is Phase.ACTIVE
                assert only.brightness() == 1.0
                # Blocked, invulnerable or not: the ship is never deep inside it (a hair of
                # SURFACE_TOLERANCE on the slope counts as touching, as in the push-out).
                assert not deeply_overlaps(ship_hitbox(run.ship), only.current_hitbox()), (
                    where,
                    tick,
                )
                blocked_once = blocked_once or run.ship.against_island
            assert blocked_once, where
            assert not [line for line in run_lines(caplog) if line.startswith("drifter touch")]
            assert not [line for line in run_lines(caplog) if line.startswith("life lost")]
            assert not [line for line in run_lines(caplog) if "game over" in line]
    # A coin the ship is not near and a hazard far away change nothing either: an island beside
    # them is not a hit and not a collect.
    spread = run_of(
        resting(320.0, 300.0), island("box", 320.0, 300.0), rock(600.0, 100.0), coin(40.0, 400.0)
    )
    after = step_run(spread, NO_KEY)
    assert after.lives == LIVES_START
    assert after.coin_points == 0
    assert after.drifters[0].rehit_ticks_left == 0
    assert after.drifters[1].rehit_ticks_left == 0


@pytest.mark.parametrize("protected", [False, True])
def test_a_ship_in_the_respawn_wait_is_carried_down_by_an_island_and_falls_off_the_floor(
    protected: bool, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    start_invuln = 1000 if protected else 0
    # The island's bottom edge is on the waiting ship's top edge (224). It moves 1.1 a tick and
    # carries the ship, which keeps waiting. The ship's top edge reaches the floor when its
    # center is at 496: 240 + 1.1 k >= 496 first at k = 233.
    run = run_of(
        spawn(),
        island("rectangle", 320.0, 164.0),
        waiting=True,
        invuln_ticks_left=start_invuln,
    )
    for k in range(1, 233):
        run = step_run(run, NO_KEY)
        assert run.waiting, k
        assert run.lives == LIVES_START, k
        assert run.ship.x == 320.0
        assert run.ship.y == pytest.approx(240.0 + SCROLL_SPEED * k, abs=1e-6), k
        assert run.ship.vy == pytest.approx(SCROLL_SPEED, abs=1e-9), k
        assert run.ship.against_island, k
        assert run.invuln_ticks_left == max(start_invuln - k, 0)
    fell = step_run(run, NO_KEY)
    lines = run_lines(caplog)
    assert fell.ship == spawn()
    assert f"respawn from x=320.00 y=496.30 wait={not protected}" in lines
    assert not any(line.startswith("respawn clear") for line in lines)
    if protected:
        # A protected fall costs no life and waits for no press.
        assert fell.lives == LIVES_START
        assert not fell.waiting
        assert fell.invuln_ticks_left == start_invuln - 233
    else:
        assert fell.lives == LIVES_START - 1
        assert fell.waiting
        assert fell.invuln_ticks_left == INVULN_TICKS
        assert "life lost lives=2" in lines


def test_a_ship_in_the_respawn_wait_with_no_island_on_it_stays_exactly_as_it_was() -> None:
    far = island("rectangle", 320.0, 600.0)
    for drifters in ((), (far,)):
        run = run_of(spawn(), *drifters, waiting=True)
        for _ in range(60):
            run = step_run(run, NO_KEY)
            assert run.waiting
            assert run.ship == spawn()
            assert not run.ship.against_island
    # A press ends the wait and the ship moves that tick.
    run = step_run(run, Thrust(up=True))
    assert not run.waiting
    assert run.ship != spawn()


RESPAWN_CASES: tuple[tuple[str, str, float, float, float | None], ...] = (
    # name, variant, island center y, ship y after the fall, or None when the spawn is clear.
    # Spawn box: x 304 to 336, y 224 to 256 at the respawn point (320, 240).
    ("above: top edge 220, up 36, down 116", "rectangle", 280.0, 204.0, 204.0),
    ("above on the top line: top edge 200, up 56", "rectangle", 260.0, 184.0, 184.0),
    ("above passes the top line: top edge 199, up 57", "rectangle", 259.0, 335.0, 335.0),
    ("above passes the top line, nearer: top edge 190", "rectangle", 250.0, 326.0, 326.0),
    ("tie but above passes the top line: top edge 180", "rectangle", 240.0, 316.0, 316.0),
    ("below is nearer: top edge 120", "rectangle", 180.0, 256.0, 256.0),
    ("tie, both free: the L's bar 220 to 260", "l_shape", 200.0, 204.0, 204.0),
    ("touching from below: top edge 256", "rectangle", 316.0, SPAWN_Y, None),
    ("touching from above: bottom edge 224", "rectangle", 164.0, SPAWN_Y, None),
    ("far away", "rectangle", 400.0, SPAWN_Y, None),
)


@pytest.mark.parametrize(("name", "variant", "center_y", "ship_y", "moved_to"), RESPAWN_CASES)
@pytest.mark.parametrize("protected", [False, True])
def test_a_fall_respawns_the_ship_clear_of_an_island_over_the_respawn_point(
    name: str,
    variant: str,
    center_y: float,
    ship_y: float,
    moved_to: float | None,
    protected: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    # The ship falls on this tick (its top edge reaches the floor); the world is still, so the
    # island stands where it is put.
    falling = Ship(x=320.0, y=495.0, vx=0.0, vy=5.5)
    run = run_of(
        falling,
        island(variant, 320.0, center_y),
        scroll=STILL,
        invuln_ticks_left=INVULN_TICKS if protected else 0,
    )
    fell = step_run(run, NO_KEY)
    lines = run_lines(caplog)
    assert fell.ship == Ship(x=320.0, y=ship_y, vx=0.0, vy=0.0), name
    assert not hitboxes_overlap(ship_hitbox(fell.ship), fell.drifters[0].current_hitbox()), name
    from_index = lines.index(f"respawn from x=320.00 y=500.50 wait={not protected}")
    clear = [line for line in lines if line.startswith("respawn clear of island")]
    if moved_to is None:
        assert clear == [], name
    else:
        assert clear == [f"respawn clear of island y={moved_to:.2f}"], name
        # `respawn clear of island` comes right after `respawn from`.
        assert lines[from_index + 1] == clear[0], name
    if protected:
        assert fell.lives == LIVES_START
        assert not fell.waiting
        assert not any(line.startswith("life lost") for line in lines)
    else:
        assert fell.lives == LIVES_START - 1
        assert fell.waiting
        assert fell.invuln_ticks_left == INVULN_TICKS
        assert lines.index("life lost lives=2") < from_index


def test_a_fall_respawns_clear_of_the_island_where_it_stands_after_the_scroll_moved_it() -> None:
    # The world moves 1.1 this tick, so the island is at its new place when the ship respawns:
    # top edge 219.5 + 1.1 = 220.6, so up is 35.4 and the ship's bottom edge lands on it.
    run = run_of(Ship(x=320.0, y=495.0, vx=0.0, vy=5.5), island("rectangle", 320.0, 279.5))
    fell = step_run(run, NO_KEY)
    assert fell.ship.y == pytest.approx(204.6, abs=1e-9)
    assert fell.ship.x == 320.0
    assert (fell.ship.vx, fell.ship.vy) == (0.0, 0.0)
    assert not hitboxes_overlap(ship_hitbox(fell.ship), fell.drifters[0].current_hitbox())


def test_an_island_logs_drifter_spawn_and_drifter_gone_only(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    run = replace(start_run(), scroll=SCROLLING)
    run = add_drifters(run, [Placement(DrifterType.FLOATING_ISLAND, x=320.0)], TUNING)
    for _ in range(546):
        run = step_run(replace(run, ship=FAR_LEFT), NO_KEY)
    assert run.drifters == ()
    assert run_lines(caplog) == [
        "drifter spawn id=1 type=floating_island variant=rectangle x=320.00 y=-60.00 "
        "speed=0.00 level=1",
        "drifter gone id=1 type=floating_island x=320.00 y=540.60",
    ]
    # Nothing under core.drifters, core.collision or core.popup logs either.
    quiet = ("core.drifters", "core.collision", "core.popup")
    assert not [r for r in caplog.records if r.name.startswith(quiet)]
    # An island a ship rides logs the same two run lines; the contact line is core.ship's.
    caplog.clear()
    ride = run_of(resting(320.0, 200.0), island("rectangle", 320.0, 300.0))
    ride = replace(ride, drifters=(replace(ride.drifters[0], uid=1),), next_uid=2)
    for _ in range(40):
        ride = step_run(ride, NO_KEY)
    assert ride.ship.against_island
    assert run_lines(caplog) == []
    ship_lines = [r.getMessage() for r in caplog.records if r.name == SHIP_LOGGER]
    assert len([line for line in ship_lines if line.startswith("island contact")]) == 1
    assert not [r for r in caplog.records if r.name.startswith(quiet)]


def test_island_ground_holds_every_active_islands_shapes_in_order_and_the_scroll_step() -> None:
    l_shape = replace(island("l_shape", 100.0, 200.0), uid=1)
    waiting = replace(island("rectangle", 400.0, 300.0), uid=2, phase=Phase.WARNING)
    inverted_triangle = replace(island("triangle", 300.0, 150.0, invert=True), uid=3)
    gone = replace(island("box", 250.0, 250.0), uid=4, phase=Phase.GONE)
    hazard = replace(rock(200.0, 200.0), uid=5)
    pickup = replace(coin(220.0, 220.0), uid=6)
    box = replace(island("box", 500.0, 350.0), uid=7)
    drifters = (l_shape, waiting, inverted_triangle, gone, hazard, pickup, box)
    expected: Hitbox = (
        Box(100.0, 240.0, 320.0, 40.0),
        Box(-40.0, 200.0, 40.0, 120.0),
        Polygon(((140.0, 210.0), (460.0, 90.0), (140.0, 90.0))),
        Box(500.0, 350.0, 120.0, 120.0),
    )
    for step_px in (0.0, 1.1, 3.7):
        ground = island_ground(drifters, step_px)
        assert ground.hitbox == expected, step_px
        assert ground.velocity_x == 0.0
        assert ground.velocity_y == step_px
    # The order is the drifters' order, one island's shapes in its own order.
    reversed_ground = island_ground(tuple(reversed(drifters)), 1.1)
    assert reversed_ground.hitbox == (
        Box(500.0, 350.0, 120.0, 120.0),
        Polygon(((140.0, 210.0), (460.0, 90.0), (140.0, 90.0))),
        Box(100.0, 240.0, 320.0, 40.0),
        Box(-40.0, 200.0, 40.0, 120.0),
    )
    # Every shape is the island's current one, so a moved island moves its shapes.
    moved = replace(box, y=360.0)
    assert island_ground((moved,), 1.1).hitbox == (Box(500.0, 360.0, 120.0, 120.0),)
    # With no island, or no ACTIVE one, the ground holds nothing.
    assert island_ground((), 1.1).hitbox == ()
    assert island_ground((hazard, pickup), 1.1).hitbox == ()
    assert island_ground((waiting, gone), 1.1).hitbox == ()
