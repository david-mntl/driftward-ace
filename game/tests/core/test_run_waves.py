"""The run's waves: the level, the due placements, the wave clock inside a tick, the retry.

Contract: docs/contracts/systems/run.md, Diagram (the one-tick flowchart, Drifters entering, the
level rise timeline), Interface (`waves`, `level`, `wave_spawns_due`, `start_run`), Rules (The
level; steps 3, 5 and 9a; a game-over tick; `add_drifters`; Other rules; Logging);
docs/contracts/systems/scroll.md, Diagram and Rules (The step, The next step's movement);
docs/contracts/systems/waves.md, Rules (The wave clock, Seeds). Task:
docs/contracts/DRA-76/tasks/DRA-76-09-qa-engineer.md. One test per behavior it lists. The wave
books and the tuning records are built here from the GDD values below, never read from
game/waves/ or game/tuning/, and no expected number is imported from the code under test.
"""

import logging
import random
from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction

import pytest

from core.collision import Box, Circle
from core.drifters.base import Drifter, DrifterType, Phase
from core.drifters.coin import Coin, CoinTypeExtra, CoinVariantExtra
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.run import Run, add_drifters, start_run, step_run
from core.scroll import Scroll
from core.ship import Ship, Thrust, spawn
from core.waves import (
    LevelPlaylist,
    Wave,
    WaveBook,
    WaveKind,
    WavePlacement,
    WaveRun,
    start_waves,
)

LIVES_START: int = 3
INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

LEVEL_COUNT: int = 8
"""Source: 08-difficulty.md, rule 1 (Level 8 is the last)."""

SCROLL_SPEED_1: Fraction = Fraction("1.1")
"""px/tick at Level 1. Source: 03-world-and-camera.md, scroll_base (guess)."""

SCROLL_START_DELAY: int = 30
"""Ticks of a still world. Source: 03-world-and-camera.md, scroll_start_delay (guess)."""

SCROLL_MULT: tuple[Fraction, ...] = tuple(
    Fraction(tenths, 10) for tenths in (10, 11, 12, 13, 14, 15, 16, 17)
)
"""Scroll speed × per level, Level 1 first. Source: 08-difficulty.md, level table (locked)."""

HAZARD_SPEED_MULT: tuple[float, ...] = (1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42)
"""Hazard speed × per level, Level 1 first. Source: 08-difficulty.md, level table (locked)."""

THRUST_SIDE: float = 0.42
DRAG_X: float = 0.94
TOP_SIDE_SPEED: float = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
"""px/tick. Source: 04-ship.md, Values, thrust_side, drag_x (guess), derived values."""

SPEED_RATIO: float = 0.375
"""Level 1 meteorite speed as a multiple of the top sideways speed. Source:
drifters/01-meteorite.md, speed_ratio (guess)."""

LEVEL_1_SPEED: float = SPEED_RATIO * TOP_SIDE_SPEED
"""px/tick. Source: 08-difficulty.md, level table (hazard speed × 1.00 at Level 1)."""

WARNING_TICKS: int = 60
"""Source: 07-drifters.md, entry_warning_ticks (guess)."""

