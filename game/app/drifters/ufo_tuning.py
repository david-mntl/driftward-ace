"""The UFO's tuning file: its checks, and the records built from it.

The file has a schema of its own: each variant gives its disc and dome sizes, the weave and its
band are shared, its hitbox is worked out by core.drifters.ufo, and every variant and the weave
must pass core.drifters.ufo.check_ufo_variant and check_ufo_weave. The loader registers itself by
type, so the app names no drifter.

Source: docs/contracts/systems/app.md, Rules, Tuning loader (The UFO's file);
docs/contracts/schemas/ufo-tuning.schema.json.
"""

from app.drifters.checks import (
    DRIFTER_FIELDS,
    check_fields,
    check_integer,
    check_number,
    check_positive,
    check_variant_name,
    check_warning_ticks,
)
from app.drifters.registry import register_tuning
from core.drifters.base import DrifterType
from core.drifters.tuning import DrifterTypeTuning, VariantTuning
from core.drifters.ufo import UfoTypeExtra, check_ufo_variant, check_ufo_weave, ufo_hitbox

_UFO_FIELDS: frozenset[str] = DRIFTER_FIELDS | frozenset(
    {
        "weave_change_ticks_min",
        "weave_change_ticks_max",
        "weave_step_min",
        "weave_step_max",
        "weave_speed_max",
        "weave_turn",
        "band_top",
        "band_bottom",
    }
)
"""Every field of the UFO's file, all required. Source: ufo-tuning.schema.json."""


_UFO_VARIANT_FIELDS: frozenset[str] = frozenset({"disc_width", "disc_height", "dome_radius"})


@register_tuning(DrifterType.UFO)
def _load_ufo(name: str, data: object) -> DrifterTypeTuning:
    """Check the UFO's file and build its record.

    Each variant's width and height are its disc's; its hitbox, disc then dome, comes from
    core.drifters.ufo.ufo_hitbox. Every variant must pass check_ufo_variant and the weave
    check_ufo_weave; a core message is kept as it is, after the variant's path for a variant. The
    footprint check of the other files is not run: the dome lies above the disc by design.
    Source: docs/contracts/systems/app.md, Rules, Tuning loader (The UFO's file, What the loader
    builds for the UFO); ufo-tuning.schema.json.
    """
    fields: dict[str, object] = check_fields(name, "", data, _UFO_FIELDS)
    speed_ratio: float = check_number(name, "speed_ratio", fields["speed_ratio"])
    if speed_ratio < 0:
        raise ValueError(f"{name}: speed_ratio must be a number >= 0")
    warning_ticks: int = check_warning_ticks(name, fields["entry_warning_ticks"])
    band_top: float = check_number(name, "band_top", fields["band_top"])
    if band_top < 0:
        raise ValueError(f"{name}: band_top must be a number >= 0")
    extra = UfoTypeExtra(
        weave_change_ticks_min=check_integer(
            name, "weave_change_ticks_min", fields["weave_change_ticks_min"], 1
        ),
        weave_change_ticks_max=check_integer(
            name, "weave_change_ticks_max", fields["weave_change_ticks_max"], 1
        ),
        weave_step_min=float(check_positive(name, "weave_step_min", fields["weave_step_min"])),
        weave_step_max=float(check_positive(name, "weave_step_max", fields["weave_step_max"])),
        weave_speed_max=float(check_positive(name, "weave_speed_max", fields["weave_speed_max"])),
        weave_turn=float(check_positive(name, "weave_turn", fields["weave_turn"])),
        band_top=float(band_top),
        band_bottom=float(check_positive(name, "band_bottom", fields["band_bottom"])),
    )
    variants: dict[str, VariantTuning] = _ufo_variants(name, fields["variants"])
    default_variant: str = check_variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in variants:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    try:
        check_ufo_weave(extra)
    except ValueError as err:
        raise ValueError(f"{name}: {err}") from err
    return DrifterTypeTuning(
        variants=variants,
        default_variant=default_variant,
        speed_ratio=speed_ratio,
        entry_warning_ticks=warning_ticks,
        extra=extra,
    )


def _ufo_variants(name: str, data: object) -> dict[str, VariantTuning]:
    """Check the UFO's `variants` object and build each variant from its disc and dome, px."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    variants: dict[str, VariantTuning] = {}
    for key, value in data.items():
        variant: str = check_variant_name(name, f"variants.{key}", key)
        path: str = f"variants.{variant}"
        fields: dict[str, object] = check_fields(name, path, value, _UFO_VARIANT_FIELDS)
        disc_width: float = float(
            check_integer(name, f"{path}.disc_width", fields["disc_width"], 1)
        )
        disc_height: float = float(
            check_integer(name, f"{path}.disc_height", fields["disc_height"], 1)
        )
        dome_radius: float = float(
            check_integer(name, f"{path}.dome_radius", fields["dome_radius"], 1)
        )
        try:
            check_ufo_variant(disc_width, disc_height, dome_radius)
        except ValueError as err:
            raise ValueError(f"{name}: {path}: {err}") from err
        variants[variant] = VariantTuning(
            width=disc_width,
            height=disc_height,
            hitbox=ufo_hitbox(disc_width, disc_height, dome_radius),
            extra=None,
        )
    return variants
