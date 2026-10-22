"""The UFO: a wildcard mover that crosses at a steady speed, weaving up and down on a seed's path.

One drifter, two shapes: a disc and a dome on top of it. Its size and its center are the disc's.
It never aims at the ship. Its weave comes from a seed in its own state and nothing else, so
`update` is a pure function of the drifter and the context. Every number comes from the tuning
file and the spawner through `Birth`; none is set here.

Source: docs/contracts/systems/drifters.md, Rules, UFO; drifters/07-ufo.md.
"""

import logging
import math
import random
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
    scale_timer,
    tick_warning,
)
from core.drifters.registry import register_drifter
from core.levels import HAZARD_SPEED_MULT
from core.world import SCREEN_H, SCREEN_W

log = logging.getLogger(__name__)

DOME_DRAW_MARGIN: Final[float] = 1.5
"""Px added to the dome's radius in `drawn_parts`. Not a game value: the view draws a circle at a
whole-pixel center with a whole-pixel radius, each rounded, like the fireball's `DRAW_MARGIN`.
Source: drifters.md, Rationale (DRA-104)."""

ARRIVAL_TOLERANCE_PX: Final[float] = 1e-9
"""Px. A step that ends this close to `target_y` ends on it. Not a game value: it absorbs
floating-point dust so the UFO lands exactly. Source: drifters.md, Rationale (DRA-104)."""

PICK_UP_BELOW: Final[float] = 0.5
"""A first pick goes up when its draw is below this. A coin flip, not a game value."""

SEED_BITS: Final[int] = 64
"""Bits of the seed a pick hands to the next one."""

BRAKE_ROUND_DIGITS: Final[int] = 6
"""Decimals the stopping speed ratio is rounded to before it is rounded up."""


@dataclass(frozen=True, slots=True, kw_only=True)
class UfoTypeExtra(DrifterTypeExtra):
    """The UFO's values that hold for every variant: its weave and its band. Level 1 numbers."""

    weave_change_ticks_min: int
    """Fewest ticks between two picks, >= 1. Timer multiplier applied at birth."""

    weave_change_ticks_max: int
    """Most ticks between two picks, >= `weave_change_ticks_min`."""

    weave_step_min: float
    """Least distance to a new height, px, > 0. Also the least room a turn needs. Never scaled."""

    weave_step_max: float
    """Most distance to a new height, px, >= `weave_step_min`."""

    weave_speed_max: float
    """Top up-or-down speed, px/tick, > 0. Hazard speed multiplier applied at birth."""

    weave_turn: float
    """Most change of the up-or-down speed per tick, px/tick^2, > 0. Same multiplier."""

    band_top: float
    """Smallest y of the UFO's center, screen px. Never scaled."""

    band_bottom: float
    """Largest y of the UFO's center, screen px, > `band_top`."""


def ufo_hitbox(disc_width: float, disc_height: float, dome_radius: float) -> Hitbox:
    """Return the disc, then the dome, as offsets from the disc's center, px.

    The dome's center sits on the middle of the disc's top edge. Source: drifters.md, Rules, UFO,
    Hitbox.
    """
    return (
        Box(0.0, 0.0, disc_width, disc_height),
        Circle(0.0, -disc_height / 2, dome_radius),
    )


def check_ufo_variant(disc_width: float, disc_height: float, dome_radius: float) -> None:
    """Raise ValueError unless the dome's drawn box fits in the disc's width.

    So the start just outside a wall hides all of the UFO. `disc_height` is part of the
    variant's shape and plays no part in the check. Source: drifters.md, Rules, UFO, Tuning
    checks.
    """
    drawn_width: float = 2 * (dome_radius + DOME_DRAW_MARGIN)
    if drawn_width > disc_width:
        raise ValueError(
            "dome_radius is too wide for the disc: 2 × (dome_radius + "
            f"{DOME_DRAW_MARGIN:g}) must be at most disc_width ({drawn_width:g} > {disc_width:g})"
        )


def weave_stop_distance(speed: float, turn: float) -> float:
    """Return the px needed to stop from up-or-down `speed`, braking by `turn` each tick.

    `turn` x k x (k + 1) / 2, with k the whole ticks the braking takes. Pure.
    Source: drifters.md, Interface, ufo.py.
    """
    ticks: int = math.ceil(round(speed / turn, BRAKE_ROUND_DIGITS))
    return turn * ticks * (ticks + 1) / 2


