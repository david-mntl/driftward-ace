"""Play each drifter of a wave alone with the game's own physics and record where it goes.

A track is one placement from its spawn until it leaves the screen. The ship is held at the
start spot, the world scrolls at the level's speed. Tracks are lined up by trigger tick, so the
checks can compare two drifters at the same moment. Reads the game, never changes it.
"""

import math
from dataclasses import dataclass

from core.collision import Hitbox
from core.drifters.base import Phase, TickContext
from core.drifters.spawner import spawn_drifter
from core.drifters.tuning import DrifterTuning
from core.scroll import scroll_speed
from core.ship import Ship
from core.waves import Wave, WavePlacement


@dataclass(frozen=True)
class Frame:
    """One tick of a drifter's life."""

    age: int
    """Ticks since it spawned. 0 is the tick it came due."""
    phase: Phase
    x: float
    y: float
    hitbox: Hitbox
    """Placed hitbox, () unless ACTIVE."""
    visible: bool
    """An entry warning counts as on screen, as the seam rule says."""


@dataclass(frozen=True)
class Track:
    index: int
    """Position in the wave's placement list, 0 first."""
    item: WavePlacement
    start_tick: int
    """Tick, counted from the wave's start, on which the placement comes due."""
    frames: tuple[Frame, ...]
    entered: bool
    """The drifter was ACTIVE and partly on screen at some tick."""

    @property
    def kind(self) -> str:
        return self.item.placement.drifter_type.value

    @property
    def name(self) -> str:
        variant: str = self.item.placement.variant or ""
        return f"#{self.index + 1} {self.kind} {variant}".strip()


def start_tick(at_px: float, level: int) -> int:
    """The tick, from the wave's start, on which a trigger distance comes due."""
    return math.ceil(round(at_px / scroll_speed(level), 6))


def build_tracks(
    wave: Wave, level: int, tuning: DrifterTuning, ship: Ship, max_ticks: int
) -> list[Track]:
    """Follow every placement of `wave` at `level`. Raises ValueError if one will not spawn."""
    context: TickContext = TickContext(ship=ship, scroll_step_px=scroll_speed(level))
    tracks: list[Track] = []
    for index, item in enumerate(wave.placements):
        drifter = spawn_drifter(item.placement, level, tuning).settle_warning(context)
        frames: list[Frame] = []
        entered: bool = False
        for age in range(max_ticks + 1):
            on_screen: bool = drifter.is_partly_on_screen()
            active: bool = drifter.phase is Phase.ACTIVE
            entered = entered or (active and on_screen)
            frames.append(
                Frame(
                    age,
                    drifter.phase,
                    drifter.x,
                    drifter.y,
                    drifter.current_hitbox(),
                    drifter.phase is Phase.WARNING or on_screen,
                )
            )
            drifter = drifter.update(context).mark_entered()
            if drifter.phase is Phase.GONE or (
                drifter.has_entered and not drifter.is_partly_on_screen()
            ):
                break
        tracks.append(
            Track(index, item, start_tick(item.at_px, level), tuple(frames), entered)
        )
    return tracks
