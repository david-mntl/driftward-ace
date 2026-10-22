"""The floating island: a parked blocker that moves down only with the scroll.

One drifter, five variants by shape kind and size. Touching it never hurts and never pays: it is
ground the ship can't enter. Every number comes from the tuning file through `Birth`; none is
set here.

Source: docs/contracts/systems/drifters.md, Rules, Floating island; drifters/05-floating-islands.md.
"""

import logging
from dataclasses import dataclass, replace
from enum import Enum
from typing import ClassVar, Final, Self

from core.collision import Box, Hitbox, Polygon
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
)
from core.drifters.registry import register_drifter

log = logging.getLogger(__name__)


class IslandShape(Enum):
    """The shape kinds an island variant can have. Source: 05-floating-islands.md, Shapes."""

    RECTANGLE = "rectangle"
    """A filled rectangle. The box variant is one too."""

    L_SHAPE = "l_shape"
    """A bar along the bottom and an upright at the left end, full height."""

    T_SHAPE = "t_shape"
    """A bar along the top and a stem centered under it, full height."""

    TRIANGLE = "triangle"
    """A right triangle: base along the bottom, straight side on the left."""


INVERTIBLE_SHAPES: Final[frozenset[IslandShape]] = frozenset(
    {IslandShape.L_SHAPE, IslandShape.T_SHAPE, IslandShape.TRIANGLE}
)
"""Shapes a placement may invert. Source: drifters/05-floating-islands.md, rule 9."""


@dataclass(frozen=True, slots=True)
class IslandVariantExtra(VariantExtra):
    """The island's per-variant value: its shape kind."""

    shape: IslandShape
    """The variant's shape kind."""


@dataclass(frozen=True, slots=True, kw_only=True)
class IslandTypeExtra(DrifterTypeExtra):
    """The island's values that hold for every variant. Final numbers, px."""

    arm: float
    """The L's and the T's arm thickness, px, above 0."""


def island_hitbox(
    shape: IslandShape, width: float, height: float, arm: float, invert: bool
) -> Hitbox:
    """Return the island's shapes as offsets from its center, px, y down.

    `invert` mirrors the shape top to bottom. Pure. Source: drifters/05-floating-islands.md,
    hitbox (guess); 07-drifters.md, rule 8.
    """
    half_w: float = width / 2
    half_h: float = height / 2
    offset: float = (height - arm) / 2
    sign: float = -1.0 if invert else 1.0
    match shape:
        case IslandShape.RECTANGLE:
            return (Box(0.0, 0.0, width, height),)
        case IslandShape.L_SHAPE:
            return (
                Box(0.0, sign * offset, width, arm),
                Box(-(width - arm) / 2, 0.0, arm, height),
            )
        case IslandShape.T_SHAPE:
            return (Box(0.0, -sign * offset, width, arm), Box(0.0, 0.0, arm, height))
        case IslandShape.TRIANGLE:
            return (
                Polygon(
                    (
                        (-half_w, -sign * half_h),
                        (half_w, sign * half_h),
                        (-half_w, sign * half_h),
                    )
                ),
            )


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class FloatingIsland(Drifter):
    """Forced-path blocker. Sits still in the world and moves down only with the scroll."""

    drifter_type: ClassVar[DrifterType] = DrifterType.FLOATING_ISLAND
    parked: ClassVar[bool] = True

    shape: IslandShape = IslandShape.RECTANGLE
    """The shape kind, from the variant."""

    invert: bool = False
    """The placement's invert: the shape upside down."""

    arm: float = 0.0
    """The L's and the T's arm thickness, px, from the type."""

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the island ACTIVE, with no entry warning, from its variant and type values.

        Raises ValueError when the placement switches a specialty on, when the tuning has no
        `IslandVariantExtra` or no `IslandTypeExtra`, or when `invert` is set on a shape that
        has none. The hitbox is rebuilt here, so `invert` turns it upside down.
        """
        name: str = cls.drifter_type.value
        if birth.specialty_enabled is True:
            raise ValueError(f"{name} has no specialty")
        variant_extra: VariantExtra | None = birth.variant_extra
        if not isinstance(variant_extra, IslandVariantExtra):
            raise ValueError(f"{name} variant '{birth.variant}' has no shape")
        type_extra: DrifterTypeExtra | None = birth.type_extra
        if not isinstance(type_extra, IslandTypeExtra):
            raise ValueError(f"{name} tuning has no type values")
        if birth.invert and variant_extra.shape not in INVERTIBLE_SHAPES:
            raise ValueError(f"{name} variant '{birth.variant}' has no invert")
        return replace(
            born_drifter(cls, birth),
            phase=Phase.ACTIVE,
            ticks_in_phase=0,
            shape=variant_extra.shape,
            invert=birth.invert,
            arm=type_extra.arm,
            hitbox=island_hitbox(
                variant_extra.shape, birth.width, birth.height, type_extra.arm, birth.invert
            ),
        )

    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        """Return the start center, px. x is required. y None: bottom edge on the top edge."""
        if x is None:
            raise ValueError(f"{cls.drifter_type.value} placement needs x")
        return x, -height / 2 if y is None else y

    def update(self, ctx: TickContext) -> Self:
        """Move down by the scroll step while ACTIVE. WARNING and GONE stay as they are."""
        if self.phase is not Phase.ACTIVE:
            return self
        return replace(self, y=self.y + ctx.scroll_step_px, ticks_in_phase=self.ticks_in_phase + 1)

    def effect_on_touch(self) -> TouchEffect:
        """Touching the island blocks the ship. It never hits and never pays."""
        return TouchEffect.BLOCK
