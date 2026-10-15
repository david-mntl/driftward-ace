"""The debug test spawn list: meteorites at set places, so start positions can be tested.

Debug mode only; normal mode spawns nothing yet. A temporary stand-in kept in scope report
DRA-29 only, not in the GDD. Not a wave: no wave file, no wave clock, no picker. Waves replace it.
Not a startup module: it imports core.objects, so only app.frame imports it, inside the guard.

Source: docs/contracts/systems/app.md, Interface and Rules, Debug test spawn list;
scope report DRA-29, Test spawn list.
"""

import logging

from core.objects.base import ObjectType
from core.objects.spawner import Placement

log = logging.getLogger(__name__)

DEBUG_SPAWN_PERIOD: int = 180
"""Ticks. The list repeats every 3 s. Source: scope report DRA-29, Test spawn list."""

DEBUG_SPAWNS: tuple[tuple[int, Placement], ...] = (
    (0, Placement(ObjectType.METEORITE, x=160.0, variant="small")),
    (60, Placement(ObjectType.METEORITE, x=320.0, variant="medium")),
    (120, Placement(ObjectType.METEORITE, x=480.0, variant="big")),
)
"""(offset in ticks within the period, placement). Small, medium, big at x 160, 320, 480, each
at its default start y, one second (60 ticks) apart, in that order.
Source: scope report DRA-29, Test spawn list."""


def debug_spawns_due(ticks: int) -> tuple[Placement, ...]:
    """Return the placements due on this tick of play.

    ticks is run.scroll.ticks after the tick: 1 on the first tick of play. () when ticks < 1.
    Otherwise every placement whose offset is (ticks - 1) % DEBUG_SPAWN_PERIOD.
    """
    if ticks < 1:
        return ()
    offset: int = (ticks - 1) % DEBUG_SPAWN_PERIOD
    return tuple(placement for due, placement in DEBUG_SPAWNS if due == offset)
