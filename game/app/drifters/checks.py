"""Shared checks for the drifter tuning files: field sets, numbers, shapes and variant names.

Every drifter's own tuning module (app/drifters/<drifter>_tuning.py) builds on these, so the rule
for a field type has one home. Each check raises ValueError naming the file and the field, as the
schemas say. Source: docs/contracts/systems/app.md, Rules, Tuning loader;
docs/contracts/schemas/drifter-tuning.schema.json.
"""

import math
import re
from collections.abc import Callable
from typing import TypeGuard

from core.collision import Box, Circle, Hitbox
from core.drifters.base import VariantExtra
from core.drifters.tuning import DrifterTypeTuning, VariantTuning

_VARIANT_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
"""Variant names. Source: drifter-tuning.schema.json, $defs.variant_name."""


DRIFTER_FIELDS: frozenset[str] = frozenset(
    {"default_variant", "variants", "speed_ratio", "entry_warning_ticks"}
)


VARIANT_FIELDS: frozenset[str] = frozenset({"width", "height", "hitbox"})


_CIRCLE_FIELDS: frozenset[str] = frozenset({"shape", "cx", "cy", "r"})


_BOX_FIELDS: frozenset[str] = frozenset({"shape", "cx", "cy", "w", "h"})


type ExtraBuilder = Callable[[str, str, dict[str, object], Hitbox], VariantExtra]
"""Checks a variant's own fields and hitbox, then builds its VariantExtra.

Called with (file name, variant path, the variant's fields, its checked hitbox).
"""


def check_even_size(name: str, path: str, value: object) -> int:
    """Return value if it is an even int >= 2 (never a bool), else raise."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 2 or value % 2:
        raise ValueError(f"{name}: {path} must be an even integer >= 2")
    return value


def check_shape(name: str, path: str, data: object) -> Circle | Box:
    """Check one hitbox shape, a circle or a box, and build it. Offsets from the center, px."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: {path} must be an object")
    kind: object = data.get("shape")
    if kind == "circle":
        fields: dict[str, object] = check_fields(name, path, data, _CIRCLE_FIELDS)
        return Circle(
            cx=check_number(name, f"{path}.cx", fields["cx"]),
            cy=check_number(name, f"{path}.cy", fields["cy"]),
            r=check_positive(name, f"{path}.r", fields["r"]),
        )
    if kind == "box":
        fields = check_fields(name, path, data, _BOX_FIELDS)
        return Box(
            cx=check_number(name, f"{path}.cx", fields["cx"]),
            cy=check_number(name, f"{path}.cy", fields["cy"]),
            w=check_positive(name, f"{path}.w", fields["w"]),
            h=check_positive(name, f"{path}.h", fields["h"]),
        )
    raise ValueError(f"{name}: {path}.shape must be 'circle' or 'box'")


def check_inside(name: str, path: str, shape: Circle | Box, width: float, height: float) -> None:
    """Raise unless the shape lies inside the variant's width x height footprint, centered.

    Takes only the circles and boxes `check_shape` builds; a Line never reaches it (the chain
    lightning has its own branch). Source: 07-drifters.md, rule 8 (a hitbox is never bigger than
    what the player sees); docs/contracts/systems/app.md, Impact (DRA-47).
    """
    if isinstance(shape, Circle):
        half_w, half_h = shape.r, shape.r
    else:
        half_w, half_h = shape.w / 2, shape.h / 2
    if abs(shape.cx) + half_w > width / 2 or abs(shape.cy) + half_h > height / 2:
        raise ValueError(f"{name}: {path} must lie inside the variant's width x height")


