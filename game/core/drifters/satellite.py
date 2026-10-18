"""The satellite: a side crosser that flies from a side wall in a straight line.

Source: docs/contracts/systems/drifters.md, Rules, Satellite; drifters/02-satellite.md.
"""

import logging
import math
from dataclasses import dataclass, replace
from typing import ClassVar, Self

from core.drifters.base import (
    Birth,
    Drifter,
    DrifterType,
    Phase,
    TickContext,
    TouchEffect,
    VariantExtra,
    born_drifter,
    tick_warning,
)
from core.drifters.registry import register_drifter
from core.world import SCREEN_W

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SatelliteVariantExtra(VariantExtra):
    """The satellite's own per-variant value."""

    angle_degrees: float
    """Path angle below level, degrees, 0 <= angle < 90. 0 is flat."""


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Satellite(Drifter):
    """Side crosser. Flies from a side wall in a straight line. No turning, no targeting."""

    drifter_type: ClassVar[DrifterType] = DrifterType.SATELLITE

    invert: bool = False
    """True: enters from the right wall and flies right to left."""

    angle_degrees: float = 0.0
    """Path angle below level, degrees, from the variant."""

    velocity_x: float = 0.0
    """px/tick, positive is right. Final, set at birth."""

    velocity_y: float = 0.0
    """px/tick, positive is down. Final, set at birth."""

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the satellite in WARNING with its angle and final velocity.

        Raises ValueError when the placement switches a specialty on, or when the variant has
        no `SatelliteVariantExtra`.
        """
        name: str = cls.drifter_type.value
        if birth.specialty_enabled is True:
            raise ValueError(f"{name} has no specialty")
        extra: VariantExtra | None = birth.variant_extra
        if not isinstance(extra, SatelliteVariantExtra):
            raise ValueError(f"{name} variant '{birth.variant}' has no angle")
        angle: float = math.radians(extra.angle_degrees)
        direction: float = -1.0 if birth.invert else 1.0
        return replace(
            born_drifter(cls, birth),
            invert=birth.invert,
            angle_degrees=float(extra.angle_degrees),
            velocity_x=direction * birth.speed * math.cos(angle),
            velocity_y=birth.speed * math.sin(angle),
        )

    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        """Return the start center, px: the placement's y (required) and x.

        A missing x is just outside the wall it enters from, touching it: `-width / 2`, or
        `SCREEN_W + width / 2` with `invert`. Raises ValueError("satellite placement needs y")
        without a y.
        """
        if y is None:
            raise ValueError(f"{cls.drifter_type.value} placement needs y")
        if x is not None:
            return x, y
        return (SCREEN_W + width / 2 if invert else -width / 2), y

    def update(self, ctx: TickContext) -> Self:
        """Count the warning, or move by the velocity while ACTIVE. GONE stays as it is."""
        if self.phase is Phase.WARNING:
            return tick_warning(self)
        if self.phase is Phase.ACTIVE:
            return replace(
                self,
                x=self.x + self.velocity_x,
                y=self.y + self.velocity_y,
                ticks_in_phase=self.ticks_in_phase + 1,
            )
        return self

    def effect_on_touch(self) -> TouchEffect:
        """Touching the body or the panel bar is a hit."""
        return TouchEffect.HIT

    def warning_tilt_degrees(self) -> float:
        """Return the warning copy's turn, degrees counterclockwise, so it points where it flies.

        `-angle_degrees` flying down to the right, `+angle_degrees` with `invert`.
        """
        return self.angle_degrees if self.invert else -self.angle_degrees
