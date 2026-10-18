"""Load and check the drifter tuning files, the playtest switches and the shared hazard values.

Reads `tuning/playtest.json`, `tuning/hazards.json` and one
`tuning/drifters/<drifter_type value>.json` per DrifterType, once, at startup. Checks every rule of
their schemas by hand (pygbag has no schema library) and builds the core records. Core trusts what
this returns. Any bad file raises ValueError naming the file and the field; a missing file raises
FileNotFoundError as it is. Never falls back to a default for a missing file. A hazards field left
out keeps its default from core.drifters.base. The chain lightning's file has a schema of its own:
its layouts become ChainLayout records, and its width, height and hitbox are worked out by
core.drifters.chain_lightning, so that rule has one home. The fireball's file has one too: each
variant gives its head width, and its hitbox is worked out by core.drifters.fireball.
Not a startup module: it imports core.drifters, so only app.frame imports it, inside the guard.

Source: docs/contracts/systems/app.md, Interface and Rules, Tuning loader;
docs/contracts/schemas/drifter-tuning.schema.json, satellite-tuning.schema.json,
chain-lightning-tuning.schema.json, fireball-tuning.schema.json, playtest-switches.schema.json and
hazards.schema.json.
"""

import json
import logging
import math
import re
from collections.abc import Callable
from pathlib import Path
from typing import TypeGuard

from core.collision import Box, Circle, Hitbox
from core.drifters.base import (
    DEFAULT_REHIT_COOLDOWN_TICKS,
    DEFAULT_REHIT_DIM,
    DEFAULT_TELEGRAPH_MIN_TICKS,
    DrifterType,
    VariantExtra,
)
from core.drifters.chain_lightning import (
    ArcNodes,
    ChainLayout,
    ChainLightningTypeExtra,
    ChainLightningVariantExtra,
    InvertMirror,
    Point,
    chain_hitbox,
    layout_size,
)
from core.drifters.fireball import FireballTypeExtra, fireball_hitbox
from core.drifters.satellite import SatelliteVariantExtra
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
    VariantTuning,
)

log = logging.getLogger(__name__)

TUNING_DIR: Path = Path(__file__).resolve().parent.parent / "tuning"
"""The game's tuning folder. Read at call time, so a check can point it elsewhere."""

PLAYTEST_FILE: str = "playtest.json"
"""The playtest switches file, in TUNING_DIR."""

HAZARDS_FILE: str = "hazards.json"
"""The shared hazard values file, in TUNING_DIR. Every field optional; the file must exist."""

DRIFTERS_DIR: str = "drifters"
"""The drifter tuning folder, in TUNING_DIR. One `<drifter_type value>.json` per DrifterType."""

_VARIANT_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
"""Variant names. Source: drifter-tuning.schema.json, $defs.variant_name."""

_SWITCH_FIELDS: frozenset[str] = frozenset({"hazard_speed_scaling", "timer_scaling"})
_HAZARD_FIELDS: frozenset[str] = frozenset({"rehit_cooldown", "rehit_dim", "telegraph_min"})
_DRIFTER_FIELDS: frozenset[str] = frozenset(
    {"default_variant", "variants", "speed_ratio", "entry_warning_ticks"}
)
_CHAIN_FIELDS: frozenset[str] = _DRIFTER_FIELDS | frozenset(
    {
        "node_spacing",
        "node_size",
        "arc_width",
        "charge_ticks",
        "fire_ticks",
        "charge_rays",
        "ray_length",
        "ray_width",
        "entry_warning_icon",
    }
)
"""Every field of the chain lightning's file, all required.

Source: chain-lightning-tuning.schema.json.
"""
_CHAIN_VARIANT_FIELDS: frozenset[str] = frozenset({"nodes", "arcs", "invert_mirror"})
_CHAIN_TOLERANCE: float = 1e-6
"""Units. Arc length and layout centering. Source: chain-lightning-tuning.schema.json."""
_FIREBALL_FIELDS: frozenset[str] = _DRIFTER_FIELDS | frozenset({"angle_degrees", "tail_ratio"})
"""Every field of the fireball's file, all required. Source: fireball-tuning.schema.json."""
_FIREBALL_VARIANT_FIELDS: frozenset[str] = frozenset({"head_width"})
_VARIANT_FIELDS: frozenset[str] = frozenset({"width", "height", "hitbox"})
_CIRCLE_FIELDS: frozenset[str] = frozenset({"shape", "cx", "cy", "r"})
_BOX_FIELDS: frozenset[str] = frozenset({"shape", "cx", "cy", "w", "h"})