def check_fields(
    name: str,
    path: str,
    data: object,
    allowed: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> dict[str, object]:
    """Check that data is an object with only the allowed fields, every non-optional one there.

    Returns its fields.
    """
    where: str = path or "the file"
    if not isinstance(data, dict):
        raise ValueError(f"{name}: {where} must be an object")
    prefix: str = f"{path}." if path else ""
    missing: list[str] = sorted(allowed - optional - data.keys())
    if missing:
        raise ValueError(f"{name}: {prefix}{missing[0]} is missing")
    unknown: list[str] = sorted(str(key) for key in data.keys() - allowed)
    if unknown:
        raise ValueError(f"{name}: {prefix}{unknown[0]} is not a known field")
    return {str(key): value for key, value in data.items()}


def check_boolean(name: str, key: str, fields: dict[str, object]) -> bool:
    """Return fields[key] if it is a boolean, else raise."""
    value: object = fields[key]
    if not isinstance(value, bool):
        raise ValueError(f"{name}: {key} must be a boolean")
    return value


def is_number(value: object) -> TypeGuard[int | float]:
    """True for a finite int or float. A bool is never a number here."""
    return not isinstance(value, bool) and isinstance(value, int | float) and math.isfinite(value)


def check_number(name: str, path: str, value: object) -> float:
    """Return value if it is a number, else raise."""
    if not is_number(value):
        raise ValueError(f"{name}: {path} must be a number")
    return value


def check_positive(name: str, path: str, value: object) -> float:
    """Return value if it is a number > 0, else raise."""
    if not is_number(value) or value <= 0:
        raise ValueError(f"{name}: {path} must be a number > 0")
    return value


def check_integer(
    name: str, path: str, value: object, minimum: int, what: str | None = None
) -> int:
    """Return value if it is an int >= minimum (never a bool), else raise.

    The message reads `<path> must be <what>`, by default `an integer >= <minimum>`.
    """
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name}: {path} must be {what or f'an integer >= {minimum}'}")
    return value


def check_warning_ticks(name: str, value: object) -> int:
    """Return entry_warning_ticks if it is an int >= 1 (never a bool), else raise."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name}: entry_warning_ticks must be an integer >= 1")
    return value


def check_variant_name(name: str, path: str, value: object) -> str:
    """Return value if it is a valid variant name, else raise."""
    if not isinstance(value, str) or not _VARIANT_NAME.fullmatch(value):
        raise ValueError(f"{name}: {path} must be a string matching {_VARIANT_NAME.pattern}")
    return value


type OwnFields = tuple[frozenset[str], ExtraBuilder]
"""A drifter's own variant fields and the checker that builds its VariantExtra from them."""


def _variants(name: str, data: object, own: OwnFields | None) -> dict[str, VariantTuning]:
    """Check the `variants` object: at least one, each name valid, each variant valid."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    variants: dict[str, VariantTuning] = {}
    for key, value in data.items():
        variant: str = check_variant_name(name, f"variants.{key}", key)
        variants[variant] = _variant(name, f"variants.{variant}", value, own)
    return variants


def _variant(name: str, path: str, data: object, own: OwnFields | None) -> VariantTuning:
    """Check one variant: width and height > 0, at least one shape, each inside the footprint.

    A drifter with fields of its own (`own`) also gets those checked and its VariantExtra built.
    """
    allowed: frozenset[str] = VARIANT_FIELDS if own is None else VARIANT_FIELDS | own[0]
    fields: dict[str, object] = check_fields(name, path, data, allowed)
    width: float = check_positive(name, f"{path}.width", fields["width"])
    height: float = check_positive(name, f"{path}.height", fields["height"])
    shapes: object = fields["hitbox"]
    if not isinstance(shapes, list):
        raise ValueError(f"{name}: {path}.hitbox must be a list")
    if not shapes:
        raise ValueError(f"{name}: {path}.hitbox must have at least one shape")
    hitbox: list[Circle | Box] = []
    for index, item in enumerate(shapes):
        shape_path: str = f"{path}.hitbox[{index}]"
        shape: Circle | Box = check_shape(name, shape_path, item)
        check_inside(name, shape_path, shape, width, height)
        hitbox.append(shape)
    extra: VariantExtra | None = None if own is None else own[1](name, path, fields, tuple(hitbox))
    return VariantTuning(width=width, height=height, hitbox=tuple(hitbox), extra=extra)


def load_generic(name: str, data: object, own: OwnFields | None = None) -> DrifterTypeTuning:
    """Check a drifter's tuning file against drifter-tuning.schema.json and build its record.

    `own` is the drifter's own variant fields, when its schema adds some (the satellite's angle).
    A drifter with no module of its own registered in `app.drifters.registry` is checked here.
    """
    fields: dict[str, object] = check_fields(name, "", data, DRIFTER_FIELDS)
    variants: dict[str, VariantTuning] = _variants(name, fields["variants"], own)
    default_variant: str = check_variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in variants:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    speed_ratio: float = check_number(name, "speed_ratio", fields["speed_ratio"])
    if speed_ratio < 0:
        raise ValueError(f"{name}: speed_ratio must be a number >= 0")
    return DrifterTypeTuning(
        variants=variants,
        default_variant=default_variant,
        speed_ratio=speed_ratio,
        entry_warning_ticks=check_warning_ticks(name, fields["entry_warning_ticks"]),
    )
