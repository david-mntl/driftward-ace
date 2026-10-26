"""The last life inside the run: the burst, the frozen score, the world that runs on, game over.

Contract: docs/contracts/systems/run.md, Diagram (the state diagram, the score table, the
last-life table), Interface (DRA-125: `core/last_life.py`, `core/run.py`), Rules (steps 6.3 and
7.5, The last life, A last-life tick, A game-over tick, `next_run`, Burst, `hold_arrows`,
`add_drifters`, Score, Other rules, Logging). Task:
docs/contracts/DRA-125/tasks/DRA-125-09-qa-engineer.md. One test per behavior it lists.
The last-life values are written here, never read from game/tuning/: the delay from
02-game-flow.md, last_life_delay (guess), the burst's count, speed and size from scope report
DRA-125, Values needed (Burst), which the GDD doesn't hold yet (LD-08). The drifter tuning is
built here from the GDD values below, and no expected number is imported from the code under test.
"""

import dataclasses
import logging
import math
import random
from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction
from itertools import product

import pytest

from core.collision import Box, Circle
from core.drifters.base import Drifter, DrifterType, GrazeState, Phase
from core.drifters.coin import Coin, CoinTypeExtra, CoinVariantExtra
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.graze import GrazeRing, GrazeRules
from core.last_life import (
    Burst,
    LastLifeRules,
    start_burst,
    step_burst,
)
from core.popup import PointsPopup
from core.run import Run, add_drifters, hold_arrows, next_run, start_run, step_run
from core.scroll import Scroll, start_scroll
from core.ship import Ship, Thrust, spawn
from core.waves import (
    LevelPlaylist,
    Wave,
    WaveBook,
    WaveKind,
    WavePlacement,
    WaveRun,
    start_waves,
    step_waves,
)

LAST_LIFE_DELAY: int = 120
"""Ticks. Source: 02-game-flow.md, Values, last_life_delay (guess)."""

BURST_COUNT: int = 12
BURST_SPEED: float = 1.0
BURST_SIZE: int = 3
"""Squares, px per tick, px. Source: scope report DRA-125, Values needed, Burst (12 evenly
spread directions, 1 px per tick; the size is its stand-in until LD-08)."""

RULES: LastLifeRules = LastLifeRules(
    delay_ticks=LAST_LIFE_DELAY,
    burst_particle_count=BURST_COUNT,
    burst_particle_speed=BURST_SPEED,
    burst_particle_size=BURST_SIZE,
)
"""The values above as the run takes them."""

LIVES_START: int = 3
INVULN_TICKS: int = 30
"""Source: 05-lives-and-damage.md, Values, lives_start, invuln_ticks (locked)."""

BLINK_SWAP_TICKS: int = 6
"""Ticks. Source: scope report DRA-23, blink (one swap every 0.1 s, approved in chat); systems/
run.md, Interface."""

SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, Values, screen_h (guess)."""

SHIP_H: int = 32
"""px. Source: 04-ship.md, Values, ship_h (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

HOME_X: float = 320.0
HOME_Y: float = 240.0
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

AT_FLOOR_Y: float = SCREEN_H + SHIP_H / 2 - FALL_CAP
"""A ship at fall_cap here moves exactly FALL_CAP next tick and its top edge lands on the floor."""

SCROLL_SPEED: Fraction = Fraction("1.1")
"""px/tick at Level 1. Source: 03-world-and-camera.md, scroll_base (guess)."""

PX_PER_METER: int = 10
"""Source: 06-scoring.md, points_per_meter (locked, 1 point a meter), meters_rounding (down)."""

SCROLL_START_DELAY: int = 30
"""Ticks of a still world. Source: 03-world-and-camera.md, scroll_start_delay (guess)."""

COIN_POINTS: int = 50
"""A common coin. Source: 06-scoring.md, coin_points (locked)."""

GRAZE_POINTS: int = 25
"""Source: 06-scoring.md, graze_points (locked)."""

COIN_POPUP_TICKS: int = 60
COIN_POPUP_RISE: float = 0.5
"""Source: drifters/04-coin.md, popup (60 ticks, guess); scope report DRA-62 (0.5 px a tick)."""

REHIT_COOLDOWN: int = 180
"""Ticks. Source: 05-lives-and-damage.md, rehit_cooldown (guess)."""

MEDIUM_SIZE: float = 28.0
MEDIUM_RADIUS: float = 14.0
"""px. Source: drifters/01-meteorite.md, variants (guess)."""

WARNING_TICKS: int = 60
"""Source: 07-drifters.md, entry_warning_ticks (guess)."""

LEVEL_COUNT: int = 8
"""Source: 08-difficulty.md, rule 1."""

SEED: int = 20261019
"""A first seed for the runs with waves."""

SEED_BITS: int = 64
"""Source: systems/waves.md, Interface (`getrandbits(64)`)."""

WAVE_ZERO: str = "w0"
"""Id of Wave 0 in the book below."""

RUN_LOGGER: str = "core.run"
"""Source: systems/run.md, Logging."""

NO_KEY = Thrust()
UP = Thrust(up=True)
ALL_KEYS: tuple[Thrust, ...] = tuple(
    Thrust(up=u, down=d, left=lf, right=r) for u, d, lf, r in product((False, True), repeat=4)
)
"""Every combination of the four arrows."""

HOME_SHIP: Ship = Ship(x=HOME_X, y=HOME_Y, vx=0.0, vy=0.0)
SCROLLING: Scroll = Scroll(ticks=100, scrolled_ticks=70)
"""A scroll already moving: 70 moving ticks, and the next step moves the world 1.1 px."""


def meters_at(scrolled_ticks: int) -> int:
    """Whole meters after `scrolled_ticks` moving ticks at Level 1, worked out in whole numbers."""
    return math.floor(scrolled_ticks * SCROLL_SPEED / PX_PER_METER)


def make_tuning() -> DrifterTuning:
    """Build the meteorite and coin tuning from the GDD values above.

    The coin's records are the way `app.tuning` builds them: every variant the crystal's size and
    one box, speed_ratio 0.0 and no entry warning.
    """
    type_extra = CoinTypeExtra(
        body_height=10,
        ring_width=22,
        ring_height=8,
        glint_size=2,
        glint_left=3,
        glint_top=3,
        popup_ticks=COIN_POPUP_TICKS,
        popup_rise_per_tick=COIN_POPUP_RISE,
    )
    coin_variants: dict[str, VariantTuning] = {
        name: VariantTuning(
            width=12,
            height=20,
            hitbox=(Box(0.0, 0.0, 12.0, 10.0),),
            extra=CoinVariantExtra(points=points, glint=name == "rare"),
        )
        for name, points in {"common": COIN_POINTS, "rare": 100}.items()
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
                variants={
                    "medium": VariantTuning(
                        width=MEDIUM_SIZE,
                        height=MEDIUM_SIZE,
                        hitbox=(Circle(0.0, 0.0, MEDIUM_RADIUS),),
                    )
                },
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=WARNING_TICKS,
            ),
        },
        switches=PlaytestSwitches(),
    )


