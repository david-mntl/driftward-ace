"""The chain lightning: a telegraphed link that charges, then fires arcs between its nodes.

It falls straight down. Its 2 or 3 nodes are parts of one drifter. Every number comes from the
tuning file through `Birth`; none is set here.

Source: docs/contracts/systems/drifters.md, Rules, Chain lightning; drifters/03-chain-lightning.md.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import Enum
from typing import ClassVar, Self

from core.collision import Circle, Hitbox, Line, place_hitbox
from core.drifters.base import (
    Birth,
    Drifter,
    DrifterType,
    DrifterTypeExtra,
    Phase,
    TickContext,
    TouchEffect,
    VariantExtra,
    born_drifter,
    scale_telegraph,
    tick_warning,
)
from core.drifters.registry import register_drifter
from core.world import SCREEN_H, SCREEN_W

log = logging.getLogger(__name__)

type Point = tuple[float, float]
"""A position, px, y down."""

type ArcNodes = tuple[int, int]
"""Two node indices, from 0."""


class InvertMirror(Enum):
    """What `invert` does to a layout."""

    LEFT_RIGHT = "left_right"
    """Every node x is negated."""

    TOP_BOTTOM = "top_bottom"
    """Every node y is negated: the triangle points down."""


@dataclass(frozen=True, slots=True)
class ChainLayout:
    """One layout: where the nodes sit and which ones the lightning joins."""

    nodes: tuple[Point, ...]
    """2 or 3 node centers, px offsets from the chain's center, before invert."""

    arcs: tuple[ArcNodes, ...]
    """The node pairs the lightning joins. At least one."""

    invert_mirror: InvertMirror
    """What invert does to this layout."""


@dataclass(frozen=True, slots=True)
class ChainLightningVariantExtra(VariantExtra):
    """The chain lightning's per-variant value: its layout."""

    layout: ChainLayout


@dataclass(frozen=True, slots=True, kw_only=True)
class ChainLightningTypeExtra(DrifterTypeExtra):
    """The chain lightning's values that hold for every variant. Final numbers, px and ticks."""

    node_size: float
    """Node diameter, px, > 0."""

    arc_width: float
    """Arc thickness, px, > 0 and <= node_size."""

    charge_ticks: int
    """Level 1 charge, ticks, >= 1. Scaled at birth."""

    fire_ticks: int
    """Fire, ticks, >= 1. Never scaled."""

    charge_rays: int
    """Most rays per node, >= 1."""

    ray_length: float
    """Ray length out from the node's edge, px, > 0."""

    ray_width: float
    """Ray thickness, px, > 0."""

    warning_layout: ChainLayout
    """The layout the entry warning shows, whatever the variant."""


def mirrored_nodes(layout: ChainLayout, invert: bool) -> tuple[Point, ...]:
    """Return the layout's node centers, mirrored by its `invert_mirror` when `invert` is True."""
    if not invert:
        return layout.nodes
    if layout.invert_mirror is InvertMirror.LEFT_RIGHT:
        return tuple((-x, y) for x, y in layout.nodes)
    return tuple((x, -y) for x, y in layout.nodes)


def layout_size(nodes: Sequence[Point], node_size: float) -> tuple[float, float]:
    """Return (width, height), px, of the box around every node circle.

    That is the spread of the node centers plus `node_size`.
    """
    xs: list[float] = [x for x, _ in nodes]
    ys: list[float] = [y for _, y in nodes]
    return max(xs) - min(xs) + node_size, max(ys) - min(ys) + node_size


