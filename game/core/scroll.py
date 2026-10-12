"""World scroll state, its one-tick step and the distance counter.

The screen is fixed. The world scrolls down past it at a steady Level 1 speed after a short
delay. Distance counts that scroll. The scroll never reads the ship and the ship never
reads the scroll. Stdlib only, no frame time, no randomness, no run mode.

Source: docs/contracts/systems/scroll.md, Interface and Rules.
"""

import logging
import math
from dataclasses import dataclass
from typing import Final

log = logging.getLogger(__name__)

SCROLL_BASE: Final[float] = 1.1
"""Base scroll speed, px/tick. Source: 03-world-and-camera.md, scroll_base (guess)."""

LEVEL_1_SCROLL_MULT: Final[float] = 1.0
"""Level 1 scroll speed multiplier. Source: 08-difficulty.md, Level table (locked)."""

SCROLL_PER_TICK: Final[float] = SCROLL_BASE * LEVEL_1_SCROLL_MULT
"""Scroll speed at Level 1, px/tick: 1.1. Source: 08-difficulty.md, rule 2."""

SCROLL_START_DELAY: Final[int] = 30
"""Ticks of a still world after play starts. Source: 03-world-and-camera.md,
scroll_start_delay (guess)."""

DISTANCE_START: Final[int] = 0
"""Distance at play start, m. Source: 03-world-and-camera.md, distance_start (locked)."""

PX_PER_METER: Final[int] = 10
"""Pixels in one meter. Source: 03-world-and-camera.md, px_per_meter (locked)."""


@dataclass(frozen=True, slots=True)
class Scroll:
    """Scroll state after a tick."""

    ticks: int = 0
    """Ticks run since play started."""

    scrolled_ticks: int = 0
    """Ticks on which the world moved."""

    @property
    def distance_px(self) -> float:
        """Distance scrolled, px. Source: 03-world-and-camera.md, rules 4 and 8."""
        return DISTANCE_START * PX_PER_METER + self.scrolled_ticks * SCROLL_PER_TICK

    @property
    def meters(self) -> int:
        """Whole meters, rounded down. Source: 06-scoring.md, rule 1."""
        return math.floor(self.distance_px / PX_PER_METER)


def start_scroll() -> Scroll:
    """Return the scroll at play start: tick 0, nothing scrolled."""
    return Scroll(ticks=0, scrolled_ticks=0)


def step_scroll(scroll: Scroll) -> Scroll:
    """Advance the scroll one fixed 60 Hz tick and return the new state.

    Ticks 1 to SCROLL_START_DELAY leave the world still. Later ticks scroll it. Never
    mutates its input. Logs once, on the first tick the world moves.
    Source: 03-world-and-camera.md, rule 4; 15-tech-constraints.md, rule 2.
    """
    ticks: int = scroll.ticks + 1
    if ticks <= SCROLL_START_DELAY:
        return Scroll(ticks=ticks, scrolled_ticks=scroll.scrolled_ticks)
    moved = Scroll(ticks=ticks, scrolled_ticks=scroll.scrolled_ticks + 1)
    if moved.scrolled_ticks == 1:
        log.debug("scroll start tick=%d", moved.ticks)
    return moved
