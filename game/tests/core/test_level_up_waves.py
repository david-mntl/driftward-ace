"""The level-up rest, the rise flag and the banner's core state.

Contract: docs/contracts/systems/level-up/core.md, Interface (`core/level_up.py`, `core/waves.py`),
Rules (The level-up rest, The rise flag); docs/contracts/systems/waves.md, Rules, The wave clock,
steps 3.1, 3.2 and 2a. Task: docs/contracts/DRA-148/tasks/DRA-148-07-qa-engineer.md. One test per
behavior it lists.

Like test_waves.py, the books and rules are built here in code and no `game/tuning/` or
`game/waves/` file is read. The rest gap multipliers are written here from 08-difficulty.md (the
Rest gap x row). The GDD's rest_gap_base is 0, so the tests that need a scaled gap set it to 10
through `monkeypatch` (`core.waves.REST_GAP_BASE_TICKS`, read when the gap is worked out). Waves are
10 px long and the scroll adds 10 px a tick, so one wave ends on each tick it can.
"""

import logging
import math
import random
from collections.abc import Sequence
from dataclasses import replace
from fractions import Fraction

import pytest

from core.level_up import (
    NO_LEVEL_UP,
    LevelUpBanner,
    LevelUpRules,
    shown_level,
    start_level_up,
    step_level_up,
)
from core.waves import (
    LevelPlaylist,
    Wave,
    WaveBook,
    WaveKind,
    WaveRun,
    next_run_waves,
    start_waves,
    step_waves,
)

LAST_LEVEL: int = 8
"""Source: 08-difficulty.md, rule 1."""

REST_GAP_MULT: tuple[str, ...] = ("1.00", "0.90", "0.81", "0.73", "0.66", "0.59", "0.53", "0.48")
"""Rest gap x per level, as exact decimals. Source: 08-difficulty.md, Level table."""

SCALED_BASE: int = 10
"""A rest gap base the scaled tests set (the GDD's is 0, a guess). The multipliers then give 9, 8.1,
7.3, 6.6, 5.9, 5.3 and 4.8 ticks at Levels 2 to 8, so the round up shows."""

WAVES_LOGGER: str = "core.waves"
"""Source: waves.md, Rules, Logging."""

WAVE_ZERO: str = "w0"
STEP_PX: float = 10.0
"""Scroll per tick. Every wave is as long, so one wave ends on every tick that can end one."""


def rules_of(rest: int) -> LevelUpRules:
    """Level-up rules with `rest` ticks of rest. The banner values are the smallest legal ones."""
    return LevelUpRules(rest_ticks=rest, arrival_ticks=1, banner_ticks=2)


def wave(wave_id: str, *, extra_rest: int = 0, pool: bool = False) -> Wave:
    """A 10 px wave with no placements."""
    return Wave(
        wave_id=wave_id,
        length_px=10.0,
        kind=WaveKind.POOL if pool else WaveKind.FIXED,
        min_level=1 if pool else None,
        extra_rest_ticks=extra_rest,
        placements=(),
    )


def book_of(waves: Sequence[Wave], levels: dict[int, LevelPlaylist]) -> WaveBook:
    """A book. `levels` maps a level (1 to 8) to its playlist; the others have no slots."""
    playlists: tuple[LevelPlaylist, ...] = tuple(
        levels.get(level, LevelPlaylist()) for level in range(1, LAST_LEVEL + 1)
    )
    return WaveBook(
        waves={item.wave_id: item for item in waves}, wave_zero_id=WAVE_ZERO, playlists=playlists
    )


def climb_book(*, extra_rest: int = 0, empty: Sequence[int] = ()) -> WaveBook:
    """Wave 0 and one wave `a` (with `extra_rest`), and a one-wave playlist at every level but the
    levels in `empty`, so every end of `a` is a rise (Level 8's is not)."""
    return book_of(
        [wave(WAVE_ZERO), wave("a", extra_rest=extra_rest), wave("p", pool=True)],
        {
            level: LevelPlaylist(fixed=("a",))
            for level in range(1, LAST_LEVEL + 1)
            if level not in empty
        },
    )


