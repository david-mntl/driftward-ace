"""World scroll and distance tests. Contract: docs/contracts/systems/scroll.md, Rules.

Task: docs/contracts/DRA-13/tasks/DRA-13-04-qa-engineer.md. One test per behavior it lists.
`scroll_step_px` (DRA-62): docs/contracts/DRA-62/tasks/DRA-62-06-qa-engineer.md.
The speed per level (DRA-76): docs/contracts/DRA-76/tasks/DRA-76-02-qa-engineer.md.
Every expected number is computed from the GDD values below, never typed in as a result.
"""

import logging
import math
from fractions import Fraction

import pytest

from core.scroll import Scroll, scroll_speed, scroll_step_px, start_scroll, step_scroll

SCROLL_BASE = Fraction("1.1")
"""px/tick. Source: 03-world-and-camera.md, Values, scroll_base (guess)."""

SCROLL_START_DELAY: int = 30
"""Ticks. Source: 03-world-and-camera.md, Values, scroll_start_delay (guess)."""

LEVEL_1_SCROLL_MULT = Fraction(1)
"""Source: 08-difficulty.md, Level table, Level 1 scroll speed (locked)."""

PX_PER_METER: int = 10
"""Source: 03-world-and-camera.md, Values, px_per_meter (locked)."""

PER_TICK = SCROLL_BASE * LEVEL_1_SCROLL_MULT

SCROLL_MULT: tuple[Fraction, ...] = tuple(
    Fraction(text) for text in ("1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7")
)
"""Scroll speed × for Levels 1 to 8. Source: 08-difficulty.md, level table (locked)."""

LEVELS: range = range(1, 9)
"""Levels 1 to 8. Source: 08-difficulty.md, level table (locked)."""

BAD_LEVELS: tuple[int, ...] = (0, 9, -1, 100)
"""Levels outside 1 to 8. Source: 08-difficulty.md, level table (locked)."""


def speed_at(level: int) -> Fraction:
    """Exact px/tick at `level`: scroll_base times that level's scroll multiplier."""
    return SCROLL_BASE * SCROLL_MULT[level - 1]


def exact_distance(plan: list[tuple[int, int]]) -> Fraction:
    """Exact px scrolled after a plan of (level, moving ticks), start delay already over."""
    return sum((speed_at(level) * ticks for level, ticks in plan), Fraction(0))


def run(steps: int) -> Scroll:
    """Step a fresh scroll the given number of times."""
    scroll = start_scroll()
    for _ in range(steps):
        scroll = step_scroll(scroll)
    return scroll


def test_scroll_starts_at_zero() -> None:
    scroll = start_scroll()
    assert scroll.distance_px == 0
    assert scroll.meters == 0


def test_world_stays_still_for_start_delay() -> None:
    assert run(SCROLL_START_DELAY).distance_px == 0
    assert run(SCROLL_START_DELAY + 1).distance_px == pytest.approx(float(PER_TICK))


@pytest.mark.parametrize("n", [1, 60, 6000])
def test_scroll_speed_is_steady(n: int) -> None:
    assert run(SCROLL_START_DELAY + n).distance_px == pytest.approx(float(n * PER_TICK))


def test_meters_round_down() -> None:
    scroll = run(SCROLL_START_DELAY)
    for n in range(1001):
        expected = math.floor(n * PER_TICK / PX_PER_METER)
        assert scroll.meters == expected, f"n={n}"
        scroll = step_scroll(scroll)


@pytest.mark.smoke
def test_scroll_never_stops_or_goes_back() -> None:
    scroll = start_scroll()
    for tick in range(1, 6001):
        prev = scroll
        scroll = step_scroll(scroll)
        if tick > SCROLL_START_DELAY:
            assert scroll.distance_px > prev.distance_px, f"tick={tick}"
        assert scroll.distance_px >= prev.distance_px
        assert scroll.meters >= prev.meters


