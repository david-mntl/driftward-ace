"""Load and check the drifter tuning files and the playtest switches, once, at startup.

Reads `tuning/playtest.json` and one `tuning/drifters/<drifter_type value>.json` per DrifterType,
checks every rule of their schemas by hand (pygbag has no schema library), and builds the core
records. Core trusts what this returns. Any bad file raises ValueError naming the file and the
field; a missing file raises FileNotFoundError as it is. Never falls back to a default.
Not a startup module: it imports core.drifters, so only app.frame imports it, inside the guard.

Source: docs/contracts/systems/app.md, Interface and Rules, Tuning loader;
docs/contracts/schemas/drifter-tuning.schema.json;
docs/contracts/schemas/playtest-switches.schema.json.
"""

import json
import logging
import math
import re
from pathlib import Path
from typing import TypeGuard

from core.collision import Box, Circle, Shape
from core.drifters.base import DrifterType
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning

log = logging.getLogger(__name__)

TUNING_DIR: Path = Path(__file__).resolve().parent.parent / "tuning"
"""The game's tuning folder. Read at call time, so a check can point it elsewhere."""

PLAYTEST_FILE: str = "playtest.json"
"""The playtest switches file, in TUNING_DIR."""

DRIFTERS_DIR: str = "drifters"
"""The drifter tuning folder, in TUNING_DIR. One `<drifter_type value>.json` per DrifterType."""

_VARIANT_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
"""Variant names. Source: drifter-tuning.schema.json, $defs.variant_name."""

_SWITCH_FIELDS: frozenset[str] = frozenset({"hazard_speed_scaling", "timer_scaling"})
_DRIFTER_FIELDS: frozenset[str] = frozenset(
    {"default_variant", "variants", "speed_ratio", "entry_warning_ticks"}
)
_VARIANT_FIELDS: frozenset[str] = frozenset({"width", "height", "hitbox"})
_CIRCLE_FIELDS: frozenset[str] = frozenset({"shape", "cx", "cy", "r"})
_BOX_FIELDS: frozenset[str] = frozenset({"shape", "cx", "cy", "w", "h"})


def load_tuning() -> DrifterTuning:
    """Read and check the playtest switches and every drifter's tuning file, then build them."""
    switches: PlaytestSwitches = _load_switches(Path(PLAYTEST_FILE))
    drifters: dict[DrifterType, DrifterTypeTuning] = {
        drifter_type: _load_drifter(Path(DRIFTERS_DIR) / f"{drifter_type.value}.json")
        for drifter_type in DrifterType
    }
    log.info(
        "tuning loaded drifters=%s hazard_speed_scaling=%s timer_scaling=%s",
        ",".join(drifter_type.value for drifter_type in drifters),
        switches.hazard_speed_scaling,
        switches.timer_scaling,
    )
    return DrifterTuning(drifters=drifters, switches=switches)


def _read_json(relative: Path) -> tuple[str, object]:
    """Return (the file's name from the tuning folder down, its parsed JSON).

    Invalid JSON raises ValueError naming the file. A missing file raises FileNotFoundError.
    """
    name: str = f"tuning/{relative.as_posix()}"
    text: str = (TUNING_DIR / relative).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{name}: not valid JSON: {err}") from err
    return name, data


def _load_switches(relative: Path) -> PlaytestSwitches:
    """Check the playtest switches file and build its record."""
    name, data = _read_json(relative)
    fields: dict[str, object] = _fields(name, "", data, _SWITCH_FIELDS)
    return PlaytestSwitches(
        hazard_speed_scaling=_boolean(name, "hazard_speed_scaling", fields),
        timer_scaling=_boolean(name, "timer_scaling", fields),
    )


def _load_drifter(relative: Path) -> DrifterTypeTuning:
    """Check one drifter tuning file and build its record."""
    name, data = _read_json(relative)
    fields: dict[str, object] = _fields(name, "", data, _DRIFTER_FIELDS)
    variants: dict[str, VariantTuning] = _variants(name, fields["variants"])
    default_variant: str = _variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in variants:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    speed_ratio: float = _number(name, "speed_ratio", fields["speed_ratio"])
    if speed_ratio < 0:
        raise ValueError(f"{name}: speed_ratio must be a number >= 0")
    return DrifterTypeTuning(
        variants=variants,
        default_variant=default_variant,
        speed_ratio=speed_ratio,
        entry_warning_ticks=_warning_ticks(name, fields["entry_warning_ticks"]),
    )


