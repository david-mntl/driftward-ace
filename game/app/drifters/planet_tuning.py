"""The planet's tuning file: its checks, and the records built from it.

The file has a schema of its own: each variant gives its size and its gravity field, the field
rings' look is shared, its hitbox is worked out by core.drifters.planet, and every pull_max must
pass core.ship.check_escapable_pull. The loader registers itself by type, so the app names no
drifter.

Source: docs/contracts/systems/app.md, Rules, Tuning loader (The planet's file);
docs/contracts/schemas/planet-tuning.schema.json.
"""

from app.drifters.checks import (
    check_even_size,
    check_fields,
    check_integer,
    check_positive,
    check_variant_name,
    check_warning_ticks,
    is_number,
)
from app.drifters.registry import register_tuning
from core.drifters.base import DrifterType
from core.drifters.planet import PlanetTypeExtra, PlanetVariantExtra, planet_hitbox
from core.drifters.tuning import DrifterTypeTuning, VariantTuning
from core.ship import check_escapable_pull

_PLANET_FIELDS: frozenset[str] = frozenset(
    {
        "default_variant",
        "variants",
        "entry_warning_ticks",
        "field_ring_trip",
        "field_ring_gap",
        "field_ring_fade",
        "field_ring_count",
    }
)
"""Every field of the planet's file, all required. Source: planet-tuning.schema.json."""


_PLANET_VARIANT_FIELDS: frozenset[str] = frozenset({"size", "pull_radius", "pull_max"})


_PLANET_FADE_MAX: float = 100.0
"""field_ring_fade is a percent, 0 to 100. Source: planet-tuning.schema.json."""


@register_tuning(DrifterType.PLANET)
def _load_planet(name: str, data: object) -> DrifterTypeTuning:
    """Check the planet's file and build its record.

    Each variant's width and height are its size; its hitbox comes from
    core.drifters.planet.planet_hitbox. The planet has no speed_ratio: the record gets 0.0, which
    the spawner never reads for a parked drifter. The footprint check of the other files passes by
    construction (a circle of radius size / 2 in a size x size box) and is not run again.
    Source: docs/contracts/systems/app.md, Rules, Tuning loader (The planet's file, What the
    loader builds for the planet); planet-tuning.schema.json.
    """
    fields: dict[str, object] = check_fields(name, "", data, _PLANET_FIELDS)
    warning_ticks: int = check_warning_ticks(name, fields["entry_warning_ticks"])
    ring_trip: int = check_integer(name, "field_ring_trip", fields["field_ring_trip"], 1)
    ring_gap: int = check_integer(name, "field_ring_gap", fields["field_ring_gap"], 0)
    ring_fade: object = fields["field_ring_fade"]
    if not is_number(ring_fade) or not 0 <= ring_fade <= _PLANET_FADE_MAX:
        raise ValueError(f"{name}: field_ring_fade must be a number from 0 to 100")
    ring_count: int = check_integer(name, "field_ring_count", fields["field_ring_count"], 0)
    variants: dict[str, VariantTuning] = _planet_variants(name, fields["variants"])
    default_variant: str = check_variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in variants:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    return DrifterTypeTuning(
        variants=variants,
        default_variant=default_variant,
        speed_ratio=0.0,
        entry_warning_ticks=warning_ticks,
        extra=PlanetTypeExtra(
            field_ring_trip=ring_trip,
            field_ring_gap=ring_gap,
            field_ring_fade=float(ring_fade),
            field_ring_count=ring_count,
        ),
    )


def _planet_variants(name: str, data: object) -> dict[str, VariantTuning]:
    """Check the planet's `variants` object and build each variant.

    pull_radius must be more than size / 2, and every pull_max must pass
    core.ship.check_escapable_pull; its message is kept as it is, after the variant's path.
    """
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    variants: dict[str, VariantTuning] = {}
    for key, value in data.items():
        variant: str = check_variant_name(name, f"variants.{key}", key)
        path: str = f"variants.{variant}"
        fields: dict[str, object] = check_fields(name, path, value, _PLANET_VARIANT_FIELDS)
        size: int = check_even_size(name, f"{path}.size", fields["size"])
        pull_radius: int = check_integer(name, f"{path}.pull_radius", fields["pull_radius"], 2)
        pull_max: float = check_positive(name, f"{path}.pull_max", fields["pull_max"])
        if pull_radius <= size / 2:
            raise ValueError(f"{name}: {path}.pull_radius must be more than size / 2")
        try:
            check_escapable_pull(pull_max)
        except ValueError as err:
            raise ValueError(f"{name}: {path}.{err}") from err
        variants[variant] = VariantTuning(
            width=float(size),
            height=float(size),
            hitbox=planet_hitbox(float(size)),
            extra=PlanetVariantExtra(pull_radius=float(pull_radius), pull_max=float(pull_max)),
        )
    return variants
