"""The points popup a pickup leaves where it was collected, and its per-tick step.

Stdlib only, no frame time, no randomness. Screen px, y down.

Source: docs/contracts/systems/run.md, Interface, popup.py; drifters/04-coin.md, popup.
"""

import logging
from dataclasses import dataclass, replace

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class PointsPopup:
    """The points a pickup paid, shown where it was collected, rising, for a set time."""

    x: float
    """Center x, screen px. Never changes."""

    start_y: float
    """Center y on the tick it appears, screen px, y down."""

    points: int
    """The points it shows, at least 0."""

    lifetime_ticks: int
    """How many states it shows on, at least 1."""

    rise_per_tick: float
    """Px it rises each tick, at least 0."""

    age_ticks: int = 0
    """Ticks since it appeared. 0 on the state it appears."""

    @property
    def y(self) -> float:
        """Return the center y now, screen px: `start_y` minus the rise so far."""
        return self.start_y - self.age_ticks * self.rise_per_tick


def step_popups(popups: tuple[PointsPopup, ...]) -> tuple[PointsPopup, ...]:
    """Return every popup one tick older, in order, dropping those whose age reaches their life."""
    aged: tuple[PointsPopup, ...] = tuple(
        replace(popup, age_ticks=popup.age_ticks + 1) for popup in popups
    )
    return tuple(popup for popup in aged if popup.age_ticks < popup.lifetime_ticks)
