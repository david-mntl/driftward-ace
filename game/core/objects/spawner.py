"""The spawner: the only way an object is created, and the only place that reads a level.

The level is applied once, at birth. The object keeps its speed and never knows the level.
Pure: no logging, no randomness, no frame time.

Source: docs/contracts/systems/objects.md, Rules, Spawner; 08-difficulty.md, rules 3 to 5.
"""

import logging
from dataclasses import dataclass
from typing import Final

from core.levels import check_level, hazard_speed_mult, timer_mult
from core.objects.base import Birth, GameObject, ObjectType
from core.objects.registry import object_class
from core.objects.tuning import ObjectTuning, ObjectTypeTuning, VariantTuning
from core.ship import TOP_SIDE_SPEED

log = logging.getLogger(__name__)

BASE_LEVEL: Final[int] = 1
"""The level whose multipliers apply when a playtest switch is off."""


@dataclass(frozen=True, slots=True)
class Placement:
    """Where and how to place one object. Screen px, y down, at its center."""

    object_type: ObjectType
    """Which object to place."""

    x: float
    """Center x, screen px."""

    y: float | None = None
    """Center y, screen px. None: the object's `default_y` for its variant."""

    variant: str | None = None
    """The variant's name. None: the object's default variant."""

    as_level: int | None = None
    """Level to use for this object. None: the run's level."""

    specialty_enabled: bool | None = None
    """Specialty switch. None: the object's default."""


def spawn_object(placement: Placement, level: int, tuning: ObjectTuning) -> GameObject:
    """Create one object in WARNING from `placement`, at `level`.

    Raises ValueError for an object type with no class or no tuning, an unknown variant, or
    a level outside 1 to 8. The playtest switches beat `as_level`. Entry warnings never scale.
    """
    cls: type[GameObject] = object_class(placement.object_type)
    type_name: str = placement.object_type.value
    type_tuning: ObjectTypeTuning | None = tuning.objects.get(placement.object_type)
    if type_tuning is None:
        raise ValueError(f"no tuning for object type '{type_name}'")
    variant_name: str = (
        type_tuning.default_variant if placement.variant is None else placement.variant
    )
    variant: VariantTuning | None = type_tuning.variants.get(variant_name)
    if variant is None:
        raise ValueError(f"unknown variant '{variant_name}' for object type '{type_name}'")
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
