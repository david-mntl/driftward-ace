"""The level-up banner inside `core.run`: step 9b, the cue, the shown level, last life, new run.

Contract: docs/contracts/systems/level-up/core.md, Diagram (the table), Interface (`core/run.py`),
Rules (The banner, Pause, Game over and a new run, The shown level, The `level_up` cue);
docs/contracts/systems/run.md, Interface (DRA-148: the level-up banner), Rules (step 9b, The last
life, A last-life tick, A game-over tick, `next_run`). Task:
docs/contracts/DRA-148/tasks/DRA-148-08-qa-engineer.md. One test per behavior it lists.

Like test_run_waves.py, the wave books, the level-up rules and the runs are built here and no
`game/tuning/` or `game/waves/` file is read. The rules below are test-local values that obey the
contract's limits (arrival below banner, banner at most the rest); the expected states are worked
out from them with `expected_banner`, which reads only each state's real `level` and the rules.
The run holds its ship at home before each tick (`hold`), so nothing falls or is hit unless a test
says so.
"""

from collections.abc import Sequence
from dataclasses import replace

import pytest

from core.collision import Circle
from core.drifters.base import Drifter, DrifterType, Phase
from core.drifters.meteorite import Meteorite
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.game_flow import GameFlow, Screen, TickInput, start_flow, step_flow
from core.level_up import LevelUpBanner, LevelUpRules
from core.run import Run, next_run, start_run, step_run
from core.ship import Ship, Thrust
from core.waves import (
    LevelPlaylist,
    Wave,
    WaveBook,
    WaveKind,
    WaveRun,
    start_waves,
)

LEVEL_COUNT: int = 8
"""Source: 08-difficulty.md, rule 1 (Level 8 is the last)."""

REST: int = 20
ARRIVAL: int = 6
BANNER: int = 14
RULES: LevelUpRules = LevelUpRules(rest_ticks=REST, arrival_ticks=ARRIVAL, banner_ticks=BANNER)
"""Test-local values. Source for the limits: level-up/core.md, Interface (`arrival_ticks` >= 1,
`banner_ticks` > `arrival_ticks`, <= `rest_ticks` when it is above 0)."""

OFF: LevelUpRules = LevelUpRules(rest_ticks=0, arrival_ticks=ARRIVAL, banner_ticks=BANNER)
"""Rest 0: no rest, no banner, no cue. Source: level-up/core.md, Interface (`rest_ticks`)."""

SCROLL_BASE: float = 1.1
SCROLL_MULT: tuple[float, ...] = (1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7)
"""px/tick at Level 1 and the scroll speed x per level. Source: 03-world-and-camera.md,
scroll_base (guess); 08-difficulty.md, Level table (locked)."""

HOME: Ship = Ship(x=320.0, y=240.0, vx=0.0, vy=0.0)
"""Where the test ship stands. Source: 03-world-and-camera.md, ship_start (guess)."""

SHIP_H: int = 32
SCREEN_H: int = 480
FALL_CAP: float = 5.5
AT_FLOOR_Y: float = SCREEN_H + SHIP_H / 2 - FALL_CAP
"""A ship at fall_cap here moves exactly FALL_CAP next tick and its top edge lands on the floor.
Source: 04-ship.md, ship_h, fall_cap; 03-world-and-camera.md, screen_h."""

FALLING: Ship = Ship(x=320.0, y=AT_FLOOR_Y, vx=0.0, vy=FALL_CAP)

NO_KEY = Thrust()
UP = Thrust(up=True)
IDLE = TickInput()
CONFIRM = TickInput(confirm=True)
FOCUS_LOST = TickInput(focus_lost=True)

WAVE_ZERO: str = "w0"
SEED: int = 20261106

RISE: int = 50
"""The tick `a` ends in `level_up_book`: Wave 0 ends on tick 40 (30 still ticks and 10 moving
ones of 1.1 px against 11 px), `a` on tick 50. The level is 2 on the state after it."""


