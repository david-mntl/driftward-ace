"""Checked drifter tuning values the app hands to core. Records only.

The app checks the tuning files and builds these. Core trusts them.

Source: docs/contracts/systems/drifters.md, Interface, tuning.py.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field

from core.collision import Hitbox
from core.drifters.base import (
    DEFAULT_REHIT_COOLDOWN_TICKS,
    DEFAULT_REHIT_DIM,
    DEFAULT_TELEGRAPH_MIN_TICKS,
    GRAZE_MARGIN,
    DrifterType,
    DrifterTypeExtra,
    VariantExtra,
)

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class VariantTuning:
    """One size variant of a drifter."""

    width: float
    """Visible width, px."""

    height: float
    """Visible height, px."""

    hitbox: Hitbox
    """Shapes as offsets from the center, px."""

    extra: VariantExtra | None = None
    """The drifter's own per-variant values. None for a drifter with none."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DrifterTypeTuning:
    """The tuning of one drifter type."""

    variants: Mapping[str, VariantTuning]
    """The variants by name."""

    default_variant: str
    """One of the variant names."""

    speed_ratio: float
    """Level 1 speed as a multiple of `core.ship.TOP_SIDE_SPEED`.

    Not read for a parked drifter: the loader gives the coin 0.0.
    """

    entry_warning_ticks: int
    """Entry warning length, ticks. At least 1 for a hazard.

    0 for the coin, a pickup with no entry warning.
    """

    extra: DrifterTypeExtra | None = None
    """The type's own values. None for the meteorite and the satellite."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PlaytestSwitches:
    """Playtest switches that turn the level table off."""

    hazard_speed_scaling: bool = True
    """False: Level 1 hazard speed multiplier at every level."""

    timer_scaling: bool = True
    """False: Level 1 Timer multiplier at every level."""


@dataclass(frozen=True, slots=True, kw_only=True)
class HazardRules:
    """Values every hazard shares. A field left out keeps its default."""

    rehit_cooldown_ticks: int = DEFAULT_REHIT_COOLDOWN_TICKS
    """Ticks a hazard can't hit again after a hit, at least 0. Never scales with level."""

    rehit_dim: float = DEFAULT_REHIT_DIM
    """Brightness share of a hazard during its cooldown, 0..1."""

    telegraph_min_ticks: int = DEFAULT_TELEGRAPH_MIN_TICKS
    """The shortest a scaled telegraph may get, ticks, at least 0."""

    graze_margin: float = GRAZE_MARGIN
    """Px every hazard's graze zone grows each hitbox shape by, above 0."""


@dataclass(frozen=True, slots=True, kw_only=True)
class DrifterTuning:
    """All drifter tuning for a run."""

    drifters: Mapping[DrifterType, DrifterTypeTuning]
    """The tuning of each drifter type."""

    switches: PlaytestSwitches
    """The playtest switches."""

    hazards: HazardRules = field(default_factory=HazardRules)
    """The values every hazard shares."""
