"""The wave state, the wave clock, the playlist runner and the random picker.

Contract: docs/contracts/systems/waves.md, Diagram (the order of one run, the one-tick flowchart,
starting the next wave, the rest gap timeline), Interface (`game/core/waves.py`), Rules (Values,
The order, The wave clock, Starting a wave, Random picks, Seeds, The rest gap, Logging, Other
rules). Task: docs/contracts/DRA-76/tasks/DRA-76-07-qa-engineer.md. One test per behavior it
lists. The books, waves and placements are built here in code from the contract's rules, never
read from game/waves/ or game/tuning/, and no expected number is imported from the code under
test. A placement is told apart by its `x`, which each test sets to a number it can read back.
"""

import logging
import random
from collections.abc import Iterable, Sequence
from itertools import pairwise

import pytest

from core.drifters.base import DrifterType
from core.drifters.spawner import Placement
from core.waves import (
    LevelPlaylist,
    Wave,
    WaveBook,
    WaveKind,
    WavePlacement,
    WaveRun,
    next_run_waves,
    pick_pool_wave,
    rest_gap_ticks,
    start_waves,
    step_waves,
)

LAST_LEVEL: int = 8
"""Source: 08-difficulty.md, rule 1 (Level 8 is the last; no Level 9)."""

SEED_BITS: int = 64
"""Bits of the next seed. Source: waves.md, Interface (`getrandbits(64)`)."""

WAVES_LOGGER: str = "core.waves"
"""Logger name. Source: waves.md, Rules, Logging."""

WAVE_ZERO: str = "w0"
"""Id of Wave 0 in the books built here."""

MICRO_PX: float = 1e-6
"""A distance within this of a trigger counts as reached. Source: waves.md, Rationale (distances
are rounded to 6 decimals before a comparison)."""


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


def pool(wave_id: str, length: float = 10.0, *, min_level: int = 1, extra_rest: int = 0) -> Wave:
    """Build a pool wave with no placements."""
    return wave(wave_id, length, kind=WaveKind.POOL, min_level=min_level, extra_rest=extra_rest)


def book_of(
    waves: Iterable[Wave],
    levels: Sequence[LevelPlaylist] = (),
    *,
    zero: str = WAVE_ZERO,
) -> WaveBook:
    """Build a book. `levels` is Level 1 first; the levels it leaves out have no slots."""
    playlists: tuple[LevelPlaylist, ...] = (
        *levels,
        *(LevelPlaylist() for _ in range(LAST_LEVEL - len(levels))),
    )
    return WaveBook(
        waves={item.wave_id: item for item in waves}, wave_zero_id=zero, playlists=playlists
    )


def xs(state: WaveRun) -> tuple[float | None, ...]:
    """The x of every placement due on the last tick, in order."""
    return tuple(placement.x for placement in state.spawns_due)


def walk(state: WaveRun, distances: Iterable[float]) -> list[WaveRun]:
    """Step the waves once per distance and return the state after each tick."""
    states: list[WaveRun] = []
    for distance in distances:
        state = step_waves(state, distance)
        states.append(state)
    return states


def every(step: float, ticks: int) -> list[float]:
    """The distance after each of `ticks` ticks of `step` px (whole numbers, so exact)."""
    return [step * tick for tick in range(1, ticks + 1)]


def messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Every core.waves line so far."""
    return [record.getMessage() for record in caplog.records if record.name == WAVES_LOGGER]


def one_wave_a_tick(*, pool_ids: Sequence[str] = ("p", "q")) -> WaveBook:
    """A book where every wave is 10 px long, so at 10 px a tick one wave ends on every tick.

    Wave 0 is `w0`. Level 1: fixed `a`, `b`, `a`, then 2 random. Level 2: fixed `b`. Levels 3 to
    8: fixed `a`. Pool waves `pool_ids` at min level 1.
    """
    waves: list[Wave] = [wave(WAVE_ZERO, 10.0), wave("a", 10.0), wave("b", 10.0)]
    waves.extend(pool(wave_id) for wave_id in pool_ids)
    levels: list[LevelPlaylist] = [
        LevelPlaylist(fixed=("a", "b", "a"), random_count=2),
        LevelPlaylist(fixed=("b",)),
        *(LevelPlaylist(fixed=("a",)) for _ in range(3, LAST_LEVEL + 1)),
    ]
    return book_of(waves, levels)


def test_start_waves_gives_wave_0_at_level_1_from_0_px_with_nothing_due_and_logs_its_start(
    caplog: pytest.LogCaptureFixture,
) -> None:
    book: WaveBook = book_of(
        [wave(WAVE_ZERO, 100.0, triggers=[0.0]), wave("a", 10.0)],
        [LevelPlaylist(fixed=("a",))],
    )
    caplog.set_level(logging.DEBUG, logger=WAVES_LOGGER)

    state: WaveRun = start_waves(book, 4242)

    assert state.book is book
    assert state.level == 1
    assert state.next_slot == 0
    assert state.wave_id == WAVE_ZERO
    assert state.current_wave_id == WAVE_ZERO
    assert state.start_px == 0.0
    assert state.spawned == 0
    assert state.resting is False
    assert state.rest_ticks_left == 0
    assert state.pick_seed == 4242
    assert state.run_seed == 4242
    assert state.spawns_due == ()
    assert messages(caplog) == ["wave start id=w0 level=1 random=False"]


def test_a_placement_is_due_once_on_the_first_tick_its_trigger_is_reached_in_trigger_order() -> (
    None
):
    triggers: list[float] = [0.0, 10.0, 10.0, 25.0, 40.0, 50.0, 1500.0]
    book: WaveBook = book_of(
        [wave(WAVE_ZERO, 1000.0, triggers=triggers), wave("a", 10.0)],
        [LevelPlaylist(fixed=("a",))],
    )
    # Per tick: the distance after it and the x of what comes due. Trigger 0 is due on tick 1.
    # Two triggers of 10 come together, in order. 25 is passed between two ticks and comes on the
    # one after. 40 is reached within a micro-px (round to 6 decimals), 50 is 1e-5 short: not yet.
    script: list[tuple[float, tuple[float, ...]]] = [
        (1.1, (0.0,)),
        (9.9, ()),
        (10.0, (1.0, 2.0)),
        (10.0, ()),
        (24.9, ()),
        (26.0, (3.0,)),
        (40.0 - 0.4 * MICRO_PX, (4.0,)),
        (50.0 - 10 * MICRO_PX, ()),
        (50.0, (5.0,)),
        (60.0, ()),
        (500.0, ()),
        (999.0, ()),
    ]
    state: WaveRun = start_waves(book, 1)
    due_ever: list[float | None] = []
    for distance, expected in script:
        state = step_waves(state, distance)
        assert xs(state) == expected, distance
        assert state.wave_id == WAVE_ZERO
        due_ever.extend(xs(state))

    assert due_ever == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    assert state.spawned == 6

    # The trigger at 1500 is beyond the wave's length 1000: the wave ends, it never comes.
    state = step_waves(state, 1000.0)
    assert state.wave_id == "a"
    assert 6.0 not in xs(state)
    assert state.spawned == 0


def test_a_wave_ends_on_the_tick_its_distance_reaches_its_length_a_micro_px_short_counts() -> None:
    book: WaveBook = book_of(
        [wave(WAVE_ZERO, 100.0, triggers=[100.0, 150.0]), wave("a", 100.0)],
        [LevelPlaylist(fixed=("a",))],
    )
    ids: list[str | None] = [s.current_wave_id for s in walk(start_waves(book, 1), every(10.0, 9))]
    assert ids == [WAVE_ZERO] * 9

    state: WaveRun = start_waves(book, 1)
    for distance in every(10.0, 9):
        state = step_waves(state, distance)
    state = step_waves(state, 100.0)
    # The trigger at exactly the length is due on the ending tick; the one at 150 never is.
    assert xs(state) == (0.0,)
    assert state.wave_id == "a"
    assert state.start_px == 100.0
    assert state.spawned == 0

    # A micro-px short of the length ends it too; 1e-5 short does not.
    base: WaveRun = start_waves(book, 1)
    assert step_waves(base, 100.0 - 0.4 * MICRO_PX).wave_id == "a"
    assert step_waves(base, 100.0 - 10 * MICRO_PX).wave_id == WAVE_ZERO


def test_with_no_rest_the_next_wave_starts_where_the_last_ended_with_its_due_placements() -> None:
    book: WaveBook = book_of(
        [
            wave(WAVE_ZERO, 100.0),
            wave("a", 50.0, triggers=[0.0, 20.0, 45.0], x0=10.0),
            wave("b", 50.0, triggers=[0.0, 10.0], x0=20.0),
            wave("c", 50.0, triggers=[0.0], x0=30.0),
        ],
        [LevelPlaylist(fixed=("a", "b")), LevelPlaylist(fixed=("c",))],
    )
    state: WaveRun = start_waves(book, 1)

    state = step_waves(state, 99.0)
    assert state.wave_id == WAVE_ZERO
    assert state.spawns_due == ()

    # Wave 0 ends at 100, partway through this tick's scroll. `a` starts at 100, not at 140, and
    # the 40 px it is already into it bring 0 and 20 due on this very tick.
    state = step_waves(state, 140.0)
    assert state.wave_id == "a"
    assert state.start_px == 100.0
    assert xs(state) == (10.0, 11.0)
    assert state.spawned == 2

    # `a` ends (45 comes first), `b` starts at 150 and ends at once (50 px into it), the level
    # rises, and `c` starts at 200: all on tick 3, the due placements in order.
    state = step_waves(state, 200.0)
    assert xs(state) == (12.0, 20.0, 21.0, 30.0)
    assert state.wave_id == "c"
    assert state.level == 2
    assert state.start_px == 200.0
    assert state.resting is False
    assert state.rest_ticks_left == 0


def test_several_waves_can_end_on_one_tick_each_starting_where_the_last_ended() -> None:
    book: WaveBook = book_of(
        [
            wave(WAVE_ZERO, 100.0, triggers=[0.0], x0=1.0),
            wave("a", 10.0, triggers=[0.0, 5.0], x0=10.0),
            wave("b", 10.0, triggers=[0.0], x0=20.0),
            wave("c", 10.0, triggers=[0.0, 9.0], x0=30.0),
            wave("d", 10.0, triggers=[0.0, 5.0, 8.0], x0=40.0),
        ],
        [LevelPlaylist(fixed=("a", "b", "c", "d"))],
    )
    state: WaveRun = start_waves(book, 1)
    state = step_waves(state, 99.0)
    assert xs(state) == (1.0,)

    # Wave 0 ends at 100 and `a`, `b` and `c` end at 110, 120 and 130 on the same tick: `d`, which
    # began at 130, is 5 px in and is the one playing.
    state = step_waves(state, 135.0)
    assert xs(state) == (10.0, 11.0, 20.0, 30.0, 31.0, 40.0, 41.0)
    assert state.wave_id == "d"
    assert state.start_px == 130.0
    assert state.next_slot == 4
    assert state.spawned == 2
    assert state.level == 1


def test_fixed_waves_play_in_playlist_order_then_the_random_slots_wave_0_is_no_slot() -> None:
    book: WaveBook = one_wave_a_tick()
    states: list[WaveRun] = walk(start_waves(book, 9), every(10.0, 30))
    ids: list[str | None] = [state.current_wave_id for state in states]

    # Tick 1: Wave 0 ends and the first slot of Level 1 starts: `a`, then `b`, then `a` again.
    assert ids[0:3] == ["a", "b", "a"]
    assert [state.next_slot for state in states[0:3]] == [1, 2, 3]
    # The two random slots.
    assert ids[3] in {"p", "q"}
    assert ids[4] in {"p", "q"}
    assert [state.next_slot for state in states[3:5]] == [4, 5]
    # Level 2's playlist, then each of Levels 3 to 8 plays its one `a`.
    assert ids[5] == "b"
    assert ids[6:12] == ["a"] * 6
    assert [state.level for state in states[:13]] == [1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 7, 8, 8]
    # After Level 8's playlist only random picks play.
    assert all(wave_id in {"p", "q"} for wave_id in ids[12:])


def test_the_level_rises_on_the_tick_the_last_wave_of_its_playlist_ends_never_inside_a_wave(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Every wave is 30 px; at 10 px a tick one wave ends every third tick (3, 6, 9, ...).
    book: WaveBook = book_of(
        [wave(WAVE_ZERO, 30.0), wave("a", 30.0), wave("b", 30.0), pool("p", 30.0)],
        [
            LevelPlaylist(fixed=("a", "b")),
            *(LevelPlaylist(fixed=("a",)) for _ in range(2, LAST_LEVEL)),
        ],
    )
    caplog.set_level(logging.DEBUG, logger=WAVES_LOGGER)
    states: list[WaveRun] = walk(start_waves(book, 5), every(10.0, 45))

    # Wave 0 (tick 3 ends it), `a` (tick 6) and `b` (tick 9) fill Level 1: Level 2 starts on tick 9.
    for tick, state in enumerate(states, start=1):
        expected_level: int = 1 if tick < 9 else min(LAST_LEVEL, 2 + (tick - 9) // 3)
        assert state.level == expected_level, tick
    assert states[8].wave_id == "a"
    assert states[8].level == 2
    assert states[5].wave_id == "b"
    assert states[5].level == 1
    # Once per rise, with the new level, and none at Level 8.
    ups: list[str] = [line for line in messages(caplog) if line.startswith("level up")]
    assert ups == [f"level up level={level}" for level in range(2, LAST_LEVEL + 1)]


def test_a_level_with_no_slots_is_passed_on_the_tick_it_starts() -> None:
    book: WaveBook = book_of(
        [wave(WAVE_ZERO, 10.0), wave("a", 10.0), pool("p")],
        [
            LevelPlaylist(fixed=("a",)),
            LevelPlaylist(),
            LevelPlaylist(),
            LevelPlaylist(fixed=("a",)),
        ],
    )
    states: list[WaveRun] = walk(start_waves(book, 3), every(10.0, 6))
    # Tick 1: Wave 0 ends, `a` starts at Level 1. Tick 2: it ends, Levels 2 and 3 are empty and
    # passed, Level 4's `a` starts. Tick 3: it ends, Levels 5 to 8 are empty: Level 8 at once and a
    # random pick.
    assert [(state.level, state.current_wave_id) for state in states[:3]] == [
        (1, "a"),
        (4, "a"),
        (8, "p"),
    ]
    assert [state.next_slot for state in states[:3]] == [1, 1, 0]
    assert all(state.level == LAST_LEVEL for state in states[2:])


def test_at_level_8_the_level_never_rises_and_random_picks_go_on_forever(
    caplog: pytest.LogCaptureFixture,
) -> None:
    book: WaveBook = book_of(
        [wave(WAVE_ZERO, 10.0), wave("a", 10.0), pool("p"), pool("q")],
        [
            LevelPlaylist(fixed=("a",)),
            *(LevelPlaylist() for _ in range(2, LAST_LEVEL)),
            LevelPlaylist(fixed=("a",), random_count=1),
        ],
    )
    caplog.set_level(logging.DEBUG, logger=WAVES_LOGGER)
    states: list[WaveRun] = walk(start_waves(book, 8), every(10.0, 200))
    ids: list[str | None] = [state.current_wave_id for state in states]

    # Tick 1: `a` at Level 1. Tick 2: Level 8's `a`. Tick 3: its one random slot. Then only picks.
    assert ids[0:2] == ["a", "a"]
    assert [state.level for state in states[1:]] == [LAST_LEVEL] * 199
    assert all(wave_id in {"p", "q"} for wave_id in ids[2:])
    assert set(ids[2:]) == {"p", "q"}
    # No slot is left, and none is counted again.
    assert all(state.next_slot == 2 for state in states[2:])
    # One level up, to 8, and no more.
    assert [line for line in messages(caplog) if line.startswith("level up")] == [
        "level up level=8"
    ]


def test_a_random_pick_is_a_pool_wave_allowed_at_the_level_and_never_the_one_that_just_played() -> (
    None
):
    levels: list[LevelPlaylist] = [LevelPlaylist(fixed=("p1",), random_count=1)]
    waves: list[Wave] = [
        wave(WAVE_ZERO, 10.0),
        pool("p1"),
        pool("p2"),
        pool("p3", min_level=3),
        pool("p4", min_level=5),
        wave("f", 10.0),
    ]
    book: WaveBook = book_of(waves, levels)

    # The picker alone: at Level 1 the candidates are p1 and p2, whichever p3 and p4 say.
    for seed in range(40):
        assert pick_pool_wave(book, 1, "p1", random.Random(seed)) == "p2"
        assert pick_pool_wave(book, 1, "p2", random.Random(seed)) == "p1"
    # A wave that is not a candidate (Wave 0, a fixed wave) leaves every candidate open.
    for last in (WAVE_ZERO, "f"):
        picks: set[str] = {pick_pool_wave(book, 1, last, random.Random(s)) for s in range(40)}
        assert picks == {"p1", "p2"}
    # min_level 3 and 5 open at Levels 3 and 5, never before.
    for level, allowed in ((2, {"p1", "p2"}), (3, {"p1", "p2", "p3"}), (4, {"p1", "p2", "p3"})):
        seen: set[str] = {pick_pool_wave(book, level, "f", random.Random(s)) for s in range(80)}
        assert seen == allowed
    seen_8: set[str] = {pick_pool_wave(book, 8, "f", random.Random(s)) for s in range(120)}
    assert seen_8 == {"p1", "p2", "p3", "p4"}
    for level in (3, 8):
        for seed in range(40):
            assert pick_pool_wave(book, level, "p3", random.Random(seed)) != "p3"

    # The only allowed wave plays again, even right after itself.
    lone: WaveBook = book_of(
        [wave(WAVE_ZERO, 10.0), pool("solo", min_level=2), pool("late", min_level=6)]
    )
    for seed in range(10):
        assert pick_pool_wave(lone, 2, "solo", random.Random(seed)) == "solo"
        assert pick_pool_wave(lone, 5, "solo", random.Random(seed)) == "solo"


def started(states: Iterable[WaveRun], first: str = WAVE_ZERO) -> list[str]:
    """The ids of the waves that started, in order: a new wave is a new `start_px` (or `first`)."""
    ids: list[str] = [first]
    last_start: float = 0.0
    for state in states:
        if not state.resting and state.start_px != last_start:
            ids.append(state.wave_id)
            last_start = state.start_px
    return ids


def test_a_random_slot_never_repeats_the_last_wave_after_zero_fixed_rest_or_rise() -> None:
    for seed in range(60):
        # After Wave 0, here a pool wave that is a candidate: it is left out.
        zero_pool: WaveBook = book_of(
            [pool(WAVE_ZERO), pool("p"), pool("q")], [LevelPlaylist(random_count=1)]
        )
        after_zero: WaveRun = step_waves(start_waves(zero_pool, seed), 10.0)
        assert after_zero.wave_id in {"p", "q"}

        # After a fixed wave: a pool wave named in the playlist, then one random slot. Only `q`
        # is left to follow `p`.
        after_fixed: WaveBook = book_of(
            [wave(WAVE_ZERO, 10.0), pool("p"), pool("q")],
            [LevelPlaylist(fixed=("p",), random_count=1)],
        )
        states: list[WaveRun] = walk(start_waves(after_fixed, seed), every(10.0, 2))
        assert [state.wave_id for state in states] == ["p", "q"]

        # After random picks in a row, three pool waves.
        three: list[Wave] = [wave(WAVE_ZERO, 10.0), pool("p"), pool("q"), pool("r")]
        in_a_row: WaveBook = book_of(three, [LevelPlaylist(random_count=12)])
        played: list[str] = started(walk(start_waves(in_a_row, seed), every(10.0, 12)))
        assert len(played) == 13
        assert all(left != right for left, right in pairwise(played))

        # After a rest: the rest keeps the wave that ended, and the pick still leaves it out.
        resting: WaveBook = book_of(
            [wave(WAVE_ZERO, 10.0), pool("p", extra_rest=2), pool("q", extra_rest=2)],
            [LevelPlaylist(random_count=8)],
        )
        played = started(walk(start_waves(resting, seed), every(10.0, 30)))
        assert len(played) > 6
        assert all(left != right for left, right in pairwise(played))

        # After a level rise: each of the eight levels has one random slot, then Level 8 goes on.
        rising: WaveBook = book_of(
            [wave(WAVE_ZERO, 10.0), pool("p"), pool("q")],
            [LevelPlaylist(random_count=1) for _ in range(LAST_LEVEL)],
        )
        rise_states: list[WaveRun] = walk(start_waves(rising, seed), every(10.0, 14))
        played = started(rise_states)
        assert len(played) == 15
        assert [state.level for state in rise_states][:9] == [1, 2, 3, 4, 5, 6, 7, 8, 8]
        assert all(left != right for left, right in pairwise(played))


@pytest.mark.determinism
def test_the_same_seed_gives_the_same_waves_and_next_run_waves_restarts_with_a_new_seed() -> None:
    book: WaveBook = book_of(
        [
            wave(WAVE_ZERO, 25.0, triggers=[0.0, 12.0]),
            wave("a", 15.0, triggers=[3.0]),
            pool("p1", 12.0),
            pool("p2", 17.0, extra_rest=1),
            pool("p3", 9.0),
            pool("p4", 21.0),
            pool("p5", 8.0),
        ],
        [
            LevelPlaylist(fixed=("a",), random_count=2),
            *(LevelPlaylist(random_count=2) for _ in range(2, LAST_LEVEL + 1)),
        ],
    )
    distances: list[float] = every(5.0, 300)

    first: list[WaveRun] = walk(start_waves(book, 77), distances)
    again: list[WaveRun] = walk(start_waves(book, 77), distances)
    assert first == again

    # A different seed gives another order over many picks among five pool waves.
    other: list[WaveRun] = walk(start_waves(book, 78), distances)
    picks = [s.wave_id for s in first if not s.resting]
    other_picks = [s.wave_id for s in other if not s.resting]
    assert picks != other_picks

    # The next run: Wave 0 at Level 1 from 0 px, with a seed drawn from this run's seed.
    expected_seed: int = random.Random(77).getrandbits(SEED_BITS)
    nxt: WaveRun = next_run_waves(first[-1])
    assert nxt == start_waves(book, expected_seed)
    assert nxt.level == 1
    assert nxt.wave_id == WAVE_ZERO
    assert nxt.start_px == 0.0
    assert nxt.next_slot == 0
    assert nxt.run_seed == expected_seed
    assert nxt.run_seed != 77
    assert next_run_waves(first[0]) == nxt  # whatever the tick, the run's seed alone decides it
    # Every run after the first has a new seed and so new picks.
    third: WaveRun = next_run_waves(nxt)
    assert len({77, nxt.run_seed, third.run_seed}) == 3
    run_two: list[WaveRun] = walk(nxt, distances)
    run_three: list[WaveRun] = walk(third, distances)
    assert [s.wave_id for s in run_two] != [s.wave_id for s in first]
    assert [s.wave_id for s in run_two] != [s.wave_id for s in run_three]


def test_a_random_pick_starts_from_pick_seed_and_stores_the_next_seed_it_draws() -> None:
    book: WaveBook = book_of(
        [wave(WAVE_ZERO, 10.0), pool("p1"), pool("p2"), pool("p3")],
        [LevelPlaylist(random_count=3)],
    )
    state: WaveRun = start_waves(book, 31)
    replay: random.Random = random.Random(31)
    expected_first: str = replay.choice(["p1", "p2", "p3"])
    assert expected_first in {"p1", "p2", "p3"}

    # Tick 1: Wave 0 ends and the first random slot starts. Wave 0 is no candidate here, so all
    # three are open; the pick is the chooser's choice and the seed after it is its next 64 bits.
    state = step_waves(state, 10.0)
    assert state.wave_id == expected_first
    assert state.pick_seed == replay.getrandbits(SEED_BITS)
    assert state.run_seed == 31

    # The next pick leaves out the wave that played and starts from the stored seed.
    stored: int = state.pick_seed
    chooser: random.Random = random.Random(stored)
    others: list[str] = [wave_id for wave_id in ("p1", "p2", "p3") if wave_id != expected_first]
    expected_second: str = chooser.choice(others)
    state = step_waves(state, 20.0)
    assert state.wave_id == expected_second
    assert state.pick_seed == chooser.getrandbits(SEED_BITS)


def test_pick_pool_wave_draws_from_the_chooser_it_is_given_only() -> None:
    ids: tuple[str, ...] = ("p1", "p2", "p3", "p4", "p5")
    book: WaveBook = book_of([wave(WAVE_ZERO, 10.0), *(pool(wave_id) for wave_id in ids)])
    # The same book built in the opposite order: the picks must not depend on it.
    reversed_book: WaveBook = book_of(
        [*(pool(wave_id) for wave_id in reversed(ids)), wave(WAVE_ZERO, 10.0)]
    )

    random.seed(2024)
    global_before: tuple[object, ...] = random.getstate()
    for seed in range(30):
        chooser: random.Random = random.Random(seed)
        before: tuple[object, ...] = chooser.getstate()
        picked: str = pick_pool_wave(book, 1, WAVE_ZERO, chooser)
        # Exactly the draw of one `choice` over the candidates sorted by id.
        assert picked == random.Random(seed).choice(list(ids))
        assert pick_pool_wave(reversed_book, 1, WAVE_ZERO, random.Random(seed)) == picked
        assert chooser.getstate() != before
        assert chooser.getstate() == _state_after_choice(seed, ids)
        # The same seed, the same pick.
        assert pick_pool_wave(book, 1, WAVE_ZERO, random.Random(seed)) == picked
    assert random.getstate() == global_before

    # Left out candidate: the draw is over the others, still sorted by id.
    assert pick_pool_wave(book, 1, "p3", random.Random(5)) == random.Random(5).choice(
        ["p1", "p2", "p4", "p5"]
    )


def _state_after_choice(seed: int, ids: Sequence[str]) -> tuple[object, ...]:
    """The state of a generator seeded with `seed` after one `choice` over `ids`."""
    chooser: random.Random = random.Random(seed)
    chooser.choice(list(ids))
    return chooser.getstate()


def test_rest_gap_ticks_is_the_extra_rest_alone_at_every_level_while_the_base_is_0() -> None:
    for level in range(1, LAST_LEVEL + 1):
        for extra in (0, 1, 2, 5, 40):
            assert rest_gap_ticks(level, extra) == extra, (level, extra)


def test_a_rest_of_r_ticks_shows_on_exactly_r_states_and_the_next_wave_starts_after_it() -> None:
    for rest in (1, 2, 3, 6):
        book: WaveBook = book_of(
            [
                wave(WAVE_ZERO, 100.0, extra_rest=rest),
                wave("a", 100.0, triggers=[0.0, 5.0, 50.0], x0=10.0),
                pool("p", 1000.0),
            ],
            [LevelPlaylist(fixed=("a",))],
        )
        distances: list[float] = every(7.0, 40)
        states: list[WaveRun] = walk(start_waves(book, 2), distances)
        # 7 px a tick: tick 15 (105 px) ends Wave 0, past its length by 5 px.
        end: int = 15
        for tick in range(1, end):
            assert states[tick - 1].wave_id == WAVE_ZERO
            assert states[tick - 1].resting is False

        resting_ticks: list[int] = [t for t in range(1, 41) if states[t - 1].resting]
        assert resting_ticks == list(range(end, end + rest)), rest
        for offset, tick in enumerate(resting_ticks):
            state: WaveRun = states[tick - 1]
            assert state.rest_ticks_left == rest - offset
            assert state.current_wave_id is None
            assert state.wave_id == WAVE_ZERO  # the wave that just ended
            assert state.spawns_due == ()

        # The rest ends on tick end + rest: `a` starts at that tick's distance, not at 100 or the
        # distance after the end tick, and its trigger 0 is due right then.
        began: WaveRun = states[end + rest - 1]
        assert began.resting is False
        assert began.rest_ticks_left == 0
        assert began.current_wave_id == "a"
        assert began.start_px == distances[end + rest - 1]
        assert xs(began) == (10.0,)
        # 5 px later the next trigger is due, once.
        later: WaveRun = states[end + rest]
        assert xs(later) == (11.0,)
        assert states[end + rest + 1].spawns_due == ()


def test_no_extra_rest_leaves_no_rest_and_the_extra_rest_is_the_same_at_every_level() -> None:
    book: WaveBook = book_of(
        [
            wave(WAVE_ZERO, 10.0),
            wave("a", 10.0, extra_rest=2),
            wave("b", 10.0),
            pool("p", 1000.0),
        ],
        [LevelPlaylist(fixed=("a",)), LevelPlaylist(fixed=("b", "a", "b"))],
    )
    states: list[WaveRun] = walk(start_waves(book, 2), every(10.0, 12))
    # Tick 1: Wave 0 (no extra rest) ends and `a` starts with no rest. Tick 2: `a` ends at Level 1
    # and the level rises to 2 on that tick: 2 ticks of rest follow, shown on ticks 2 and 3.
    assert (states[0].resting, states[0].current_wave_id) == (False, "a")
    assert [(s.resting, s.rest_ticks_left) for s in states[1:3]] == [(True, 2), (True, 1)]
    assert states[1].level == 2
    assert states[3].current_wave_id == "b"
    assert states[3].start_px == 40.0
    # `b` has no extra rest: no rest after it. Then `a` at Level 2 rests 2 ticks again.
    assert states[4].current_wave_id == "a"
    assert states[4].resting is False
    assert [s.resting for s in states[5:8]] == [True, True, False]
    assert states[7].current_wave_id == "b"


def test_the_waves_log_each_event_once_in_the_contracts_order_and_nothing_on_a_quiet_tick(
    caplog: pytest.LogCaptureFixture,
) -> None:
    book: WaveBook = book_of(
        [
            wave(WAVE_ZERO, 10.0, triggers=[0.0, 4.0]),
            wave("a", 10.0, extra_rest=2),
            wave("b", 10.0),
            pool("p", 10.0),
        ],
        [LevelPlaylist(fixed=("a",)), LevelPlaylist(fixed=("b",), random_count=1)],
    )
    caplog.set_level(logging.DEBUG, logger=WAVES_LOGGER)
    state: WaveRun = start_waves(book, 6)
    seen: int = len(messages(caplog))

    def tick(distance: float) -> list[str]:
        nonlocal state, seen
        state = step_waves(state, distance)
        lines: list[str] = messages(caplog)
        new: list[str] = lines[seen:]
        seen = len(lines)
        return new

    assert messages(caplog) == ["wave start id=w0 level=1 random=False"]
    # Placements coming due is no event.
    assert tick(5.0) == []
    assert xs(state) == (0.0, 1.0)
    # Wave 0 ends, `a` starts.
    assert tick(10.0) == ["wave end id=w0", "wave start id=a level=1 random=False"]
    assert tick(15.0) == []
    # `a` ends and fills Level 1: Level 2, then a rest of 2 ticks.
    assert tick(20.0) == ["wave end id=a", "level up level=2", "rest start ticks=2"]
    # The countdown logs nothing.
    assert tick(25.0) == []
    # The rest ends: `b` starts, at Level 2 and not random.
    assert tick(30.0) == ["wave start id=b level=2 random=False"]
    # `b` ends and the next slot is random.
    assert tick(40.0) == ["wave end id=b", "wave start id=p level=2 random=True"]
    # Two waves end on one tick. `p` ends and fills Level 2; Levels 3 to 8 have no slots, so one
    # rise takes the level to 8. The next wave is a random pick, 10 px long, and it ends too.
    assert tick(65.0) == [
        "wave end id=p",
        "level up level=8",
        "wave start id=p level=8 random=True",
        "wave end id=p",
        "wave start id=p level=8 random=True",
    ]
    assert tick(69.0) == []