SHIP_H: int = 32
SCREEN_H: int = 480
SCREEN_W: int = 640
"""px. Source: 04-ship.md, ship_h; 03-world-and-camera.md, screen_h, screen_w (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

HOME_X: float = 320.0
HOME_Y: float = 240.0
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

AT_FLOOR_Y: float = SCREEN_H + SHIP_H / 2 - FALL_CAP
"""A ship at fall_cap here moves exactly FALL_CAP next tick and its top edge lands on the floor."""

CRYSTAL_W: int = 12
CRYSTAL_H: int = 20
BODY_H: int = 10
RING_W: int = 22
RING_H: int = 8
GLINT: tuple[int, int, int] = (2, 3, 3)
POINTS: dict[str, int] = {"common": 50, "rare": 100}
"""Source: drifters/04-coin.md, Values (guess); 06-scoring.md, coin_points."""

RUN_LOGGER: str = "core.run"
WAVES_LOGGER: str = "core.waves"
"""Logger names. Source: systems/run.md and systems/waves.md, Logging."""

SEED_BITS: int = 64
"""Bits of the next seed. Source: waves.md, Interface (`getrandbits(64)`)."""

NO_KEY = Thrust()
UP = Thrust(up=True)
LEFT = Thrust(left=True)

SCROLLING: Scroll = Scroll(ticks=100, scrolled_ticks=70)
"""A scroll already moving: 70 moving ticks, 77 px, and the next step moves the world."""

SEED: int = 20261019
"""A first seed for the runs below."""

WAVE_ZERO: str = "w0"
"""Id of Wave 0 in the books built here."""


def make_tuning() -> DrifterTuning:
    """Build the meteorite and coin tuning from the GDD values above.

    The coin's records are the way `app.tuning` builds them: every variant the crystal's size and
    one box, speed_ratio 0.0 and no entry warning.
    """
    type_extra = CoinTypeExtra(
        body_height=BODY_H,
        ring_width=RING_W,
        ring_height=RING_H,
        glint_size=GLINT[0],
        glint_left=GLINT[1],
        glint_top=GLINT[2],
        popup_ticks=60,
        popup_rise_per_tick=0.5,
    )
    coin_variants: dict[str, VariantTuning] = {
        name: VariantTuning(
            width=CRYSTAL_W,
            height=CRYSTAL_H,
            hitbox=(Box(0.0, 0.0, float(CRYSTAL_W), float(BODY_H)),),
            extra=CoinVariantExtra(points=points, glint=name == "rare"),
        )
        for name, points in POINTS.items()
    }
    return DrifterTuning(
        drifters={
            DrifterType.COIN: DrifterTypeTuning(
                variants=coin_variants,
                default_variant="common",
                speed_ratio=0.0,
                entry_warning_ticks=0,
                extra=type_extra,
            ),
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=(Circle(0, 0, 14),))},
                default_variant="medium",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
        },
        switches=PlaytestSwitches(),
    )


TUNING: DrifterTuning = make_tuning()


def wave(
    wave_id: str,
    length: float,
    *,
    kind: WaveKind = WaveKind.FIXED,
    min_level: int | None = None,
    extra_rest: int = 0,
    triggers: Sequence[float] = (),
    x0: float = 0.0,
) -> Wave:
    """Build a wave whose i-th placement is a meteorite with x = x0 + i, at the i-th trigger."""
    placements: tuple[WavePlacement, ...] = tuple(
        WavePlacement(
            at_px=trigger, placement=Placement(DrifterType.METEORITE, x=x0 + index, y=-20.0)
        )
        for index, trigger in enumerate(triggers)
    )
    return Wave(
        wave_id=wave_id,
        length_px=length,
        kind=kind,
        min_level=min_level,
        extra_rest_ticks=extra_rest,
        placements=placements,
    )


def book_of(waves: Sequence[Wave], levels: Sequence[LevelPlaylist] = ()) -> WaveBook:
    """Build a book. `levels` is Level 1 first; the levels it leaves out have no slots."""
    playlists: tuple[LevelPlaylist, ...] = (
        *levels,
        *(LevelPlaylist() for _ in range(LEVEL_COUNT - len(levels))),
    )
    return WaveBook(
        waves={item.wave_id: item for item in waves}, wave_zero_id=WAVE_ZERO, playlists=playlists
    )


def steady_book() -> WaveBook:
    """Wave 0 is so long that no wave ends: the level never changes inside it."""
    return book_of([wave(WAVE_ZERO, 1_000_000.0)])


def level_up_book() -> WaveBook:
    """Wave 0 and `a` are 11 px long, so at 1.1 px a tick each ends after 10 moving ticks.

    Level 1 plays `a` and then Level 2 starts. Wave `a` has one placement due on its last tick
    (trigger 11 px, x 200). Levels 2 to 8 play `long`, 10 000 px, so the level stays 2 for the
    ticks the tests walk. Wave 0 ends on tick 40 (30 still ticks and 10 moving ones), `a` on
    tick 50: the level is 2 in the state after tick 50.
    """
    waves: list[Wave] = [
        wave(WAVE_ZERO, 11.0),
        wave("a", 11.0, triggers=[11.0], x0=200.0),
        wave("long", 10_000.0),
    ]
    levels: list[LevelPlaylist] = [
        LevelPlaylist(fixed=("a",)),
        *(LevelPlaylist(fixed=("long",)) for _ in range(2, LEVEL_COUNT + 1)),
    ]
    return book_of(waves, levels)


LEVEL_UP_TICK: int = 50
"""The tick `a` ends in `level_up_book`: 30 still ticks, then 20 moving ones of 1.1 px = 22 px."""

POOL_IDS: tuple[str, ...] = ("p1", "p2", "p3", "p4")
"""Pool waves of `picks_book`, sorted by id."""


def picks_book() -> WaveBook:
    """Every wave 11 px: Wave 0 and then 40 random slots at Level 1 over four pool waves.

    A wave ends every 10 moving ticks, so the first pick starts on tick 40 and one more every 10
    ticks.
    """
    waves: list[Wave] = [wave(WAVE_ZERO, 11.0)]
    waves.extend(wave(wave_id, 11.0, kind=WaveKind.POOL, min_level=1) for wave_id in POOL_IDS)
    return book_of(waves, [LevelPlaylist(random_count=40)])


def expected_picks(seed: int, count: int) -> list[str]:
    """The first `count` picks of `picks_book` from `seed`, replayed here from the contract.

    Each pick: a `random.Random(pick_seed)`, `choice` over the pool ids sorted by id without the
    wave before it, then the next seed from `getrandbits(64)`. Source: waves.md, Rules, Starting a
    wave and Random picks.
    """
    last: str = WAVE_ZERO
    picks: list[str] = []
    for _ in range(count):
        chooser: random.Random = random.Random(seed)
        candidates: list[str] = [wave_id for wave_id in POOL_IDS if wave_id != last]
        last = chooser.choice(candidates)
        seed = chooser.getrandbits(SEED_BITS)
        picks.append(last)
    return picks


def next_seed(seed: int) -> int:
    """The seed of the run after the one that started from `seed`. Source: waves.md, Seeds."""
    return random.Random(seed).getrandbits(SEED_BITS)


def home_ship() -> Ship:
    """A resting ship at the test position."""
    return Ship(x=HOME_X, y=HOME_Y, vx=0.0, vy=0.0)


def falling_ship() -> Ship:
    """A ship whose next step puts its top edge on the floor."""
    return Ship(x=HOME_X, y=AT_FLOOR_Y, vx=0.0, vy=FALL_CAP)


def hold(run: Run) -> Run:
    """Put the ship back at home, so it never falls or touches anything while the world runs."""
    return replace(run, ship=home_ship())


def fly(run: Run, ticks: int) -> Run:
    """Step `ticks` playing ticks with no arrow held, the ship put back at home before each."""
    for _ in range(ticks):
        run = step_run(hold(run), NO_KEY)
    return run


def die(run: Run, thrust: Thrust = NO_KEY) -> Run:
    """Step one tick on which the ship falls on its last life: the run ends on that tick."""
    over: Run = step_run(replace(run, lives=1, ship=falling_ship()), thrust)
    assert over.game_over
    assert over.lives == 0
    return over


def rock(x: float, y: float, *, uid: int = 1) -> Meteorite:
    """An ACTIVE meteorite that stands still where it is put."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, x, y), 1, TUNING)
    assert isinstance(spawned, Meteorite)
    return replace(spawned, uid=uid, phase=Phase.ACTIVE, ticks_in_phase=0, speed=0.0)


