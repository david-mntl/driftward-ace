"""The planet: a parked hazard with a gravity field that pulls the ship toward its center.

One drifter holds the body, its hitbox circle and the field. It sits still in the world and moves
down only with the scroll. Touching the body is a hit; the field never hits. Every number comes
from the tuning file through `Birth`; none is set here.

Source: docs/contracts/systems/drifters.md, Rules, Planet; drifters/08-planet.md.
"""

import logging
from dataclasses import dataclass, replace
from typing import ClassVar, Final, Self

from core.collision import Box, Circle, Hitbox
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
    tick_warning,
)
from core.drifters.registry import register_drifter
from core.ship import GravityWell

log = logging.getLogger(__name__)

FIELD_DRAW_MARGIN: Final[float] = 1.0
"""Px the field ring's drawn pixels may reach past `pull_radius`. Not a game value: it covers the
1 px line's own width. Source: docs/contracts/systems/drifters.md, Rationale (DRA-96)."""

PERCENT: Final[float] = 100.0
"""Divisor that turns a percent into a 0..1 share."""


@dataclass(frozen=True, slots=True)
class PlanetVariantExtra(VariantExtra):
    """The planet's per-variant values: its gravity field."""

    pull_radius: float
    """Px from the center where the pull is 0: the field's edge, > the planet's radius."""

    pull_max: float
    """Px/tick², the pull at the surface, > 0."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanetTypeExtra(DrifterTypeExtra):
    """The planet's values that hold for every variant: the inner field rings' look."""

    field_ring_trip: int
    """Ticks an inner ring takes from `pull_radius` to the surface, >= 1."""

    field_ring_gap: int
    """Ticks each inner ring runs behind the one before it, >= 0."""

    field_ring_fade: float
    """Percent opacity of an inner ring at `pull_radius`, 0 to 100. 0 at the surface."""

    field_ring_count: int
    """How many inner rings, >= 0."""


@dataclass(frozen=True, slots=True)
class FieldRing:
    """One inner field ring on this state. A look only: it never changes the pull."""

    radius: float
    """Px from the planet's center, surface < radius <= `pull_radius`."""

    opacity: float
    """0..1, of the ring color."""


def planet_hitbox(size: float) -> Hitbox:
    """Return the planet's hitbox: one circle of radius `size` / 2, centered, px."""
    return (Circle(0.0, 0.0, size / 2),)


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Planet(Drifter):
    """Gravity well. Sits still in the world and moves down only with the scroll."""

    drifter_type: ClassVar[DrifterType] = DrifterType.PLANET
    parked: ClassVar[bool] = True

    pull_radius: float = 0.0
    """Px from the center where the pull is 0, from the variant."""

    pull_max: float = 0.0
    """Px/tick², the pull at the surface, from the variant."""

    field_ring_trip: int = 1
    """Ticks an inner ring takes from the field's edge to the surface, from the type."""

    field_ring_gap: int = 0
    """Ticks each inner ring runs behind the one before it, from the type."""

    field_ring_fade: float = 0.0
    """Percent opacity of an inner ring at the field's edge, from the type."""

    field_ring_count: int = 0
    """How many inner rings, from the type."""

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the planet in WARNING from its variant and type values.

        Raises ValueError when the placement switches a specialty on or sets `invert`, when the
        tuning has no `PlanetVariantExtra`, or when it has no `PlanetTypeExtra`.
        """
        name: str = cls.drifter_type.value
        if birth.specialty_enabled is True:
            raise ValueError(f"{name} has no specialty")
        if birth.invert:
            raise ValueError(f"{name} has no invert")
        variant_extra: VariantExtra | None = birth.variant_extra
        if not isinstance(variant_extra, PlanetVariantExtra):
            raise ValueError(f"{name} variant '{birth.variant}' has no pull")
        type_extra: DrifterTypeExtra | None = birth.type_extra
        if not isinstance(type_extra, PlanetTypeExtra):
            raise ValueError(f"{name} tuning has no type values")
        return replace(
            born_drifter(cls, birth),
            pull_radius=variant_extra.pull_radius,
            pull_max=variant_extra.pull_max,
            field_ring_trip=type_extra.field_ring_trip,
            field_ring_gap=type_extra.field_ring_gap,
            field_ring_fade=type_extra.field_ring_fade,
            field_ring_count=type_extra.field_ring_count,
        )

    @classmethod
    def start_size(
        cls, width: float, height: float, variant_extra: VariantExtra | None
    ) -> tuple[float, float]:
        """Return the field ring's box, px: 2 x (pull_radius + FIELD_DRAW_MARGIN) both ways.

        Without a `PlanetVariantExtra` it is (width, height); `born` refuses that tuning next.
        """
        if not isinstance(variant_extra, PlanetVariantExtra):
            return width, height
        side: float = _field_box_side(variant_extra.pull_radius)
        return side, side

    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        """Return the start center, px. x is required. y None: the field ring's box bottom edge
        on the top edge (`height` is that box's)."""
        if x is None:
            raise ValueError(f"{cls.drifter_type.value} placement needs x")
        return x, -height / 2 if y is None else y

    def update(self, ctx: TickContext) -> Self:
        """Count the warning in WARNING, move down by the scroll step in ACTIVE, else unchanged."""
        if self.phase is Phase.WARNING:
            return tick_warning(self)
        if self.phase is not Phase.ACTIVE:
            return self
        return replace(self, y=self.y + ctx.scroll_step_px, ticks_in_phase=self.ticks_in_phase + 1)

    def effect_on_touch(self) -> TouchEffect:
        """Touching the body is a hit. The field never hits."""
        return TouchEffect.HIT

    def surface_radius(self) -> float:
        """Return the body's radius, px: half the width."""
        return self.width / 2

    def drawn_parts(self) -> tuple[Box, ...]:
        """Return the field ring's box, px. It holds the rings and the body."""
        side: float = _field_box_side(self.pull_radius)
        return (Box(self.x, self.y, side, side),)

    def gravity_well(self) -> GravityWell | None:
        """Return the field placed at the center while ACTIVE, else None."""
        if self.phase is not Phase.ACTIVE:
            return None
        return GravityWell(
            x=self.x,
            y=self.y,
            surface_radius=self.surface_radius(),
            pull_radius=self.pull_radius,
            pull_max=self.pull_max,
        )

    def inner_rings(self) -> tuple[FieldRing, ...]:
        """Return the inner field rings while ACTIVE, else ().

        Ring `i` runs `i x field_ring_gap` ticks behind ring 0 on a cycle of `field_ring_trip`
        ticks. It slides from `pull_radius` to the surface at a steady speed and fades in a
        straight line from `field_ring_fade` percent to 0. A look only.
        """
        if self.phase is not Phase.ACTIVE:
            return ()
        surface: float = self.surface_radius()
        rings: list[FieldRing] = []
        for index in range(self.field_ring_count):
            tick: int = (self.ticks_in_phase - index * self.field_ring_gap) % self.field_ring_trip
            progress: float = tick / self.field_ring_trip
            rings.append(
                FieldRing(
                    radius=self.pull_radius - (self.pull_radius - surface) * progress,
                    opacity=self.field_ring_fade / PERCENT * (1.0 - progress),
                )
            )
        return tuple(rings)


def _field_box_side(pull_radius: float) -> float:
    """Return the side, px, of the box around the field ring and its drawn margin."""
    return 2 * (pull_radius + FIELD_DRAW_MARGIN)
