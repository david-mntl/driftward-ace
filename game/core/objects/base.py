"""The shared object base: phases, birth facts, the abstract object and its specialty slot.

An object carries final numbers only. It never knows the level. Screen px, y down, x and y at
the object's center. Stdlib and `core` only, no frame time, no randomness.

Source: docs/contracts/systems/objects.md, Interface and Rules, The base.
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


class ObjectType(Enum):
    """Every object the game knows. One member per built object spec in 07-objects.md."""

    METEORITE = "meteorite"
    """Source: objects/01-meteorite.md."""


class Phase(Enum):
    """Where an object is in its life."""

    WARNING = "warning"
    """The entry warning shows. The object can't touch anything."""

    ACTIVE = "active"
    """The object is on the field and can touch the ship."""

    GONE = "gone"
    """The object is finished. The run drops it this tick."""


class TouchEffect(Enum):
    """What touching an object does."""

    HIT = "hit"
    """A hit. Source: 05-lives-and-damage.md, rule 1."""

    COLLECT = "collect"
    """Reserved for coins. No object returns it yet."""

    NONE = "none"
    """Nothing happens."""


@dataclass(frozen=True, slots=True)
class TickContext:
    """Per-tick facts an object may read in `update`. Never the level."""

    ship: Ship
    """The ship as it was at the start of this tick."""


@dataclass(frozen=True, slots=True)
class Birth:
    """Everything the spawner settled for one new object. Final numbers only."""

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
    """The Timer multiplier for the object's own timers. An object without timers ignores it."""

    specialty_enabled: bool | None
    """The placement's specialty switch. None means the object's default."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Specialty(ABC):
    """An optional extra behavior on top of an object's movement. Only the interface exists."""

    enabled: bool
    """Switched on or off for this object."""

    @abstractmethod
    def update(self, owner: GameObject, ctx: TickContext) -> Self:
        """Advance the specialty one 60 Hz tick and return the new one."""

    def effect_on_ship(self, owner: GameObject, ship: Ship) -> Ship | None:
        """Return the ship after this specialty acts on it, or None for no effect."""
        return None


@dataclass(frozen=True, slots=True, kw_only=True)
class GameObject(ABC):
    """One object on the field after a tick. Screen px, y down, x and y at its center."""

    object_type: ClassVar[ObjectType]
    """Set by each subclass."""

    uid: int = 0
    """Unique within a run, from 1. Set by `core.run.add_objects`. 0 before that."""

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
    """Where the object is in its life."""

    ticks_in_phase: int = 0
    """Ticks spent in the current phase. 0 on the state where it starts."""

    specialty: Specialty | None = None
    """The optional extra behavior. None when the object has none."""

    hit_ship: bool = False
    """A fact: this object has hit the ship at least once. Set by the run.

    What it means for later touches is the object's own rule (`may_hit_ship`).
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

        Never true at the top, where objects enter. Source: 07-objects.md, rule 12.
        """
        if self.phase is not Phase.ACTIVE:
            return False
        half_w: float = self.width / 2
        half_h: float = self.height / 2
        return self.x + half_w <= 0 or self.x - half_w >= SCREEN_W or self.y - half_h >= SCREEN_H

    def warning_center(self) -> tuple[float, float]:
        """Return (x, y) moved just inside the screen, px: the object's footprint stays on it.

        Source: 07-objects.md, rule 9; 91-decision-log.md, row 39.
        """
        half_w: float = self.width / 2
        half_h: float = self.height / 2
        return (
            min(max(self.x, half_w), SCREEN_W - half_w),
            min(max(self.y, half_h), SCREEN_H - half_h),
        )

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the object in WARNING from `birth`.

        Raises ValueError when the placement switches a specialty on: the base has none.
        An object with a specialty or its own timers overrides this.
        """
        if birth.specialty_enabled is True:
            raise ValueError(f"{cls.object_type.value} has no specialty")
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
        """Advance one 60 Hz tick and return a new object. Never mutates self."""

    @abstractmethod
    def effect_on_touch(self) -> TouchEffect:
        """Return what touching this object does."""

    @abstractmethod
    def may_hit_ship(self) -> bool:
        """Return whether this object, in its current state, can hit the ship.

        Each object decides, for example from `hit_ship`. The base has no default (LD-06).
        """


def tick_warning[T: GameObject](obj: T) -> T:
    """Return `obj` after one WARNING tick, position unchanged.

    Once ticks_in_phase + 1 reaches warning_ticks the object turns ACTIVE with
    ticks_in_phase 0. Source: 07-objects.md, rules 1 and 9.
    """
    ticks: int = obj.ticks_in_phase + 1
    if ticks >= obj.warning_ticks:
        return replace(obj, phase=Phase.ACTIVE, ticks_in_phase=0)
    return replace(obj, ticks_in_phase=ticks)