def run_of(
    waves: WaveRun | None,
    *,
    ship: Ship | None = None,
    lives: int = LIVES_START,
    invuln_ticks_left: int = 0,
    waiting: bool = False,
    drifters: tuple[Drifter, ...] = (),
) -> Run:
    """A run on a moving scroll holding `waves`, the ship at home by default."""
    return Run(
        ship=home_ship() if ship is None else ship,
        scroll=SCROLLING,
        lives=lives,
        invuln_ticks_left=invuln_ticks_left,
        waiting=waiting,
        drifters=drifters,
        next_uid=len(drifters) + 1,
        waves=waves,
    )


def messages(caplog: pytest.LogCaptureFixture, *names: str) -> list[tuple[str, str]]:
    """Every (logger, line) of the named loggers so far, in the order logged."""
    return [(record.name, record.getMessage()) for record in caplog.records if record.name in names]


def walk_ids(run: Run, ticks: int) -> tuple[Run, list[str]]:
    """Fly `ticks` ticks and list each wave that started on the way, in order."""
    assert run.waves is not None
    seen: list[str] = []
    last: str = run.waves.wave_id
    for _ in range(ticks):
        run = fly(run, 1)
        assert run.waves is not None
        if run.waves.wave_id != last:
            last = run.waves.wave_id
            seen.append(last)
    return run, seen


