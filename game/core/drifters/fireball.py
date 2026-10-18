"""The fireball: a fast linear hazard that dives at a fixed angle from straight down.

One drifter, two circles: a head and a smaller tail touching it from behind. Every number comes
from the tuning file through `Birth`; none is set here.

Source: docs/contracts/systems/drifters.md, Rules, Fireball; drifters/06-fireball.md.
"""

import logging
import math
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
    born_drifter,
    tick_warning,
)
from core.drifters.registry import register_drifter
from core.world import SCREEN_W

log = logging.getLogger(__name__)

DRAW_MARGIN: Final[float] = 1.5
"""Px added to each circle's radius in `drawn_parts`. Not a game value: the view draws a circle at
a whole-pixel center with a whole-pixel radius, each rounded, so no drawn pixel lies farther than
radius + 1.5 from the true center. Source: drifters.md, Rationale (DRA-56)."""


@dataclass(frozen=True, slots=True, kw_only=True)
class FireballTypeExtra(DrifterTypeExtra):
    """The fireball's values that hold for every variant. Final numbers."""

    angle_degrees: float
    """Path angle from straight down, degrees, 0 <= angle < 90. Never scaled."""

    tail_ratio: float
    """Tail radius as a share of the head's radius, > 0."""


def fireball_hitbox(
    head_width: float, tail_ratio: float, angle_degrees: float, invert: bool
) -> Hitbox:
    """Return the two circles, head first, as offsets from the head's center, px.

    The tail touches the head from behind along the path: up and to the left, or up and to the
    right with `invert`. Source: drifters/06-fireball.md, hitbox; drifters.md, Rules, Fireball.
    """
    head_radius: float = head_width / 2
    distance: float = (1 + tail_ratio) * head_radius
    angle: float = math.radians(angle_degrees)
    side: float = 1.0 if invert else -1.0
    tail: Circle = Circle(
        side * distance * math.sin(angle),
        -distance * math.cos(angle),
        tail_ratio * head_radius,
    )
    return (Circle(0.0, 0.0, head_radius), tail)


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Fireball(Drifter):
    """Fast linear hazard. Dives in a straight line, through walls and drifters, never turning."""

    drifter_type: ClassVar[DrifterType] = DrifterType.FIREBALL

    invert: bool = False
    """True: flies down and to the left, and enters at the right."""

    angle_degrees: float = 0.0
    """Path angle from straight down, degrees, from the type."""

    tail_ratio: float = 0.0
    """Tail radius divided by head radius, from the type."""

    velocity_x: float = 0.0
    """px/tick, positive is right. Final, set at birth."""

    velocity_y: float = 0.0
    """px/tick, positive is down. Final, set at birth."""

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the fireball in WARNING with its hitbox, angle and final velocity.

        Raises ValueError when the placement switches a specialty on, or when the tuning has no
        `FireballTypeExtra`.
        """
        name: str = cls.drifter_type.value
        if birth.specialty_enabled is True:
            raise ValueError(f"{name} has no specialty")
        extra: DrifterTypeExtra | None = birth.type_extra
        if not isinstance(extra, FireballTypeExtra):
            raise ValueError(f"{name} tuning has no type values")
        angle: float = math.radians(extra.angle_degrees)
        direction: float = -1.0 if birth.invert else 1.0
        return replace(
            born_drifter(cls, birth),
            hitbox=fireball_hitbox(
                birth.width, extra.tail_ratio, extra.angle_degrees, birth.invert
            ),
            invert=birth.invert,
            angle_degrees=float(extra.angle_degrees),
            tail_ratio=extra.tail_ratio,
            velocity_x=direction * birth.speed * math.sin(angle),
            velocity_y=birth.speed * math.cos(angle),
        )

    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        """Return the start center, px. Never raises.

        No x and no y: the corner, the head's center on the wall and its bottom edge on the top
        edge. An x only: along the top. A y only: a side, the head fully outside the wall.
        """
        radius: float = width / 2
        if y is not None:
            if x is not None:
                return x, y
            return (SCREEN_W + radius if invert else -radius), y
        corner_x: float = SCREEN_W if invert else 0.0
        return (corner_x if x is None else x), -radius

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
        """Touching the head or the tail is a hit."""
        return TouchEffect.HIT

    def drawn_parts(self) -> tuple[Box, ...]:
        """Return one box per hitbox circle, in hitbox order, its radius plus `DRAW_MARGIN`."""
        return tuple(
            Box(
                self.x + circle.cx,
                self.y + circle.cy,
                2 * (circle.r + DRAW_MARGIN),
                2 * (circle.r + DRAW_MARGIN),
            )
            for circle in self.hitbox
            if isinstance(circle, Circle)
        )

    def warning_tilt_degrees(self) -> float:
        """Return the warning copy's turn, degrees counterclockwise, so the head leads.

        `+angle_degrees` flying down to the right, `-angle_degrees` with `invert`.
        """
        return -self.angle_degrees if self.invert else self.angle_degrees

    def warning_copy(self) -> Self:
        """Return the comet laid straight down, tail above the head, sized head plus tail."""
        radius: float = self.width / 2
        return replace(
            self,
            width=2 * radius,
            height=2 * (1 + self.tail_ratio) * radius,
            hitbox=(
                Circle(0.0, self.tail_ratio * radius, radius),
                Circle(0.0, -radius, self.tail_ratio * radius),
            ),
        )
