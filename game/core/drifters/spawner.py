"""The spawner: the only way a drifter is created, and the only place that reads a level.

The level is applied once, at birth. The drifter keeps its speed and never knows the level.
Pure: no logging, no randomness, no frame time.

Source: docs/contracts/systems/drifters.md, Rules, Spawner; 08-difficulty.md, rules 3 to 5.
"""

import logging
from dataclasses import dataclass
from typing import Final

from core.drifters.base import Birth, Drifter, DrifterType
from core.drifters.registry import drifter_class
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, VariantTuning
from core.levels import check_level, hazard_speed_mult, timer_mult
from core.ship import TOP_SIDE_SPEED

log = logging.getLogger(__name__)

BASE_LEVEL: Final[int] = 1
"""The level whose multipliers apply when a playtest switch is off."""


@dataclass(frozen=True, slots=True)
class Placement:
    """Where and how to place one drifter. Screen px, y down, at its center."""

    drifter_type: DrifterType
    """Which drifter to place."""

    x: float
    """Center x, screen px."""

    y: float | None = None
    """Center y, screen px. None: the drifter's `default_y` for its variant."""

    variant: str | None = None
    """The variant's name. None: the drifter's default variant."""

    as_level: int | None = None
    """Level to use for this drifter. None: the run's level."""

    specialty_enabled: bool | None = None
    """Specialty switch. None: the drifter's default."""


def spawn_drifter(placement: Placement, level: int, tuning: DrifterTuning) -> Drifter:
    """Create one drifter in WARNING from `placement`, at `level`.

    Raises ValueError for a drifter type with no class or no tuning, an unknown variant, or
    a level outside 1 to 8. The playtest switches beat `as_level`. Entry warnings never scale.
    """
    cls: type[Drifter] = drifter_class(placement.drifter_type)
    type_name: str = placement.drifter_type.value
    type_tuning: DrifterTypeTuning | None = tuning.drifters.get(placement.drifter_type)
    if type_tuning is None:
        raise ValueError(f"no tuning for drifter type '{type_name}'")
    variant_name: str = (
        type_tuning.default_variant if placement.variant is None else placement.variant
    )
    variant: VariantTuning | None = type_tuning.variants.get(variant_name)
    if variant is None:
        raise ValueError(f"unknown variant '{variant_name}' for drifter type '{type_name}'")
    use_level: int = level if placement.as_level is None else placement.as_level
    check_level(use_level)
    speed_level: int = use_level if tuning.switches.hazard_speed_scaling else BASE_LEVEL
    timer_level: int = use_level if tuning.switches.timer_scaling else BASE_LEVEL
    y: float = cls.default_y(variant.height) if placement.y is None else placement.y
    return cls.born(
        Birth(
            x=placement.x,
            y=y,
            variant=variant_name,
            width=variant.width,
            height=variant.height,
            hitbox=variant.hitbox,
            speed=type_tuning.speed_ratio * TOP_SIDE_SPEED * hazard_speed_mult(speed_level),
            warning_ticks=type_tuning.entry_warning_ticks,
            timer_mult=timer_mult(timer_level),
            specialty_enabled=placement.specialty_enabled,
        )
    )