def test_a_run_with_no_waves_is_at_level_1_with_nothing_due_and_a_retry_has_no_waves(
    caplog: pytest.LogCaptureFixture,
) -> None:
    for run in (start_run(), start_run(None)):
        assert run.waves is None
        assert run.level == 1
        assert run.wave_spawns_due == ()

    run = start_run()
    exact: Fraction = Fraction(0)
    for tick in range(1, 71):
        run = step_run(hold(run), NO_KEY)
        if tick > SCROLL_START_DELAY:
            exact += SCROLL_SPEED_1
        assert run.waves is None, tick
        assert run.level == 1, tick
        assert run.wave_spawns_due == (), tick
        assert run.scroll.distance_px == pytest.approx(float(exact), abs=1e-9), tick
    assert run.scroll.scrolled_ticks == 40
    assert run.scroll.raised_level_ticks == (0,) * (LEVEL_COUNT - 1)

    over: Run = die(run)
    assert over.waves is None
    assert over.level == 1
    assert over.wave_spawns_due == ()
    frozen: Run = step_run(over, NO_KEY)
    assert frozen.waves is None
    assert frozen.scroll == over.scroll

    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    caplog.set_level(logging.DEBUG, logger=WAVES_LOGGER)
    caplog.clear()
    again: Run = step_run(frozen, UP)
    assert again.waves is None
    assert again.level == 1
    assert again.wave_spawns_due == ()
    assert again.scroll == start_run().scroll
    assert again.lives == LIVES_START
    assert not again.game_over
    assert messages(caplog, RUN_LOGGER, WAVES_LOGGER) == [(RUN_LOGGER, "new run")]


def test_a_run_with_waves_takes_its_level_and_due_placements_from_them() -> None:
    book: WaveBook = steady_book()
    waves: WaveRun = start_waves(book, SEED)

    started: Run = start_run(waves)
    assert started.waves is waves
    assert started.level == 1
    assert started.wave_spawns_due == ()
    assert started.scroll == start_run().scroll
    assert started.drifters == ()
    assert started.score == 0

    due: tuple[Placement, ...] = (
        Placement(DrifterType.METEORITE, x=11.0, y=-20.0),
        Placement(DrifterType.COIN, x=22.0, y=-10.0),
    )
    for level in range(1, LEVEL_COUNT + 1):
        run: Run = start_run(replace(waves, level=level, spawns_due=due))
        assert run.level == level
        assert run.wave_spawns_due == due


def waves_ending_on_the_next_tick() -> WaveRun:
    """Wave 0 ends on the next tick of `SCROLLING`, with a placement due on that tick.

    Wave 0 is 78 px long with a placement at 78 px. The scroll is at 77 px and moves 1.1 px, so
    the wave ends on the next tick (78.1 px) and the placement is due then. The extra rest of 3
    ticks makes the wave clock visible: the rest starts on that tick with 3 ticks left, and each
    later playing tick takes 1 from it. A tick the clock skipped or ran twice shows in that count.
    """
    book: WaveBook = book_of(
        [wave(WAVE_ZERO, 78.0, extra_rest=3, triggers=[78.0], x0=7.0), wave("a", 50.0)],
        [LevelPlaylist(fixed=("a",))],
    )
    return start_waves(book, SEED)


def assert_the_wave_clock_ran_once(run: Run) -> None:
    """The state after the tick `waves_ending_on_the_next_tick` ends Wave 0 on."""
    assert run.waves is not None
    assert run.waves.resting
    assert run.waves.rest_ticks_left == 3
    assert run.waves.wave_id == WAVE_ZERO
    assert run.waves.current_wave_id is None
    assert [placement.x for placement in run.wave_spawns_due] == [7.0]
    assert run.level == 1


