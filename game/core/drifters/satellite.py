"""The satellite: a side crosser that flies from a side wall in a straight line.

Its panels swing on a sine, and the panel part of its hitbox swings with them, so the hitbox
always matches the drawn frame. Source: docs/contracts/systems/drifters.md, Rules, Satellite;
drifters/02-satellite.md.
"""

import logging
import math
from dataclasses import dataclass, replace
from typing import ClassVar, Self

from core.collision import Box, Circle, Hitbox, Polygon, Shape, place_hitbox
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

    swing_degrees: float = 0.0
    """Largest panel turn either way, degrees, >= 0. 0 never swings."""

    swing_frames: int = 1
    """Steps in one full swing, there and back, >= 1. Matches the sprite's frame count."""

    swing_ticks_per_frame: int = 1
    """Ticks each swing step lasts, >= 1."""

    field_ticks_per_frame: int = 1
    """Ticks each magnetism-field frame shows, >= 1. Look only."""

    swing_hitbox: tuple[Box, ...] = ()
    """The panels' boxes at level, offsets from the center. They turn with the swing.

    The loader always sets these fields from the tuning file; the defaults only serve tests that
    build the extra by hand."""


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Satellite(Drifter):
    """Side crosser. Flies from a side wall in a straight line. No turning, no targeting."""

    drifter_type: ClassVar[DrifterType] = DrifterType.SATELLITE

    invert: bool = False
    """True: enters from the right wall and flies right to left."""

    angle_degrees: float = 0.0
    """Path angle below level, degrees, from the variant."""

    swing_degrees: float = 0.0
    """Largest panel turn either way, degrees, from the variant."""

    swing_frames: int = 1
    """Steps in one full swing, from the variant."""

    swing_ticks_per_frame: int = 1
    """Ticks each swing step lasts, from the variant."""

    field_ticks_per_frame: int = 1
    """Ticks each magnetism-field frame shows, from the variant. Look only; never changes play."""

    swing_hitbox: tuple[Box, ...] = ()
    """The panels' boxes at level, offsets from the center, from the variant. `hitbox` holds the
    parts that stay still (the body)."""

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
            swing_degrees=float(extra.swing_degrees),
            swing_frames=extra.swing_frames,
            swing_ticks_per_frame=extra.swing_ticks_per_frame,
            field_ticks_per_frame=extra.field_ticks_per_frame,
            swing_hitbox=extra.swing_hitbox,
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

    def swing_frame(self) -> int:
        """Return the swing step shown now, 0 .. swing_frames - 1. 0 is level.

        Counted from the tick it turned ACTIVE; 0 in any other phase.
        """
        if self.phase is not Phase.ACTIVE:
            return 0
        return (self.ticks_in_phase // self.swing_ticks_per_frame) % self.swing_frames

    def swing_angle(self) -> float:
        """Return the panels' turn now, degrees counterclockwise on screen as drawn facing right.

        `swing_degrees * sin(2 pi * step / swing_frames)`: level at step 0, a full turn there and
        back over one swing. The art script draws its frames with the same formula.
        """
        return self.swing_degrees * math.sin(2 * math.pi * self.swing_frame() / self.swing_frames)

    def current_hitbox(self) -> Hitbox:
        """Return the body shapes and the panel boxes turned by the swing, placed. () unless ACTIVE.

        A panel box turns about the satellite's center into a four-corner polygon. With `invert`
        the art is mirrored, so every shape is mirrored too.
        """
        if self.phase is not Phase.ACTIVE:
            return ()
        turn: float = math.radians(self.swing_angle())
        cos_t, sin_t = math.cos(turn), math.sin(turn)
        mirror: float = -1.0 if self.invert else 1.0
        panels: list[Polygon] = []
        for box in self.swing_hitbox:
            corners: list[tuple[float, float]] = []
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                px: float = box.cx + sx * box.w / 2
                py: float = box.cy + sy * box.h / 2
                corners.append((mirror * (px * cos_t + py * sin_t), -px * sin_t + py * cos_t))
            panels.append(Polygon(tuple(corners)))
        body: Hitbox = (
            tuple(_mirrored(shape) for shape in self.hitbox) if self.invert else self.hitbox
        )
        return place_hitbox((*body, *panels), self.x, self.y)

    def effect_on_touch(self) -> TouchEffect:
        """Touching the body or a panel is a hit."""
        return TouchEffect.HIT

    def warning_tilt_degrees(self) -> float:
        """Return the warning copy's turn, degrees counterclockwise, so it points where it flies.

        `-angle_degrees` flying down to the right, `+angle_degrees` with `invert`.
        """
        return self.angle_degrees if self.invert else -self.angle_degrees


def _mirrored(shape: Shape) -> Shape:
    """Return a body shape mirrored left to right about the center. Raises TypeError unless it
    is a Circle or a Box, the shapes the loader allows."""
    if isinstance(shape, Circle):
        return Circle(-shape.cx, shape.cy, shape.r)
    if isinstance(shape, Box):
        return Box(-shape.cx, shape.cy, shape.w, shape.h)
    raise TypeError(f"satellite body shape must be a circle or a box, not {type(shape).__name__}")
