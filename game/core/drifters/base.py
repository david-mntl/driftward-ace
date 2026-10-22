"""The shared drifter base: phases, birth facts, the abstract drifter and its specialty slot.

A drifter carries final numbers only. It never knows the level. Screen px, y down, x and y at
the drifter's center. Stdlib and `core` only, no frame time, no randomness.

Source: docs/contracts/systems/drifters.md, Interface and Rules, The base.
"""

from __future__ import annotations

import logging
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from enum import Enum
from typing import ClassVar, Final, Self

from core.collision import Box, Hitbox, grow_hitbox, place_hitbox
from core.popup import PointsPopup
from core.ship import Ship
from core.world import SCREEN_H, SCREEN_W

log = logging.getLogger(__name__)

GRAZE_MARGIN: Final[int] = 14
"""Graze zone margin around a hazard's hitbox, px. Source: 06-scoring.md, graze_margin (locked)."""

ENTRY_WARNING_SIZE: Final[int] = 24
"""Entry warning diameter, px, the same for every drifter. Source: 07-drifters.md,
entry_warning_size (guess)."""

DEFAULT_REHIT_COOLDOWN_TICKS: Final[int] = 180
"""Ticks a hazard can't hit again after a hit. Source: 05-lives-and-damage.md, rehit_cooldown
(guess)."""

DEFAULT_REHIT_DIM: Final[float] = 0.75
"""Brightness share of a hazard during its re-hit cooldown, 0..1. Source:
05-lives-and-damage.md, rehit_dim (guess)."""

DEFAULT_TELEGRAPH_MIN_TICKS: Final[int] = 45
"""Shortest a scaled telegraph may get, ticks. Source: 07-drifters.md, telegraph_min (locked)."""

TIMER_ROUND_DIGITS: Final[int] = 6
"""Decimals a scaled timer is rounded to before it is rounded up, so float error adds no tick."""


class DrifterType(Enum):
    """Every drifter the game knows. One member per built drifter spec in 07-drifters.md."""

    METEORITE = "meteorite"
    """Source: drifters/01-meteorite.md."""

    SATELLITE = "satellite"
    """Source: drifters/02-satellite.md."""

    CHAIN_LIGHTNING = "chain_lightning"
    """Source: drifters/03-chain-lightning.md."""

    FIREBALL = "fireball"
    """Source: drifters/06-fireball.md."""

    COIN = "coin"
    """Source: drifters/04-coin.md."""

    FLOATING_ISLAND = "floating_island"
    """Source: drifters/05-floating-islands.md."""


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
    """Touching it collects it: it pays and goes. The coin. Source: 06-scoring.md, rule 2."""

    BLOCK = "block"
    """Touching it neither hurts nor pays: it is ground the ship can't enter. The floating
    island. Source: 07-drifters.md, Summary (Blocker)."""

    NONE = "none"
    """Nothing happens."""


@dataclass(frozen=True, slots=True)
class TickContext:
    """Per-tick facts a drifter may read in `update`. Never the level."""

    ship: Ship
    """The ship as it was at the start of this tick."""

    scroll_step_px: float = 0.0
    """Px the world scrolls down on this tick. 0.0 before the scroll starts. A parked drifter
    moves by it. Source: 03-world-and-camera.md, rule 9."""


@dataclass(frozen=True, slots=True)
class VariantExtra:
    """Base of a drifter's own per-variant values. Empty.

    A drifter that needs some subclasses it in its own module.
    """


