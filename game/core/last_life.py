"""The last life's values and the burst the ship bursts into, with its per-tick step.

Stdlib only, no frame time, no randomness. Screen px, y down. The burst is a stand-in until the
life-lost feedback feature (LD-08).

Source: docs/contracts/systems/run.md, Interface (DRA-125) and Rules, Burst.
"""

import logging
import math
from dataclasses import dataclass, replace
from typing import Final

log = logging.getLogger(__name__)

DEFAULT_LAST_LIFE_DELAY_TICKS: Final[int] = 120
"""Ticks from the burst to game over. Source: 02-game-flow.md, last_life_delay (guess)."""

DEFAULT_BURST_PARTICLE_COUNT: Final[int] = 12
"""Squares in the burst. Source: scope report DRA-125, Values needed, Burst (stand-in until
LD-08)."""

DEFAULT_BURST_PARTICLE_SPEED: Final[float] = 1.0
"""Px each square moves per tick. Source: scope report DRA-125, Values needed, Burst (stand-in
until LD-08)."""

DEFAULT_BURST_PARTICLE_SIZE: Final[int] = 3
"""Side of each square, px. Source: scope report DRA-125, Values needed, Burst (stand-in until
LD-08)."""


@dataclass(frozen=True, slots=True, kw_only=True)
class LastLifeRules:
    """The last life's values a run uses. A field left out keeps its default."""

    delay_ticks: int = DEFAULT_LAST_LIFE_DELAY_TICKS
    """Ticks from the burst to game over, at least 1."""

    burst_particle_count: int = DEFAULT_BURST_PARTICLE_COUNT
    """Squares in the burst, at least 1."""

    burst_particle_speed: float = DEFAULT_BURST_PARTICLE_SPEED
    """Px each square moves per tick, at least 0."""

    burst_particle_size: int = DEFAULT_BURST_PARTICLE_SIZE
    """Px, the side of each square, at least 1."""


DEFAULT_LAST_LIFE_RULES: Final[LastLifeRules] = LastLifeRules()
"""LastLifeRules with every default."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Burst:
    """The ship bursting on the last life: squares flying out from one point and fading."""

    x: float
    """Origin x, screen px. Never changes."""

    y: float
    """Origin y, screen px, y down. Never changes."""

    particle_count: int
    """Squares, at least 1."""

    speed_per_tick: float
    """Px each square moves per tick, at least 0."""

    particle_size: int
    """Px, the side of each square, at least 1."""

    lifetime_ticks: int
    """The last-life delay, ticks, at least 1."""

    age_ticks: int = 0
    """Ticks since it started. 0 on the state of the tick lives reach 0."""

    @property
    def opacity(self) -> float:
        """1 - age_ticks / lifetime_ticks, never below 0: 1.0 at age 0, 0.0 once finished."""
        return max(0.0, 1.0 - self.age_ticks / self.lifetime_ticks)

    @property
    def finished(self) -> bool:
        """True once the burst has lived its lifetime."""
        return self.age_ticks >= self.lifetime_ticks

    @property
    def particle_centers(self) -> tuple[tuple[float, float], ...]:
        """One (x, y) center per square, k = 0 to particle_count - 1, at the current age.

        Square k flies along the angle 2 pi k / particle_count from straight right toward
        straight down, so square 0 flies right. Depends on the age alone. Pure.
        """
        reach: float = self.age_ticks * self.speed_per_tick
        angles: tuple[float, ...] = tuple(
            2 * math.pi * k / self.particle_count for k in range(self.particle_count)
        )
        return tuple(
            (self.x + reach * math.cos(angle), self.y + reach * math.sin(angle)) for angle in angles
        )


def start_burst(rules: LastLifeRules, x: float, y: float) -> Burst:
    """Return a burst at age 0 at (x, y) with the rules' count, speed and size.

    The rules' `delay_ticks` is its lifetime. Source: systems/run.md, Interface (DRA-125).
    """
    return Burst(
        x=x,
        y=y,
        particle_count=rules.burst_particle_count,
        speed_per_tick=rules.burst_particle_speed,
        particle_size=rules.burst_particle_size,
        lifetime_ticks=rules.delay_ticks,
    )


def step_burst(burst: Burst) -> Burst:
    """Return the same burst one tick older. Pure."""
    return replace(burst, age_ticks=burst.age_ticks + 1)