@pytest.mark.determinism
def test_step_is_pure() -> None:
    scroll = run(5)
    before = Scroll(ticks=scroll.ticks, scrolled_ticks=scroll.scrolled_ticks)
    step_scroll(scroll)
    assert scroll == before
    assert run(200) == run(200)


def test_scroll_start_logs_once(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="core.scroll")
    run(600)
    lines = [r.getMessage() for r in caplog.records if r.getMessage().startswith("scroll start")]
    assert len(lines) == 1
    assert "tick=31" in lines[0]


def test_scroll_step_px_is_zero_to_tick_30_then_the_scroll_speed_and_matches_step_scroll(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="core.scroll")
    scroll = start_scroll()
    for next_tick in range(1, 301):
        before = Scroll(ticks=scroll.ticks, scrolled_ticks=scroll.scrolled_ticks)
        lines_before = len(caplog.records)
        px = scroll_step_px(scroll)
        # Reading the step changes nothing and logs nothing.
        assert scroll == before
        assert len(caplog.records) == lines_before
        expected = 0.0 if next_tick <= SCROLL_START_DELAY else float(PER_TICK)
        assert px == pytest.approx(expected, abs=1e-12), f"step to tick {next_tick}"
        if next_tick <= SCROLL_START_DELAY:
            assert px == 0.0, f"step to tick {next_tick}"
        moved = step_scroll(scroll)
        assert moved.distance_px - scroll.distance_px == pytest.approx(px, abs=1e-9), (
            f"step to tick {next_tick}"
        )
        scroll = moved
    # The one `scroll start` line still comes from step_scroll alone.
    starts = [r.getMessage() for r in caplog.records if r.getMessage().startswith("scroll start")]
    assert len(starts) == 1
    assert scroll_step_px(run(SCROLL_START_DELAY - 1)) == 0.0
    assert scroll_step_px(run(SCROLL_START_DELAY)) == pytest.approx(float(PER_TICK))


def test_scroll_speed_is_the_base_times_the_level_scroll_mult() -> None:
    for level in LEVELS:
        assert scroll_speed(level) == pytest.approx(float(speed_at(level)), abs=1e-12), level
    assert scroll_speed(1) == pytest.approx(1.1)
    assert scroll_speed(2) == pytest.approx(1.21)
    assert scroll_speed(8) == pytest.approx(1.87)
    for bad in BAD_LEVELS:
        with pytest.raises(ValueError, match=str(bad)):
            scroll_speed(bad)


def test_a_step_at_a_level_moves_the_world_at_that_speed_once_the_delay_is_over() -> None:
    for level in LEVELS:
        scroll = start_scroll()
        for tick in range(1, SCROLL_START_DELAY + 1):
            scroll = step_scroll(scroll, level)
            # The start delay: nothing moves and nothing is counted for the level.
            assert scroll.ticks == tick
            assert scroll.scrolled_ticks == 0, f"level {level} tick {tick}"
            assert scroll.raised_level_ticks == (0,) * 7, f"level {level} tick {tick}"
            assert scroll.distance_px == 0, f"level {level} tick {tick}"
        for moving in range(1, 201):
            before = scroll.distance_px
            scroll = step_scroll(scroll, level)
            assert scroll.scrolled_ticks == moving
            assert scroll.distance_px - before == pytest.approx(float(speed_at(level)), abs=1e-9)
            # The tick is counted for its level: Level 1 has no entry, Levels 2 to 8 have one.
            expected_raised = [0] * 7
            if level > 1:
                expected_raised[level - 2] = moving
            assert list(scroll.raised_level_ticks) == expected_raised, f"level {level}"
        assert scroll.distance_px == pytest.approx(float(200 * speed_at(level)), rel=1e-9)
    for bad in BAD_LEVELS:
        for scroll in (start_scroll(), run(SCROLL_START_DELAY + 5)):
            with pytest.raises(ValueError, match=str(bad)):
                step_scroll(scroll, bad)