def chain_hitbox(
    nodes: Sequence[Point], arcs: Sequence[ArcNodes], node_size: float, arc_width: float
) -> Hitbox:
    """Return the full firing set, offsets from the chain's center.

    One `Line` per arc, node center to node center, in arcs order; then one `Circle` per node,
    in node order.
    """
    lines: tuple[Line, ...] = tuple(
        Line(nodes[a][0], nodes[a][1], nodes[b][0], nodes[b][1], arc_width) for a, b in arcs
    )
    circles: tuple[Circle, ...] = tuple(Circle(x, y, node_size / 2) for x, y in nodes)
    return lines + circles


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class ChainLightning(Drifter):
    """Telegraphed link. Falls straight down, charges, then fires arcs between its nodes.

    The cycle repeats until it leaves. No targeting, no specialty.
    """

    drifter_type: ClassVar[DrifterType] = DrifterType.CHAIN_LIGHTNING

    invert: bool = False
    """The placement's invert."""

    nodes: tuple[Point, ...] = ()
    """Node centers, px offsets from (x, y), invert applied."""

    arcs: tuple[ArcNodes, ...] = ()
    """Node index pairs, from the variant."""

    node_size: float = 0.0
    """Node diameter, px."""

    arc_width: float = 0.0
    """Arc thickness, px."""

    charge_ticks: int = 1
    """Final charge, ticks: Timer x applied, never below telegraph_min."""

    fire_ticks: int = 1
    """Fire, ticks. Never scaled."""

    charge_rays: int = 1
    """Most rays per node."""

    ray_length: float = 0.0
    """Ray length out from the node's edge, px."""

    ray_width: float = 1.0
    """Ray thickness, px."""

    warning_layout: ChainLayout | None = None
    """The entry warning's icon layout, before invert. Never inverted."""

    warning_node: int | None = None
    """Index of the node the warning shows above. Set by `settle_warning`."""

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the chain lightning in WARNING with its layout, timers and look values.

        Raises ValueError when the placement switches a specialty on, when the variant has no
        `ChainLightningVariantExtra`, or when the tuning has no `ChainLightningTypeExtra`.
        Source: Rules, Chain lightning, Born.
        """
        name: str = cls.drifter_type.value
        if birth.specialty_enabled is True:
            raise ValueError(f"{name} has no specialty")
        variant_extra: VariantExtra | None = birth.variant_extra
        if not isinstance(variant_extra, ChainLightningVariantExtra):
            raise ValueError(f"{name} variant '{birth.variant}' has no layout")
        type_extra: DrifterTypeExtra | None = birth.type_extra
        if not isinstance(type_extra, ChainLightningTypeExtra):
            raise ValueError(f"{name} tuning has no type values")
        nodes: tuple[Point, ...] = mirrored_nodes(variant_extra.layout, birth.invert)
        arcs: tuple[ArcNodes, ...] = variant_extra.layout.arcs
        return replace(
            born_drifter(cls, birth),
            hitbox=chain_hitbox(nodes, arcs, type_extra.node_size, type_extra.arc_width),
            invert=birth.invert,
            nodes=nodes,
            arcs=arcs,
            node_size=type_extra.node_size,
            arc_width=type_extra.arc_width,
            charge_ticks=scale_telegraph(
                type_extra.charge_ticks, birth.timer_mult, birth.telegraph_min_ticks
            ),
            fire_ticks=type_extra.fire_ticks,
            charge_rays=type_extra.charge_rays,
            ray_length=type_extra.ray_length,
            ray_width=type_extra.ray_width,
            warning_layout=type_extra.warning_layout,
        )

    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        """Return the start center, px: the placement's x (required) and y.

        A missing y is `-height / 2`: the bottom of its box on the top edge, fully off screen.
        Raises ValueError("chain_lightning placement needs x") without an x.
        """
        if x is None:
            raise ValueError(f"{cls.drifter_type.value} placement needs x")
        return x, -height / 2 if y is None else y

    def update(self, ctx: TickContext) -> Self:
        """Count the warning, or fall by `speed` px while ACTIVE. GONE stays as it is."""
        if self.phase is Phase.WARNING:
            return tick_warning(self)
        if self.phase is Phase.ACTIVE:
            return replace(self, y=self.y + self.speed, ticks_in_phase=self.ticks_in_phase + 1)
        return self

    def effect_on_touch(self) -> TouchEffect:
        """Touching a firing arc, or a node while one of its arcs fires, is a hit."""
        return TouchEffect.HIT

    def _cycle_tick(self) -> int:
        """Return the tick within the charge-then-fire cycle, from 0."""
        return self.ticks_in_phase % (self.charge_ticks + self.fire_ticks)

    def is_charging(self) -> bool:
        """Return True while ACTIVE and in the charge part of the cycle."""
        return self.phase is Phase.ACTIVE and self._cycle_tick() < self.charge_ticks

    def is_firing(self) -> bool:
        """Return True while ACTIVE and in the fire part of the cycle."""
        return self.phase is Phase.ACTIVE and self._cycle_tick() >= self.charge_ticks

    def charge_ray_count(self) -> int:
        """Return the rays per node now: 1 up to `charge_rays` while charging, else 0."""
        if not self.is_charging():
            return 0
        return 1 + self._cycle_tick() * self.charge_rays // self.charge_ticks

    def node_centers(self) -> tuple[Point, ...]:
        """Return each node's center, screen px, in node order."""
        return tuple((self.x + ox, self.y + oy) for ox, oy in self.nodes)

    def nodes_on_screen(self) -> tuple[bool, ...]:
        """Return per node whether its node_size square shares area with the screen (strict)."""
        half: float = self.node_size / 2
        return tuple(
            nx - half < SCREEN_W and nx + half > 0 and ny - half < SCREEN_H and ny + half > 0
            for nx, ny in self.node_centers()
        )

    def firing_arcs(self) -> tuple[int, ...]:
        """Return the arc indices that fire now, ascending. () unless firing."""
        if not self.is_firing():
            return ()
        on_screen: tuple[bool, ...] = self.nodes_on_screen()
        return tuple(i for i, (a, b) in enumerate(self.arcs) if on_screen[a] and on_screen[b])

    def current_hitbox(self) -> Hitbox:
        """Return the placed firing arcs, then the nodes they touch. () when nothing fires."""
        firing: tuple[int, ...] = self.firing_arcs()
        if not firing:
            return ()
        touched: set[int] = {node for i in firing for node in self.arcs[i]}
        lines: Hitbox = tuple(self.hitbox[i] for i in firing)
        circles: Hitbox = tuple(
            self.hitbox[len(self.arcs) + n] for n in range(len(self.nodes)) if n in touched
        )
        return place_hitbox(lines + circles, self.x, self.y)

    def warning_center(self) -> tuple[float, float]:
        """Return where the entry warning is drawn, px.

        The settled node's center (the chain's own center before it is settled), clamped so the
        whole warning, a circle of radius half the warning copy's width, shows.
        """
        radius: float = self.warning_copy().width / 2
        cx, cy = self.x, self.y
        if self.warning_node is not None:
            cx, cy = self.node_centers()[self.warning_node]
        return (
            min(max(cx, radius), SCREEN_W - radius),
            min(max(cy, radius), SCREEN_H - radius),
        )

    def warning_copy(self) -> Self:
        """Return this chain in the warning layout, sized on it: the triangle, never mirrored."""
        if self.warning_layout is None:
            return self
        width, height = layout_size(self.warning_layout.nodes, self.node_size)
        return replace(
            self,
            nodes=self.warning_layout.nodes,
            arcs=self.warning_layout.arcs,
            width=width,
            height=height,
            hitbox=chain_hitbox(
                self.warning_layout.nodes,
                self.warning_layout.arcs,
                self.node_size,
                self.arc_width,
            ),
        )

    def settle_warning(self, ctx: TickContext) -> Self:
        """Return the chain with `warning_node` set to the node nearest the ship's center.

        Ties go to the smaller node x, then the lower index.
        """

        def nearness(item: tuple[int, Point]) -> tuple[float, float, int]:
            index, (nx, ny) = item
            return (ctx.ship.x - nx) ** 2 + (ctx.ship.y - ny) ** 2, nx, index

        nearest: int = min(enumerate(self.node_centers()), key=nearness)[0]
        return replace(self, warning_node=nearest)