def test_the_waves_step_once_on_every_playing_tick() -> None:
    waves: WaveRun = waves_ending_on_the_next_tick()

    # The respawn wait, with no press: the world and the waves keep going, the ship stays.
    waiting: Run = run_of(waves, ship=spawn(), waiting=True)
    after_wait: Run = step_run(waiting, NO_KEY)
    assert_the_wave_clock_ran_once(after_wait)
    assert after_wait.waiting
    assert after_wait.ship == spawn()
    ticks_left: list[int] = []
    resting: list[bool] = []
    due: list[int] = []
    ids: list[str | None] = []
    run: Run = after_wait
    for _ in range(4):
        run = step_run(run, NO_KEY)
        assert run.waves is not None
        assert run.waiting
        ticks_left.append(run.waves.rest_ticks_left)
        resting.append(run.waves.resting)
        due.append(len(run.wave_spawns_due))
        ids.append(run.waves.current_wave_id)
    assert ticks_left == [2, 1, 0, 0]
    assert resting == [True, True, False, False]
    assert due == [0, 0, 0, 0]
    assert ids == [None, None, "a", "a"]

    # The press that ends the wait: the ship thrusts and the waves step as usual.
    pressed: Run = step_run(waiting, UP)
    assert_the_wave_clock_ran_once(pressed)
    assert not pressed.waiting

    # Protected ticks.
    protected: Run = run_of(waves, invuln_ticks_left=INVULN_TICKS)
    after_protected: Run = step_run(protected, NO_KEY)
    assert_the_wave_clock_ran_once(after_protected)
    assert after_protected.invuln_ticks_left == INVULN_TICKS - 1
    assert after_protected.lives == LIVES_START

    # A fall tick that costs a life, and a fall tick while protected.
    fall: Run = step_run(run_of(waves, ship=falling_ship()), NO_KEY)
    assert_the_wave_clock_ran_once(fall)
    assert fall.lives == LIVES_START - 1
    assert fall.waiting
    protected_fall: Run = step_run(
        run_of(waves, ship=falling_ship(), invuln_ticks_left=INVULN_TICKS), NO_KEY
    )
    assert_the_wave_clock_ran_once(protected_fall)
    assert protected_fall.lives == LIVES_START
    assert not protected_fall.waiting

    # The tick lives reach 0 by a fall, and by a hit.
    by_fall: Run = step_run(run_of(waves, ship=falling_ship(), lives=1), NO_KEY)
    assert by_fall.game_over
    assert by_fall.lives == 0
    assert_the_wave_clock_ran_once(by_fall)
    hit_run: Run = run_of(waves, lives=1, drifters=(rock(HOME_X, HOME_Y),))
    by_hit: Run = step_run(hit_run, NO_KEY)
    assert by_hit.game_over
    assert by_hit.lives == 0
    assert by_hit.ship != falling_ship()
    assert_the_wave_clock_ran_once(by_hit)

    # A plain playing tick, to compare: the same.
    assert_the_wave_clock_ran_once(step_run(run_of(waves), NO_KEY))


def test_the_world_moves_at_the_speed_of_the_level_going_into_the_tick() -> None:
    run: Run = add_drifters(
        start_run(start_waves(level_up_book(), SEED)),
        [Placement(DrifterType.COIN, 600.0, 100.0, variant="common")],
        TUNING,
    )
    coin: Drifter = run.drifters[0]
    assert isinstance(coin, Coin)
    exact: Fraction = Fraction(0)
    coin_y: float = coin.y
    for tick in range(1, 71):
        level_in: int = run.level
        before: Scroll = run.scroll
        run = step_run(hold(run), NO_KEY)
        assert level_in == (1 if tick <= LEVEL_UP_TICK else 2), tick
        assert run.level == (1 if tick < LEVEL_UP_TICK else 2), tick
        step: Fraction = SCROLL_SPEED_1 * SCROLL_MULT[level_in - 1] if tick > 30 else Fraction(0)
        exact += step
        moved: float = run.scroll.distance_px - before.distance_px
        assert moved == pytest.approx(float(step), abs=1e-9), tick
        assert run.scroll.distance_px == pytest.approx(float(exact), abs=1e-9), tick
        # Step 3 moved the parked coin by the same distance step 5 moved the world.
        new_y: float = run.drifters[0].y
        assert new_y - coin_y == pytest.approx(moved, abs=1e-9), tick
        coin_y = new_y
    # The level-up tick moved 1.1 px, the next 1.21 px.
    assert run.scroll.scrolled_ticks == 40
    assert run.scroll.raised_level_ticks[0] == 70 - LEVEL_UP_TICK
    assert run.scroll.raised_level_ticks[1:] == (0,) * (LEVEL_COUNT - 2)
    assert run.scroll.distance_px == pytest.approx(22.0 + 20 * 1.21, abs=1e-9)
    assert run.scroll.meters == 4  # 46.2 px

    # A run whose waves are at any level moves at that level's speed, on its first moving tick.
    for level in range(1, LEVEL_COUNT + 1):
        waves: WaveRun = replace(start_waves(steady_book(), SEED), level=level)
        entered: Run = run_of(waves)
        stepped: Run = step_run(entered, NO_KEY)
        moved_px: float = stepped.scroll.distance_px - entered.scroll.distance_px
        assert moved_px == pytest.approx(float(SCROLL_SPEED_1 * SCROLL_MULT[level - 1]), abs=1e-9)
        assert stepped.level == level


