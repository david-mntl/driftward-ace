"""World scroll and distance tests. Contract: docs/contracts/systems/scroll.md, Rules.

Task: docs/contracts/DRA-13/tasks/DRA-13-04-qa-engineer.md. One test per behavior it lists.
`scroll_step_px` (DRA-62): docs/contracts/DRA-62/tasks/DRA-62-06-qa-engineer.md.
Every expected number is computed from the GDD values below, never typed in as a result.
"""

import logging
import math
from fractions import Fraction

import pytest

from core.scroll import Scroll, scroll_step_px, start_scroll, step_scroll

SCROLL_BASE = Fraction("1.1")
"""px/tick. Source: 03-world-and-camera.md, Values, scroll_base (guess)."""

SCROLL_START_DELAY: int = 30
"""Ticks. Source: 03-world-and-camera.md, Values, scroll_start_delay (guess)."""

LEVEL_1_SCROLL_MULT = Fraction(1)
"""Source: 08-difficulty.md, Level table, Level 1 scroll speed (locked)."""

PX_PER_METER: int = 10
"""Source: 03-world-and-camera.md, Values, px_per_meter (locked)."""

PER_TICK = SCROLL_BASE * LEVEL_1_SCROLL_MULT


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