def run_for(
    book: WaveBook, ticks: int, *, rules: LevelUpRules | None = None, seed: int = 2
) -> list[WaveRun]:
    """The state after each of `ticks` ticks. `rules` None leaves the argument out."""
    state: WaveRun = start_waves(book, seed) if rules is None else start_waves(book, seed, rules)
    states: list[WaveRun] = []
    for tick in range(1, ticks + 1):
        state = step_waves(state, STEP_PX * tick)
        states.append(state)
    return states


def rise_indexes(states: Sequence[WaveRun]) -> list[int]:
    """The index of every state whose level is above the one before it (the start is Level 1)."""
    previous: int = 1
    found: list[int] = []
    for index, state in enumerate(states):
        if state.level > previous:
            found.append(index)
        previous = state.level
    return found


def rest_run(states: Sequence[WaveRun], start: int) -> list[WaveRun]:
    """The resting states from `start` on, up to the first state that is not resting."""
    run: list[WaveRun] = []
    for state in states[start:]:
        if not state.resting:
            break
        run.append(state)
    return run


def scaled_gap(level: int) -> int:
    """The rest gap at `level` with the base `SCALED_BASE`, rounded up. Exact, in fractions."""
    return math.ceil(Fraction(SCALED_BASE) * Fraction(REST_GAP_MULT[level - 1]))


@pytest.mark.parametrize(("rest", "extra"), [(2, 0), (5, 0), (5, 3), (150, 0), (150, 7)])
def test_a_rise_adds_the_level_up_rest_to_the_extra_rest_and_it_counts_down_on_that_many_states(
    rest: int, extra: int
) -> None:
    states: list[WaveRun] = run_for(
        climb_book(extra_rest=extra), rest + extra + 20, rules=rules_of(rest)
    )
    # Tick 1: Wave 0 ends, `a` starts. Tick 2: `a` ends and the level rises. The gap is 0 here.
    assert (states[0].level, states[0].resting) == (1, False)
    rise: WaveRun = states[1]
    assert (rise.level, rise.resting, rise.level_rose) == (2, True, True)
    total: int = rest + extra
    assert rise.rest_ticks_left == total
    resting: list[WaveRun] = rest_run(states, 1)
    assert len(resting) == total
    assert [state.rest_ticks_left for state in resting] == list(range(total, 0, -1))
    assert all(state.current_wave_id is None and state.wave_id == "a" for state in resting)
    assert all(state.spawns_due == () and state.level == 2 for state in resting)
    # The rest ends on tick 2 + total: the next wave starts at that tick's distance.
    began: WaveRun = states[1 + total]
    assert (began.resting, began.rest_ticks_left, began.current_wave_id) == (False, 0, "a")
    assert began.start_px == STEP_PX * (2 + total)
    assert began.level == 2


@pytest.mark.parametrize("rest", [7, 150])
def test_the_rest_after_a_rise_at_a_scaled_level_adds_the_unscaled_rest_to_the_scaled_gap(
    monkeypatch: pytest.MonkeyPatch, rest: int
) -> None:
    monkeypatch.setattr("core.waves.REST_GAP_BASE_TICKS", SCALED_BASE)
    states: list[WaveRun] = run_for(climb_book(), 320 + 7 * rest, rules=rules_of(rest))
    rises: list[int] = rise_indexes(states)
    assert len(rises) == LAST_LEVEL - 1
    for index in rises:
        level: int = states[index].level
        expected: int = scaled_gap(level) + rest
        assert states[index].level_rose is True
        assert states[index].rest_ticks_left == expected, level
        assert len(rest_run(states, index)) == expected, level
    # The gap shrinks with the level but the level-up rest does not.
    assert [states[index].rest_ticks_left - rest for index in rises] == [
        9,
        9,
        8,
        7,
        6,
        6,
        5,
    ]