def test_distance_over_several_levels_is_each_levels_ticks_times_its_speed_summed() -> None:
    plans: list[list[tuple[int, int]]] = [
        [(level, 1000) for level in LEVELS],
        [(1, 7), (3, 130), (8, 55), (2, 1), (5, 800)],
        [(8, 1500), (4, 1)],
    ]
    boundaries_hit = 0
    for plan in plans:
        scroll = run(SCROLL_START_DELAY)
        done: list[tuple[int, int]] = []
        for level, ticks in plan:
            for count in range(1, ticks + 1):
                scroll = step_scroll(scroll, level)
                exact = exact_distance([*done, (level, count)])
                assert scroll.distance_px == pytest.approx(float(exact), rel=1e-12, abs=1e-9)
                # Whole meters round down, exactly, with no meter lost on a boundary.
                assert scroll.meters == math.floor(exact / PX_PER_METER), (
                    f"level {level} count {count}"
                )
                if exact > 0 and exact % PX_PER_METER == 0:
                    boundaries_hit += 1
            done.append((level, ticks))
    # The runs above do land exactly on whole meters, so the guard was exercised.
    assert boundaries_hit > 0


def test_scroll_step_px_equals_what_step_scroll_adds_at_every_level() -> None:
    schedule: list[tuple[int, int]] = [(level, 60) for level in LEVELS]
    schedule += [(8, 5), (1, 5), (6, 5)]
    for level in LEVELS:
        scroll = start_scroll()
        for next_tick in range(1, 121):
            before = Scroll(
                ticks=scroll.ticks,
                scrolled_ticks=scroll.scrolled_ticks,
                raised_level_ticks=scroll.raised_level_ticks,
            )
            px = scroll_step_px(scroll, level)
            assert scroll == before
            moved = step_scroll(scroll, level)
            assert moved.distance_px - scroll.distance_px == pytest.approx(px, abs=1e-9)
            if next_tick <= SCROLL_START_DELAY:
                assert px == 0.0, f"level {level} step to tick {next_tick}"
            else:
                assert px == pytest.approx(float(speed_at(level)), abs=1e-12)
                assert px == pytest.approx(scroll_speed(level), abs=1e-12)
            scroll = moved
    # Across a level change, with the level of each step passed to both.
    scroll = start_scroll()
    for level, ticks in schedule:
        for _ in range(ticks):
            px = scroll_step_px(scroll, level)
            moved = step_scroll(scroll, level)
            assert moved.distance_px - scroll.distance_px == pytest.approx(px, abs=1e-9)
            scroll = moved


def test_with_no_level_both_behave_as_level_1() -> None:
    plain = start_scroll()
    level_one = start_scroll()
    for next_tick in range(1, 400):
        assert scroll_step_px(plain) == scroll_step_px(level_one, 1)
        assert scroll_step_px(plain) == (
            0.0 if next_tick <= SCROLL_START_DELAY else pytest.approx(float(PER_TICK))
        )
        plain = step_scroll(plain)
        level_one = step_scroll(level_one, 1)
        assert plain == level_one, f"tick {next_tick}"
        assert plain.raised_level_ticks == (0,) * 7
        assert plain.distance_px == pytest.approx(
            float(max(0, next_tick - SCROLL_START_DELAY) * PER_TICK), abs=1e-9
        )


def test_scroll_start_logs_once_per_scroll_at_every_level(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="core.scroll")
    for level in LEVELS:
        caplog.clear()
        scroll = start_scroll()
        for _ in range(600):
            scroll = step_scroll(scroll, level)
        lines = [r.getMessage() for r in caplog.records]
        assert len(lines) == 1, f"level {level}: {lines}"
        assert lines[0].startswith("scroll start")
        assert "tick=31" in lines[0]
    # A level change after the start adds no line; a new scroll logs its own.
    caplog.clear()
    scroll = start_scroll()
    for level in LEVELS:
        for _ in range(100):
            scroll = step_scroll(scroll, level)
    assert len(caplog.records) == 1
    step_scroll(run(SCROLL_START_DELAY), 5)
    assert len(caplog.records) == 2
