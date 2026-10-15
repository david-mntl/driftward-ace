"""The shared drifter base: phases, birth facts, the abstract drifter and its specialty slot.

A drifter carries final numbers only. It never knows the level. Screen px, y down, x and y at
the drifter's center. Stdlib and `core` only, no frame time, no randomness.

Source: docs/contracts/systems/drifters.md, Interface and Rules, The base.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import Enum
from typing import ClassVar, Final, Self

from core.collision import Hitbox, grow_hitbox, place_hitbox
from core.ship import Ship
from core.world import SCREEN_H, SCREEN_W

log = logging.getLogger(__name__)

GRAZE_MARGIN: Final[int] = 14
"""Graze zone margin around a hazard's hitbox, px. Source: 06-scoring.md, graze_margin (locked)."""


class DrifterType(Enum):
    """Every drifter the game knows. One member per built drifter spec in 07-drifters.md."""

    METEORITE = "meteorite"
    """Source: drifters/01-meteorite.md."""


class Phase(Enum):
    """Where a drifter is in its life."""

    WARNING = "warning"
    """The entry warning shows. The drifter can't touch anything."""

    ACTIVE = "active"
    """The drifter is on the field and can touch the ship."""

    GONE = "gone"
    """The drifter is finished. The run drops it this tick."""


class TouchEffect(Enum):
    """What touching a drifter does."""

    HIT = "hit"
    """A hit. Source: 05-lives-and-damage.md, rule 1."""

    COLLECT = "collect"
    """Reserved for coins. No drifter returns it yet."""

    NONE = "none"
    """Nothing happens."""


@dataclass(frozen=True, slots=True)
class TickContext:
    """Per-tick facts a drifter may read in `update`. Never the level."""

    ship: Ship
    """The ship as it was at the start of this tick."""


@dataclass(frozen=True, slots=True)
class Birth:
    """Everything the spawner settled for one new drifter. Final numbers only."""

    x: float
    """Center x, screen px."""

    y: float
    """Center y, screen px, y down."""

    variant: str
    """The variant's name."""

    width: float
    """The variant's visible width, px."""

    height: float
    """The variant's visible height, px."""

    hitbox: Hitbox
    """The variant's shapes, as offsets from the center."""

    speed: float
    """Final speed, px/tick. The hazard speed multiplier is already applied."""

    warning_ticks: int
    """Entry warning length, ticks. Never scaled."""

    timer_mult: float
    """The Timer multiplier for the drifter's own timers. A drifter without timers ignores it."""

    specialty_enabled: bool | None
    """The placement's specialty switch. None means the drifter's default."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Specialty(ABC):
    """An optional extra behavior on top of a drifter's movement. Only the interface exists."""

    enabled: bool
    """Switched on or off for this drifter."""

    @abstractmethod
    def update(self, owner: Drifter, ctx: TickContext) -> Self:
        """Advance the specialty one 60 Hz tick and return the new one."""

    def effect_on_ship(self, owner: Drifter, ship: Ship) -> Ship | None:
        """Return the ship after this specialty acts on it, or None for no effect."""
        return None


@dataclass(frozen=True, slots=True, kw_only=True)
class Drifter(ABC):
    """One drifter on the field after a tick. Screen px, y down, x and y at its center."""

    drifter_type: ClassVar[DrifterType]
    """Set by each subclass."""

    uid: int = 0
    """Unique within a run, from 1. Set by `core.run.add_drifters`. 0 before that."""

    x: float
    """Center x, screen px."""

    y: float
    """Center y, screen px, y down."""

    variant: str
    """The variant's name, for example "medium"."""

    width: float
    """Visible width, px, from the variant."""

    height: float
    """Visible height, px, from the variant."""

    speed: float
    """Final speed, px/tick, set by the spawner."""

    hitbox: Hitbox
    """Shapes as offsets from (x, y), from the variant."""

    warning_ticks: int
    """Entry warning length, ticks."""

    phase: Phase = Phase.WARNING
    """Where the drifter is in its life."""

    ticks_in_phase: int = 0
    """Ticks spent in the current phase. 0 on the state where it starts."""

    specialty: Specialty | None = None
    """The optional extra behavior. None when the drifter has none."""

    hit_ship: bool = False
    """A fact: this drifter has hit the ship at least once. Set by the run.

    What it means for later touches is the drifter's own rule (`may_hit_ship`).
    """

    def current_hitbox(self) -> Hitbox:
        """Return the placed hitbox, or () unless the phase is ACTIVE."""
        if self.phase is not Phase.ACTIVE:
            return ()
        return place_hitbox(self.hitbox, self.x, self.y)

    def graze_zone(self) -> Hitbox:
        """Return the current hitbox grown by GRAZE_MARGIN, or () unless a touch is a HIT.

        Source: 06-scoring.md, rules 3 and 5.
        """
        if self.effect_on_touch() is not TouchEffect.HIT:
            return ()
        return grow_hitbox(self.current_hitbox(), GRAZE_MARGIN)

    def is_off_screen(self) -> bool:
        """Return True only in ACTIVE, when fully past a side wall or fully below the floor.

        Never true at the top, where drifters enter. Source: 07-drifters.md, rule 12.
        """
        if self.phase is not Phase.ACTIVE:
            return False
        half_w: float = self.width / 2
        half_h: float = self.height / 2
        return self.x + half_w <= 0 or self.x - half_w >= SCREEN_W or self.y - half_h >= SCREEN_H

    def warning_center(self) -> tuple[float, float]:
        """Return (x, y) moved just inside the screen, px: the drifter's footprint stays on it.

        Source: 07-drifters.md, rule 9; 91-decision-log.md, row 39.
        """
        half_w: float = self.width / 2
        half_h: float = self.height / 2
        return (
            min(max(self.x, half_w), SCREEN_W - half_w),
            min(max(self.y, half_h), SCREEN_H - half_h),
        )

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the drifter in WARNING from `birth`.

        Raises ValueError when the placement switches a specialty on: the base has none.
        A drifter with a specialty or its own timers overrides this.
        """
        if birth.specialty_enabled is True:
            raise ValueError(f"{cls.drifter_type.value} has no specialty")
        return cls(
            x=birth.x,
            y=birth.y,
            variant=birth.variant,
            width=birth.width,
            height=birth.height,
            speed=birth.speed,
            hitbox=birth.hitbox,
            warning_ticks=birth.warning_ticks,
        )

    @classmethod
    @abstractmethod
    def default_y(cls, height: float) -> float:
        """Return the start y, px, a placement gets when it sets none."""

    @abstractmethod
    def update(self, ctx: TickContext) -> Self:
        """Advance one 60 Hz tick and return a new drifter. Never mutates self."""

    @abstractmethod
    def effect_on_touch(self) -> TouchEffect:
        """Return what touching this drifter does."""

    @abstractmethod
    def may_hit_ship(self) -> bool:
        """Return whether this drifter, in its current state, can hit the ship.

        Each drifter decides, for example from `hit_ship`. The base has no default (LD-06).
        """


def tick_warning[T: Drifter](drifter: T) -> T:
    """Return `drifter` after one WARNING tick, position unchanged.

    Once ticks_in_phase + 1 reaches warning_ticks the drifter turns ACTIVE with
    ticks_in_phase 0. Source: 07-drifters.md, rules 1 and 9.
    """
    ticks: int = drifter.ticks_in_phase + 1
    if ticks >= drifter.warning_ticks:
        return replace(drifter, phase=Phase.ACTIVE, ticks_in_phase=0)
    return replace(drifter, ticks_in_phase=ticks)
