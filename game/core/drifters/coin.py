"""The coin: a parked pickup that moves down only with the scroll and pays points when collected.

One drifter: a crystal whose middle rectangle is the hitbox, with a ring across its middle. Every
number comes from the tuning file through `Birth`; none is set here.

Source: docs/contracts/systems/drifters.md, Rules, Coin; drifters/04-coin.md.
"""

import logging
from dataclasses import dataclass, replace
from typing import ClassVar, Self

from core.collision import Box, Hitbox
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
from core.popup import PointsPopup

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CoinVariantExtra(VariantExtra):
    """The coin's per-variant values."""

    points: int
    """Points paid when collected, at least 1. 50 common, 100 rare."""

    glint: bool
    """True: the view draws the glint. The rare coin."""


@dataclass(frozen=True, slots=True, kw_only=True)
class CoinTypeExtra(DrifterTypeExtra):
    """The coin's values that hold for every variant. Final numbers, px and ticks."""

    body_height: int
    """The crystal's middle rectangle height, px, even, less than the crystal's. The hitbox's."""

    ring_width: int
    """The ring's ellipse width, px, even."""

    ring_height: int
    """The ring's ellipse height, px, even."""

    glint_size: int
    """The glint's side, px, at least 1."""

    glint_left: int
    """The glint's left edge, px from the crystal box's left edge."""

    glint_top: int
    """The glint's top edge, px from the crystal box's top edge."""

    popup_ticks: int
    """How long the points popup shows, ticks, at least 1."""

    popup_rise_per_tick: float
    """How far the points popup rises each tick, px, at least 0."""


def coin_hitbox(crystal_width: float, body_height: float) -> Hitbox:
    """Return the crystal's middle rectangle as one centered box, px.

    The points, the ring and the glint never count. Source: drifters/04-coin.md, hitbox (guess).
    """
    return (Box(0.0, 0.0, crystal_width, body_height),)


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Coin(Drifter):
    """Pickup. Sits still in the world and moves down only with the scroll. Collected on touch."""

    drifter_type: ClassVar[DrifterType] = DrifterType.COIN
    parked: ClassVar[bool] = True

    points: int = 0
    """Points paid when collected, from the variant."""

    glint: bool = False
    """True: the view draws the glint, from the variant."""

    body_height: int = 0
    """The crystal's middle rectangle height, px, from the type."""

    ring_width: int = 0
    """The ring's width, px, from the type."""

    ring_height: int = 0
    """The ring's height, px, from the type."""

    glint_size: int = 0
    """The glint's side, px, from the type."""

    glint_left: int = 0
    """The glint's left edge, px from the crystal box's left edge, from the type."""

    glint_top: int = 0
    """The glint's top edge, px from the crystal box's top edge, from the type."""

    popup_ticks: int = 1
    """How long the points popup shows, ticks, from the type."""

    popup_rise_per_tick: float = 0.0
    """How far the points popup rises each tick, px, from the type."""

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the coin ACTIVE, with no entry warning, from its variant and type values.

        Raises ValueError when the placement switches a specialty on or sets `invert`, or when
        the tuning has no `CoinVariantExtra` or no `CoinTypeExtra`.
        """
        name: str = cls.drifter_type.value
        if birth.specialty_enabled is True:
            raise ValueError(f"{name} has no specialty")
        if birth.invert:
            raise ValueError(f"{name} has no invert")
        variant_extra: VariantExtra | None = birth.variant_extra
        if not isinstance(variant_extra, CoinVariantExtra):
            raise ValueError(f"{name} variant '{birth.variant}' has no points")
        type_extra: DrifterTypeExtra | None = birth.type_extra
        if not isinstance(type_extra, CoinTypeExtra):
            raise ValueError(f"{name} tuning has no type values")
        return replace(
            born_drifter(cls, birth),
            phase=Phase.ACTIVE,
            ticks_in_phase=0,
            points=variant_extra.points,
            glint=variant_extra.glint,
            body_height=type_extra.body_height,
            ring_width=type_extra.ring_width,
            ring_height=type_extra.ring_height,
            glint_size=type_extra.glint_size,
            glint_left=type_extra.glint_left,
            glint_top=type_extra.glint_top,
            popup_ticks=type_extra.popup_ticks,
            popup_rise_per_tick=type_extra.popup_rise_per_tick,
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
        """Touching the coin collects it. It never hits."""
        return TouchEffect.COLLECT

    def drawn_parts(self) -> tuple[Box, ...]:
        """Return the crystal's box, then the ring's box, both centered on the coin, px."""
        return (
            Box(self.x, self.y, self.width, self.height),
            Box(self.x, self.y, self.ring_width, self.ring_height),
        )

    def collect_points(self) -> int:
        """Return the points paid when collected."""
        return self.points

    def collect_popup(self) -> PointsPopup:
        """Return the points popup at the coin's center, at age 0."""
        return PointsPopup(
            x=self.x,
            start_y=self.y,
            points=self.points,
            lifetime_ticks=self.popup_ticks,
            rise_per_tick=self.popup_rise_per_tick,
        )