def test_a_wave_end_with_no_rise_adds_nothing_to_the_rest() -> None:
    book: WaveBook = book_of(
        [wave(WAVE_ZERO), wave("a", extra_rest=2), wave("b")],
        {1: LevelPlaylist(fixed=("a", "a", "b")), 2: LevelPlaylist(fixed=("b",))},
    )
    states: list[WaveRun] = run_for(book, 12, rules=rules_of(5))
    # Tick 1: Wave 0 ends. Tick 2: the first `a` ends with two slots left: 2 ticks, not 7.
    # Tick 4: the second `a` ends with one slot left: 2 ticks again. `b` ends the level on tick 7.
    assert [(s.resting, s.rest_ticks_left, s.level, s.level_rose) for s in states[:8]] == [
        (False, 0, 1, False),
        (True, 2, 1, False),
        (True, 1, 1, False),
        (False, 0, 1, False),
        (True, 2, 1, False),
        (True, 1, 1, False),
        (False, 0, 1, False),
        (True, 5, 2, True),
    ]
    assert states[0].current_wave_id == "a"
    assert states[3].current_wave_id == "a"
    assert states[6].current_wave_id == "b"
    assert all(state.level == 1 for state in states[:7])


def test_wave_0_ending_and_every_wave_at_level_8_after_the_last_playlist_wave_are_no_rise() -> None:
    # Wave 0 ends with 2 extra rest: no rise (the level stays 1) and a rest of 2, not 7.
    zero: WaveBook = book_of(
        [
            Wave(
                wave_id=WAVE_ZERO,
                length_px=10.0,
                kind=WaveKind.FIXED,
                min_level=None,
                extra_rest_ticks=2,
                placements=(),
            ),
            wave("a"),
        ],
        {1: LevelPlaylist(fixed=("a",)), 2: LevelPlaylist(fixed=("a",))},
    )
    first: list[WaveRun] = run_for(zero, 4, rules=rules_of(5))
    assert [(s.level, s.resting, s.rest_ticks_left, s.level_rose) for s in first] == [
        (1, True, 2, False),
        (1, True, 1, False),
        (1, False, 0, False),
        (2, True, 5, True),
    ]
    assert first[2].current_wave_id == "a"

    # Levels 1 to 7 climb on `a`. Level 8 has `z` (1 extra rest), then random waves `p` (1 extra
    # rest): every end from `z` on is no rise and rests 1 tick.
    book: WaveBook = book_of(
        [wave(WAVE_ZERO), wave("a"), wave("z", extra_rest=1), wave("p", extra_rest=1, pool=True)],
        {
            **{level: LevelPlaylist(fixed=("a",)) for level in range(1, LAST_LEVEL)},
            LAST_LEVEL: LevelPlaylist(fixed=("z",)),
        },
    )
    states: list[WaveRun] = run_for(book, 200, rules=rules_of(5))
    z_at: int = next(i for i, s in enumerate(states) if s.wave_id == "z" and not s.resting)
    after: list[WaveRun] = states[z_at:]
    assert states[z_at].level == LAST_LEVEL
    assert all(state.level == LAST_LEVEL and not state.level_rose for state in after)
    assert all(state.rest_ticks_left <= 1 for state in after)
    played: list[str] = [state.wave_id for state in after if not state.resting]
    assert played[0] == "z"
    assert played.count("p") > 10
    ends: list[WaveRun] = [state for state in after if state.resting]
    assert len(ends) > 10
    assert all(state.rest_ticks_left == 1 for state in ends)


@pytest.mark.parametrize(("empty", "reached"), [((2,), 3), ((2, 3), 4), ((2, 3, 4, 5, 6, 7), 8)])
def test_a_level_with_an_empty_playlist_is_passed_on_the_same_tick_and_the_rest_is_added_once(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    empty: tuple[int, ...],
    reached: int,
) -> None:
    monkeypatch.setattr("core.waves.REST_GAP_BASE_TICKS", SCALED_BASE)
    rest: int = 6
    caplog.set_level(logging.DEBUG, logger=WAVES_LOGGER)
    # 12 ticks reach the first rise (state 11) and stop there, so the log holds that rise alone.
    run_for(climb_book(empty=empty), 12, rules=rules_of(rest))
    lines: list[str] = [r.getMessage() for r in caplog.records if r.name == WAVES_LOGGER]
    states: list[WaveRun] = run_for(climb_book(empty=empty), 60, rules=rules_of(rest))
    rises: list[int] = rise_indexes(states)
    first: int = rises[0]
    # Wave 0 ends on tick 1 and rests the Level 1 gap (10 ticks). `a` starts on tick 11 and ends
    # on tick 12, which is state 11.
    assert first == 1 + SCALED_BASE
    state: WaveRun = states[first]
    expected: int = scaled_gap(reached) + rest
    assert (state.level, state.level_rose, state.resting) == (reached, True, True)
    assert state.rest_ticks_left == expected
    assert len(rest_run(states, first)) == expected
    # The skipped levels never show on a state, and the rise is one event with one rest.
    assert all(s.level in (1, reached) for s in states[: first + expected + 1])
    assert lines.count(f"level up level={reached}") == 1
    assert [line for line in lines if line.startswith("level up")] == [f"level up level={reached}"]
    assert lines.count(f"rest start ticks={expected}") == 1


