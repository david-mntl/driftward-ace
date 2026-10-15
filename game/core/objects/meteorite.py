"""The meteorite: a falling blocker that drops straight down at its speed.

Source: docs/contracts/systems/objects.md, Rules, Meteorite; objects/01-meteorite.md.
"""

import logging
from dataclasses import dataclass, replace
from typing import ClassVar, Self

from core.objects.base import GameObject, ObjectType, Phase, TickContext, TouchEffect, tick_warning
from core.objects.registry import register_object

log = logging.getLogger(__name__)


@register_object
@dataclass(frozen=True, slots=True, kw_only=True)
class Meteorite(GameObject):
    """Falling blocker. Falls straight down at its speed. No drift, no spin, no specialty."""

    object_type: ClassVar[ObjectType] = ObjectType.METEORITE

    @classmethod
    def default_y(cls, height: float) -> float:
        """Return the start y, px: the bottom edge on the top edge of the screen."""
        return -height / 2

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

    def may_hit_ship(self) -> bool:
        """Return True until it has hit the ship once.

        Meteorite-only stand-in while LD-06 is open: a meteorite that hit the ship can't hit
        it again, even while it still overlaps. Source: scope report DRA-29, Stand-ins.
        """
        return not self.hit_ship