def weave_brake_speed(distance: float, turn: float) -> float:
    """Return the fastest up-or-down speed, px/tick, that braking by `turn` stops in `distance`.

    With k the smallest whole number >= 0 such that `distance` <= turn x (k + 1) x (k + 2) / 2,
    it is distance / (k + 1) + turn x k / 2: braking v, v - turn, ... covers exactly `distance`.
    0.0 at distance 0. Pure. Source: drifters.md, Rules, UFO, Ease.
    """
    ticks: int = max(0, math.ceil((math.sqrt(1 + 8 * distance / turn) - 3) / 2))
    while distance > turn * (ticks + 1) * (ticks + 2) / 2:
        ticks += 1
    while ticks > 0 and distance <= turn * ticks * (ticks + 1) / 2:
        ticks -= 1
    return distance / (ticks + 1) + turn * ticks / 2


def check_ufo_weave(extra: UfoTypeExtra) -> None:
    """Raise ValueError for tuning the weave rules can't keep.

    The checks run in a fixed order and the first that fails raises. Source: drifters.md, Rules,
    UFO, Tuning checks.
    """
    if extra.weave_change_ticks_max < extra.weave_change_ticks_min:
        raise ValueError("weave_change_ticks_max must be at least weave_change_ticks_min")
    if extra.weave_step_max < extra.weave_step_min:
        raise ValueError("weave_step_max must be at least weave_step_min")
    if extra.band_bottom <= extra.band_top:
        raise ValueError("band_bottom must be more than band_top")
    if extra.band_bottom > SCREEN_H:
        raise ValueError(f"band_bottom must be at most the screen height ({SCREEN_H})")
    height: float = extra.band_bottom - extra.band_top
    if height < 2 * extra.weave_step_min:
        raise ValueError(
            "the band must be at least 2 × weave_step_min tall "
            f"({height:g} < {2 * extra.weave_step_min:g})"
        )
    top_mult: float = max(HAZARD_SPEED_MULT)
    distance: float = weave_stop_distance(
        extra.weave_speed_max * top_mult, extra.weave_turn * top_mult
    )
    if extra.weave_step_min < distance:
        raise ValueError(
            "weave_step_min must be at least the stopping distance at the top hazard speed "
            f"× ({extra.weave_step_min:g} < {distance:g})"
        )


@dataclass(frozen=True, slots=True)
class _Weave:
    """The part of a UFO one weave step reads and changes. Private: it exists so a tick copies
    the drifter once instead of once per step."""

    weaving: bool
    ticks_left: int
    up: bool | None
    seed: int
    target_y: float
    y: float
    velocity_y: float