type _ExtraBuilder = Callable[[str, str, dict[str, object], Hitbox], VariantExtra]
"""Checks a variant's own fields and hitbox, then builds its VariantExtra.

Called with (file name, variant path, the variant's fields, its checked hitbox).
"""


def load_tuning() -> DrifterTuning:
    """Read and check the playtest switches, the hazard values and every drifter's file."""
    switches: PlaytestSwitches = _load_switches(Path(PLAYTEST_FILE))
    hazards: HazardRules = _load_hazards(Path(HAZARDS_FILE))
    drifters: dict[DrifterType, DrifterTypeTuning] = {
        drifter_type: _load_drifter(Path(DRIFTERS_DIR) / f"{drifter_type.value}.json", drifter_type)
        for drifter_type in DrifterType
    }
    log.info(
        "tuning loaded drifters=%s hazard_speed_scaling=%s timer_scaling=%s "
        "rehit_cooldown=%d rehit_dim=%.2f telegraph_min=%d",
        ",".join(drifter_type.value for drifter_type in drifters),
        switches.hazard_speed_scaling,
        switches.timer_scaling,
        hazards.rehit_cooldown_ticks,
        hazards.rehit_dim,
        hazards.telegraph_min_ticks,
    )
    return DrifterTuning(drifters=drifters, switches=switches, hazards=hazards)


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


def _load_hazards(relative: Path) -> HazardRules:
    """Check the shared hazard values file and build its record. `{}` is valid.

    A field left out keeps its default from core.drifters.base. Source: hazards.schema.json.
    """
    name, data = _read_json(relative)
    fields: dict[str, object] = _fields(name, "", data, _HAZARD_FIELDS, optional=_HAZARD_FIELDS)
    cooldown: object = fields.get("rehit_cooldown", DEFAULT_REHIT_COOLDOWN_TICKS)
    if isinstance(cooldown, bool) or not isinstance(cooldown, int) or cooldown < 0:
        raise ValueError(f"{name}: rehit_cooldown must be an integer >= 0")
    dim: object = fields.get("rehit_dim", DEFAULT_REHIT_DIM)
    if not _is_number(dim) or not 0 <= dim <= 1:
        raise ValueError(f"{name}: rehit_dim must be a number from 0 to 1")
    telegraph_min: int = _integer(
        name, "telegraph_min", fields.get("telegraph_min", DEFAULT_TELEGRAPH_MIN_TICKS), 0
    )
    return HazardRules(
        rehit_cooldown_ticks=cooldown, rehit_dim=dim, telegraph_min_ticks=telegraph_min
    )


def _load_drifter(relative: Path, drifter_type: DrifterType) -> DrifterTypeTuning:
    """Check one drifter tuning file and build its record.

    A drifter type with fields of its own (in _OWN_FIELDS) is checked against its own schema.
    The chain lightning's and the fireball's files have schemas of their own throughout
    (_load_chain_lightning, _load_fireball).
    """
    name, data = _read_json(relative)
    if drifter_type is DrifterType.CHAIN_LIGHTNING:
        return _load_chain_lightning(name, data)
    if drifter_type is DrifterType.FIREBALL:
        return _load_fireball(name, data)
    fields: dict[str, object] = _fields(name, "", data, _DRIFTER_FIELDS)
    variants: dict[str, VariantTuning] = _variants(name, fields["variants"], drifter_type)
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