TUNING: DrifterTuning = make_tuning()


def rock(
    x: float,
    y: float,
    *,
    speed: float = 0.0,
    phase: Phase = Phase.ACTIVE,
    has_entered: bool = False,
    rehit: int = 0,
    graze: GrazeState = GrazeState.OUTSIDE,
) -> Meteorite:
    """A medium meteorite put where it is told, ACTIVE with speed 0 unless said otherwise."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, x, y), 1, TUNING)
    assert isinstance(spawned, Meteorite)
    if phase is Phase.WARNING:
        return spawned
    return replace(
        spawned,
        phase=phase,
        ticks_in_phase=0,
        speed=speed,
        has_entered=has_entered,
        rehit_ticks_left=rehit,
        graze_state=graze,
    )


def coin(x: float, y: float) -> Coin:
    """A common coin, ACTIVE from birth."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.COIN, x, y), 1, TUNING)
    assert isinstance(spawned, Coin)
    return spawned


def wave(wave_id: str, length: float, *, triggers: Sequence[float] = (), x0: float = 0.0) -> Wave:
    """A fixed wave whose i-th placement is a meteorite with x = x0 + i at the i-th trigger."""
    return Wave(
        wave_id=wave_id,
        length_px=length,
        kind=WaveKind.FIXED,
        min_level=None,
        placements=tuple(
            WavePlacement(
                at_px=trigger,
                placement=Placement(DrifterType.METEORITE, x=x0 + index, y=-20.0),
            )
            for index, trigger in enumerate(triggers)
        ),
    )


def level_up_book() -> WaveBook:
    """Wave 0 and `a` are 11 px long, so at 1.1 px a tick each ends after 10 moving ticks.

    Level 1 plays `a` and then Level 2 starts. Wave `a` has one placement due on its last tick
    (trigger 11 px, x 200). Levels 2 to 8 play `long`. From tick 1 of a run (30 still ticks first),
    Wave 0 ends on tick 40 and `a` on tick 50: the level is 2 in the state after tick 50.
    """
    waves: list[Wave] = [
        wave(WAVE_ZERO, 11.0),
        wave("a", 11.0, triggers=[11.0], x0=200.0),
        wave("long", 10_000.0),
    ]
    playlists: tuple[LevelPlaylist, ...] = (
        LevelPlaylist(fixed=("a",)),
        *(LevelPlaylist(fixed=("long",)) for _ in range(2, LEVEL_COUNT + 1)),
    )
    return WaveBook(
        waves={item.wave_id: item for item in waves}, wave_zero_id=WAVE_ZERO, playlists=playlists
    )


BOOK: WaveBook = level_up_book()


def run_of(
    *drifters: Drifter,
    ship: Ship = HOME_SHIP,
    lives: int = LIVES_START,
    scroll: Scroll = SCROLLING,
    waiting: bool = False,
    invuln_ticks_left: int = 0,
    rules: LastLifeRules = RULES,
    popups: tuple[PointsPopup, ...] = (),
    rings: tuple[GrazeRing, ...] = (),
    waves: WaveRun | None = None,
    held: Thrust = NO_KEY,
    graze_rules: GrazeRules | None = None,
) -> Run:
    """A run on the given scroll with the drifters numbered from 1, in order."""
    base: Run = start_run(waves, GrazeRules() if graze_rules is None else graze_rules, rules)
    numbered: tuple[Drifter, ...] = tuple(replace(d, uid=i + 1) for i, d in enumerate(drifters))
    return replace(
        base,
        ship=ship,
        scroll=scroll,
        lives=lives,
        waiting=waiting,
        invuln_ticks_left=invuln_ticks_left,
        popups=popups,
        graze_rings=rings,
        drifters=numbered,
        next_uid=len(numbered) + 1,
        held=held,
    )


def falling_ship(vx: float = 0.0) -> Ship:
    """A ship whose next step with no key puts its top edge on the floor."""
    return Ship(x=200.0, y=AT_FLOOR_Y, vx=vx, vy=FALL_CAP)


def fall_run(*drifters: Drifter, lives: int = 1, **fields: object) -> Run:
    """A run whose ship falls past the floor on the next tick with no key."""
    return run_of(*drifters, ship=falling_ship(), lives=lives, **fields)  # type: ignore[arg-type]