def make_tuning() -> DrifterTuning:
    """The meteorite the hit tests put on the ship, from the GDD (medium, circle radius 14)."""
    return DrifterTuning(
        drifters={
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={"medium": VariantTuning(width=28, height=28, hitbox=(Circle(0, 0, 14),))},
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=60,
            ),
        },
        switches=PlaytestSwitches(),
    )


TUNING: DrifterTuning = make_tuning()


def wave(wave_id: str, length: float = 11.0, *, pool: bool = False) -> Wave:
    """A wave with no placements. A pool wave is open from Level 1."""
    return Wave(
        wave_id=wave_id,
        length_px=length,
        kind=WaveKind.POOL if pool else WaveKind.FIXED,
        min_level=1 if pool else None,
        extra_rest_ticks=0,
        placements=(),
    )


def book_of(waves: Sequence[Wave], levels: Sequence[LevelPlaylist]) -> WaveBook:
    """A book. `levels` is Level 1 first; the levels it leaves out have no slots."""
    playlists: tuple[LevelPlaylist, ...] = (
        *levels,
        *(LevelPlaylist() for _ in range(LEVEL_COUNT - len(levels))),
    )
    return WaveBook(
        waves={item.wave_id: item for item in waves}, wave_zero_id=WAVE_ZERO, playlists=playlists
    )


def level_up_book() -> WaveBook:
    """Wave 0 and `a` are 11 px, so each ends after 10 moving ticks: Level 2 starts on tick 50.

    Levels 2 to 8 play `long` (10 000 px), so the level stays 2 for the ticks the tests walk.
    """
    return book_of(
        [wave(WAVE_ZERO), wave("a"), wave("long", 10_000.0)],
        [
            LevelPlaylist(fixed=("a",)),
            *(LevelPlaylist(fixed=("long",)) for _ in range(2, LEVEL_COUNT + 1)),
        ],
    )


def climb_book() -> WaveBook:
    """Every level plays `a` (11 px) once: seven rises, and Level 8's `a` ends with no rise.

    The pool wave `p` plays after it, as the run goes on at Level 8 (Level 8 has no end).
    """
    return book_of(
        [wave(WAVE_ZERO), wave("a"), wave("p", pool=True)],
        [LevelPlaylist(fixed=("a",)) for _ in range(LEVEL_COUNT)],
    )


def skip_book(empty: Sequence[int]) -> WaveBook:
    """Level 1 plays `a`; the levels in `empty` have no slots, so a rise passes over them."""
    return book_of(
        [wave(WAVE_ZERO), wave("a"), wave("long", 10_000.0)],
        [
            LevelPlaylist()
            if level in empty
            else LevelPlaylist(fixed=("a",) if level == 1 else ("long",))
            for level in range(1, LEVEL_COUNT + 1)
        ],
    )


def waves_of(book: WaveBook, rules: LevelUpRules | None = RULES) -> WaveRun:
    """The wave state at tick 0. `rules` None leaves the argument out."""
    return start_waves(book, SEED) if rules is None else start_waves(book, SEED, rules)


def hold(run: Run) -> Run:
    """Put the ship back at home, so it never falls or touches anything while the world runs."""
    return replace(run, ship=HOME)


def flown(run: Run, ticks: int) -> list[Run]:
    """The run and the state after each of `ticks` playing ticks, ship held at home, no key."""
    states: list[Run] = [run]
    for _ in range(ticks):
        run = step_run(hold(run), NO_KEY)
        states.append(run)
    return states


def timeline(
    ticks: int, book: WaveBook | None = None, rules: LevelUpRules | None = RULES
) -> list[Run]:
    """`states[t]` is the state after tick t of a new run on `book` (`states[0]` the start)."""
    return flown(start_run(waves_of(level_up_book() if book is None else book, rules)), ticks)


def rises(states: Sequence[Run]) -> list[int]:
    """The ticks on which the real level went up."""
    return [tick for tick in range(1, len(states)) if states[tick].level > states[tick - 1].level]


