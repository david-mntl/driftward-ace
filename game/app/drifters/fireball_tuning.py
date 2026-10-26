"""The fireball's tuning file: its checks, and the records built from it.

The file has a schema of its own: each variant gives its head width, and its hitbox is worked out
by core.drifters.fireball. The loader registers itself by type, so the app names no drifter.

Source: docs/contracts/systems/app.md, Rules, Tuning loader (The fireball's file);
docs/contracts/schemas/fireball-tuning.schema.json.
"""

from app.drifters.checks import (
    DRIFTER_FIELDS,
    check_fields,
    check_number,
    check_positive,
    check_variant_name,
    check_warning_ticks,
    is_number,
)
from app.drifters.registry import register_tuning
from core.drifters.base import DrifterType
from core.drifters.fireball import FireballTypeExtra, fireball_hitbox
from core.drifters.tuning import DrifterTypeTuning, VariantTuning

_FIREBALL_FIELDS: frozenset[str] = DRIFTER_FIELDS | frozenset({"angle_degrees", "tail_ratio"})
"""Every field of the fireball's file, all required. Source: fireball-tuning.schema.json."""


_FIREBALL_VARIANT_FIELDS: frozenset[str] = frozenset({"head_width"})


@register_tuning(DrifterType.FIREBALL)
def _load_fireball(name: str, data: object) -> DrifterTypeTuning:
    """Check the fireball's file and build its record.

    Each variant's width and height are its head width; its hitbox, head then tail, comes from
    core.drifters.fireball.fireball_hitbox, not inverted. The footprint check of the other files
    is not run: the tail lies outside the head's footprint by design.
    Source: docs/contracts/systems/app.md, Rules, Tuning loader (The fireball's file, What the
    loader builds for the fireball); fireball-tuning.schema.json.
    """
    fields: dict[str, object] = check_fields(name, "", data, _FIREBALL_FIELDS)
    speed_ratio: float = check_number(name, "speed_ratio", fields["speed_ratio"])
    if speed_ratio < 0:
        raise ValueError(f"{name}: speed_ratio must be a number >= 0")
    warning_ticks: int = check_warning_ticks(name, fields["entry_warning_ticks"])
    angle: object = fields["angle_degrees"]
    if not is_number(angle) or not 0 <= angle < 90:
        raise ValueError(f"{name}: angle_degrees must be a number >= 0 and < 90")
    tail_ratio: float = check_positive(name, "tail_ratio", fields["tail_ratio"])
    head_widths: dict[str, float] = _fireball_head_widths(name, fields["variants"])
    default_variant: str = check_variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in head_widths:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    variants: dict[str, VariantTuning] = {
        variant: VariantTuning(
            width=head_width,
            height=head_width,
            hitbox=fireball_hitbox(head_width, tail_ratio, angle, False),
            extra=None,
        )
        for variant, head_width in head_widths.items()
    }
    return DrifterTypeTuning(
        variants=variants,
        default_variant=default_variant,
        speed_ratio=speed_ratio,
        entry_warning_ticks=warning_ticks,
        extra=FireballTypeExtra(angle_degrees=angle, tail_ratio=tail_ratio),
    )


def _fireball_head_widths(name: str, data: object) -> dict[str, float]:
    """Check the fireball's `variants` object and return each variant's head width, px."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    head_widths: dict[str, float] = {}
    for key, value in data.items():
        variant: str = check_variant_name(name, f"variants.{key}", key)
        path: str = f"variants.{variant}"
        fields: dict[str, object] = check_fields(name, path, value, _FIREBALL_VARIANT_FIELDS)
        head_widths[variant] = check_positive(name, f"{path}.head_width", fields["head_width"])
    return head_widths
