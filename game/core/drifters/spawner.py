"""The spawner: the only way a drifter is created, and the only place that reads a level.

The level is applied once, at birth. The drifter keeps its speed and never knows the level.
Pure: no logging, no randomness, no frame time.

Source: docs/contracts/systems/drifters.md, Rules, Spawner; 08-difficulty.md, rules 3 to 5.
"""

import logging
import random
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

    x: float | None = None
    """Center x, screen px. None: the drifter's default x (`start_position`)."""

    y: float | None = None
    """Center y, screen px. None: the drifter's default y (`start_position`)."""

    variant: str | None = None
    """The variant's name. None: the drifter's default variant."""

    as_level: int | None = None
    """Level to use for this drifter. None: the run's level."""

    specialty_enabled: bool | None = None
    """Specialty switch. None: the drifter's default."""

    invert: bool = False
    """The spec's invert. A drifter without one refuses True."""

    speed: float | None = None
    """Level 1 speed, px/tick along the path, replacing the default. None: the default.

    Hazard speed multiplier still applies. Debug test spawn list only (scope report DRA-39).
    """

    seed: int | None = None
    """0 to `MAX_SEED`. Picks a seeded drifter's path. Required for a seeded drifter (its `born`
    raises without one), refused for any other. The loaders fill it with `placement_seed` when
    the file leaves it out. Source: drifters/07-ufo.md, seed (locked)."""


MAX_SEED: Final[int] = 4_294_967_295
"""The largest seed a file may give, 2^32 - 1. Not a game value: the size `placement_seed`
draws."""

DEBUG_SPAWNS_SOURCE: Final[str] = "debug_spawns"
"""The source name of the debug list's rows, for `placement_seed`."""


def placement_seed(source: str, index: int) -> int:
    """Return the default seed, 0 to `MAX_SEED`, of the placement at `index` (from 0) in `source`.

    `source` is a wave id, or `DEBUG_SPAWNS_SOURCE`. Python seeds a generator from text with
    SHA-512, so the result is the same on every platform and every run. Pure.
    Source: drifters.md, Rules, Spawner, Placement seed.
    """
    return random.Random(f"{source}#{index}").getrandbits(MAX_SEED.bit_length())


def _birth_speed(
    cls: type[Drifter], placement: Placement, type_tuning: DrifterTypeTuning, speed_mult: float
) -> float:
    """Return the final speed, px/tick: 0.0 for a parked drifter, else Level 1 speed x `speed_mult`.

    Raises ValueError when a parked drifter's placement sets a speed. Source: drifters.md,
    Rules, Spawner, step 4.
    """
    if cls.parked:
        if placement.speed is not None:
            raise ValueError(f"{placement.drifter_type.value} has no speed")
        return 0.0
    base_speed: float = (
        type_tuning.speed_ratio * TOP_SIDE_SPEED if placement.speed is None else placement.speed
    )
    return base_speed * speed_mult


def _check_seed(cls: type[Drifter], placement: Placement) -> None:
    """Raise ValueError("<type> has no seed") when a seed is set for a drifter that isn't seeded."""
    if placement.seed is not None and not cls.seeded:
        raise ValueError(f"{placement.drifter_type.value} has no seed")


def spawn_drifter(placement: Placement, level: int, tuning: DrifterTuning) -> Drifter:
    """Create one drifter from `placement`, at `level`: in WARNING, or ACTIVE for the coin.

    Raises ValueError for a drifter type with no class or no tuning, an unknown variant, a
    level outside 1 to 8, a coordinate, specialty or invert the drifter refuses, a speed for
    a parked drifter, or a seed for a drifter that isn't seeded. The playtest switches beat
    `as_level`. Entry warnings and the re-hit cooldown never scale.
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
    speed_mult: float = hazard_speed_mult(speed_level)
    speed: float = _birth_speed(cls, placement, type_tuning, speed_mult)
    start_width, start_height = cls.start_size(variant.width, variant.height, variant.extra)
    x, y = cls.start_position(placement.x, placement.y, start_width, start_height, placement.invert)
    _check_seed(cls, placement)
    return cls.born(
        Birth(
            x=x,
            y=y,
            variant=variant_name,
            width=variant.width,
            height=variant.height,
            hitbox=variant.hitbox,
            speed=speed,
            warning_ticks=type_tuning.entry_warning_ticks,
            timer_mult=timer_mult(timer_level),
            specialty_enabled=placement.specialty_enabled,
            invert=placement.invert,
            variant_extra=variant.extra,
            rehit_cooldown_ticks=tuning.hazards.rehit_cooldown_ticks,
            rehit_dim=tuning.hazards.rehit_dim,
            type_extra=type_tuning.extra,
            telegraph_min_ticks=tuning.hazards.telegraph_min_ticks,
            hazard_speed_mult=speed_mult,
            seed=placement.seed,
            graze_margin=tuning.hazards.graze_margin,
        )
    )
