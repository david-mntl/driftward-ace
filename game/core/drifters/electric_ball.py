"""The electric ball: a falling pulse node that charges, then fires a circle of lightning.

It falls straight down, charges, fires a circle around itself, and charges again until it leaves.
The circle is part of the one drifter: it joins through the hitbox and `drawn_parts`. Every
number comes from the tuning file through `Birth`; none is set here.

Source: docs/contracts/systems/drifters/electric-ball/core.md; drifters/10-electric-ball.md.
"""

import logging
from dataclasses import dataclass, replace
from typing import ClassVar, Final, Self

from core.collision import Box, Circle, Hitbox, place_hitbox
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

PULSE_DRAW_MARGIN: Final[float] = 1.5
"""Px added to the pulse box's half side in `drawn_parts`. Not a game value: the view draws a
circle at a whole-pixel center with a whole-pixel radius, each rounded, so no drawn pixel lies
farther than radius + 1.5 from the true center. Same reason as the fireball's DRAW_MARGIN.
Source: electric-ball/rationale.md."""


@dataclass(frozen=True, slots=True)
class ElectricBallVariantExtra(VariantExtra):
    """The electric ball's per-variant value: how far its pulse reaches."""

    pulse_radius: float
    """Px from the ball's center, greater than half the ball's size."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ElectricBallTypeExtra(DrifterTypeExtra):
    """The electric ball's values that hold for every variant. Final numbers, px and ticks."""

    charge_ticks: int
    """Level 1 charge, ticks, >= 1. Scaled at birth."""

    fire_ticks: int
    """Fire, ticks, >= 1. Never scaled."""

    charge_rays: int
    """Most rays around the ball, >= 1."""

    ray_length: float
    """Ray length out from the ball's edge, px, > 0."""

    ray_width: float
    """Ray thickness, px, > 0."""

    outline_width: float
    """Thickness of the charge outline of the pulse circle, px, > 0."""

    rim_width: float
    """Thickness of the firing circle's bright rim, inside the circle, px, > 0."""

    fill_opacity: float
    """How opaque the firing circle's fill is, > 0 and <= 1."""


def electric_ball_hitbox(pulse_radius: float) -> Hitbox:
    """Return the firing circle as an offset from the ball's center, px.

    The ball itself has no hitbox. Source: drifters/10-electric-ball.md, hitbox.
    """
    return (Circle(0.0, 0.0, pulse_radius),)


def check_electric_ball_variant(ball_size: float, pulse_radius: float) -> None:
    """Raise ValueError unless the pulse circle reaches past the ball, px.

    Source: electric-ball/core.md, Rules, Tuning checks.
    """
    half: float = ball_size / 2
    if pulse_radius <= half:
        raise ValueError(
            f"pulse_radius must be more than ball_size / 2 ({pulse_radius:g} <= {half:g})"
        )


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class ElectricBall(Drifter):
    """Pulse node. Falls straight down, charges, then fires a circle of lightning around itself.

    The cycle repeats until it leaves. No targeting, no specialty, no seed.
    """

    drifter_type: ClassVar[DrifterType] = DrifterType.ELECTRIC_BALL

    pulse_radius: float = 0.0
    """Px from the ball's center, from the variant."""

    charge_ticks: int = 1
    """Final charge, ticks: Timer x applied, never below telegraph_min."""

    fire_ticks: int = 1
    """Fire, ticks. Never scaled."""

    charge_rays: int = 1
    """Most rays."""

    ray_length: float = 0.0
    """Ray length out from the ball's edge, px."""

    ray_width: float = 1.0
    """Ray thickness, px."""

    outline_width: float = 1.0
    """Charge outline thickness, px."""

    rim_width: float = 1.0
    """Firing circle rim thickness, px."""

    fill_opacity: float = 0.0
    """Opacity of the firing circle's fill, 0..1."""

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the electric ball in WARNING with its pulse, timers and look values.

        `invert` is accepted and changes nothing. Raises ValueError when the placement switches a
        specialty on, when the variant has no `ElectricBallVariantExtra`, or when the tuning has
        no `ElectricBallTypeExtra`, in that order. Source: electric-ball/core.md, Rules, Born.
        """
        name: str = cls.drifter_type.value
        if birth.specialty_enabled is True:
            raise ValueError(f"{name} has no specialty")
        variant_extra: VariantExtra | None = birth.variant_extra
        if not isinstance(variant_extra, ElectricBallVariantExtra):
            raise ValueError(f"{name} variant '{birth.variant}' has no pulse_radius")
        type_extra: DrifterTypeExtra | None = birth.type_extra
        if not isinstance(type_extra, ElectricBallTypeExtra):
            raise ValueError(f"{name} tuning has no type values")
        return replace(
            born_drifter(cls, birth),
            pulse_radius=variant_extra.pulse_radius,
            charge_ticks=scale_telegraph(
                type_extra.charge_ticks, birth.timer_mult, birth.telegraph_min_ticks
            ),
            fire_ticks=type_extra.fire_ticks,
            charge_rays=type_extra.charge_rays,
            ray_length=type_extra.ray_length,
            ray_width=type_extra.ray_width,
            outline_width=type_extra.outline_width,
            rim_width=type_extra.rim_width,
            fill_opacity=type_extra.fill_opacity,
        )

    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        """Return the start center, px: the placement's x (required) and y.

        A missing y is `-height / 2`: the ball's box touching the top edge from above, fully off
        screen. `invert` is not read. Raises ValueError("electric_ball placement needs x")
        without an x.
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

    @classmethod
    def telegraph_ticks(cls, type_extra: DrifterTypeExtra | None) -> int | None:
        """Return the charge, ticks, from the type's file: the telegraph before the circle fires."""
        return type_extra.charge_ticks if isinstance(type_extra, ElectricBallTypeExtra) else None

    def effect_on_touch(self) -> TouchEffect:
        """Touching the firing circle is a hit."""
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

    def ball_on_screen(self) -> bool:
        """Return True when the ball's box shares area with the screen (strict)."""
        half_w: float = self.width / 2
        half_h: float = self.height / 2
        return (
            self.x - half_w < SCREEN_W
            and self.x + half_w > 0
            and self.y - half_h < SCREEN_H
            and self.y + half_h > 0
        )

    def pulse_fires(self) -> bool:
        """Return True while the circle fires: firing, with the ball on screen."""
        return self.is_firing() and self.ball_on_screen()

    def charge_ray_count(self) -> int:
        """Return the rays now: 1 up to `charge_rays` while charging on screen, else 0."""
        if not (self.is_charging() and self.ball_on_screen()):
            return 0
        return 1 + self._cycle_tick() * self.charge_rays // self.charge_ticks

    def outline_level(self) -> float:
        """Return the charge outline's share of full color, 0..1: rays shown over most rays."""
        return self.charge_ray_count() / self.charge_rays

    def current_hitbox(self) -> Hitbox:
        """Return the pulse circle placed at the ball while it fires. () otherwise."""
        if not self.pulse_fires():
            return ()
        return place_hitbox(self.hitbox, self.x, self.y)

    def drawn_parts(self) -> tuple[Box, ...]:
        """Return the ball's box, and the pulse box around circle and rays while the ball shows."""
        ball: Box = Box(self.x, self.y, self.width, self.height)
        if not self.ball_on_screen():
            return (ball,)
        side: float = 2 * (
            max(self.pulse_radius, self.width / 2 + self.ray_length) + PULSE_DRAW_MARGIN
        )
        return (ball, Box(self.x, self.y, side, side))