def test_with_no_level_up_the_same_book_rests_as_before_and_a_rest_of_0_adds_nothing() -> None:
    assert NO_LEVEL_UP.rest_ticks == 0
    assert start_waves(climb_book(), 2).level_up_rules is NO_LEVEL_UP
    for extra in (0, 3):
        book: WaveBook = climb_book(extra_rest=extra)
        default: list[WaveRun] = run_for(book, 16)
        off: list[WaveRun] = run_for(book, 16, rules=NO_LEVEL_UP)
        zero: list[WaveRun] = run_for(book, 16, rules=rules_of(0))
        assert off == default
        assert [replace(state, level_up_rules=NO_LEVEL_UP) for state in zero] == default
        # The rise on tick 2 rests the wave's extra rest alone (the gap is 0), and with none,
        # `a` of Level 2 starts on the rise tick itself.
        rise: WaveRun = default[1]
        assert (rise.level, rise.level_rose) == (2, True)
        assert rise.resting is (extra > 0)
        assert rise.rest_ticks_left == extra
        if extra == 0:
            assert rise.current_wave_id == "a"
            assert rise.start_px == STEP_PX * 2
        else:
            assert len(rest_run(default, 1)) == extra


def test_level_rose_is_true_on_the_rise_state_alone_and_false_on_every_other_state() -> None:
    rest: int = 4
    book: WaveBook = book_of(
        [wave(WAVE_ZERO), wave("a", extra_rest=1), wave("b"), wave("p", pool=True)],
        {
            1: LevelPlaylist(fixed=("a", "b")),
            2: LevelPlaylist(fixed=("b",)),
            3: LevelPlaylist(fixed=("a",)),
        },
    )
    for rules in (rules_of(rest), NO_LEVEL_UP):
        states: list[WaveRun] = run_for(book, 40, rules=rules)
        rises: list[int] = rise_indexes(states)
        assert len(rises) >= 2
        flagged: list[int] = [i for i, state in enumerate(states) if state.level_rose]
        assert flagged == rises
        for index in rises:
            # On every state of the rest after the rise state, the flag is False. With no level-up
            # rest a rise can be followed at once by a wave that ends in another rise next tick.
            for state in rest_run(states, index)[1:]:
                assert state.level_rose is False
            if rules.rest_ticks > 0:
                assert not states[index + 1].level_rose
        # Wave ends with no rise (Wave 0, the first `a`) never raise it.
        assert states[0].level_rose is False
        assert states[1].level_rose is False

    # A rise with no rest after it (no level-up rest, no extra rest) is flagged too.
    states = run_for(climb_book(), 6, rules=NO_LEVEL_UP)
    assert (states[1].level, states[1].level_rose, states[1].resting) == (2, True, False)
    assert states[1].current_wave_id == "a"

    # One long step ends Wave 0, `a` (a rise), then `a` again of Level 2 (a rise) and more, with no
    # rest between them (no rest anywhere). A flag set by 3.1 stays set to the end of the call.
    climb: WaveBook = climb_book()
    jumped: WaveRun = step_waves(start_waves(climb, 2), 1000.0)
    assert jumped.level == LAST_LEVEL
    assert jumped.level_rose is True
    # A call that ends waves with no rise leaves it False.
    plain: WaveBook = book_of(
        [wave(WAVE_ZERO), wave("a"), wave("b")], {1: LevelPlaylist(fixed=("a", "a", "a", "b"))}
    )
    flat: WaveRun = step_waves(start_waves(plain, 2, rules_of(5)), 35.0)
    assert (flat.level, flat.level_rose, flat.resting) == (1, False, False)
    assert flat.current_wave_id == "a"
    # The call after a flagged one clears it.
    assert step_waves(jumped, 1010.0).level_rose is False


