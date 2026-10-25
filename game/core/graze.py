"""The graze rule: follow the ship through each hazard's graze zone and pay the exits.

A hazard pays one graze when the ship leaves its zone without having touched it, while the ship
flies and is not invulnerable. Also the graze values, the graze ring and the popup a paid graze
shows. Stdlib and `core` only. No frame time, no randomness, no run mode.

Source: docs/contracts/systems/run.md, Interface (DRA-117) and Rules, step 5b; 06-scoring.md.
"""

import logging
from dataclasses import dataclass, replace
from typing import Final

from core.collision import Hitbox, hitboxes_overlap
from core.drifters.base import Drifter, GrazeState, TouchEffect
from core.popup import PointsPopup, PopupKind
from core.ship import Ship

log = logging.getLogger(__name__)

DEFAULT_GRAZE_POINTS: Final[int] = 25
"""Points a paid graze adds. Source: 06-scoring.md, graze_points (locked)."""

DEFAULT_GRAZE_POPUP_TICKS: Final[int] = 60
"""States a graze popup shows on. Source: 06-scoring.md, graze_popup (guess)."""

DEFAULT_GRAZE_POPUP_RISE_PER_TICK: Final[float] = 0.5
"""Px a graze popup rises each tick. Source: 06-scoring.md, graze_popup (guess)."""

DEFAULT_GRAZE_RING_TICKS: Final[int] = 15
"""States a graze ring shows on. Source: 06-scoring.md, graze_ring (guess)."""

DEFAULT_GRAZE_RING_START_DIAMETER: Final[float] = 16.0
"""Px across a graze ring starts at. Source: 06-scoring.md, graze_ring (guess)."""

DEFAULT_GRAZE_RING_END_DIAMETER: Final[float] = 32.0
"""Px across a graze ring grows toward. Source: 06-scoring.md, graze_ring (guess)."""

DEFAULT_GRAZE_RING_WIDTH: Final[int] = 1
"""Line width of a graze ring, px. Source: 06-scoring.md, graze_ring (guess)."""


@dataclass(frozen=True, slots=True, kw_only=True)
class GrazeRules:
    """The graze values a run uses, from game/tuning/scoring.json. A missing one is the default."""

    points: int = DEFAULT_GRAZE_POINTS
    """Points per graze, at least 0."""

    popup_ticks: int = DEFAULT_GRAZE_POPUP_TICKS
    """States a graze popup shows on, at least 1."""

    popup_rise_per_tick: float = DEFAULT_GRAZE_POPUP_RISE_PER_TICK
    """Px a graze popup rises each tick, at least 0."""

    ring_ticks: int = DEFAULT_GRAZE_RING_TICKS
    """States a graze ring shows on, at least 1."""

    ring_start_diameter: float = DEFAULT_GRAZE_RING_START_DIAMETER
    """Px across on the state the ring appears, above 0."""

    ring_end_diameter: float = DEFAULT_GRAZE_RING_END_DIAMETER
    """Px across the ring grows toward, above 0."""

    ring_width: int = DEFAULT_GRAZE_RING_WIDTH
    """Line width, px, at least 1."""


DEFAULT_GRAZE_RULES: Final[GrazeRules] = GrazeRules()
"""The graze rules with every default."""


@dataclass(frozen=True, slots=True, kw_only=True)
class GrazeRing:
    """The ring a paid graze shows around the ship, growing and fading for a set time."""

    start_diameter: float
    """Px across on the state it appears."""

    end_diameter: float
    """Px across it grows toward."""

    line_width: int
    """Line width, px."""

    lifetime_ticks: int
    """How many states it shows on, at least 1."""

    age_ticks: int = 0
    """Ticks since it appeared. 0 on the state it appears."""

    @property
    def diameter(self) -> float:
        """Return the px across now: a steady step from the start toward the end."""
        span: float = self.end_diameter - self.start_diameter
        return self.start_diameter + span * self.age_ticks / self.lifetime_ticks

    @property
    def opacity(self) -> float:
        """Return 1.0 on the state it appears, falling steadily; above 0 on every state it shows."""
        return 1 - self.age_ticks / self.lifetime_ticks