def expected_banner(states: Sequence[Run], tick: int, rules: LevelUpRules) -> LevelUpBanner | None:
    """The banner the contract's Diagram gives on the state after `tick`.

    Worked out from the real level of each state: the latest rise at or before `tick` starts a
    banner at age 0, which lives `banner_ticks` states. Rest 0 has none.
    """
    if rules.rest_ticks == 0:
        return None
    started: list[int] = [rise for rise in rises(states) if rise <= tick]
    if not started or tick - started[-1] >= rules.banner_ticks:
        return None
    rise: int = started[-1]
    return LevelUpBanner(
        level=states[rise].level,
        previous_level=states[rise - 1].level,
        arrival_ticks=rules.arrival_ticks,
        lifetime_ticks=rules.banner_ticks,
        age_ticks=tick - rise,
    )


def expected_hud_level(
    states: Sequence[Run], tick: int, rules: LevelUpRules, banner: LevelUpBanner | None
) -> int:
    """The level the HUD shows: the one before the rise until the arrival age, else the real one."""
    if banner is not None and banner.age_ticks < rules.arrival_ticks:
        return states[tick - banner.age_ticks - 1].level
    return states[tick].level


def assert_follows_the_diagram(states: Sequence[Run], rules: LevelUpRules) -> None:
    """Every state's banner, shown level and cue are the Diagram's, from the level alone."""
    for tick in range(len(states)):
        banner: LevelUpBanner | None = expected_banner(states, tick, rules)
        assert states[tick].level_up == banner, tick
        assert states[tick].hud_level == expected_hud_level(states, tick, rules, banner), tick
        assert states[tick].level_up_cue == (banner is not None and banner.age_ticks == 0), tick


def rock_on_ship() -> Meteorite:
    """An ACTIVE meteorite with no speed, on the home ship."""
    spawned: Drifter = spawn_drifter(Placement(DrifterType.METEORITE, 320.0, 240.0), 1, TUNING)
    assert isinstance(spawned, Meteorite)
    return replace(spawned, uid=1, phase=Phase.ACTIVE, ticks_in_phase=0, speed=0.0)


def lose_last_life(run: Run, how: str) -> Run:
    """The next tick of `run` on its last life, lost by a fall or by a hit on a still rock."""
    if how == "fall":
        last: Run = step_run(replace(run, lives=1, ship=FALLING), NO_KEY)
    else:
        hit: Run = replace(run, lives=1, ship=HOME, drifters=(rock_on_ship(),), next_uid=2)
        last = step_run(hit, NO_KEY)
    assert last.last_life
    assert last.lives == 0
    assert last.burst is not None
    return last


def last_life_ticks(run: Run, count: int) -> list[Run]:
    """`run` and the states after `count` more last-life ticks, no key."""
    states: list[Run] = [run]
    for _ in range(count):
        run = step_run(run, NO_KEY)
        states.append(run)
    return states


def to_game_over(run: Run) -> Run:
    """Step a last-life run with no key until game over."""
    assert run.last_life
    for _ in range(500):
        run = step_run(run, NO_KEY)
        if run.game_over:
            return run
    raise AssertionError("the last life never ended")