def _variants(name: str, data: object, drifter_type: DrifterType) -> dict[str, VariantTuning]:
    """Check the `variants` object: at least one, each name valid, each variant valid."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    variants: dict[str, VariantTuning] = {}
    for key, value in data.items():
        variant: str = _variant_name(name, f"variants.{key}", key)
        variants[variant] = _variant(name, f"variants.{variant}", value, drifter_type)
    return variants


def _variant(name: str, path: str, data: object, drifter_type: DrifterType) -> VariantTuning:
    """Check one variant: width and height > 0, at least one shape, each inside the footprint.

    A drifter type with fields of its own also gets those checked and its VariantExtra built.
    """
    own: tuple[frozenset[str], _ExtraBuilder] | None = _OWN_FIELDS.get(drifter_type)
    allowed: frozenset[str] = _VARIANT_FIELDS if own is None else _VARIANT_FIELDS | own[0]
    fields: dict[str, object] = _fields(name, path, data, allowed)
    width: float = _positive(name, f"{path}.width", fields["width"])
    height: float = _positive(name, f"{path}.height", fields["height"])
    shapes: object = fields["hitbox"]
    if not isinstance(shapes, list):
        raise ValueError(f"{name}: {path}.hitbox must be a list")
    if not shapes:
        raise ValueError(f"{name}: {path}.hitbox must have at least one shape")
    hitbox: list[Circle | Box] = []
    for index, item in enumerate(shapes):
        shape_path: str = f"{path}.hitbox[{index}]"
        shape: Circle | Box = _shape(name, shape_path, item)
        _check_inside(name, shape_path, shape, width, height)
        hitbox.append(shape)
    extra: VariantExtra | None = None if own is None else own[1](name, path, fields, tuple(hitbox))
    return VariantTuning(width=width, height=height, hitbox=tuple(hitbox), extra=extra)


def _satellite_extra(
    name: str, path: str, fields: dict[str, object], hitbox: Hitbox
) -> SatelliteVariantExtra:
    """Check a satellite variant: exactly two boxes (body, then panel bar) and its angle.

    Source: satellite-tuning.schema.json; drifters/02-satellite.md, variants.
    """
    if len(hitbox) != 2 or not all(isinstance(shape, Box) for shape in hitbox):
        raise ValueError(f"{name}: {path}.hitbox must be exactly two boxes")
    angle: object = fields["angle_degrees"]
    if not _is_number(angle) or not 0 <= angle < 90:
        raise ValueError(f"{name}: {path}.angle_degrees must be a number >= 0 and < 90")
    return SatelliteVariantExtra(angle_degrees=angle)


_OWN_FIELDS: dict[DrifterType, tuple[frozenset[str], _ExtraBuilder]] = {
    DrifterType.SATELLITE: (frozenset({"angle_degrees"}), _satellite_extra),
}
"""Drifter types with fields of their own: the extra variant fields and their checker.

