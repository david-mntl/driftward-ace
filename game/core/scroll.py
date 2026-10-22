"""World scroll state, its one-tick step and the distance counter.

The screen is fixed. After a short delay the world scrolls down past it at a steady speed
set by the level the caller passes. Distance counts that scroll. The scroll never reads the
ship and the ship never reads the scroll. Stdlib only, no frame time, no randomness, no run mode.

Source: docs/contracts/systems/scroll.md, Interface and Rules.
"""

import logging
import math
from dataclasses import dataclass, replace
from typing import Final

from core.levels import FIRST_LEVEL, LEVEL_COUNT, check_level, scroll_mult

log = logging.getLogger(__name__)

SCROLL_BASE: Final[float] = 1.1
"""Base scroll speed, px/tick. Source: 03-world-and-camera.md, scroll_base (guess)."""

SCROLL_START_DELAY: Final[int] = 30
"""Ticks of a still world after play starts. Source: 03-world-and-camera.md,
scroll_start_delay (guess)."""

DISTANCE_START: Final[int] = 0
"""Distance at play start, m. Source: 03-world-and-camera.md, distance_start (locked)."""

PX_PER_METER: Final[int] = 10
"""Pixels in one meter. Source: 03-world-and-camera.md, px_per_meter (locked)."""

DISTANCE_DECIMALS: Final[int] = 6
"""Float guard, not a game value: a distance is rounded to this many decimals (micro-px)
before it is floored to meters or compared with a wave trigger. Source: systems/scroll.md."""


@dataclass(frozen=True, slots=True)
class Scroll:
    """Scroll state after a tick."""

    ticks: int = 0
    """Ticks run since play started."""

    scrolled_ticks: int = 0
    """Ticks on which the world moved, at any level."""

    raised_level_ticks: tuple[int, ...] = (0,) * (LEVEL_COUNT - 1)
    """Ticks on which the world moved at Levels 2 to 8, Level 2 first. The ticks at Level 1
    are scrolled_ticks minus their sum."""

    @property
    def distance_px(self) -> float:
        """Distance scrolled, px. Source: 03-world-and-camera.md, rules 4 and 8."""
        level_1_ticks: int = self.scrolled_ticks - sum(self.raised_level_ticks)
        weighted_ticks: float = scroll_mult(FIRST_LEVEL) * level_1_ticks
        for index, level_ticks in enumerate(self.raised_level_ticks):
            weighted_ticks += scroll_mult(index + FIRST_LEVEL + 1) * level_ticks
        return DISTANCE_START * PX_PER_METER + SCROLL_BASE * weighted_ticks

    @property
    def meters(self) -> int:
        """Whole meters, rounded down after the float guard. Source: 06-scoring.md, rule 1."""
        return math.floor(round(self.distance_px, DISTANCE_DECIMALS) / PX_PER_METER)


def scroll_speed(level: int) -> float:
    """Return the scroll speed at `level`, px/tick. Raises ValueError outside 1 to 8.

    Source: 03-world-and-camera.md, rule 4; 08-difficulty.md, rule 2.
    """
    return SCROLL_BASE * scroll_mult(level)


def start_scroll() -> Scroll:
    """Return the scroll at play start: tick 0, nothing scrolled."""
    return Scroll(ticks=0, scrolled_ticks=0)


def scroll_step_px(scroll: Scroll, level: int = FIRST_LEVEL) -> float:
    """Return how far the world moves down, px, on the tick that steps `scroll` at `level`.

    scroll_speed(level) once the next tick passes SCROLL_START_DELAY, else 0.0. Reads the same
    rule as `step_scroll`, so the two agree on every tick. Pure, logs nothing.
    Source: 03-world-and-camera.md, rules 4 and 9; systems/scroll.md, The next step's movement.
    """
    speed: float = scroll_speed(level)
    if scroll.ticks + 1 > SCROLL_START_DELAY:
        return speed
    return 0.0


def _count_level_tick(raised: tuple[int, ...], level: int) -> tuple[int, ...]:
    """Return `raised` with one more moving tick at `level`. Level 1 has no entry."""
    if level == FIRST_LEVEL:
        return raised
    index: int = level - FIRST_LEVEL - 1
    return (*raised[:index], raised[index] + 1, *raised[index + 1 :])


def step_scroll(scroll: Scroll, level: int = FIRST_LEVEL) -> Scroll:
    """Advance the scroll one fixed 60 Hz tick at `level` and return the new state.

    Ticks 1 to SCROLL_START_DELAY leave the world still. Later ticks scroll it at the speed of
    `level`. Raises ValueError for a level outside 1 to 8. Never mutates its input. Logs once,
    on the first tick the world moves.
    Source: 03-world-and-camera.md, rule 4; 15-tech-constraints.md, rule 2.
    """
    check_level(level)
    ticks: int = scroll.ticks + 1
    if ticks <= SCROLL_START_DELAY:
        return replace(scroll, ticks=ticks)
    moved: Scroll = Scroll(
        ticks=ticks,
        scrolled_ticks=scroll.scrolled_ticks + 1,
        raised_level_ticks=_count_level_tick(scroll.raised_level_ticks, level),
    )
    if moved.scrolled_ticks == 1:
        log.debug("scroll start tick=%d", moved.ticks)
    return moved
