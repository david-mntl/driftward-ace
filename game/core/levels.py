"""The level table: hazard speed and Timer multipliers per level, and where levels start.

Levels are 1 to 8. Stdlib only, pure, no frame time, no randomness.

Source: docs/contracts/systems/objects.md, Interface and Rules, Levels; 08-difficulty.md.
"""

import logging
from typing import Final

log = logging.getLogger(__name__)

LEVEL_COUNT: Final[int] = 8
"""Number of levels. Source: 08-difficulty.md, level table (locked)."""

HAZARD_SPEED_MULT: Final[tuple[float, ...]] = (1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42)
"""Hazard speed multiplier per level, Level 1 first. Source: 08-difficulty.md (locked)."""

TIMER_MULT: Final[tuple[float, ...]] = (1.00, 0.94, 0.89, 0.85, 0.81, 0.77, 0.74, 0.70)
"""Timer multiplier per level, Level 1 first. Source: 08-difficulty.md (guess)."""

LEVEL_STARTS_M: Final[tuple[int, ...]] = (0,)
"""Distance in meters where each level starts, Level 1 first.

Only Level 1 (0 m) is known. Levels 2 to 8 are TBD (DF-05) and join here when set.
Source: 08-difficulty.md, Starts at row.
"""


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


def level_at(meters: int) -> int:
    """Return the highest level whose start is at or below `meters`, never less than 1."""
    return max(1, sum(1 for start in LEVEL_STARTS_M if start <= meters))
