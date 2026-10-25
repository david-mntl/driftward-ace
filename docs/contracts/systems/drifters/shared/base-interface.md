# Drifters, the base, interface
Part of: drifters
Read when: you write or review code in `game/core/drifters/base.py`.

## Interface

Import root is `game/`, as in the tests. Core modules import stdlib and `core` only, never pygame, `ui` or `app`. Every module-level constant is `typing.Final`. Every dataclass is `frozen=True, slots=True`. Every module with code has `log = logging.getLogger(__name__)`; `core.drifters` and `core.collision` log nothing (the run logs the drifter lifecycle, `docs/contracts/systems/run.md`, Logging).

### game/core/drifters/base.py
```python
# Imports: stdlib, core.collision, core.ship (Ship; GravityWell from DRA-96), core.world,
# core.popup (DRA-62, for PointsPopup).
GRAZE_MARGIN: Final[int] = 14  # 06-scoring.md, graze_margin, px (locked)
DEFAULT_REHIT_COOLDOWN_TICKS: Final[int] = (
    180  # 05-lives-and-damage.md, rehit_cooldown, ticks (guess). DRA-39
)
DEFAULT_REHIT_DIM: Final[float] = (
    0.75  # 05-lives-and-damage.md, rehit_dim, × brightness (guess). DRA-39
)
DEFAULT_TELEGRAPH_MIN_TICKS: Final[int] = (
    45  # 07-drifters.md, telegraph_min, ticks (locked). DRA-47
)


class DrifterType(Enum):
    """Every drifter the game knows. One member per drifter spec in 07-drifters.md that is built."""

    METEORITE = "meteorite"  # drifters/01-meteorite.md
    SATELLITE = "satellite"  # drifters/02-satellite.md. DRA-39
    CHAIN_LIGHTNING = "chain_lightning"  # drifters/03-chain-lightning.md. DRA-47
    FIREBALL = "fireball"  # drifters/06-fireball.md. DRA-56
    COIN = "coin"  # drifters/04-coin.md. DRA-62
    FLOATING_ISLAND = "floating_island"  # drifters/05-floating-islands.md. DRA-86
    PLANET = "planet"  # drifters/08-planet.md. DRA-96
    UFO = "ufo"  # drifters/07-ufo.md. DRA-104
    ELECTRIC_BALL = "electric_ball"  # drifters/10-electric-ball.md. DRA-111


class Phase(Enum):
    WARNING = "warning"  # the entry warning shows; the drifter can't touch anything
    ACTIVE = "active"  # the drifter is on the field and can touch the ship
    GONE = "gone"  # the drifter is finished; the run drops it this tick


class TouchEffect(Enum):
    HIT = "hit"  # touching it is a hit (05-lives-and-damage.md, rule 1)
    COLLECT = "collect"  # touching it collects it: it pays and goes (06-scoring.md, rule 2). The coin. DRA-62
    BLOCK = "block"  # touching it neither hurts nor pays: it is ground the ship can't enter
    # (07-drifters.md, Summary, Blocker). The floating island. DRA-86
    NONE = "none"  # touching it does nothing


@dataclass(frozen=True, slots=True)
class TickContext:
    """Per-tick facts a drifter may read in update(). Never the level."""

    ship: Ship  # the ship as it was at the start of this tick
    scroll_step_px: float = 0.0  # DRA-62. px the world scrolls down on this tick, from
    # core.scroll.scroll_step_px. 0.0 before the scroll starts. A parked drifter moves by it


@dataclass(frozen=True, slots=True)
class VariantExtra:
    """Base of a drifter's own per-variant values. Empty. A drifter that needs some
    subclasses it in its own module (the satellite: SatelliteVariantExtra). DRA-39."""


@dataclass(frozen=True, slots=True)
class DrifterTypeExtra:                                             # DRA-47
    """Base of a drifter's own values that hold for every variant. Empty. A drifter that needs
    some subclasses it in its own module (the chain lightning: ChainLightningTypeExtra)."""

@dataclass(frozen=True, slots=True)
class Birth:
    """Everything the spawner settled for one new drifter. Final numbers only."""

    x: float  # center x, screen px
    y: float  # center y, screen px, y down
    variant: str  # the variant's name
    width: float  # the variant's visible width, px
    height: float  # the variant's visible height, px
    hitbox: Hitbox  # the variant's shapes, offsets from the center
    speed: float  # final speed, px/tick, hazard speed × already applied
    warning_ticks: int  # entry warning length, ticks, never scaled
    timer_mult: float  # the Timer × to apply to the drifter's own timers (the chain lightning's charge)
    specialty_enabled: (
        bool | None
    )  # the placement's switch; None = the drifter's default
    invert: bool  # the placement's invert. DRA-39
    variant_extra: (
        VariantExtra | None
    )  # the variant's own values, None for a drifter with none. DRA-39
    rehit_cooldown_ticks: int  # re-hit cooldown length, ticks, never scaled. DRA-39
    rehit_dim: float  # brightness during the cooldown, 0..1. DRA-39
    type_extra: (
        DrifterTypeExtra | None
    )  # the drifter type's own values, None for a drifter with none. DRA-47
    telegraph_min_ticks: int  # the shortest a scaled telegraph may get, ticks. DRA-47
    hazard_speed_mult: float = 1.0  # DRA-104. The hazard speed × the spawner applied to speed
    # (the level's, or Level 1's with the switch off), for a drifter's own speeds (the UFO's weave)
    seed: int | None = None  # DRA-104. The placement's seed, for a seeded drifter; None otherwise


@dataclass(frozen=True, slots=True, kw_only=True)
class Specialty(ABC):
    """An optional extra behavior on top of a drifter's movement. Only the base exists."""

    enabled: bool  # switched on or off for this drifter

    @abstractmethod
    def update(self, owner: Drifter, ctx: TickContext) -> Self: ...
    def effect_on_ship(self, owner: Drifter, ship: Ship) -> Ship | None:
        ...
        # None: no effect. The default, and the only behavior so far.


@dataclass(frozen=True, slots=True, kw_only=True)
class Drifter(ABC):
    """One drifter on the field after a tick. Screen px, y down, x and y at its center."""

    drifter_type: ClassVar[DrifterType]  # set by each subclass
    parked: ClassVar[bool] = False  # DRA-62. True: it sits still in the world and moves only with
    # the scroll (03-world-and-camera.md, rule 9). The coin. Read by the spawner
    seeded: ClassVar[bool] = False  # DRA-104. True: its path comes from a seed, and every placement
    # of it carries one (the UFO). Read by the spawner and by the loaders that give a default seed
    uid: int = 0  # unique within a run, from 1. Set by core.run.add_drifters; 0 before
    x: float  # center x, screen px
    y: float  # center y, screen px, y down
    variant: str  # the variant's name, e.g. "medium"
    width: float  # visible width, px, from the variant
    height: float  # visible height, px, from the variant
    speed: float  # final speed, px/tick, set by the spawner
    hitbox: Hitbox  # shapes as offsets from (x, y), from the variant
    warning_ticks: int  # entry warning length, ticks
    phase: Phase = Phase.WARNING
    ticks_in_phase: int = (
        0  # ticks spent in the current phase. 0 on the state it starts
    )
    specialty: Specialty | None = None
    has_entered: bool = False  # DRA-39. It has been at least partly on screen while ACTIVE. Set by the run
    rehit_cooldown_ticks: int = (
        DEFAULT_REHIT_COOLDOWN_TICKS  # DRA-39. Cooldown length, ticks, from the spawner
    )
    rehit_dim: float = (
        DEFAULT_REHIT_DIM  # DRA-39. Brightness while cooling, 0..1, from the spawner
    )
    rehit_ticks_left: int = 0  # DRA-39. Ticks of re-hit cooldown still to come. 0 = it may hit. Set by the run

    def current_hitbox(self) -> Hitbox:
        ...
        # () unless phase is ACTIVE. Otherwise place_hitbox(hitbox, x, y).

    def graze_zone(self) -> Hitbox:
        ...
        # grow_hitbox(current_hitbox(), GRAZE_MARGIN) when effect_on_touch() is HIT, else ().

    def drawn_parts(self) -> tuple[Box, ...]:
        ...  # DRA-56
        # Upright boxes, screen px, that together hold every pixel the drifter's view draws while
        # ACTIVE. Here one box: Box(x, y, width, height), the footprint.

    def is_partly_on_screen(self) -> bool:
        ...  # DRA-39, judged on drawn_parts() from DRA-56
        # True when any box of drawn_parts() shares area with the screen (strict).

    def mark_entered(self) -> Self:
        ...  # DRA-39
        # self with has_entered True when ACTIVE and partly on screen; otherwise self unchanged.

    def is_off_screen(self) -> bool:
        ...  # judged on drawn_parts() from DRA-56
        # True only in ACTIVE, once has_entered, when every box of drawn_parts() is fully past a
        # side wall or fully below the floor. Never at the top.

    def warning_center(self) -> tuple[float, float]:
        ...
        # Where the entry warning is drawn: (x, y) moved just inside the screen.

    def warning_tilt_degrees(self) -> float:
        ...  # DRA-39
        # How far the warning copy is turned, degrees, counterclockwise on screen. 0.0 here.

    def warning_copy(self) -> Self:
        ...  # DRA-47
        # The drifter whose look the entry warning shows, scaled to a 14 px longest side.
        # self here.

    def settle_warning(self, ctx: TickContext) -> Self:
        ...  # DRA-47
        # Fix where the entry warning shows, from the ship at the moment the drifter enters the run.
        # Called once, by core.run.add_drifters. self unchanged here.

    def may_hit_ship(self) -> bool:
        ...  # DRA-39: concrete, the shared rule
        # rehit_ticks_left == 0. Subclasses don't override it.

    def brightness(self) -> float:
        ...  # DRA-39
        # rehit_dim while rehit_ticks_left > 0, else 1.0.

    def collect_points(self) -> int:
        ...  # DRA-62
        # Points the run adds to coin_points when it collects this drifter. 0 here.

    def collect_popup(self) -> PointsPopup | None:
        ...  # DRA-62
        # The points popup the run shows when it collects this drifter, born at age 0.
        # None here: no popup.

    def gravity_well(self) -> GravityWell | None:
        ...  # DRA-96
        # The gravity field this drifter pulls the ship with on this tick, placed at its center.
        # None here: no field.

    @classmethod
    def start_size(
        cls, width: float, height: float, variant_extra: VariantExtra | None
    ) -> tuple[float, float]:
        ...  # DRA-96
        # The width and height the spawner hands start_position: the box around everything the
        # drifter draws while ACTIVE. (width, height) here: the footprint.

    @classmethod
    def telegraph_ticks(cls, type_extra: DrifterTypeExtra | None) -> int | None:
        ...
        # The telegraph's length, ticks, before the level's scale and floor, or None: the drifter
        # has none (the default). wave_check reads it. An entry warning is not a telegraph.

    @classmethod
    def born(cls, birth: Birth) -> Self:
        ...
        # born_drifter(cls, birth), after two checks: raises ValueError("<type> has no specialty")
        # when birth.specialty_enabled is True, and ValueError("<type> has no invert") when
        # birth.invert is True. A subclass with a specialty, an invert or its own fields overrides it.

    @classmethod
    @abstractmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        ...  # DRA-39, replaces default_y
        # The center a new drifter starts at. A coordinate the placement set is kept; a missing
        # one gets the drifter's default. Raises ValueError("<type> placement needs <x or y>")
        # for a missing coordinate the drifter has no default for.

    @abstractmethod
    def update(self, ctx: TickContext) -> Self:
        ...
        # Advance one 60 Hz tick and return a new drifter. Never mutates self.

    @abstractmethod
    def effect_on_touch(self) -> TouchEffect: ...


def born_drifter[T: Drifter](cls: type[T], birth: Birth) -> T:
    ...  # DRA-39. PEP 695, bound Drifter
    # cls built in WARNING from birth's shared fields: x, y, variant, width, height, speed, hitbox,
    # warning_ticks, rehit_cooldown_ticks, rehit_dim. Every other field keeps its default, so a
    # subclass's own fields need defaults. No checks.


def tick_warning[T: Drifter](obj: T) -> T:
    ...  # PEP 695 type parameter, bound Drifter
    # The shared WARNING step: ticks_in_phase + 1, or ACTIVE with ticks_in_phase 0 once
    # ticks_in_phase + 1 reaches warning_ticks. Position unchanged.

def scale_timer(ticks: int, timer_mult: float) -> int: ...          # DRA-47
    # A drifter's own timer at its level: ticks × timer_mult rounded up to a whole tick.
def scale_telegraph(ticks: int, timer_mult: float, telegraph_min_ticks: int) -> int: ...   # DRA-47
    # A telegraph at its level: max(scale_timer(ticks, timer_mult), telegraph_min_ticks).
```
The code documents each field with the comment above, as `core/ship.py` does for `Ship`. `Drifter` and `Specialty` refer to each other, so the module uses `from __future__ import annotations` or string annotations. With `slots=True` the methods never use the zero-argument `super()`. DRA-39 removes the field `hit_ship` and the abstract `default_y`; `may_hit_ship` is no longer abstract. DRA-47 adds `warning_copy` and `settle_warning`, both concrete with a do-nothing default, so the meteorite, the satellite and the registry test's stubs need no change. DRA-56 adds `drawn_parts`, concrete, whose default is the footprint the two screen tests used before, so no existing drifter, stub or test changes behavior; `base.py` imports `Box` from `core.collision` for it. DRA-62 adds the `COIN` member, `TickContext.scroll_step_px` with a default of 0.0 (every existing `TickContext(ship=...)` call still builds), the class attribute `parked` (False) and the concrete `collect_points` (0) and `collect_popup` (None), so no existing drifter, stub or test changes behavior. `PointsPopup` is in `game/core/popup.py` (`docs/contracts/systems/run.md`, Interface). DRA-96 adds the `PLANET` member and two concrete hooks with do-nothing defaults, `gravity_well` (None) and the classmethod `start_size` (the footprint), so no existing drifter, stub or test changes behavior. `telegraph_ticks` is another concrete classmethod hook, None by default, so none of them changes either; the chain lightning overrides it. `GravityWell` is in `game/core/ship.py` (`docs/contracts/systems/ship.md`, Interface). DRA-104 adds the `UFO` member, the class attribute `seeded` (False) and two `Birth` fields with defaults at the end, `hazard_speed_mult` (1.0) and `seed` (None), so every existing `Birth(...)` call still builds and no existing drifter, stub or test changes behavior. DRA-111 adds the `ELECTRIC_BALL` member, last, and nothing else here: the electric ball builds on the hooks that exist (`systems/drifters/electric-ball/core.md`).
