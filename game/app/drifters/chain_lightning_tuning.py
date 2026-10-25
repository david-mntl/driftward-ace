"""The chain lightning's tuning file: its checks, and the records built from it.

The file has a schema of its own: its layouts become ChainLayout records, and its width, height and
hitbox are worked out by core.drifters.chain_lightning, so that rule has one home. The loader
registers itself by type, so the app names no drifter.

Source: docs/contracts/systems/app.md, Rules, Tuning loader (The chain lightning's file);
docs/contracts/schemas/chain-lightning-tuning.schema.json.
"""

import math

from app.drifters.checks import (
    DRIFTER_FIELDS,
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
from core.drifters.tuning import DrifterTypeTuning, VariantTuning

_CHAIN_FIELDS: frozenset[str] = DRIFTER_FIELDS | frozenset(
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


@register_tuning(DrifterType.CHAIN_LIGHTNING)
def _load_chain_lightning(name: str, data: object) -> DrifterTypeTuning:
    """Check the chain lightning's file and build its record.

    Each variant's layout is scaled by node_spacing into px; its width, height and hitbox come from
    core.drifters.chain_lightning. The footprint check of the other files is not run: lines are
    never read as boxes, and arc_width <= node_size keeps every line inside its nodes.
    Source: docs/contracts/systems/app.md, Rules, Tuning loader (The chain lightning's file, What
    the loader builds for the chain lightning); chain-lightning-tuning.schema.json.
    """
    fields: dict[str, object] = check_fields(name, "", data, _CHAIN_FIELDS)
    speed_ratio: float = check_number(name, "speed_ratio", fields["speed_ratio"])
    if speed_ratio < 0:
        raise ValueError(f"{name}: speed_ratio must be a number >= 0")
    warning_ticks: int = check_warning_ticks(name, fields["entry_warning_ticks"])
    node_spacing: float = check_positive(name, "node_spacing", fields["node_spacing"])
    node_size: float = check_positive(name, "node_size", fields["node_size"])
    arc_width: float = check_positive(name, "arc_width", fields["arc_width"])
    ray_length: float = check_positive(name, "ray_length", fields["ray_length"])
    ray_width: float = check_positive(name, "ray_width", fields["ray_width"])
    charge_ticks: int = check_integer(name, "charge_ticks", fields["charge_ticks"], 1)
    fire_ticks: int = check_integer(name, "fire_ticks", fields["fire_ticks"], 1)
    charge_rays: int = check_integer(name, "charge_rays", fields["charge_rays"], 1)
    if arc_width > node_size:
        raise ValueError(f"{name}: arc_width must be <= node_size")
    layouts: dict[str, ChainLayout] = _chain_layouts(name, fields["variants"], node_spacing)
    default_variant: str = check_variant_name(name, "default_variant", fields["default_variant"])
    if default_variant not in layouts:
        raise ValueError(f"{name}: default_variant must be one of the variant names")
    icon: str = check_variant_name(name, "entry_warning_icon", fields["entry_warning_icon"])
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
        variant: str = check_variant_name(name, f"variants.{key}", key)
        layouts[variant] = _chain_layout(name, f"variants.{variant}", value, node_spacing)
    return layouts


def _chain_layout(name: str, path: str, data: object, node_spacing: float) -> ChainLayout:
    """Check one chain lightning variant: its nodes, its arcs and invert_mirror.

    Nodes are in units of node_spacing. Every arc joins two different nodes 1 unit apart, no two
    arcs join the same pair, and the box around the nodes is centered on 0, 0. Builds the layout
    with every node multiplied by node_spacing.
    """
    fields: dict[str, object] = check_fields(name, path, data, _CHAIN_VARIANT_FIELDS)
    raw_nodes: object = fields["nodes"]
    if not isinstance(raw_nodes, list) or not 2 <= len(raw_nodes) <= 3:
        raise ValueError(f"{name}: {path}.nodes must be a list of 2 or 3 points")
    units: list[Point] = []
    for index, point in enumerate(raw_nodes):
        if (
            not isinstance(point, list)
            or len(point) != 2
            or not is_number(point[0])
            or not is_number(point[1])
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
        first: int = check_integer(name, arc_path, pair[0], 0, "a list of two integers >= 0")
        second: int = check_integer(name, arc_path, pair[1], 0, "a list of two integers >= 0")
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
