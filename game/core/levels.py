"""The level table: the per-level multipliers for hazard speed, Timer, scroll speed and Rest gap.

Levels are 1 to 8. Stdlib only, pure, no frame time, no randomness.

Source: docs/contracts/systems/drifters.md, Interface and Rules, Levels; 08-difficulty.md.
"""

import logging
from typing import Final

log = logging.getLogger(__name__)

LEVEL_COUNT: Final[int] = 8
"""Number of levels. Source: 08-difficulty.md, level table (locked)."""

FIRST_LEVEL: Final[int] = 1
"""The level a run starts at. Source: 08-difficulty.md, rule 1."""

HAZARD_SPEED_MULT: Final[tuple[float, ...]] = (1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42)
"""Hazard speed multiplier per level, Level 1 first. Source: 08-difficulty.md (locked)."""

TIMER_MULT: Final[tuple[float, ...]] = (1.00, 0.94, 0.89, 0.85, 0.81, 0.77, 0.74, 0.70)
"""Timer multiplier per level, Level 1 first. Source: 08-difficulty.md (guess)."""

SCROLL_MULT: Final[tuple[float, ...]] = (1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7)
"""Scroll speed multiplier per level, Level 1 first. Source: 08-difficulty.md (locked)."""

REST_GAP_MULT: Final[tuple[float, ...]] = (1.00, 0.90, 0.81, 0.73, 0.66, 0.59, 0.53, 0.48)
"""Rest gap multiplier per level, Level 1 first. Source: 08-difficulty.md (locked)."""


def check_level(level: int) -> None:
    """Raise ValueError unless `level` is 1 to LEVEL_COUNT."""
    if not 1 <= level <= LEVEL_COUNT:
        raise ValueError(f"level {level} is outside 1 to {LEVEL_COUNT}")


def hazard_speed_mult(level: int) -> float:
    """Return the hazard speed multiplier of `level`, 1 to LEVEL_COUNT."""
    check_level(level)
    return HAZARD_SPEED_MULT[level - 1]


def timer_mult(level: int) -> float:
    """Return the Timer multiplier of `level`, 1 to LEVEL_COUNT."""
    check_level(level)
    return TIMER_MULT[level - 1]


def scroll_mult(level: int) -> float:
    """Return the scroll speed multiplier of `level`, 1 to LEVEL_COUNT."""
    check_level(level)
    return SCROLL_MULT[level - 1]


def rest_gap_mult(level: int) -> float:
    """Return the Rest gap multiplier of `level`, 1 to LEVEL_COUNT."""
    check_level(level)
    return REST_GAP_MULT[level - 1]