def test_next_run_waves_keeps_the_rules_and_starts_a_clean_run_from_the_next_seed() -> None:
    rest: int = 5
    rules: LevelUpRules = rules_of(rest)
    book: WaveBook = climb_book()
    seed: int = 9
    state: WaveRun = start_waves(book, seed, rules)
    for tick in (1, 2):
        state = step_waves(state, STEP_PX * tick)
    assert state.level_rose is True
    nxt: WaveRun = next_run_waves(state)
    expected_seed: int = random.Random(seed).getrandbits(64)
    assert nxt == start_waves(book, expected_seed, rules)
    assert nxt.level_up_rules == rules
    assert (nxt.level, nxt.level_rose, nxt.resting, nxt.pick_seed, nxt.run_seed) == (
        1,
        False,
        False,
        expected_seed,
        expected_seed,
    )
    # The next run rests the same way: the rise on its tick 2 rests 5.
    after: list[WaveRun] = []
    for tick in (1, 2):
        nxt = step_waves(nxt, STEP_PX * tick)
        after.append(nxt)
    assert (after[1].level, after[1].level_rose, after[1].rest_ticks_left) == (2, True, rest)
    # With no rules given, the next run has none either.
    assert next_run_waves(start_waves(book, seed)).level_up_rules is NO_LEVEL_UP


def test_the_banner_starts_at_age_0_and_ages_a_tick_a_step_until_it_reaches_the_lifetime() -> None:
    rules: LevelUpRules = LevelUpRules(rest_ticks=20, arrival_ticks=3, banner_ticks=6)
    banner: LevelUpBanner = start_level_up(rules, 2, 4)
    assert (banner.level, banner.previous_level) == (4, 2)
    assert (banner.arrival_ticks, banner.lifetime_ticks, banner.age_ticks) == (3, 6, 0)

    ages: list[int] = []
    current: LevelUpBanner | None = banner
    while current is not None:
        ages.append(current.age_ticks)
        assert (current.level, current.previous_level) == (4, 2)
        assert (current.arrival_ticks, current.lifetime_ticks) == (3, 6)
        before: LevelUpBanner = current
        current = step_level_up(current)
        assert before.age_ticks == ages[-1]  # the old banner is never changed
        assert len(ages) <= 6
    assert ages == [0, 1, 2, 3, 4, 5]
    # The step from age 5 (lifetime - 1) is the one that returns None.
    assert step_level_up(replace(banner, age_ticks=4)) == replace(banner, age_ticks=5)
    assert step_level_up(replace(banner, age_ticks=5)) is None
    # The smallest legal banner (arrival 1, lifetime 2) lives on ages 0 and 1.
    small: LevelUpBanner = start_level_up(rules_of(2), 1, 2)
    after_small: LevelUpBanner | None = step_level_up(small)
    assert after_small is not None
    assert after_small.age_ticks == 1
    assert step_level_up(after_small) is None


def test_shown_level_is_the_previous_level_below_the_arrival_age_and_the_real_level_from_it() -> (
    None
):
    rules: LevelUpRules = LevelUpRules(rest_ticks=20, arrival_ticks=3, banner_ticks=6)
    banner: LevelUpBanner = start_level_up(rules, 2, 4)
    # A skipped level: the HUD keeps 2 until age 3, then shows the real level 4.
    shown: list[int] = [shown_level(replace(banner, age_ticks=age), 4) for age in range(6)]
    assert shown == [2, 2, 2, 4, 4, 4]
    assert shown_level(None, 4) == 4
    for level in range(1, LAST_LEVEL + 1):
        assert shown_level(None, level) == level
    # An arrival age of 1 switches on the first step.
    quick: LevelUpBanner = start_level_up(rules_of(2), 7, 8)
    assert shown_level(quick, 8) == 7
    assert shown_level(replace(quick, age_ticks=1), 8) == 8