def test_the_banner_starts_on_the_state_after_the_rise_tick_at_age_0_and_ages_one_a_tick() -> None:
    states: list[Run] = timeline(RISE + BANNER + 3)
    assert rises(states) == [RISE]

    for tick in range(RISE):
        assert states[tick].level == 1
        assert states[tick].level_up is None, tick

    started: LevelUpBanner | None = states[RISE].level_up
    assert started == LevelUpBanner(
        level=2,
        previous_level=1,
        arrival_ticks=ARRIVAL,
        lifetime_ticks=BANNER,
        age_ticks=0,
    )
    for age in range(BANNER):
        banner: LevelUpBanner | None = states[RISE + age].level_up
        assert banner is not None, age
        assert banner.age_ticks == age
        assert (banner.level, banner.previous_level) == (2, 1)
        assert (banner.arrival_ticks, banner.lifetime_ticks) == (ARRIVAL, BANNER)
    assert_follows_the_diagram(states, RULES)

    # A later rise (Level 2 to 3, then up to 8) carries its own previous level and level.
    climb: list[Run] = timeline(400, climb_book())
    rise_ticks: list[int] = rises(climb)
    assert len(rise_ticks) == LEVEL_COUNT - 1
    for index, tick in enumerate(rise_ticks):
        banner = climb[tick].level_up
        assert banner is not None
        assert (banner.previous_level, banner.level, banner.age_ticks) == (index + 1, index + 2, 0)
        assert climb[tick + 1].level_up is not None
        assert climb[tick + 1].level_up == replace(banner, age_ticks=1)
    assert_follows_the_diagram(climb, RULES)


def test_the_cue_is_true_on_the_rise_state_only_and_a_rest_of_0_has_no_banner_and_no_cue() -> None:
    climb: list[Run] = timeline(400, climb_book())
    rise_ticks: list[int] = rises(climb)
    assert len(rise_ticks) == LEVEL_COUNT - 1
    assert [tick for tick, state in enumerate(climb) if state.level_up_cue] == rise_ticks

    for rules in (OFF, None):
        rest_off: list[Run] = timeline(400, climb_book(), rules)
        assert len(rises(rest_off)) == LEVEL_COUNT - 1  # the level still rises, the moment is gone
        for tick, state in enumerate(rest_off):
            assert state.level_up is None, tick
            assert state.level_up_cue is False, tick
            assert state.hud_level == state.level, tick
    assert timeline(RISE + 5, rules=OFF)[RISE].level == 2


def test_the_hud_shows_the_previous_level_until_the_arrival_age_then_the_real_level() -> None:
    states: list[Run] = timeline(RISE + BANNER + 2)
    for age in range(BANNER + 2):
        state: Run = states[RISE + age]
        assert state.level == 2
        assert state.level_reached == 2
        assert state.hud_level == (1 if age < ARRIVAL else 2), age
    assert states[RISE + ARRIVAL - 1].hud_level == 1
    assert states[RISE + ARRIVAL].hud_level == 2
    assert states[RISE - 1].hud_level == 1

    # The scroll speed is the new level's at once, while the HUD still shows the old one.
    for tick in range(RISE + 1, RISE + ARRIVAL):
        step_px: float = states[tick].scroll.distance_px - states[tick - 1].scroll.distance_px
        assert states[tick].hud_level == 1
        assert step_px == pytest.approx(SCROLL_BASE * SCROLL_MULT[1], abs=1e-9), tick
    before_px: float = states[RISE - 1].scroll.distance_px - states[RISE - 2].scroll.distance_px
    assert before_px == pytest.approx(SCROLL_BASE * SCROLL_MULT[0], abs=1e-9)

    # The level reached on a last life lost during the pop is the real one.
    last: Run = lose_last_life(states[RISE + 1], "fall")
    assert last.level == 2
    assert last.level_reached == 2


def test_the_banner_is_none_after_its_lifetime_and_through_waves_without_a_rise() -> None:
    states: list[Run] = timeline(RISE + BANNER + 60)
    assert states[RISE + BANNER - 1].level_up is not None
    for tick in range(RISE + BANNER, len(states)):
        assert states[tick].level_up is None, tick
        assert states[tick].level_up_cue is False, tick
        assert states[tick].hud_level == 2, tick

    # Wave 0 ends on tick 40 and starts the Level 1 playlist: no rise, no banner.
    assert states[40].waves is not None
    assert states[40].waves.wave_id == "a"
    for tick in range(1, RISE):
        assert states[tick].level_up is None, tick
        assert states[tick].level_up_cue is False, tick

    # Level 8 never rises: seven banners and none for the end of Level 8's wave.
    climb: list[Run] = timeline(600, climb_book())
    assert len(rises(climb)) == LEVEL_COUNT - 1
    assert climb[-1].level == LEVEL_COUNT
    last_rise: int = rises(climb)[-1]
    assert [state.level_up_cue for state in climb[last_rise + 1 :]] == [False] * (
        len(climb) - last_rise - 1
    )
    for tick in range(last_rise + BANNER, len(climb)):
        assert climb[tick].level_up is None, tick
    assert_follows_the_diagram(climb, RULES)

    # A run with no waves never has a banner.
    bare: list[Run] = flown(start_run(), 120)
    for tick, state in enumerate(bare):
        assert state.waves is None
        assert state.level_up is None, tick
        assert state.level_up_cue is False, tick
        assert state.hud_level == 1, tick