@dataclass(frozen=True, slots=True)
class GrazeCheck:
    """What one graze check found."""

    drifters: tuple[Drifter, ...]
    """Every drifter given, in order, its graze_state brought up to date."""

    paid: tuple[Drifter, ...]
    """The drifters that paid a graze on this check, in drifter order."""


def check_grazes(drifters: tuple[Drifter, ...], ship_box: Hitbox, may_pay: bool) -> GrazeCheck:
    """Follow the ship through every hazard's graze zone and find the grazes that pay.

    `may_pay` is False while the ship is protected or standing in the respawn wait: an exit
    then pays nothing and the hazard goes back to OUTSIDE. Pure, never mutates its input.
    Source: systems/run.md, Rules, step 5b; 06-scoring.md, rules 3 to 6.
    """
    checked: list[tuple[Drifter, bool]] = [
        _check_one(drifter, ship_box, may_pay) for drifter in drifters
    ]
    return GrazeCheck(
        drifters=tuple(drifter for drifter, _ in checked),
        paid=tuple(drifter for drifter, paid in checked if paid),
    )


def _check_one(drifter: Drifter, ship_box: Hitbox, may_pay: bool) -> tuple[Drifter, bool]:
    """Return the drifter with its graze state brought up to date, and whether it paid."""
    if drifter.effect_on_touch() is not TouchEffect.HIT or drifter.graze_state is GrazeState.SPENT:
        return drifter, False
    if hitboxes_overlap(drifter.current_hitbox(), ship_box):
        return replace(drifter, graze_state=GrazeState.SPENT), False
    if _ship_in_zone(drifter, ship_box):
        return _with_state(drifter, GrazeState.INSIDE), False
    if drifter.graze_state is GrazeState.INSIDE and may_pay:
        return replace(drifter, graze_state=GrazeState.SPENT), True
    return _with_state(drifter, GrazeState.OUTSIDE), False


def _ship_in_zone(drifter: Drifter, ship_box: Hitbox) -> bool:
    """True when the drifter is on screen and its graze zone overlaps `ship_box`.

    A drifter off screen is dropped this tick, so its zone counts as gone.
    """
    return not drifter.is_off_screen() and hitboxes_overlap(drifter.graze_zone(), ship_box)


def _with_state(drifter: Drifter, state: GrazeState) -> Drifter:
    """Return the drifter with `state`, or the same object when it already has it."""
    if drifter.graze_state is state:
        return drifter
    return replace(drifter, graze_state=state)


def graze_popup(rules: GrazeRules, ship: Ship) -> PointsPopup:
    """Return the popup of a paid graze at age 0, centered on the ship, showing the graze points."""
    return PointsPopup(
        x=ship.x,
        start_y=ship.y,
        points=rules.points,
        lifetime_ticks=rules.popup_ticks,
        rise_per_tick=rules.popup_rise_per_tick,
        kind=PopupKind.GRAZE,
    )


def graze_ring(rules: GrazeRules) -> GrazeRing:
    """Return a graze ring at age 0 with the rules' ring values."""
    return GrazeRing(
        start_diameter=rules.ring_start_diameter,
        end_diameter=rules.ring_end_diameter,
        line_width=rules.ring_width,
        lifetime_ticks=rules.ring_ticks,
    )


def step_graze_rings(rings: tuple[GrazeRing, ...]) -> tuple[GrazeRing, ...]:
    """Return every ring one tick older, in order, dropping those whose age reaches their life."""
    aged: tuple[GrazeRing, ...] = tuple(
        replace(ring, age_ticks=ring.age_ticks + 1) for ring in rings
    )
    return tuple(ring for ring in aged if ring.age_ticks < ring.lifetime_ticks)