def test_drifters_added_after_a_level_up_tick_are_born_at_the_new_level() -> None:
    run: Run = fly(start_run(start_waves(level_up_book(), SEED)), LEVEL_UP_TICK - 1)
    assert run.level == 1
    assert run.wave_spawns_due == ()
    old: Run = add_drifters(run, [Placement(DrifterType.METEORITE, 100.0, -20.0)], TUNING)
    assert old.drifters[0].speed == pytest.approx(LEVEL_1_SPEED * HAZARD_SPEED_MULT[0])

    risen: Run = step_run(hold(old), NO_KEY)
    assert risen.level == 2
    assert [placement.x for placement in risen.wave_spawns_due] == [200.0]
    added: Run = add_drifters(
        risen,
        [
            *risen.wave_spawns_due,
            Placement(DrifterType.METEORITE, 300.0, -20.0, as_level=1),
            Placement(DrifterType.METEORITE, 400.0, -20.0, as_level=5),
        ],
        TUNING,
    )
    speeds: list[float] = [drifter.speed for drifter in added.drifters]
    assert speeds == pytest.approx(
        [
            LEVEL_1_SPEED * HAZARD_SPEED_MULT[0],
            LEVEL_1_SPEED * HAZARD_SPEED_MULT[1],
            LEVEL_1_SPEED * HAZARD_SPEED_MULT[0],
            LEVEL_1_SPEED * HAZARD_SPEED_MULT[4],
        ]
    )
    assert [drifter.uid for drifter in added.drifters] == [1, 2, 3, 4]

    # The drifters already on the field keep their speed as the run goes on at Level 2.
    later: Run = added
    for _ in range(3):
        later = step_run(hold(later), NO_KEY)
        assert later.level == 2
        assert [drifter.speed for drifter in later.drifters] == speeds
    again: Run = add_drifters(later, [Placement(DrifterType.METEORITE, 500.0, -20.0)], TUNING)
    assert again.drifters[4].speed == pytest.approx(LEVEL_1_SPEED * HAZARD_SPEED_MULT[1])
    assert [drifter.speed for drifter in again.drifters[:4]] == speeds


def test_game_over_freezes_the_waves_and_the_world() -> None:
    run: Run = fly(start_run(start_waves(picks_book(), SEED)), 45)
    assert run.waves is not None
    assert run.waves.wave_id != WAVE_ZERO

    over: Run = die(run, LEFT)
    assert over.waves is not None
    assert not over.retry_armed
    assert over.waves.wave_id == run.waves.wave_id
    assert over.scroll.ticks == run.scroll.ticks + 1

    # Held arrows, a changed arrow, a release (it arms the retry), more release ticks: nothing
    # moves, and the wave clock never runs.
    frozen: Run = over
    for thrust in (LEFT, UP, UP, NO_KEY, NO_KEY, NO_KEY):
        frozen = step_run(frozen, thrust)
        assert frozen.game_over
        assert frozen.waves == over.waves
        assert frozen.wave_spawns_due == over.wave_spawns_due
        assert frozen.level == over.level
        assert frozen.scroll == over.scroll
        assert frozen.ship == over.ship
    assert frozen.retry_armed

    # A game over deep in the run, with a rest running: the countdown holds too.
    last_life: Run = run_of(waves_ending_on_the_next_tick(), lives=1, ship=falling_ship())
    resting: Run = step_run(last_life, NO_KEY)
    assert resting.game_over
    assert resting.waves is not None
    assert resting.waves.rest_ticks_left == 3
    for _ in range(5):
        resting = step_run(resting, NO_KEY)
        assert resting.waves is not None
        assert resting.waves.rest_ticks_left == 3
        assert resting.waves.resting


