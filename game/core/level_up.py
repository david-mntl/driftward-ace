"""Level-up: the rules record, the banner's state and the level the HUD shows.

The banner is a value aged one tick at a time. Its age is the one clock every part of the banner
reads. Stdlib only: no randomness, no frame time, no run mode.

Source: docs/contracts/systems/level-up/core.md, Interface and Rules.
"""

import logging
from dataclasses import dataclass, replace
from typing import Final

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class LevelUpRules:
    """The level-up values a run plays with, from game/tuning/level_up.json."""

    rest_ticks: int
    """Ticks added to the rest on a level rise, >= 0. 0 is off: no rest, no banner, no cue."""

    arrival_ticks: int
    """Banner age at which the HUD switches to the new level, ticks, >= 1."""

    banner_ticks: int
    """Ticks the banner lives, > arrival_ticks. <= rest_ticks when rest_ticks > 0."""


NO_LEVEL_UP: Final[LevelUpRules] = LevelUpRules(rest_ticks=0, arrival_ticks=1, banner_ticks=2)
"""Level-up off. The default of a WaveRun, so a run built without rules plays as before.
Source: docs/contracts/systems/level-up/core.md, Interface (`rest_ticks` 0 is off). Only
`rest_ticks` is read while off, so the other two are the smallest values the record allows."""


@dataclass(frozen=True, slots=True, kw_only=True)
class LevelUpBanner:
    """The banner of one level rise, aged tick by tick."""

    level: int
    """The level reached (the run's real level), 2 to LEVEL_COUNT."""

    previous_level: int
    """The level before the rise, FIRST_LEVEL to level - 1."""

    arrival_ticks: int
    """Copied from the rules, ticks."""

    lifetime_ticks: int
    """Copied from the rules (banner_ticks), ticks."""

    age_ticks: int = 0
    """Ticks since the rise. 0 on the state after the rise tick."""


def start_level_up(rules: LevelUpRules, previous_level: int, level: int) -> LevelUpBanner:
    """Return a banner at age 0 with the rules' arrival and banner ticks."""
    return LevelUpBanner(
        level=level,
        previous_level=previous_level,
        arrival_ticks=rules.arrival_ticks,
        lifetime_ticks=rules.banner_ticks,
    )


def step_level_up(banner: LevelUpBanner) -> LevelUpBanner | None:
    """Return the banner one tick older, or None once its age reaches `lifetime_ticks`."""
    age: int = banner.age_ticks + 1
    if age >= banner.lifetime_ticks:
        return None
    return replace(banner, age_ticks=age)


def shown_level(banner: LevelUpBanner | None, level: int) -> int:
    """Return the level the HUD shows.

    `banner.previous_level` while a banner exists and its age is below `arrival_ticks`, else
    `level`, the run's real level.
    """
    if banner is not None and banner.age_ticks < banner.arrival_ticks:
        return banner.previous_level
    return level