@pytest.mark.parametrize("empty", [(2,), (2, 3), (2, 3, 4, 5, 6, 7)])
def test_a_skipped_level_shows_the_level_reached_in_the_banner_and_the_shown_level(
    empty: tuple[int, ...],
) -> None:
    reached: int = 2 + len(empty)
    states: list[Run] = timeline(RISE + BANNER + 3, skip_book(empty))
    assert rises(states) == [RISE]
    assert states[RISE].level == reached

    banner: LevelUpBanner | None = states[RISE].level_up
    assert banner == LevelUpBanner(
        level=reached,
        previous_level=1,
        arrival_ticks=ARRIVAL,
        lifetime_ticks=BANNER,
        age_ticks=0,
    )
    for age in range(BANNER + 3):
        state: Run = states[RISE + age]
        assert state.level == reached
        assert state.level_reached == reached
        assert state.hud_level == (1 if age < ARRIVAL else reached), age
        assert state.hud_level != 2 or reached == 2
    assert states[RISE].level_up_cue is True
    assert_follows_the_diagram(states, RULES)


@pytest.mark.parametrize("age", [0, 1, ARRIVAL - 1, ARRIVAL, BANNER - 1])
def test_a_run_the_flow_does_not_step_keeps_its_banner_age(age: int) -> None:
    states: list[Run] = timeline(RISE + BANNER)
    frozen: Run = states[RISE + age]
    assert frozen.level_up is not None
    assert frozen.level_up.age_ticks == age

    playing: GameFlow = replace(
        start_flow(frozen), screen=Screen.PLAYING, confirm_held=False, arrows_held=NO_KEY
    )
    paused: GameFlow = step_flow(playing, CONFIRM)
    assert paused.screen is Screen.PAUSED
    assert paused.run.level_up == frozen.level_up

    for keys in (
        IDLE,
        TickInput(thrust=UP),
        TickInput(thrust=UP),
        FOCUS_LOST,
        IDLE,
        TickInput(thrust=Thrust(left=True)),
    ):
        paused = step_flow(paused, keys)
        assert paused.screen is Screen.PAUSED
        assert paused.run_stepped is False
        assert paused.run.level_up == frozen.level_up
        assert paused.run.hud_level == frozen.hud_level
        assert paused.run.level == frozen.level
        assert paused.run.waves == frozen.waves

    resumed: GameFlow = step_flow(step_flow(paused, IDLE), CONFIRM)
    assert resumed.screen is Screen.PLAYING
    assert resumed.run.level_up == frozen.level_up
    assert resumed.run.hud_level == frozen.hud_level

    stepped: GameFlow = step_flow(resumed, IDLE)
    assert stepped.run_stepped is True
    following: LevelUpBanner | None = states[RISE + age + 1].level_up
    assert stepped.run.level_up == following
    if following is not None:
        assert following.age_ticks == age + 1