def _variants(name: str, data: object) -> dict[str, VariantTuning]:
    """Check the `variants` object: at least one, each name valid, each variant valid."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    variants: dict[str, VariantTuning] = {}
    for key, value in data.items():
        variant: str = _variant_name(name, f"variants.{key}", key)
        variants[variant] = _variant(name, f"variants.{variant}", value)
    return variants


def _variant(name: str, path: str, data: object) -> VariantTuning:
    """Check one variant: width and height > 0, at least one shape, each inside the footprint."""
    fields: dict[str, object] = _fields(name, path, data, _VARIANT_FIELDS)
    width: float = _positive(name, f"{path}.width", fields["width"])
    height: float = _positive(name, f"{path}.height", fields["height"])
    shapes: object = fields["hitbox"]
    if not isinstance(shapes, list):
        raise ValueError(f"{name}: {path}.hitbox must be a list")
    if not shapes:
        raise ValueError(f"{name}: {path}.hitbox must have at least one shape")
    hitbox: list[Shape] = []
    for index, item in enumerate(shapes):
        shape_path: str = f"{path}.hitbox[{index}]"
        shape: Shape = _shape(name, shape_path, item)
        _check_inside(name, shape_path, shape, width, height)
        hitbox.append(shape)
    return VariantTuning(width=width, height=height, hitbox=tuple(hitbox))


def _shape(name: str, path: str, data: object) -> Shape:
    """Check one hitbox shape, a circle or a box, and build it. Offsets from the center, px."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: {path} must be an object")
    kind: object = data.get("shape")
    if kind == "circle":
        fields: dict[str, object] = _fields(name, path, data, _CIRCLE_FIELDS)
        return Circle(
            cx=_number(name, f"{path}.cx", fields["cx"]),
            cy=_number(name, f"{path}.cy", fields["cy"]),
            r=_positive(name, f"{path}.r", fields["r"]),
        )
    if kind == "box":
        fields = _fields(name, path, data, _BOX_FIELDS)
        return Box(
            cx=_number(name, f"{path}.cx", fields["cx"]),
            cy=_number(name, f"{path}.cy", fields["cy"]),
            w=_positive(name, f"{path}.w", fields["w"]),
            h=_positive(name, f"{path}.h", fields["h"]),
        )
    raise ValueError(f"{name}: {path}.shape must be 'circle' or 'box'")


def _check_inside(name: str, path: str, shape: Shape, width: float, height: float) -> None:
    """Raise unless the shape lies inside the variant's width x height footprint, centered.

    Source: 07-drifters.md, rule 8 (a hitbox is never bigger than what the player sees).
    """
    if isinstance(shape, Circle):
        half_w, half_h = shape.r, shape.r
    else:
        half_w, half_h = shape.w / 2, shape.h / 2
    if abs(shape.cx) + half_w > width / 2 or abs(shape.cy) + half_h > height / 2:
        raise ValueError(f"{name}: {path} must lie inside the variant's width x height")


def _fields(name: str, path: str, data: object, allowed: frozenset[str]) -> dict[str, object]:
    """Check that data is an object with exactly the allowed fields, and return it."""
    where: str = path or "the file"
    if not isinstance(data, dict):
        raise ValueError(f"{name}: {where} must be an object")
    prefix: str = f"{path}." if path else ""
    missing: list[str] = sorted(allowed - data.keys())
    if missing:
        raise ValueError(f"{name}: {prefix}{missing[0]} is missing")
    unknown: list[str] = sorted(str(key) for key in data.keys() - allowed)
    if unknown:
        raise ValueError(f"{name}: {prefix}{unknown[0]} is not a known field")
    return {str(key): value for key, value in data.items()}


def _boolean(name: str, key: str, fields: dict[str, object]) -> bool:
    """Return fields[key] if it is a boolean, else raise."""
    value: object = fields[key]
    if not isinstance(value, bool):
        raise ValueError(f"{name}: {key} must be a boolean")
    return value


def _is_number(value: object) -> TypeGuard[int | float]:
    """True for a finite int or float. A bool is never a number here."""
    return not isinstance(value, bool) and isinstance(value, int | float) and math.isfinite(value)


def _number(name: str, path: str, value: object) -> float:
    """Return value if it is a number, else raise."""
    if not _is_number(value):
        raise ValueError(f"{name}: {path} must be a number")
    return value


def _positive(name: str, path: str, value: object) -> float:
    """Return value if it is a number > 0, else raise."""
    if not _is_number(value) or value <= 0:
        raise ValueError(f"{name}: {path} must be a number > 0")
    return value


def _warning_ticks(name: str, value: object) -> int:
    """Return entry_warning_ticks if it is an int >= 1 (never a bool), else raise."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name}: entry_warning_ticks must be an integer >= 1")
    return value


def _variant_name(name: str, path: str, value: object) -> str:
    """Return value if it is a valid variant name, else raise."""
    if not isinstance(value, str) or not _VARIANT_NAME.fullmatch(value):
        raise ValueError(f"{name}: {path} must be a string matching {_VARIANT_NAME.pattern}")
    return value
