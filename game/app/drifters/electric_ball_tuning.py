"""The electric ball's tuning file: its checks, and the records built from it.

The file has a schema of its own: each variant gives its ball size and pulse radius, the charge
and fire cycle and the look's widths are shared, its hitbox is worked out by
core.drifters.electric_ball, and every variant must pass check_electric_ball_variant. The loader
registers itself by type, so the app names no drifter.

Source: docs/contracts/systems/app/tuning-loader.md, Rules (The electric ball's file);
docs/contracts/schemas/electric-ball-tuning.schema.json.
"""

from app.drifters.checks import (
    DRIFTER_FIELDS,
    check_even_size,
    check_fields,
    check_integer,
    check_number,
    check_positive,
    check_variant_name,
    check_warning_ticks,
    is_number,
)
from app.drifters.registry import register_tuning
from core.drifters.base import DrifterType
from core.drifters.electric_ball import (
    ElectricBallTypeExtra,
    ElectricBallVariantExtra,
    check_electric_ball_variant,
    electric_ball_hitbox,
)
from core.drifters.tuning import DrifterTypeTuning, VariantTuning

_ELECTRIC_BALL_FIELDS: frozenset[str] = DRIFTER_FIELDS | frozenset(
    {
        "charge_ticks",
        "fire_ticks",
        "charge_rays",
        "ray_length",
        "ray_width",
        "outline_width",
        "rim_width",
        "fill_opacity",
    }
)
"""Every field of the electric ball's file, all required.

Source: electric-ball-tuning.schema.json.
"""


_ELECTRIC_BALL_VARIANT_FIELDS: frozenset[str] = frozenset({"ball_size", "pulse_radius"})


@register_tuning(DrifterType.ELECTRIC_BALL)
def _load_electric_ball(name: str, data: object) -> DrifterTypeTuning:
    """Check the electric ball's file and build its record.

    Each variant's width and height are its ball_size; its hitbox, the pulse circle, comes from
    core.drifters.electric_ball.electric_ball_hitbox. The footprint check of the other files is
    not run: the pulse circle lies outside the ball by design. Source: tuning-loader.md, Rules
    (The electric ball's file, What the loader builds for the electric ball).
    """
    fields: dict[str, object] = check_fields(name, "", data, _ELECTRIC_BALL_FIELDS)
    speed_ratio: float = check_number(name, "speed_ratio", fields["speed_ratio"])
    if speed_ratio < 0:
        raise ValueError(f"{name}: speed_ratio must be a number >= 0")
    warning_ticks: int = check_warning_ticks(name, fields["entry_warning_ticks"])
    fill_opacity: object = fields["fill_opacity"]
    if not is_number(fill_opacity) or not 0 < fill_opacity <= 1:
        raise ValueError(f"{name}: fill_opacity must be a number > 0 and <= 1")
    extra = ElectricBallTypeExtra(
        charge_ticks=check_integer(name, "charge_ticks", fields["charge_ticks"], 1),
        fire_ticks=check_integer(name, "fire_ticks", fields["fire_ticks"], 1),
        charge_rays=check_integer(name, "charge_rays", fields["charge_rays"], 1),
        ray_length=float(check_positive(name, "ray_length", fields["ray_length"])),
        ray_width=float(check_positive(name, "ray_width", fields["ray_width"])),
        outline_width=float(check_positive(name, "outline_width", fields["outline_width"])),
        rim_width=float(check_positive(name, "rim_width", fields["rim_width"])),
        fill_opacity=float(fill_opacity),
    )
    variants: dict[str, VariantTuning] = _electric_ball_variants(name, fields["variants"])
    default_variant: str = check_variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in variants:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    return DrifterTypeTuning(
        variants=variants,
        default_variant=default_variant,
        speed_ratio=speed_ratio,
        entry_warning_ticks=warning_ticks,
        extra=extra,
    )


def _electric_ball_variants(name: str, data: object) -> dict[str, VariantTuning]:
    """Check the electric ball's `variants` object and build each variant, px.

    Every variant must pass check_electric_ball_variant; its message is kept as it is, after the
    variant's path.
    """
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    variants: dict[str, VariantTuning] = {}
    for key, value in data.items():
        variant: str = check_variant_name(name, f"variants.{key}", key)
        path: str = f"variants.{variant}"
        fields: dict[str, object] = check_fields(name, path, value, _ELECTRIC_BALL_VARIANT_FIELDS)
        ball_size: float = float(check_even_size(name, f"{path}.ball_size", fields["ball_size"]))
        pulse_radius: float = float(
            check_integer(name, f"{path}.pulse_radius", fields["pulse_radius"], 1)
        )
        try:
            check_electric_ball_variant(ball_size, pulse_radius)
        except ValueError as err:
            raise ValueError(f"{name}: {path}: {err}") from err
        variants[variant] = VariantTuning(
            width=ball_size,
            height=ball_size,
            hitbox=electric_ball_hitbox(pulse_radius),
            extra=ElectricBallVariantExtra(pulse_radius=pulse_radius),
        )
    return variants