@pytest.mark.parametrize("how", ["fall", "hit"])
@pytest.mark.parametrize("age", [0, 2, ARRIVAL, BANNER - 1])
def test_a_hit_or_a_fall_during_the_banner_changes_nothing_about_its_age_or_levels(
    how: str, age: int
) -> None:
    twin: list[Run] = timeline(RISE + BANNER + 4)
    before: Run = twin[RISE + age - 1] if age > 0 else twin[RISE - 1]
    start: int = RISE + age - 1 if age > 0 else RISE - 1

    # The tick after `before` costs a life: a fall (the ship's top edge lands on the floor) or a
    # hit (a still rock on the ship). Five lives, so it is not the last life.
    if how == "fall":
        hurt: Run = step_run(replace(before, ship=FALLING), NO_KEY)
        assert hurt.lives == before.lives - 1
    else:
        hurt = step_run(replace(hold(before), drifters=(rock_on_ship(),), next_uid=2), NO_KEY)
        assert hurt.lives == before.lives - 1
    assert not hurt.last_life
    assert hurt.level_up == twin[start + 1].level_up
    assert hurt.hud_level == twin[start + 1].hud_level
    assert hurt.level_up_cue == twin[start + 1].level_up_cue
    assert hurt.level == twin[start + 1].level

    # Ticks on after it, with the ship wherever the run put it and no key: the banner is the twin's.
    run: Run = hurt
    for tick in range(start + 2, len(twin)):
        run = step_run(run, NO_KEY)
        assert run.level_up == twin[tick].level_up, tick
        assert run.hud_level == twin[tick].hud_level, tick
        assert run.level_up_cue == twin[tick].level_up_cue, tick
        assert run.level == twin[tick].level, tick
        assert not run.last_life, tick


@pytest.mark.parametrize("how", ["fall", "hit"])
def test_losing_the_last_life_during_the_banner_sets_it_to_none_and_a_later_rise_starts_none(
    how: str,
) -> None:
    states: list[Run] = timeline(RISE + BANNER)

    # During the banner, before the arrival: the HUD would show Level 1, now it shows the real 2.
    mid: Run = states[RISE + 2]
    assert mid.level_up is not None
    assert mid.hud_level == 1
    last: Run = lose_last_life(mid, how)
    assert last.level == 2
    assert last.level_up is None
    assert last.level_up_cue is False
    assert last.hud_level == last.level == 2
    for state in last_life_ticks(last, 130):
        assert state.level_up is None
        assert state.level_up_cue is False
        assert state.hud_level == state.level
        if state.game_over:
            break

    # On the rise state itself (age 0, cue True): the next tick is the last-life tick.
    assert states[RISE].level_up_cue is True
    last = lose_last_life(states[RISE], how)
    assert last.level_up is None
    assert last.hud_level == 2

    # A rise on a later last-life tick: the burst is already there, so no banner and no cue.
    before: Run = states[RISE - 8]
    assert before.level == 1
    over: Run = lose_last_life(before, how)
    seen_rise: bool = False
    for state in last_life_ticks(over, 20)[1:]:
        assert state.last_life
        assert state.level_up is None
        assert state.level_up_cue is False
        assert state.hud_level == state.level
        seen_rise = seen_rise or state.level == 2
    assert seen_rise

    # A rise on the very tick the last life is lost.
    on_rise: Run = lose_last_life(states[RISE - 1], how)
    assert on_rise.level == 2
    assert on_rise.last_life
    assert on_rise.level_up is None
    assert on_rise.level_up_cue is False
    assert on_rise.hud_level == 2
    assert on_rise.waves is not None
    assert on_rise.waves.level_rose is True
    for state in last_life_ticks(on_rise, 25)[1:]:
        assert state.level_up is None
        assert state.level_up_cue is False


