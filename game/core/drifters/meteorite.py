"""The meteorite: a falling blocker that drops straight down at its speed.

Source: docs/contracts/systems/drifters.md, Rules, Meteorite; drifters/01-meteorite.md.
"""

import logging
from dataclasses import dataclass, replace
from typing import ClassVar, Self

from core.drifters.base import Drifter, DrifterType, Phase, TickContext, TouchEffect, tick_warning
from core.drifters.registry import register_drifter

log = logging.getLogger(__name__)


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Meteorite(Drifter):
    """Falling blocker. Falls straight down at its speed. No drift, no spin, no specialty."""

    drifter_type: ClassVar[DrifterType] = DrifterType.METEORITE

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