@dataclass(frozen=True, slots=True)
class DrifterTypeExtra:
    """Base of a drifter's own values that hold for every variant. Empty.

    A drifter that needs some subclasses it in its own module.
    """


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

    invert: bool
    """The placement's invert."""

    variant_extra: VariantExtra | None
    """The variant's own values. None for a drifter with none."""

    rehit_cooldown_ticks: int
    """Re-hit cooldown length, ticks. Never scaled."""

    rehit_dim: float
    """Brightness during the re-hit cooldown, 0..1."""

    type_extra: DrifterTypeExtra | None
    """The drifter type's own values. None for a drifter with none."""

    telegraph_min_ticks: int
    """The shortest a scaled telegraph may get, ticks."""


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

    parked: ClassVar[bool] = False
    """True: the drifter sits still in the world and moves only with the scroll (the coin). Read
    by the spawner. Source: 03-world-and-camera.md, rule 9."""

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

    has_entered: bool = False
    """It has been at least partly on screen while ACTIVE. Set by the run (`mark_entered`)."""

    rehit_cooldown_ticks: int = DEFAULT_REHIT_COOLDOWN_TICKS
    """Re-hit cooldown length, ticks, from the spawner."""

    rehit_dim: float = DEFAULT_REHIT_DIM
    """Brightness while the re-hit cooldown runs, 0..1, from the spawner."""

    rehit_ticks_left: int = 0
    """Ticks of re-hit cooldown still to come. 0 means it may hit. Set by the run."""

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

    def drawn_parts(self) -> tuple[Box, ...]:
        """Return upright boxes, screen px, that hold every pixel the view draws while ACTIVE.

        One box here: the width x height footprint. A drifter whose look reaches outside its
        footprint overrides this. Source: 07-drifters.md, rule 12; 91-decision-log.md, row 64.
        """
        return (Box(self.x, self.y, self.width, self.height),)

    def is_partly_on_screen(self) -> bool:
        """Return True when any drawn part shares area with the screen.

        Touching an edge from outside doesn't count. Source: 07-drifters.md, rule 12;
        91-decision-log.md, rows 58 and 64.
        """
        return any(_box_on_screen(part) for part in self.drawn_parts())

    def mark_entered(self) -> Self:
        """Return the drifter with `has_entered` True once it is ACTIVE and partly on screen.

        Otherwise it returns the drifter unchanged. `has_entered` never goes back to False.
        """
        if self.has_entered or self.phase is not Phase.ACTIVE or not self.is_partly_on_screen():
            return self
        return replace(self, has_entered=True)

    def is_off_screen(self) -> bool:
        """Return True only in ACTIVE, once entered, with every drawn part past a side or the floor.

        Each part may leave by a different edge. Never true at the top, where drifters enter, and
        never before `has_entered`. Source: 07-drifters.md, rule 12; 91-decision-log.md, rows 58
        and 64.
        """
        if self.phase is not Phase.ACTIVE or not self.has_entered:
            return False
        return all(_box_past_edge(part) for part in self.drawn_parts())

    def warning_center(self) -> tuple[float, float]:
        """Return (x, y) moved just inside the screen, px: the whole warning stays on it.

        Source: 07-drifters.md, rule 9; 91-decision-log.md, rows 39 and 62.
        """
        half: float = ENTRY_WARNING_SIZE / 2
        return (
            min(max(self.x, half), SCREEN_W - half),
            min(max(self.y, half), SCREEN_H - half),
        )

    def warning_tilt_degrees(self) -> float:
        """Return how far the entry warning's copy is turned, degrees, counterclockwise.

        0.0: the copy stays upright. A drifter whose warning shows where it flies overrides it.
        """
        return 0.0

    def warning_copy(self) -> Self:
        """Return the drifter the entry warning shows at half size. The drifter itself here.

        Its width also sizes the warning. Source: 07-drifters.md, entry_warning_size.
        """
        return self

    def settle_warning(self, ctx: TickContext) -> Self:
        """Return the drifter with its entry warning fixed from the ship in `ctx`.

        Called once, by `core.run.add_drifters`. Never moves the drifter or changes its phase or
        timers. The drifter unchanged here. Source: drifters/03-chain-lightning.md, rule 2.
        """
        return self

    def may_hit_ship(self) -> bool:
        """Return True while no re-hit cooldown runs: the one rule every hazard shares.

        Source: 05-lives-and-damage.md, rule 1.5; 91-decision-log.md, row 54.
        """
        return self.rehit_ticks_left == 0

    def brightness(self) -> float:
        """Return the share of normal brightness to draw at, 0..1.

        `rehit_dim` while the re-hit cooldown runs, else 1.0. Source: 05-lives-and-damage.md,
        rule 1.5, rehit_dim.
        """
        if self.rehit_ticks_left > 0:
            return self.rehit_dim
        return 1.0

    def collect_points(self) -> int:
        """Return the points the run adds to the coin points when it collects this drifter.

        0 here. Source: 06-scoring.md, rule 2.
        """
        return 0

    def collect_popup(self) -> PointsPopup | None:
        """Return the points popup the run shows when it collects this drifter, at age 0.

        None here: no popup. Source: drifters/04-coin.md, popup.
        """
        return None

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the drifter in WARNING from `birth`.

        Raises ValueError when the placement switches a specialty on or sets `invert`: the
        base has neither. A drifter with a specialty, an invert or its own fields overrides this.
        """
        name: str = cls.drifter_type.value
        if birth.specialty_enabled is True:
            raise ValueError(f"{name} has no specialty")
        if birth.invert:
            raise ValueError(f"{name} has no invert")
        return born_drifter(cls, birth)

    @classmethod
    @abstractmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        """Return the center, px, a new drifter starts at.

        A coordinate the placement set is kept. A missing one gets the drifter's default, or
        raises ValueError("<type> placement needs <x or y>") when the drifter has none.
        """

    @abstractmethod
    def update(self, ctx: TickContext) -> Self:
        """Advance one 60 Hz tick and return a new drifter. Never mutates self."""

    @abstractmethod
    def effect_on_touch(self) -> TouchEffect:
        """Return what touching this drifter does."""


def born_drifter[T: Drifter](cls: type[T], birth: Birth) -> T:
    """Return a `cls` in WARNING built from the shared fields of `birth`. No checks.

    Every other field keeps its default, so a subclass's own fields need defaults.
    """
    return cls(
        x=birth.x,
        y=birth.y,
        variant=birth.variant,
        width=birth.width,
        height=birth.height,
        speed=birth.speed,
        hitbox=birth.hitbox,
        warning_ticks=birth.warning_ticks,
        rehit_cooldown_ticks=birth.rehit_cooldown_ticks,
        rehit_dim=birth.rehit_dim,
    )


def _box_on_screen(box: Box) -> bool:
    """Return True when `box` shares area with the screen. Touching an edge from outside: False."""
    return (
        box.cx - box.w / 2 < SCREEN_W
        and box.cx + box.w / 2 > 0
        and box.cy - box.h / 2 < SCREEN_H
        and box.cy + box.h / 2 > 0
    )


def _box_past_edge(box: Box) -> bool:
    """Return True when `box` is fully past a side wall or fully below the floor, never the top."""
    return (
        box.cx + box.w / 2 <= 0 or box.cx - box.w / 2 >= SCREEN_W or box.cy - box.h / 2 >= SCREEN_H
    )


def tick_warning[T: Drifter](drifter: T) -> T:
    """Return `drifter` after one WARNING tick, position unchanged.

    Once ticks_in_phase + 1 reaches warning_ticks the drifter turns ACTIVE with
    ticks_in_phase 0. Source: 07-drifters.md, rules 1 and 9.
    """
    ticks: int = drifter.ticks_in_phase + 1
    if ticks >= drifter.warning_ticks:
        return replace(drifter, phase=Phase.ACTIVE, ticks_in_phase=0)
    return replace(drifter, ticks_in_phase=ticks)


def scale_timer(ticks: int, timer_mult: float) -> int:
    """Return `ticks` x `timer_mult` rounded up to a whole tick.

    Rounded to 6 decimals first, so a float error never adds a tick: 120 x 0.85 is 102.
    Source: 08-difficulty.md, rules 4 and 5.
    """
    return math.ceil(round(ticks * timer_mult, TIMER_ROUND_DIGITS))


def scale_telegraph(ticks: int, timer_mult: float, telegraph_min_ticks: int) -> int:
    """Return a telegraph at its level: never shorter than `telegraph_min_ticks`.

    Source: 08-difficulty.md, rules 4 and 5; 07-drifters.md, telegraph_min (locked).
    """
    return max(scale_timer(ticks, timer_mult), telegraph_min_ticks)