A drifter type not listed here follows drifter-tuning.schema.json and has no VariantExtra.
Source: docs/contracts/systems/app.md, Rules, Tuning loader (A drifter's own fields).
"""


def _load_chain_lightning(name: str, data: object) -> DrifterTypeTuning:
    """Check the chain lightning's file and build its record.

    Each variant's layout is scaled by node_spacing into px; its width, height and hitbox come from
    core.drifters.chain_lightning. The footprint check of the other files is not run: lines are
    never read as boxes, and arc_width <= node_size keeps every line inside its nodes.
    Source: docs/contracts/systems/app.md, Rules, Tuning loader (The chain lightning's file, What
    the loader builds for the chain lightning); chain-lightning-tuning.schema.json.
    """
    fields: dict[str, object] = _fields(name, "", data, _CHAIN_FIELDS)
    speed_ratio: float = _number(name, "speed_ratio", fields["speed_ratio"])
    if speed_ratio < 0:
        raise ValueError(f"{name}: speed_ratio must be a number >= 0")
    warning_ticks: int = _warning_ticks(name, fields["entry_warning_ticks"])
    node_spacing: float = _positive(name, "node_spacing", fields["node_spacing"])
    node_size: float = _positive(name, "node_size", fields["node_size"])
    arc_width: float = _positive(name, "arc_width", fields["arc_width"])
    ray_length: float = _positive(name, "ray_length", fields["ray_length"])
    ray_width: float = _positive(name, "ray_width", fields["ray_width"])
    charge_ticks: int = _integer(name, "charge_ticks", fields["charge_ticks"], 1)
    fire_ticks: int = _integer(name, "fire_ticks", fields["fire_ticks"], 1)
    charge_rays: int = _integer(name, "charge_rays", fields["charge_rays"], 1)
    if arc_width > node_size:
        raise ValueError(f"{name}: arc_width must be <= node_size")
    layouts: dict[str, ChainLayout] = _chain_layouts(name, fields["variants"], node_spacing)
    default_variant: str = _variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in layouts:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    icon: str = _variant_name(name, "entry_warning_icon", fields["entry_warning_icon"])
    if icon not in layouts:
        raise ValueError(f"{name}: entry_warning_icon must be one of the variant names")
    variants: dict[str, VariantTuning] = {}
    for variant, layout in layouts.items():
        width, height = layout_size(layout.nodes, node_size)
        variants[variant] = VariantTuning(
            width=width,
            height=height,
            hitbox=chain_hitbox(layout.nodes, layout.arcs, node_size, arc_width),
            extra=ChainLightningVariantExtra(layout=layout),
        )
    return DrifterTypeTuning(
        variants=variants,
        default_variant=default_variant,
        speed_ratio=speed_ratio,
        entry_warning_ticks=warning_ticks,
        extra=ChainLightningTypeExtra(
            node_size=node_size,
            arc_width=arc_width,
            charge_ticks=charge_ticks,
            fire_ticks=fire_ticks,
            charge_rays=charge_rays,
            ray_length=ray_length,
            ray_width=ray_width,
            warning_layout=layouts[icon],
        ),
    )


def _chain_layouts(name: str, data: object, node_spacing: float) -> dict[str, ChainLayout]:
    """Check the chain lightning's `variants` object and build one layout per variant, in px."""
    if not isinstance(data, dict):
        raise ValueError(f"{name}: variants must be an object")
    if not data:
        raise ValueError(f"{name}: variants must have at least one variant")
    layouts: dict[str, ChainLayout] = {}
    for key, value in data.items():
        variant: str = _variant_name(name, f"variants.{key}", key)
        layouts[variant] = _chain_layout(name, f"variants.{variant}", value, node_spacing)
    return layouts


def _chain_layout(name: str, path: str, data: object, node_spacing: float) -> ChainLayout:
    """Check one chain lightning variant: its nodes, its arcs and invert_mirror.

    Nodes are in units of node_spacing. Every arc joins two different nodes 1 unit apart, no two
    arcs join the same pair, and the box around the nodes is centered on 0, 0. Builds the layout
    with every node multiplied by node_spacing.
    """
    fields: dict[str, object] = _fields(name, path, data, _CHAIN_VARIANT_FIELDS)
    raw_nodes: object = fields["nodes"]
    if not isinstance(raw_nodes, list) or not 2 <= len(raw_nodes) <= 3:
        raise ValueError(f"{name}: {path}.nodes must be a list of 2 or 3 points")
    units: list[Point] = []
    for index, point in enumerate(raw_nodes):
        if (
            not isinstance(point, list)
            or len(point) != 2
            or not _is_number(point[0])
            or not _is_number(point[1])
        ):
            raise ValueError(f"{name}: {path}.nodes[{index}] must be a list of two numbers")
        units.append((float(point[0]), float(point[1])))
    raw_arcs: object = fields["arcs"]
    if not isinstance(raw_arcs, list) or not raw_arcs:
        raise ValueError(f"{name}: {path}.arcs must be a list of at least one pair")
    arcs: list[ArcNodes] = []
    for index, pair in enumerate(raw_arcs):
        arc_path: str = f"{path}.arcs[{index}]"
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"{name}: {arc_path} must be a list of two integers >= 0")
        first: int = _integer(name, arc_path, pair[0], 0, "a list of two integers >= 0")
        second: int = _integer(name, arc_path, pair[1], 0, "a list of two integers >= 0")
        if first == second or first >= len(units) or second >= len(units):
            raise ValueError(f"{name}: {arc_path} must name two different nodes of its variant")
        if any({first, second} == {a, b} for a, b in arcs):
            raise ValueError(f"{name}: {arc_path} must not join the same two nodes as another arc")
        (x1, y1), (x2, y2) = units[first], units[second]
        if abs(math.hypot(x2 - x1, y2 - y1) - 1) > _CHAIN_TOLERANCE:
            raise ValueError(f"{name}: {arc_path} must join two nodes 1 unit apart")
        arcs.append((first, second))
    xs: list[float] = [x for x, _ in units]
    ys: list[float] = [y for _, y in units]
    if (
        abs((min(xs) + max(xs)) / 2) > _CHAIN_TOLERANCE
        or abs((min(ys) + max(ys)) / 2) > _CHAIN_TOLERANCE
    ):
        raise ValueError(f"{name}: {path}.nodes must be centered on 0, 0")
    mirror: object = fields["invert_mirror"]
    if mirror not in {member.value for member in InvertMirror}:
        raise ValueError(f"{name}: {path}.invert_mirror must be 'left_right' or 'top_bottom'")
    return ChainLayout(
        nodes=tuple((x * node_spacing, y * node_spacing) for x, y in units),
        arcs=tuple(arcs),
        invert_mirror=InvertMirror(mirror),
    )