def test_a_retry_starts_wave_0_at_level_1_with_a_new_seed() -> None:
    book: WaveBook = picks_book()
    first: Run = start_run(start_waves(book, SEED))
    run, ids = walk_ids(first, 95)
    assert ids == expected_picks(SEED, 6)

    over: Run = die(run)
    assert over.retry_armed
    retry: Run = step_run(over, UP)

    second_seed: int = next_seed(SEED)
    assert second_seed != SEED
    assert retry.waves is not None
    assert retry.waves.book is book
    assert retry.waves.wave_id == WAVE_ZERO
    assert retry.waves.current_wave_id == WAVE_ZERO
    assert retry.level == 1
    assert retry.waves.next_slot == 0
    assert retry.waves.start_px == 0.0
    assert retry.waves.spawned == 0
    assert not retry.waves.resting
    assert retry.waves.rest_ticks_left == 0
    assert retry.waves.run_seed == second_seed
    assert retry.waves.pick_seed == second_seed
    assert retry.wave_spawns_due == ()
    assert retry.scroll == start_run().scroll
    assert retry.lives == LIVES_START
    assert retry.drifters == ()
    assert retry.score == 0
    assert not retry.game_over

    # The new run's picks come from the new seed, and are not the first run's picks.
    _, new_ids = walk_ids(retry, 95)
    assert new_ids == expected_picks(second_seed, 6)
    assert new_ids != ids

    # Every retry draws again from the seed of the run before it.
    third: Run = step_run(die(fly(retry, 5)), UP)
    assert third.waves is not None
    assert third.waves.run_seed == next_seed(second_seed)
    assert third.waves.pick_seed == next_seed(second_seed)
    assert third.waves.run_seed not in (SEED, second_seed)


@pytest.mark.determinism
def test_the_same_first_seed_gives_the_same_run_of_waves_and_retries() -> None:
    def script(seed: int) -> list[Run]:
        run: Run = start_run(start_waves(picks_book(), seed))
        states: list[Run] = []
        for _ in range(95):
            run = step_run(hold(run), NO_KEY)
            states.append(run)
        run = die(run)
        states.append(run)
        run = step_run(run, UP)
        states.append(run)
        for _ in range(95):
            run = step_run(hold(run), NO_KEY)
            states.append(run)
        return states

    assert script(SEED) == script(SEED)
    assert script(SEED) != script(SEED + 1)


def test_a_retry_logs_new_run_then_the_waves_start_and_a_tick_logs_the_waves_last(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger=RUN_LOGGER)
    caplog.set_level(logging.DEBUG, logger=WAVES_LOGGER)

    # The retry tick.
    over: Run = die(fly(start_run(start_waves(level_up_book(), SEED)), 3))
    caplog.clear()
    step_run(over, UP)
    assert messages(caplog, RUN_LOGGER, WAVES_LOGGER) == [
        (RUN_LOGGER, "new run"),
        (WAVES_LOGGER, "wave start id=w0 level=1 random=False"),
    ]

    # The level-up tick on a fall with a drop: the run's lines, then the waves' lines.
    before: Run = fly(start_run(start_waves(level_up_book(), SEED)), LEVEL_UP_TICK - 1)
    gone: Meteorite = replace(rock(100.0, SCREEN_H + 100.0), has_entered=True)
    fall_tick: Run = replace(before, ship=falling_ship(), drifters=(gone,), next_uid=2)
    caplog.clear()
    out: Run = step_run(fall_tick, NO_KEY)
    assert out.level == 2
    seen: list[tuple[str, str]] = messages(caplog, RUN_LOGGER, WAVES_LOGGER)
    assert [name for name, _ in seen] == [RUN_LOGGER] * 3 + [WAVES_LOGGER] * 3
    lines: list[str] = [line for _, line in seen]
    assert lines[0] == "life lost lives=2"
    assert lines[1].startswith("respawn from ")
    assert lines[2].startswith("drifter gone id=1 type=meteorite")
    assert lines[3:] == [
        "wave end id=a",
        "level up level=2",
        "wave start id=long level=2 random=False",
    ]

    # The same tick on the last life: the game over line, then the waves' lines.
    caplog.clear()
    ended: Run = step_run(replace(fall_tick, lives=1), NO_KEY)
    assert ended.game_over
    seen = messages(caplog, RUN_LOGGER, WAVES_LOGGER)
    assert [name for name, _ in seen] == [RUN_LOGGER] * 3 + [WAVES_LOGGER] * 3
    lines = [line for _, line in seen]
    assert lines[0] == "life lost lives=0"
    assert lines[1] == "game over meters=2"
    assert lines[2].startswith("drifter gone id=1 type=meteorite")
    assert lines[3:] == [
        "wave end id=a",
        "level up level=2",
        "wave start id=long level=2 random=False",
    ]
