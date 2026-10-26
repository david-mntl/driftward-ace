"""The floating island's tuning file: its checks, and the records built from it.

The file has a schema of its own: each variant gives its shape kind and size, the arm is shared,
and its hitbox is worked out by core.drifters.floating_island. The loader registers itself by
type, so the app names no drifter.

Source: docs/contracts/systems/app.md, Rules, Tuning loader (The floating island's file);
docs/contracts/schemas/floating-island-tuning.schema.json.
"""

from app.drifters.checks import check_even_size, check_fields, check_variant_name
from app.drifters.registry import register_tuning
from core.drifters.base import DrifterType
from core.drifters.floating_island import (
    IslandShape,
    IslandTypeExtra,
    IslandVariantExtra,
    island_hitbox,
)
from core.drifters.tuning import DrifterTypeTuning, VariantTuning

_ISLAND_FIELDS: frozenset[str] = frozenset({"default_variant", "variants", "arm"})
"""Every field of the floating island's file, all required.

Source: floating-island-tuning.schema.json.
"""


_ISLAND_VARIANT_FIELDS: frozenset[str] = frozenset({"shape", "width", "height"})


_ISLAND_ARM_SHAPES: frozenset[IslandShape] = frozenset({IslandShape.L_SHAPE, IslandShape.T_SHAPE})
"""Shapes whose width and height must be more than arm.

Source: floating-island-tuning.schema.json.
"""


@register_tuning(DrifterType.FLOATING_ISLAND)
def _load_floating_island(name: str, data: object) -> DrifterTypeTuning:
    """Check the floating island's file and build its record.

    Each variant's hitbox comes from core.drifters.floating_island.island_hitbox, not inverted.
    The island has no speed_ratio and no entry warning: the record gets 0.0 and 0, which nothing
    reads for a parked blocker. The footprint check of the other files is not run: island_hitbox
    builds the shapes inside the footprint, and a polygon is never read as a box.
    Source: docs/contracts/systems/app.md, Rules, Tuning loader (The floating island's file, What
    the loader builds for the floating island); floating-island-tuning.schema.json.
    """
    fields: dict[str, object] = check_fields(name, "", data, _ISLAND_FIELDS)
    arm: int = check_even_size(name, "arm", fields["arm"])
    variants: dict[str, VariantTuning] = _island_variants(name, fields["variants"], arm)
    default_variant: str = check_variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in variants:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    return DrifterTypeTuning(
        variants=variants,
        default_variant=default_variant,
        speed_ratio=0.0,
        entry_warning_ticks=0,
        extra=IslandTypeExtra(arm=float(arm)),
    )


def _island_variants(name: str, data: object, arm: int) -> dict[str, VariantTuning]:
    """Check the floating island's `variants` object and build each variant, un-inverted."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    kinds: str = ", ".join(member.value for member in IslandShape)
    variants: dict[str, VariantTuning] = {}
    for key, value in data.items():
        variant: str = check_variant_name(name, f"variants.{key}", key)
        path: str = f"variants.{variant}"
        fields: dict[str, object] = check_fields(name, path, value, _ISLAND_VARIANT_FIELDS)
        raw_shape: object = fields["shape"]
        if raw_shape not in {member.value for member in IslandShape}:
            raise ValueError(f"{name}: {path}.shape must be one of {kinds}")
        shape: IslandShape = IslandShape(raw_shape)
        width: int = check_even_size(name, f"{path}.width", fields["width"])
        height: int = check_even_size(name, f"{path}.height", fields["height"])
        if shape in _ISLAND_ARM_SHAPES:
            if arm >= width:
                raise ValueError(f"{name}: {path}.width must be more than arm")
            if arm >= height:
                raise ValueError(f"{name}: {path}.height must be more than arm")
        variants[variant] = VariantTuning(
            width=float(width),
            height=float(height),
            hitbox=island_hitbox(shape, float(width), float(height), float(arm), False),
            extra=IslandVariantExtra(shape=shape),
        )
    return variants
