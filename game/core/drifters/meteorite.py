"""The meteorite: a falling blocker that drops straight down at its speed.

Source: docs/contracts/systems/drifters.md, Rules, Meteorite; drifters/01-meteorite.md.
"""

import logging
from dataclasses import dataclass, replace
from typing import ClassVar, Self

from core.collision import Box
from core.drifters.base import (
    Birth,
    Drifter,
    DrifterType,
    Phase,
    TickContext,
    TouchEffect,
    VariantExtra,
    tick_warning,
)
from core.drifters.registry import register_drifter

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MeteoriteVariantExtra(VariantExtra):
    """The meteorite's per-variant value: how wide its drawn rock is."""

    drawn_width: float
    """Side of the square the drawn rock fits in, px, at least the variant's width. The art has
    lumps outside the hit circle, so it is wider than the footprint."""


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Meteorite(Drifter):
    """Falling blocker. Falls straight down at its speed. No drift, no spin, no specialty."""

    drifter_type: ClassVar[DrifterType] = DrifterType.METEORITE

    drawn_width: float = 0.0
    """Side of the square the drawn rock fits in, px, from the variant. Set at birth. 0 means the
    footprint."""

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the meteorite in WARNING, with the variant's drawn width when it has one.

        A variant with no `MeteoriteVariantExtra` is drawn no wider than its footprint. The app's
        loader always gives one, so that is only for a tuning built by hand.
        """
        meteorite: Self = super(Meteorite, cls).born(birth)
        extra: VariantExtra | None = birth.variant_extra
        if isinstance(extra, MeteoriteVariantExtra):
            return replace(meteorite, drawn_width=extra.drawn_width)
        return meteorite

    @classmethod
    def start_size(
        cls, width: float, height: float, variant_extra: VariantExtra | None
    ) -> tuple[float, float]:
        """Return the drawn rock's box, `drawn_width` square, never smaller than the footprint.

        The spawner starts the meteorite from this box, so the whole drawn rock begins off screen.
        Source: 07-drifters.md, rule 14.
        """
        if isinstance(variant_extra, MeteoriteVariantExtra):
            return max(variant_extra.drawn_width, width), max(variant_extra.drawn_width, height)
        return width, height

    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        """Return the start center, px: the placement's x (required) and y.

        A missing y is `-height / 2`: the bottom edge on the top edge of the screen.
        Raises ValueError("meteorite placement needs x") without an x.
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
        """Touching a meteorite is a hit."""
        return TouchEffect.HIT

    def drawn_parts(self) -> tuple[Box, ...]:
        """Return the drawn rock's box, centered on the meteorite, px.

        It is `drawn_width` square, but never smaller than the footprint. The art is wider than
        the footprint, so the drifter leaves only once the whole rock is gone.
        """
        return (
            Box(
                self.x,
                self.y,
                max(self.drawn_width, self.width),
                max(self.drawn_width, self.height),
            ),
        )