@register_drifter
@dataclass(frozen=True, slots=True, kw_only=True)
class Ufo(Drifter):
    """Wildcard mover. Crosses from a side wall at a steady speed, weaving up and down.

    Its path comes from its seed. It never aims at the ship.
    """

    drifter_type: ClassVar[DrifterType] = DrifterType.UFO
    seeded: ClassVar[bool] = True

    invert: bool = False
    """True: enters at the right wall and flies left."""

    velocity_x: float = 0.0
    """px/tick, positive is right: the speed, or minus it with `invert`. Final."""

    seed: int = 0
    """The placement's seed. Final."""

    weave_seed: int = 0
    """The seed of the next pick. Starts at `seed`."""

    band_top: float = 0.0
    """Smallest y of the center, screen px, from the type."""

    band_bottom: float = 0.0
    """Largest y of the center, screen px, from the type."""

    weave_change_ticks_min: int = 1
    """Fewest ticks between two picks. Final: Timer multiplier applied, rounded up."""

    weave_change_ticks_max: int = 1
    """Most ticks between two picks. Final: Timer multiplier applied, rounded up."""

    weave_step_min: float = 0.0
    """Least distance to a new height, px, from the type."""

    weave_step_max: float = 0.0
    """Most distance to a new height, px, from the type."""

    weave_speed_max: float = 0.0
    """Top up-or-down speed, px/tick. Final: hazard speed multiplier applied."""

    weave_turn: float = 0.0
    """Most change of the up-or-down speed per tick, px/tick^2. Final: same."""

    weaving: bool = False
    """It has been fully on screen while ACTIVE, and weaves. Never goes back to False."""

    weave_ticks_left: int = 0
    """Ticks until the next pick, while weaving."""

    weave_up: bool | None = None
    """The way the last pick went: True up, False down. None before the first."""

    target_y: float = 0.0
    """The height it eases toward, screen px."""

    velocity_y: float = 0.0
    """Up-or-down speed, px/tick, positive is down."""

    @classmethod
    def born(cls, birth: Birth) -> Self:
        """Build the UFO in WARNING with its weave values at their final numbers.

        Raises ValueError, in this order, for a specialty switched on, tuning with no
        `UfoTypeExtra`, a missing seed, and a y outside the band.
        """
        name: str = cls.drifter_type.value
        if birth.specialty_enabled is True:
            raise ValueError(f"{name} has no specialty")
        extra: DrifterTypeExtra | None = birth.type_extra
        if not isinstance(extra, UfoTypeExtra):
            raise ValueError(f"{name} tuning has no type values")
        if birth.seed is None:
            raise ValueError(f"{name} placement needs seed")
        if not extra.band_top <= birth.y <= extra.band_bottom:
            raise ValueError(
                f"{name} placement y {birth.y:g} is outside its band "
                f"{extra.band_top:g} to {extra.band_bottom:g}"
            )
        return replace(
            born_drifter(cls, birth),
            invert=birth.invert,
            velocity_x=-birth.speed if birth.invert else birth.speed,
            seed=birth.seed,
            weave_seed=birth.seed,
            band_top=extra.band_top,
            band_bottom=extra.band_bottom,
            weave_change_ticks_min=scale_timer(extra.weave_change_ticks_min, birth.timer_mult),
            weave_change_ticks_max=scale_timer(extra.weave_change_ticks_max, birth.timer_mult),
            weave_step_min=extra.weave_step_min,
            weave_step_max=extra.weave_step_max,
            weave_speed_max=extra.weave_speed_max * birth.hazard_speed_mult,
            weave_turn=extra.weave_turn * birth.hazard_speed_mult,
            target_y=birth.y,
        )

    @classmethod
    def start_position(
        cls, x: float | None, y: float | None, width: float, height: float, invert: bool
    ) -> tuple[float, float]:
        """Return the start center, px.

        Raises ValueError("ufo placement needs y") without a y. No x: just outside the wall it
        enters from, the disc touching it.
        """
        if y is None:
            raise ValueError(f"{cls.drifter_type.value} placement needs y")
        if x is not None:
            return x, y
        return (SCREEN_W + width / 2 if invert else -width / 2), y

    def update(self, ctx: TickContext) -> Self:
        """Count the warning, or fly and weave one ACTIVE tick. GONE stays as it is.

        The ship and the scroll in `ctx` are never read. Source: drifters.md, Rules, UFO, Update.
        """
        if self.phase is Phase.WARNING:
            return tick_warning(self)
        if self.phase is Phase.ACTIVE:
            return self._tick_active()
        return self

    def effect_on_touch(self) -> TouchEffect:
        """Touching the disc or the dome is a hit."""
        return TouchEffect.HIT

    def drawn_parts(self) -> tuple[Box, ...]:
        """Return the disc's box, then the dome's: its radius plus `DOME_DRAW_MARGIN` each side."""
        return self._drawn_parts_at(self.x)

    def is_fully_on_screen(self) -> bool:
        """Return True when every drawn part lies inside the screen, edges allowed."""
        return self._fully_on_screen_at(self.x)

    def _drawn_parts_at(self, x: float) -> tuple[Box, ...]:
        """Return `drawn_parts` as they would be with the center at `x` and the current y."""
        parts: list[Box] = []
        for shape in self.hitbox:
            if isinstance(shape, Box):
                parts.append(Box(x + shape.cx, self.y + shape.cy, shape.w, shape.h))
            elif isinstance(shape, Circle):
                side: float = 2 * (shape.r + DOME_DRAW_MARGIN)
                parts.append(Box(x + shape.cx, self.y + shape.cy, side, side))
        return tuple(parts)

    def _fully_on_screen_at(self, x: float) -> bool:
        """Return True when every drawn part lies inside the screen with the center at `x`."""
        return all(
            part.cx - part.w / 2 >= 0
            and part.cx + part.w / 2 <= SCREEN_W
            and part.cy - part.h / 2 >= 0
            and part.cy + part.h / 2 <= SCREEN_H
            for part in self._drawn_parts_at(x)
        )

    def _weave_state(self) -> _Weave:
        """Return the fields one weave step reads and changes, as one small record."""
        return _Weave(
            weaving=self.weaving,
            ticks_left=self.weave_ticks_left,
            up=self.weave_up,
            seed=self.weave_seed,
            target_y=self.target_y,
            y=self.y,
            velocity_y=self.velocity_y,
        )

    def _tick_active(self) -> Self:
        """Return the UFO after one ACTIVE tick: move across, pick when due, ease up or down.

        One `replace` per tick, because a copy of this many fields is the dearest step.
        """
        x: float = self.x + self.velocity_x
        weave: _Weave = self._weave_state()
        if weave.weaving:
            weave = self._count_down(weave)
        elif self._fully_on_screen_at(x):
            weave = self._pick(replace(weave, weaving=True))
        if not weave.weaving:
            return replace(self, x=x, ticks_in_phase=self.ticks_in_phase + 1)
        weave = self._ease(weave)
        return replace(
            self,
            x=x,
            y=weave.y,
            ticks_in_phase=self.ticks_in_phase + 1,
            weaving=True,
            weave_ticks_left=weave.ticks_left,
            weave_up=weave.up,
            weave_seed=weave.seed,
            target_y=weave.target_y,
            velocity_y=weave.velocity_y,
        )

    def _count_down(self, weave: _Weave) -> _Weave:
        """Return `weave` one tick closer to its next pick, picking when the count ends."""
        counted: _Weave = replace(weave, ticks_left=weave.ticks_left - 1)
        return counted if counted.ticks_left > 0 else self._pick(counted)

    def _pick(self, weave: _Weave) -> _Weave:
        """Return `weave` with a new height, interval and next seed, drawn from its seed.

        Draws only `random()` and, last, `getrandbits()`, so one seed gives one sequence of
        draws on every platform. Source: drifters.md, Rules, UFO, Pick.
        """
        chooser: random.Random = random.Random(weave.seed)
        want_up: bool = chooser.random() < PICK_UP_BELOW if weave.up is None else not weave.up
        span: int = self.weave_change_ticks_max - self.weave_change_ticks_min + 1
        ticks: int = self.weave_change_ticks_min + math.floor(chooser.random() * span)
        step: float = self.weave_step_min + chooser.random() * (
            self.weave_step_max - self.weave_step_min
        )
        room_up: float = weave.y - self.band_top
        room_down: float = self.band_bottom - weave.y
        if (room_up if want_up else room_down) < self.weave_step_min:
            want_up = not want_up
        target: float = weave.y - min(step, room_up) if want_up else weave.y + min(step, room_down)
        return replace(
            weave,
            up=want_up,
            ticks_left=ticks,
            seed=chooser.getrandbits(SEED_BITS),
            target_y=target,
        )

    def _ease(self, weave: _Weave) -> _Weave:
        """Return `weave` after one up-or-down step toward its target, never passing it.

        The speed never passes `weave_speed_max` or changes by more than `weave_turn` a tick, and
        it brakes so it lands exactly on the target. The new y is clamped to the band, which only
        absorbs float dust. Source: drifters.md, Rules, UFO, Ease and Band.
        """
        remaining: float = weave.target_y - weave.y
        want: float = 0.0
        if remaining != 0:
            brake: float = weave_brake_speed(abs(remaining), self.weave_turn)
            want = math.copysign(min(self.weave_speed_max, brake), remaining)
        change: float = max(-self.weave_turn, min(self.weave_turn, want - weave.velocity_y))
        velocity: float = weave.velocity_y + change
        y: float = weave.y + velocity
        if abs(weave.target_y - y) <= ARRIVAL_TOLERANCE_PX:
            y = weave.target_y
        y = min(max(y, self.band_top), self.band_bottom)
        return replace(weave, y=y, velocity_y=velocity)