def _load_fireball(name: str, data: object) -> DrifterTypeTuning:
    """Check the fireball's file and build its record.

    Each variant's width and height are its head width; its hitbox, head then tail, comes from
    core.drifters.fireball.fireball_hitbox, not inverted. The footprint check of the other files
    is not run: the tail lies outside the head's footprint by design.
    Source: docs/contracts/systems/app.md, Rules, Tuning loader (The fireball's file, What the
    loader builds for the fireball); fireball-tuning.schema.json.
    """
    fields: dict[str, object] = _fields(name, "", data, _FIREBALL_FIELDS)
    speed_ratio: float = _number(name, "speed_ratio", fields["speed_ratio"])
    if speed_ratio < 0:
        raise ValueError(f"{name}: speed_ratio must be a number >= 0")
    warning_ticks: int = _warning_ticks(name, fields["entry_warning_ticks"])
    angle: object = fields["angle_degrees"]
    if not _is_number(angle) or not 0 <= angle < 90:
        raise ValueError(f"{name}: angle_degrees must be a number >= 0 and < 90")
    tail_ratio: float = _positive(name, "tail_ratio", fields["tail_ratio"])
    head_widths: dict[str, float] = _fireball_head_widths(name, fields["variants"])
    default_variant: str = _variant_name(name, "default_variant", fields["default_variant"])
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
        variant: str = _variant_name(name, f"variants.{key}", key)
        path: str = f"variants.{variant}"
        fields: dict[str, object] = _fields(name, path, value, _FIREBALL_VARIANT_FIELDS)
        head_widths[variant] = _positive(name, f"{path}.head_width", fields["head_width"])
    return head_widths


def _shape(name: str, path: str, data: object) -> Circle | Box:
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


def _check_inside(name: str, path: str, shape: Circle | Box, width: float, height: float) -> None:
    """Raise unless the shape lies inside the variant's width x height footprint, centered.

    Takes only the circles and boxes `_shape` builds; a Line never reaches it (the chain lightning
    has its own branch). Source: 07-drifters.md, rule 8 (a hitbox is never bigger than what the
    player sees); docs/contracts/systems/app.md, Impact (DRA-47).
    """
    if isinstance(shape, Circle):
        half_w, half_h = shape.r, shape.r
    else:
        half_w, half_h = shape.w / 2, shape.h / 2
    if abs(shape.cx) + half_w > width / 2 or abs(shape.cy) + half_h > height / 2:
        raise ValueError(f"{name}: {path} must lie inside the variant's width x height")


def _fields(
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


def _integer(name: str, path: str, value: object, minimum: int, what: str | None = None) -> int:
    """Return value if it is an int >= minimum (never a bool), else raise.

    The message reads `<path> must be <what>`, by default `an integer >= <minimum>`.
    """
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name}: {path} must be {what or f'an integer >= {minimum}'}")
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