def hit_run(*drifters: Drifter, lives: int = 1, **fields: object) -> Run:
    """A run whose ship rests at home with a still meteorite on it: the next tick is a hit."""
    return run_of(rock(HOME_X, HOME_Y), *drifters, lives=lives, **fields)  # type: ignore[arg-type]


def play(run: Run, ticks: int, thrust: Thrust = NO_KEY) -> list[Run]:
    """The run after the tick it was given, then after each of `ticks` more, all with `thrust`."""
    states: list[Run] = [step_run(run, thrust)]
    for _ in range(ticks):
        states.append(step_run(states[-1], thrust))
    return states


def over_run(run: Run) -> Run:
    """Step a run on its last life until game over, with no key."""
    while not run.game_over:
        run = step_run(run, NO_KEY)
    return run


def drifter_ids(run: Run) -> tuple[int, ...]:
    """The uids on the field, in order."""
    return tuple(d.uid for d in run.drifters)


def drifter_of(run: Run, uid: int) -> Drifter:
    """The drifter with `uid`."""
    found: list[Drifter] = [d for d in run.drifters if d.uid == uid]
    assert len(found) == 1, f"uid {uid} is on the field {len(found)} times"
    return found[0]


def lines_of(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Every line the run logged, in order."""
    return [r.getMessage() for r in caplog.records if r.name == RUN_LOGGER]


def all_lines(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Every line any core logger wrote, in order."""
    return [r.getMessage() for r in caplog.records]


def expected_visible(invuln_ticks_left: int) -> bool:
    """The blink as the contract's table sets it, worked out here."""
    if invuln_ticks_left == 0:
        return True
    return ((INVULN_TICKS - invuln_ticks_left) // BLINK_SWAP_TICKS) % 2 == 0


def test_losing_the_last_life_by_a_fall_starts_the_last_life_on_that_tick() -> None:
    before: Run = replace(fall_run(rock(100.0, 100.0)), ship=falling_ship(vx=2.0))

    run = step_run(before, NO_KEY)

    expected_score: int = meters_at(71)
    assert run.lives == 0
    assert not run.waiting
    assert not run.invulnerable
    assert not run.game_over
    assert run.last_life
    assert run.ship != spawn(), "the ship must not respawn on the last life"
    assert run.ship.y - SHIP_H / 2 >= SCREEN_H, "the ship stays where it fell"
    assert run.burst is not None
    assert run.burst.x == run.ship.x
    assert run.burst.x != before.ship.x, "the burst is at the ship's x after the tick's move"
    assert run.burst.y == SCREEN_H
    assert run.burst.age_ticks == 0
    assert run.burst.opacity == 1.0
    assert not run.burst.finished
    assert (
        run.burst.particle_count,
        run.burst.speed_per_tick,
        run.burst.particle_size,
        run.burst.lifetime_ticks,
    ) == (BURST_COUNT, BURST_SPEED, BURST_SIZE, LAST_LIFE_DELAY)
    assert run.final_score == expected_score
    assert run.score == expected_score
    assert run.scroll.meters == expected_score

    protected = step_run(replace(before, invuln_ticks_left=5), NO_KEY)
    assert protected.lives == 1, "a protected fall costs no life"
    assert protected.burst is None
    assert protected.final_score is None
    assert not protected.last_life


@pytest.mark.parametrize("how", ["playing", "waiting", "press"])
def test_losing_the_last_life_by_a_hit_puts_the_burst_at_the_ships_center(how: str) -> None:
    ship: Ship = Ship(x=250.0, y=300.0, vx=0.0, vy=0.0) if how == "playing" else HOME_SHIP
    target: Drifter = rock(ship.x, ship.y)
    before: Run = run_of(target, ship=ship, lives=1, waiting=how != "playing")
    thrust: Thrust = UP if how == "press" else NO_KEY

    run = step_run(before, thrust)

    assert run.last_life
    assert run.lives == 0
    assert not run.waiting
    assert not run.game_over
    assert run.burst is not None
    assert (run.burst.x, run.burst.y) == (run.ship.x, run.ship.y)
    assert run.burst.age_ticks == 0
    assert run.burst.y != SCREEN_H
    assert run.final_score == run.score == meters_at(71)
    if how == "waiting":
        assert run.ship == HOME_SHIP, "a ship standing in the wait is not stepped"
        assert (run.burst.x, run.burst.y) == (HOME_X, HOME_Y)
    else:
        assert run.ship != ship, "the ship moved on this tick and the burst follows it"

    protected = step_run(replace(before, invuln_ticks_left=3, waiting=False), NO_KEY)
    assert protected.lives == 1, "a hazard passes through a protected ship"
    assert protected.burst is None
    assert not protected.last_life


@pytest.mark.parametrize("how", ["fall", "hit"])
def test_a_coin_and_a_graze_paid_on_the_death_tick_are_in_the_final_score(how: str) -> None:
    exiting: Meteorite = rock(100.0, 100.0, graze=GrazeState.INSIDE)
    if how == "fall":
        ship: Ship = Ship(x=320.0, y=AT_FLOOR_Y, vx=0.0, vy=FALL_CAP)
        before = run_of(exiting, coin(320.0, 496.0), ship=ship, lives=1)
    else:
        before = run_of(
            exiting, coin(HOME_X, HOME_Y), rock(HOME_X, HOME_Y), ship=HOME_SHIP, lives=1
        )

    run = step_run(before, NO_KEY)

    assert run.last_life
    assert run.lives == 0
    assert run.coin_points == COIN_POINTS
    assert run.grazes == 1
    expected: int = meters_at(71) + COIN_POINTS + GRAZE_POINTS
    assert run.final_score == expected
    assert run.score == expected
    assert [p.points for p in run.popups] == [COIN_POINTS, GRAZE_POINTS]
    assert len(run.graze_rings) == 1
    assert run.drifters[0].graze_state is GrazeState.SPENT


def test_a_last_life_tick_moves_the_scroll_the_drifters_and_ages_popups_rings_and_cooldowns() -> (
    None
):
    popup = PointsPopup(x=50.0, start_y=300.0, points=77, lifetime_ticks=4, rise_per_tick=0.5)
    ring = GrazeRing(start_diameter=16.0, end_diameter=32.0, line_width=1, lifetime_ticks=4)
    before: Run = hit_run(
        coin(HOME_X, HOME_Y),  # uid 2: collected on the death tick
        rock(100.0, 100.0, speed=2.0, rehit=10),  # uid 3: falls 2 px a tick
        rock(500.0, 470.0, speed=5.0, has_entered=True),  # uid 4: leaves past the floor
        rock(500.0, 100.0, phase=Phase.WARNING),  # uid 5: warning, then active
        popups=(popup,),
        rings=(ring,),
    )
    assert drifter_ids(before) == (1, 2, 3, 4, 5)

    states: list[Run] = play(before, 70)

    assert states[0].last_life
    assert drifter_ids(states[0]) == (1, 3, 4, 5), "the collected coin is gone on tick L"
    for k, state in enumerate(states):
        assert state.scroll.ticks == 101 + k
        assert state.scroll.scrolled_ticks == 71 + k
        assert state.ship == states[0].ship
        assert drifter_of(state, 3).y == 100.0 + 2.0 * (k + 1)
        assert drifter_of(state, 3).rehit_ticks_left == max(0, 9 - k)
        assert drifter_of(state, 1).rehit_ticks_left == REHIT_COOLDOWN - k
        assert (4 in drifter_ids(state)) == (k < 4), f"the leaving rock, state {k}"
        warner: Drifter = drifter_of(state, 5)
        if k + 1 < WARNING_TICKS:
            assert (warner.phase, warner.ticks_in_phase) == (Phase.WARNING, k + 1)
        else:
            assert (warner.phase, warner.ticks_in_phase) == (Phase.ACTIVE, k + 1 - WARNING_TICKS)
        mine: list[PointsPopup] = [p for p in state.popups if p.points == 77]
        assert len(mine) == (1 if k + 1 < 4 else 0)
        for p in mine:
            assert p.age_ticks == k + 1
            assert p.y == 300.0 - 0.5 * (k + 1)
        assert [r.age_ticks for r in state.graze_rings] == ([k + 1] if k + 1 < 4 else [])
        coin_popups: list[PointsPopup] = [p for p in state.popups if p.points == COIN_POINTS]
        assert len(coin_popups) == (1 if k < COIN_POPUP_TICKS else 0)
        for p in coin_popups:  # the parked coin moved with the scroll, 1.1 px, before its pay
            assert p.age_ticks == k
            assert p.y == pytest.approx(HOME_Y + 1.1 - COIN_POPUP_RISE * k)
    assert states[-1].scroll.meters == meters_at(71 + 70)


def test_the_wave_clock_runs_and_the_scroll_starts_on_last_life_ticks() -> None:
    run: Run = fall_run(
        rock(500.0, 470.0, speed=5.0, has_entered=True),
        scroll=start_scroll(),
        waves=start_waves(BOOK, SEED),
    )
    states: list[Run] = play(run, LAST_LIFE_DELAY)
    assert states[0].last_life

    replay: WaveRun = start_waves(BOOK, SEED)
    for index, state in enumerate(states):
        tick: int = index + 1
        assert state.scroll.scrolled_ticks == max(0, tick - SCROLL_START_DELAY)
        replay = step_waves(replay, state.scroll.distance_px)
        assert state.waves == replay, f"the wave clock, tick {tick}"
        assert state.level == (2 if tick >= 50 else 1)
        due: tuple[Placement, ...] = state.wave_spawns_due
        if tick == 50:
            assert [p.x for p in due] == [200.0], "wave a's placement comes due on tick 50"
        else:
            assert due == (), f"nothing due on tick {tick}"
    assert states[-1].game_over
    assert states[48].scroll.distance_px - states[47].scroll.distance_px == pytest.approx(1.1)
    assert states[50].scroll.distance_px - states[49].scroll.distance_px == pytest.approx(1.21)


def test_no_collect_graze_fall_or_hit_happens_in_the_last_life_and_the_score_stays() -> None:
    last: Run = step_run(hit_run(), NO_KEY)
    assert last.last_life
    on_ship_hazard: Meteorite = rock(HOME_X, HOME_Y)
    on_ship_coin: Coin = coin(HOME_X, HOME_Y)
    leaving: Meteorite = rock(100.0, 100.0, graze=GrazeState.INSIDE)
    before: Run = replace(
        last,
        drifters=(
            *last.drifters,
            replace(on_ship_hazard, uid=10),
            replace(on_ship_coin, uid=11),
            replace(leaving, uid=12),
        ),
        next_uid=13,
    )

    states: list[Run] = play(before, 40)

    for k, state in enumerate(states):
        assert state.lives == 0
        assert state.ship == last.ship
        assert not state.waiting
        assert not state.invulnerable
        assert state.coin_points == last.coin_points
        assert state.grazes == last.grazes
        assert state.score == state.final_score == last.final_score
        assert drifter_of(state, 11).phase is Phase.ACTIVE, "the coin on the ship is not collected"
        hazard: Drifter = drifter_of(state, 10)
        assert hazard.rehit_ticks_left == 0, "a hazard on the ship starts no cooldown"
        assert hazard.graze_state is GrazeState.OUTSIDE
        assert drifter_of(state, 12).graze_state is GrazeState.INSIDE
        assert state.burst is not None
        assert (state.burst.x, state.burst.y) == (last.burst.x, last.burst.y)  # type: ignore[union-attr]
        assert state.burst.age_ticks == k + 1
        assert not state.ship_visible
        assert [p.points for p in state.popups if p.points == GRAZE_POINTS] == []
    assert states[-1].scroll.meters > last.scroll.meters, "the meters keep counting"
    assert states[-1].score == last.final_score

    fallen: Run = step_run(fall_run(), NO_KEY)
    assert fallen.last_life
    for k, state in enumerate(play(fallen, 10)):
        assert state.ship == fallen.ship, "a ship below the floor falls no more"
        assert state.lives == 0
        assert not state.waiting
        assert state.invuln_ticks_left == 0
        assert state.burst is not None
        assert fallen.burst is not None
        assert (state.burst.x, state.burst.y) == (fallen.burst.x, SCREEN_H)
        assert state.burst.age_ticks == k + 1
        assert state.final_score == fallen.final_score


def test_arrows_do_nothing_in_the_last_life() -> None:
    for before in (
        step_run(hit_run(rock(100.0, 100.0, speed=2.0)), NO_KEY),
        step_run(fall_run(), NO_KEY),
    ):
        assert before.last_life
        plain: Run = step_run(before, NO_KEY)
        for thrust in ALL_KEYS:
            moved: Run = step_run(before, thrust)
            assert moved == replace(plain, held=thrust), f"{thrust}"
            assert moved.ship == before.ship
            assert not moved.waiting
            assert moved.last_life
        keyed: list[Run] = []
        run: Run = before
        for thrust in (UP, UP, NO_KEY, Thrust(left=True), Thrust(up=True, right=True), NO_KEY):
            run = step_run(run, thrust)
            keyed.append(run)
        assert all(state.ship == before.ship for state in keyed)
        assert [s.burst.age_ticks for s in keyed if s.burst] == [1, 2, 3, 4, 5, 6]


def test_add_drifters_adds_during_the_last_life_and_nothing_at_game_over() -> None:
    placement: Placement = Placement(DrifterType.METEORITE, x=120.0, y=-20.0)
    last: Run = step_run(hit_run(), NO_KEY)
    assert last.last_life

    grown: Run = add_drifters(last, [placement], TUNING)

    assert len(grown.drifters) == len(last.drifters) + 1
    added: Drifter = grown.drifters[-1]
    assert added.uid == last.next_uid
    assert added.phase is Phase.WARNING
    assert added.ticks_in_phase == 0
    assert grown.next_uid == last.next_uid + 1
    assert replace(grown, drifters=last.drifters, next_uid=last.next_uid) == last
    after: Run = step_run(grown, NO_KEY)
    assert drifter_of(after, added.uid).ticks_in_phase == 1, "the new drifter plays on"

    waves_run: list[Run] = play(fall_run(scroll=start_scroll(), waves=start_waves(BOOK, SEED)), 49)
    on_50: Run = waves_run[49]
    assert on_50.last_life
    assert len(on_50.wave_spawns_due) == 1
    from_waves: Run = add_drifters(on_50, on_50.wave_spawns_due, TUNING)
    assert [d.x for d in from_waves.drifters] == [200.0]
    assert from_waves.drifters[0].phase is Phase.WARNING

    over: Run = over_run(last)
    assert over.game_over
    assert add_drifters(over, [placement], TUNING) == over
    assert add_drifters(over, [placement, placement], TUNING) == over


@pytest.mark.parametrize(
    "rules",
    [
        pytest.param(RULES, id="default"),
        pytest.param(LastLifeRules(delay_ticks=1), id="one tick"),
        pytest.param(LastLifeRules(delay_ticks=2), id="two ticks"),
        pytest.param(
            LastLifeRules(
                delay_ticks=7,
                burst_particle_count=5,
                burst_particle_speed=2.5,
                burst_particle_size=4,
            ),
            id="custom",
        ),
    ],
)
@pytest.mark.parametrize("how", ["fall", "hit"])
def test_game_over_comes_exactly_delay_ticks_after_the_death_tick(
    rules: LastLifeRules, how: str
) -> None:
    before: Run = fall_run(rules=rules) if how == "fall" else hit_run(rules=rules)
    delay: int = rules.delay_ticks

    states: list[Run] = play(before, delay + 2)

    for index, state in enumerate(states):
        assert state.burst is not None
        assert state.final_score == states[0].final_score
        if index < delay:
            assert state.last_life, f"state {index}"
            assert not state.game_over
            assert state.burst.age_ticks == index
            assert not state.burst.finished
            assert state.burst.opacity == pytest.approx(1 - index / delay)
            assert state.burst.opacity > 0.0
            assert state.burst.lifetime_ticks == delay
        else:
            assert state.game_over, f"state {index}"
            assert not state.last_life
            assert state.burst.age_ticks == delay
            assert state.burst.finished
            assert state.burst.opacity == 0.0
    shown: list[bool] = [
        s.last_life and s.burst is not None and not s.burst.finished and s.burst.opacity > 0.0
        for s in states
    ]
    assert shown.count(True) == delay, "the burst shows on delay_ticks states"
    assert shown[:delay] == [True] * delay
    first_over: int = next(i for i, s in enumerate(states) if s.game_over)
    assert first_over == delay, "game over is on tick L + delay_ticks"
    custom: Burst = states[0].burst  # type: ignore[assignment]
    assert (custom.particle_count, custom.speed_per_tick, custom.particle_size) == (
        rules.burst_particle_count,
        rules.burst_particle_speed,
        rules.burst_particle_size,
    )


def test_a_game_over_tick_changes_nothing_but_held() -> None:
    short: LastLifeRules = replace(RULES, delay_ticks=3)
    popup = PointsPopup(x=50.0, start_y=300.0, points=77, lifetime_ticks=100, rise_per_tick=0.5)
    ring = GrazeRing(start_diameter=16.0, end_diameter=32.0, line_width=1, lifetime_ticks=100)
    over: Run = over_run(
        hit_run(
            rock(100.0, 100.0, speed=2.0, rehit=50),
            rock(500.0, 100.0, phase=Phase.WARNING),
            rules=short,
            popups=(popup,),
            rings=(ring,),
            waves=start_waves(BOOK, SEED),
            scroll=start_scroll(),
        )
    )
    assert over.game_over
    assert over.lives == 0
    assert over.burst is not None
    assert not hasattr(over, "retry_armed"), "the arrow retry is gone"

    for held, thrust in product(ALL_KEYS, ALL_KEYS):
        after: Run = step_run(replace(over, held=held), thrust)
        assert after == replace(over, held=thrust), f"held {held}, thrust {thrust}"
        assert after.game_over
        assert after.burst is over.burst
        assert after.final_score == over.final_score

    run: Run = over
    for thrust in (UP, UP, NO_KEY, Thrust(left=True), ALL_KEYS[-1], NO_KEY, UP, NO_KEY):
        run = step_run(run, thrust)
        assert run == replace(over, held=thrust)
    assert not run.last_life
    assert run.drifters == over.drifters
    assert run.waves == over.waves
    assert run.scroll == over.scroll


@pytest.mark.parametrize(
    "rules",
    [
        pytest.param(RULES, id="default"),
        pytest.param(
            LastLifeRules(
                delay_ticks=9,
                burst_particle_count=5,
                burst_particle_speed=2.5,
                burst_particle_size=4,
            ),
            id="custom",
        ),
    ],
)
def test_the_burst_starts_on_the_origin_flies_evenly_and_fades_evenly(
    rules: LastLifeRules, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger="core.last_life")
    origin: tuple[float, float] = (123.5, 301.25)
    burst: Burst = start_burst(rules, *origin)

    assert burst.age_ticks == 0
    assert burst.particle_centers == (origin,) * rules.burst_particle_count
    assert burst.opacity == 1.0
    assert not burst.finished
    assert (burst.x, burst.y) == origin

    states: list[Burst] = [burst]
    for _ in range(rules.delay_ticks + 3):
        states.append(step_burst(states[-1]))
    count: int = rules.burst_particle_count
    for age, state in enumerate(states):
        assert (state.x, state.y) == origin, "the origin never moves"
        assert state.age_ticks == age
        reach: float = age * rules.burst_particle_speed
        centers = state.particle_centers
        assert len(centers) == count
        for k, (cx, cy) in enumerate(centers):
            angle: float = 2 * math.pi * k / count
            assert cx == pytest.approx(origin[0] + reach * math.cos(angle), abs=1e-9)
            assert cy == pytest.approx(origin[1] + reach * math.sin(angle), abs=1e-9)
        assert state.opacity == pytest.approx(max(0.0, 1 - age / rules.delay_ticks))
        assert state.finished == (age >= rules.delay_ticks)
    steps: list[float] = [
        states[i].opacity - states[i + 1].opacity for i in range(rules.delay_ticks)
    ]
    assert steps == pytest.approx([1 / rules.delay_ticks] * rules.delay_ticks), "an even fade"
    assert states[rules.delay_ticks].opacity == 0.0
    assert states[-1].opacity == 0.0, "never below 0"
    assert all(s.opacity > 0.0 for s in states[: rules.delay_ticks])

    # Square 0 flies right and, with four squares, square 1 flies down (+y), 2 left, 3 up.
    four: Burst = replace(start_burst(replace(rules, burst_particle_count=4), 100.0, 100.0))
    quarter: Burst = step_burst(four)
    speed: float = rules.burst_particle_speed
    expected: list[tuple[float, float]] = [
        (100.0 + speed, 100.0),
        (100.0, 100.0 + speed),
        (100.0 - speed, 100.0),
        (100.0, 100.0 - speed),
    ]
    for got, want in zip(quarter.particle_centers, expected, strict=True):
        assert got == pytest.approx(want, abs=1e-9)

    # Pure: nothing mutates, the same input gives the same output, nothing is logged.
    again: Burst = start_burst(rules, *origin)
    assert step_burst(again) == step_burst(again)
    assert again.age_ticks == 0
    assert again == burst
    assert again.particle_centers == again.particle_centers
    assert step_burst(again) == replace(again, age_ticks=1)
    assert [r for r in caplog.records if r.name == "core.last_life"] == []


def test_ship_visible_is_false_from_the_death_tick_on_and_as_before_until_then() -> None:
    cooldown_rock: Meteorite = replace(rock(HOME_X, HOME_Y), rehit_cooldown_ticks=40)
    run: Run = run_of(cooldown_rock, lives=2)
    seen: list[tuple[int, bool, int]] = []
    for tick in range(1, 50):
        run = step_run(replace(run, ship=HOME_SHIP), NO_KEY)
        seen.append((tick, run.ship_visible, run.invuln_ticks_left))
        if run.burst is not None:
            break

    assert run.last_life, "the second hit, on tick 42, is the last life"
    assert seen[-1][0] == 42
    assert seen[0][2] == INVULN_TICKS
    for tick, visible, left in seen[:-1]:
        assert visible == expected_visible(left), f"tick {tick}, invuln_ticks_left {left}"
    assert any(not visible for _, visible, _ in seen[:-1]), "the blink hid the ship before it burst"
    assert seen[-1][1] is False
    for state in play(run, LAST_LIFE_DELAY + 3):
        assert not state.ship_visible

    by_fall: Run = step_run(fall_run(), NO_KEY)
    assert not by_fall.ship_visible
    assert start_run().ship_visible
    assert replace(start_run(), invuln_ticks_left=24).ship_visible is expected_visible(24)


def test_next_run_gives_a_fresh_run_like_start_run_with_the_same_values() -> None:
    graze: GrazeRules = GrazeRules(points=7, popup_ticks=5, ring_ticks=4)
    custom: LastLifeRules = LastLifeRules(
        delay_ticks=4, burst_particle_count=3, burst_particle_speed=0.5, burst_particle_size=2
    )
    popup = PointsPopup(x=50.0, start_y=300.0, points=77, lifetime_ticks=100, rise_per_tick=0.5)
    ring = GrazeRing(start_diameter=16.0, end_diameter=32.0, line_width=1, lifetime_ticks=100)

    def finished(waves: WaveRun | None) -> Run:
        return over_run(
            hit_run(
                rock(100.0, 100.0, speed=2.0),
                coin(HOME_X, HOME_Y),
                rules=custom,
                graze_rules=graze,
                popups=(popup,),
                rings=(ring,),
                waves=waves,
                scroll=start_scroll() if waves is not None else SCROLLING,
                held=UP,
            )
        )

    def assert_fresh(fresh: Run) -> None:
        assert fresh.score == 0
        assert fresh.final_score is None
        assert fresh.burst is None
        assert fresh.drifters == ()
        assert fresh.next_uid == 1
        assert fresh.lives == LIVES_START
        assert fresh.coin_points == 0
        assert fresh.grazes == 0
        assert fresh.popups == ()
        assert fresh.graze_rings == ()
        assert fresh.ship == spawn()
        assert fresh.scroll == start_scroll()
        assert fresh.held == NO_KEY
        assert not fresh.waiting
        assert not fresh.invulnerable
        assert not fresh.game_over
        assert not fresh.last_life
        assert fresh.ship_visible
        assert fresh.graze_rules == graze
        assert fresh.last_life_rules == custom

    no_waves: Run = finished(None)
    assert no_waves.game_over
    assert no_waves.score > 0
    fresh_none: Run = next_run(no_waves)
    assert_fresh(fresh_none)
    assert fresh_none.waves is None
    assert fresh_none == start_run(None, graze, custom)
    assert fresh_none.level == 1

    with_waves: Run = finished(start_waves(BOOK, SEED))
    assert with_waves.waves is not None
    assert with_waves.score > 0
    second: Run = next_run(with_waves)
    assert_fresh(second)
    assert second.waves is not None
    assert second.level == 1
    assert second.waves.level == 1
    assert second.waves.current_wave_id == WAVE_ZERO
    assert second.waves.run_seed == random.Random(SEED).getrandbits(SEED_BITS)
    assert second.waves.pick_seed == second.waves.run_seed
    assert second.waves.run_seed != SEED
    assert second.waves.spawns_due == ()
    assert second.waves.book is BOOK
    assert second == start_run(second.waves, graze, custom)
    third: Run = next_run(second)
    assert third.waves is not None
    assert third.waves.run_seed == random.Random(second.waves.run_seed).getrandbits(SEED_BITS)

    for any_state in (with_waves, step_run(finished(None), NO_KEY), step_run(fall_run(), NO_KEY)):
        again: Run = next_run(any_state)
        assert not again.game_over
        assert again.burst is None
        assert again.final_score is None
        assert again.lives == LIVES_START
        assert again.score == 0
    assert with_waves.game_over, "the old run is left as it was"


def test_hold_arrows_changes_only_held_and_a_held_arrow_is_not_a_press_after_it() -> None:
    fell: Run = step_run(fall_run(lives=2), NO_KEY)
    assert fell.waiting
    assert fell.held == NO_KEY

    paused: Run = hold_arrows(fell, UP)
    for field in dataclasses.fields(Run):
        if field.name != "held":
            assert getattr(paused, field.name) == getattr(fell, field.name), field.name
    assert paused.held == UP
    assert fell.held == NO_KEY, "the input run is not changed"

    assert step_run(fell, UP).waiting is False, "control: a fresh press ends the wait"
    assert step_run(paused, UP).waiting is True, "an arrow held into the tick is no press"
    assert step_run(paused, UP).ship == fell.ship
    assert step_run(paused, Thrust(up=True, left=True)).waiting is False, "a fresh press does"
    assert step_run(paused, NO_KEY).waiting is True
    assert step_run(step_run(paused, NO_KEY), UP).waiting is False, "released, then pressed"

    pressed_then_released: Run = hold_arrows(replace(fell, held=UP), NO_KEY)
    assert pressed_then_released.held == NO_KEY
    assert step_run(pressed_then_released, UP).waiting is False

    for any_state in (
        step_run(hit_run(), NO_KEY),
        over_run(hit_run(rules=replace(RULES, delay_ticks=2))),
    ):
        held: Run = hold_arrows(any_state, Thrust(down=True))
        assert held == replace(any_state, held=Thrust(down=True))
        assert held.drifters == any_state.drifters


def test_hold_arrows_logs_nothing(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="core")
    run: Run = start_run()
    caplog.clear()

    hold_arrows(run, UP)

    assert all_lines(caplog) == []


def test_start_run_with_fewer_arguments_builds_the_run_it_built_before() -> None:
    graze: GrazeRules = GrazeRules(points=3)
    waves: WaveRun = start_waves(BOOK, SEED)
    default_rules: LastLifeRules = LastLifeRules(
        delay_ticks=LAST_LIFE_DELAY,
        burst_particle_count=BURST_COUNT,
        burst_particle_speed=BURST_SPEED,
        burst_particle_size=BURST_SIZE,
    )

    plain: Run = start_run()
    with_waves: Run = start_run(waves)
    with_graze: Run = start_run(waves, graze)
    with_all: Run = start_run(waves, graze, RULES)

    assert plain == Run(ship=spawn(), scroll=start_scroll())
    assert plain.waves is None
    assert plain.graze_rules == GrazeRules()
    assert with_waves == replace(plain, waves=waves)
    assert with_graze == replace(plain, waves=waves, graze_rules=graze)
    assert with_all == with_graze
    for run in (plain, with_waves, with_graze, with_all):
        assert run.last_life_rules == default_rules, "the default last-life values"
        assert run.burst is None
        assert run.final_score is None
        assert not run.last_life
        assert not run.game_over
        assert run.lives == LIVES_START
        assert run.score == 0
        assert run.drifters == ()
        assert run.next_uid == 1
        assert run.grazes == 0
        assert run.popups == ()
        assert run.graze_rings == ()
    assert start_run(graze_rules=graze).graze_rules == graze
    assert start_run(last_life_rules=default_rules) == plain
    custom: LastLifeRules = LastLifeRules(delay_ticks=9)
    assert start_run(last_life_rules=custom).last_life_rules == custom


def test_the_last_life_logs_last_life_after_life_lost_and_game_over_once(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="core")
    before: Run = hit_run(coin(HOME_X, HOME_Y), rock(100.0, 100.0, graze=GrazeState.INSIDE))

    caplog.clear()
    last: Run = step_run(before, NO_KEY)
    death: list[str] = lines_of(caplog)

    score: int = meters_at(71) + COIN_POINTS + GRAZE_POINTS
    assert last.final_score == score
    assert death == [
        "drifter touch id=2 type=coin effect=collect",
        "drifter graze id=3 type=meteorite",
        "drifter touch id=1 type=meteorite effect=hit",
        "life lost lives=0",
        f"last life score={score}",
        "drifter gone id=2 type=coin x=320.00 y=241.10",
    ]
    last_life_records = [r for r in caplog.records if r.getMessage().startswith("last life")]
    assert len(last_life_records) == 1
    assert last_life_records[0].levelno == logging.INFO
    assert not any(line.startswith("respawn from") for line in death)

    caplog.clear()
    step_run(fall_run(), NO_KEY)
    assert lines_of(caplog) == ["life lost lives=0", f"last life score={meters_at(71)}"]
    assert [r.levelno for r in caplog.records] == [logging.DEBUG, logging.INFO]

    caplog.clear()
    states: list[Run] = []
    run: Run = fall_run(
        rock(500.0, 470.0, speed=5.0, has_entered=True),
        rock(500.0, 100.0, phase=Phase.WARNING),
        scroll=start_scroll(),
        waves=start_waves(BOOK, SEED),
    )
    per_tick: list[list[str]] = []
    for _ in range(LAST_LIFE_DELAY + 3):
        mark: int = len(caplog.records)
        run = step_run(run, NO_KEY)
        states.append(run)
        per_tick.append([r.getMessage() for r in caplog.records[mark:]])

    assert per_tick[0] == ["life lost lives=0", "last life score=0"]
    allowed: tuple[str, ...] = (
        "drifter active",
        "drifter gone",
        "scroll start",
        "wave end",
        "level up",
        "rest start",
        "wave start",
    )
    for tick, lines in enumerate(per_tick[1:LAST_LIFE_DELAY], start=2):
        for line in lines:
            assert line.startswith(allowed), f"tick {tick}: {line!r}"
    assert per_tick[4][0].startswith("drifter gone id=1 type=meteorite"), "the rock leaves, tick 5"
    assert per_tick[30] == ["scroll start tick=31"]
    assert per_tick[39] == ["wave end id=w0", "wave start id=a level=1 random=False"]
    assert per_tick[49][:2] == ["wave end id=a", "level up level=2"]
    assert any(line.startswith("drifter active id=2 type=meteorite") for line in per_tick[59])
    assert per_tick[LAST_LIFE_DELAY][-1] == "game over score=0"
    game_over_records = [r for r in caplog.records if r.getMessage().startswith("game over")]
    assert len(game_over_records) == 1, "game over logs once"
    assert game_over_records[0].levelno == logging.INFO
    assert states[LAST_LIFE_DELAY].game_over
    assert per_tick[LAST_LIFE_DELAY + 1] == [], "a game-over tick logs nothing"
    assert per_tick[LAST_LIFE_DELAY + 2] == []

    # The game-over line carries the final score, a coin and a graze included.
    caplog.clear()
    over: Run = over_run(step_run(before, NO_KEY))
    assert over.final_score == score
    assert f"game over score={score}" in lines_of(caplog)


def test_next_run_logs_new_run_then_the_waves_start(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="core")
    with_waves: Run = over_run(
        hit_run(rules=replace(RULES, delay_ticks=2), waves=start_waves(BOOK, SEED))
    )
    no_waves: Run = over_run(hit_run(rules=replace(RULES, delay_ticks=2)))

    caplog.clear()
    next_run(with_waves)
    assert all_lines(caplog) == ["new run", f"wave start id={WAVE_ZERO} level=1 random=False"]
    assert [r.name for r in caplog.records] == [RUN_LOGGER, "core.waves"]
    assert caplog.records[0].levelno == logging.INFO

    caplog.clear()
    next_run(no_waves)
    assert all_lines(caplog) == ["new run"]
