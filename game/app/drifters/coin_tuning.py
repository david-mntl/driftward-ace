"""The coin's tuning file: its checks, and the records built from it.

The file has a schema of its own: each variant gives its points and glint, the crystal's sizes are
shared, and its hitbox is worked out by core.drifters.coin. The loader registers itself by type,
so the app names no drifter.

Source: docs/contracts/systems/app.md, Rules, Tuning loader (The coin's file);
docs/contracts/schemas/coin-tuning.schema.json.
"""

from app.drifters.checks import (
    check_even_size,
    check_fields,
    check_integer,
    check_number,
    check_variant_name,
)
from app.drifters.registry import register_tuning
from core.drifters.base import DrifterType
from core.drifters.coin import CoinTypeExtra, CoinVariantExtra, coin_hitbox
from core.drifters.tuning import DrifterTypeTuning, VariantTuning

_COIN_FIELDS: frozenset[str] = frozenset(
    {
        "default_variant",
        "variants",
        "crystal_width",
        "crystal_height",
        "body_height",
        "ring_width",
        "ring_height",
        "glint_size",
        "glint_left",
        "glint_top",
        "popup_ticks",
        "popup_rise_per_tick",
    }
)
"""Every field of the coin's file, all required. Source: coin-tuning.schema.json."""


_COIN_VARIANT_FIELDS: frozenset[str] = frozenset({"points", "glint"})


@register_tuning(DrifterType.COIN)
def _load_coin(name: str, data: object) -> DrifterTypeTuning:
    """Check the coin's file and build its record.

    Every variant has the crystal's width and height; its hitbox is the crystal's middle
    rectangle from core.drifters.coin.coin_hitbox. The coin has no speed_ratio and no entry
    warning: the record gets 0.0 and 0, which nothing reads for a parked pickup. The footprint
    check of the other files passes by the rules below and is not run again.
    Source: docs/contracts/systems/app.md, Rules, Tuning loader (The coin's file, What the loader
    builds for the coin); coin-tuning.schema.json.
    """
    fields: dict[str, object] = check_fields(name, "", data, _COIN_FIELDS)
    width: int = check_even_size(name, "crystal_width", fields["crystal_width"])
    height: int = check_even_size(name, "crystal_height", fields["crystal_height"])
    body_height: int = check_even_size(name, "body_height", fields["body_height"])
    ring_width: int = check_even_size(name, "ring_width", fields["ring_width"])
    ring_height: int = check_even_size(name, "ring_height", fields["ring_height"])
    glint_size: int = check_integer(name, "glint_size", fields["glint_size"], 1)
    glint_left: int = check_integer(name, "glint_left", fields["glint_left"], 0)
    glint_top: int = check_integer(name, "glint_top", fields["glint_top"], 0)
    popup_ticks: int = check_integer(name, "popup_ticks", fields["popup_ticks"], 1)
    rise: float = check_number(name, "popup_rise_per_tick", fields["popup_rise_per_tick"])
    if rise < 0:
        raise ValueError(f"{name}: popup_rise_per_tick must be a number >= 0")
    if body_height >= height:
        raise ValueError(f"{name}: body_height must be less than crystal_height")
    if glint_left + glint_size > width or glint_top + glint_size > height:
        raise ValueError(f"{name}: the glint must lie inside the crystal's box")
    extras: dict[str, CoinVariantExtra] = _coin_variants(name, fields["variants"])
    default_variant: str = check_variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in extras:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    variants: dict[str, VariantTuning] = {
        variant: VariantTuning(
            width=float(width),
            height=float(height),
            hitbox=coin_hitbox(width, body_height),
            extra=extra,
        )
        for variant, extra in extras.items()
    }
    return DrifterTypeTuning(
        variants=variants,
        default_variant=default_variant,
        speed_ratio=0.0,
        entry_warning_ticks=0,
        extra=CoinTypeExtra(
            body_height=body_height,
            ring_width=ring_width,
            ring_height=ring_height,
            glint_size=glint_size,
            glint_left=glint_left,
            glint_top=glint_top,
            popup_ticks=popup_ticks,
            popup_rise_per_tick=rise,
        ),
    )


def _coin_variants(name: str, data: object) -> dict[str, CoinVariantExtra]:
    """Check the coin's `variants` object and return each variant's points and glint."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    extras: dict[str, CoinVariantExtra] = {}
    for key, value in data.items():
        variant: str = check_variant_name(name, f"variants.{key}", key)
        path: str = f"variants.{variant}"
        fields: dict[str, object] = check_fields(name, path, value, _COIN_VARIANT_FIELDS)
        glint: object = fields["glint"]
        if not isinstance(glint, bool):
            raise ValueError(f"{name}: {path}.glint must be a boolean")
        extras[variant] = CoinVariantExtra(
            points=check_integer(name, f"{path}.points", fields["points"], 1), glint=glint
        )
    return extras