@pytest.mark.parametrize("how", ["fall", "hit"])
def test_a_game_over_tick_changes_no_banner_and_next_run_starts_with_none_and_the_same_rules(
    how: str,
) -> None:
    states: list[Run] = timeline(RISE + BANNER)
    last: Run = lose_last_life(states[RISE + 2], how)
    over: Run = to_game_over(last)
    assert over.level_up is None
    assert over.hud_level == over.level
    assert over.level_up_cue is False
    for keys in (NO_KEY, UP, Thrust(left=True, right=True)):
        frozen: Run = step_run(over, keys)
        assert frozen.level_up is None
        assert frozen.hud_level == over.hud_level
        assert frozen.level_up_cue is False

    # A game-over tick changes nothing: a banner put on the state is still there, as it was.
    injected: LevelUpBanner = LevelUpBanner(
        level=2, previous_level=1, arrival_ticks=ARRIVAL, lifetime_ticks=BANNER, age_ticks=3
    )
    held: Run = replace(over, level_up=injected)
    assert step_run(held, NO_KEY).level_up == injected

    # A new run, from game over, from the last life and from the middle of a banner.
    for source in (over, last, states[RISE + 2], states[RISE]):
        fresh: Run = next_run(source)
        assert fresh.level_up is None
        assert fresh.hud_level == 1
        assert fresh.level_up_cue is False
        assert fresh.level == 1
        assert fresh.waves is not None
        assert fresh.waves.level_up_rules == RULES
        assert fresh.waves.level_rose is False

        again: list[Run] = flown(fresh, RISE + 3)
        assert [state.level_up for state in again[:RISE]] == [None] * RISE
        assert again[RISE].level_up == LevelUpBanner(
            level=2,
            previous_level=1,
            arrival_ticks=ARRIVAL,
            lifetime_ticks=BANNER,
            age_ticks=0,
        )
        assert again[RISE].level_up_cue is True
        assert again[RISE + 1].level_up_cue is False

    # With rest 0 the new run has the rules (off) and no banner.
    off_over: Run = to_game_over(lose_last_life(timeline(RISE + 2, rules=OFF)[RISE + 1], how))
    fresh_off: Run = next_run(off_over)
    assert fresh_off.waves is not None
    assert fresh_off.waves.level_up_rules == OFF
    assert fresh_off.level_up is None
    assert all(state.level_up is None for state in flown(fresh_off, RISE + 3))


def test_the_respawn_wait_and_protected_ticks_age_the_banner_like_any_playing_tick() -> None:
    twin: list[Run] = timeline(RISE + BANNER + 6)

    # A fall before the rise: the ship waits on the respawn spot through the rise, then a press
    # ends the wait and the banner goes on aging through the protected ticks.
    fall_tick: int = RISE - 5
    run: Run = step_run(replace(twin[fall_tick - 1], ship=FALLING), NO_KEY)
    assert run.waiting
    assert run.lives == twin[fall_tick - 1].lives - 1
    states: list[Run] = [run]
    press_tick: int = RISE + 4
    for tick in range(fall_tick + 1, len(twin)):
        keys: Thrust = UP if tick == press_tick else NO_KEY
        run = step_run(run, keys)
        states.append(run)
        assert run.level_up == twin[tick].level_up, tick
        assert run.hud_level == twin[tick].hud_level, tick
        assert run.level_up_cue == twin[tick].level_up_cue, tick
        assert run.level == twin[tick].level, tick

    by_tick: dict[int, Run] = {fall_tick + index: state for index, state in enumerate(states)}
    assert by_tick[RISE].waiting is True
    assert by_tick[RISE].level_up_cue is True
    assert by_tick[RISE + 3].waiting is True
    waiting_banner: LevelUpBanner | None = by_tick[RISE + 3].level_up
    assert waiting_banner is not None
    assert waiting_banner.age_ticks == 3
    assert by_tick[press_tick].waiting is False
    protected: list[int] = [
        tick for tick, state in by_tick.items() if tick > RISE and state.invuln_ticks_left > 0
    ]
    assert protected
    for tick in protected:
        banner: LevelUpBanner | None = by_tick[tick].level_up
        assert banner == twin[tick].level_up
    assert any(
        by_tick[tick].level_up is not None and not by_tick[tick].waiting for tick in protected
    )
    assert by_tick[RISE + BANNER].level_up is None
    assert by_tick[RISE + BANNER - 1].level_up is not None
