"""Ship state and its one-tick physics step.

The step runs on the fixed 60 Hz tick: thrust, gravity, drag, fall cap, move, side walls,
floating islands, the top-line ceiling. It never respawns the ship. The floor check is
`is_below_floor`, used by `core.run`, which decides what a fall costs. It never mutates its
input, never reads frame time, randomness or the run mode.

The ship's hitbox is an inverted T of two upright boxes, a bar and a foot, that fits the
SHIP_W by SHIP_H square. `ship_hitbox` places it at the ship's center. `TOP_SIDE_SPEED` is
the top sideways speed with a side key held.

Floating islands are ground, handed in as one `Ground`. `block_ship` moves the ship out of it the
shortest way and drops the speed into the surface, measured against the ground's own motion.
`spawn_clear` gives the fall respawn spot moved straight up or down out of the ground.

Source: docs/contracts/systems/ship.md, Interface and Rules.
"""

import logging
from dataclasses import dataclass, replace
from typing import Final, Literal, NamedTuple

from core.collision import (
    SURFACE_TOLERANCE,
    Box,
    Direction,
    Hitbox,
    deeply_overlaps,
    exit_distance,
    place_hitbox,
    push_directions,
)
from core.world import SCREEN_H, SCREEN_W, TOP_LINE_Y

log = logging.getLogger(__name__)

SHIP_W: Final[int] = 32
"""Ship width, px. Source: 04-ship.md, ship_w (guess)."""

SHIP_H: Final[int] = 32
"""Ship height, px. Source: 04-ship.md, ship_h (guess)."""

GRAVITY: Final[float] = 0.16
"""Added to vy every tick, px/tick². Source: 04-ship.md, gravity (guess)."""

THRUST_SIDE: Final[float] = 0.42
"""Left or right thrust, px/tick². Source: 04-ship.md, thrust_side (guess)."""

THRUST_UP: Final[float] = 0.42
"""Up thrust, px/tick². Source: 04-ship.md, thrust_up (guess)."""

THRUST_DOWN: Final[float] = 0.42
"""Down thrust, px/tick². Source: 04-ship.md, thrust_down (guess)."""

DRAG_X: Final[float] = 0.94
"""Multiplies vx every tick. Source: 04-ship.md, drag_x (guess)."""

FALL_CAP: Final[float] = 5.5
"""Highest downward speed, px/tick. Source: 04-ship.md, fall_cap (guess)."""

SPAWN_X: Final[float] = 320.0
"""Spawn center x, px. Source: 03-world-and-camera.md, ship_start (guess);
05-lives-and-damage.md, fall_respawn (locked)."""

SPAWN_Y: Final[float] = 240.0
"""Spawn center y, px. Source: 03-world-and-camera.md, ship_start (guess);
05-lives-and-damage.md, fall_respawn (locked)."""

TOP_SIDE_SPEED: Final[float] = THRUST_SIDE * DRAG_X / (1 - DRAG_X)
"""Top sideways speed with a side key held, px/tick (about 6.58). Source: 04-ship.md,
derived values. Recompute when THRUST_SIDE or DRAG_X changes."""

HITBOX_BAR_W: Final[int] = 12
"""Width of the hitbox bar, px. The bar is SHIP_H tall. Source: 04-ship.md, hitbox (guess)."""

HITBOX_FOOT_H: Final[int] = 12
"""Height of the hitbox foot, px. The foot is SHIP_W wide. Source: 04-ship.md, hitbox (guess)."""

SHIP_HITBOX: Final[Hitbox] = (
    Box(cx=0, cy=0, w=HITBOX_BAR_W, h=SHIP_H),
    Box(cx=0, cy=SHIP_H / 2 - HITBOX_FOOT_H / 2, w=SHIP_W, h=HITBOX_FOOT_H),
)
"""The ship's inverted T, as offsets from its center, px: the bar, then the foot along the
bottom. Source: 04-ship.md, hitbox (guess); 91-decision-log.md, row 35."""

Wall = Literal["left", "right"]

_UP: Final[Direction] = (0.0, -1.0)
_DOWN: Final[Direction] = (0.0, 1.0)


@dataclass(frozen=True, slots=True)
class Thrust:
    """Which arrow keys are held this tick."""

    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False


@dataclass(frozen=True, slots=True)
class Ship:
    """Ship state after a tick. Screen px, y down. x and y are the ship's center."""

    x: float
    """Center x, screen px."""

    y: float
    """Center y, screen px, y down."""

    vx: float
    """Horizontal velocity, px/tick. Positive is right."""

    vy: float
    """Vertical velocity, px/tick. Positive is down (falling)."""

    wall: Wall | None = None
    """The wall the ship was clamped against this tick, None if none."""

    at_top_line: bool = False
    """True when the top line (ceiling) clamped the ship this tick."""

    against_island: bool = False
    """True when a floating island pushed the ship out this tick."""


@dataclass(frozen=True, slots=True)
class Ground:
    """The ground the ship can't enter this tick: every floating island, as one. Screen px."""

    hitbox: Hitbox = ()
    """Every island's shapes, placed: boxes and polygons only."""

    velocity_x: float = 0.0
    """Px the ground moved this tick. Positive is right."""

    velocity_y: float = 0.0
    """Px the ground moved this tick. Positive is down."""


NO_GROUND: Final[Ground] = Ground()
"""No island: the step is exactly the step without ground."""


class _Push(NamedTuple):
    """A way out of the ground: the unit direction and how far along it, px."""

    direction: Direction
    distance: float


def spawn() -> Ship:
    """Return the ship at (SPAWN_X, SPAWN_Y), at rest, touching nothing.

    Source: 03-world-and-camera.md, ship_start; 05-lives-and-damage.md, fall_respawn.
    """
    return Ship(x=SPAWN_X, y=SPAWN_Y, vx=0.0, vy=0.0)


def spawn_clear(ground: Ground) -> Ship:
    """Return the respawn ship, moved straight up or down out of the ground if it holds it.

    The spawn point itself when the ground doesn't hold the ship there. The spot above is used
    when its top edge stays at or below the top line and is no farther than the spot below.
    Equally near: above. Pure, no logging.
    Source: systems/ship.md, Rules, Respawn spot; 05-lives-and-damage.md, rule 2.3.
    """
    ship: Ship = spawn()
    moving: Hitbox = ship_hitbox(ship)
    if not deeply_overlaps(moving, ground.hitbox):
        return ship
    up: float = exit_distance(moving, ground.hitbox, _UP)
    down: float = exit_distance(moving, ground.hitbox, _DOWN)
    if up <= down and SPAWN_Y - up - SHIP_H / 2 >= TOP_LINE_Y:
        return replace(ship, y=SPAWN_Y - up)
    return replace(ship, y=SPAWN_Y + down)


def step(ship: Ship, thrust: Thrust, ground: Ground = NO_GROUND) -> Ship:
    """Advance the ship one 60 Hz tick and return the new ship. Never mutates the input.

    Pure apart from DEBUG event logging on `core.ship`: a line when wall, island or top-line
    contact starts, in that order. No line on a tick where nothing happened. Never respawns the
    ship, even past the floor: `is_below_floor` reports that and `core.run` applies the fall.
    Source: 04-ship.md, rule 2 (tick order); systems/ship.md, Rules and Logging.
    """
    vx, vy = _accelerate(ship.vx, ship.vy, thrust)
    x: float = ship.x + vx
    y: float = ship.y + vy
    x, vx, wall = _clamp_to_walls(x, vx)
    walled = Ship(
        x=x,
        y=y,
        vx=vx,
        vy=vy,
        wall=wall,
        at_top_line=ship.at_top_line,
        against_island=ship.against_island,
    )
    if walled.wall is not None and walled.wall != ship.wall:
        log.debug("wall hit side=%s x=%.2f y=%.2f", walled.wall, walled.x, walled.y)
    blocked: Ship = block_ship(walled, ground)
    y, vy, at_top_line = _stop_at_top_line(blocked.y, blocked.vy)
    moved: Ship = replace(blocked, y=y, vy=vy, at_top_line=at_top_line)
    if moved.at_top_line and not ship.at_top_line:
        log.debug("top line stop x=%.2f y=%.2f", moved.x, moved.y)
    return moved


def block_ship(ship: Ship, ground: Ground) -> Ship:
    """Push the ship out of the ground the shortest way and return it, flagged for this tick.

    The ship moves just to the surface. The part of its speed going into the surface, measured
    against the ground's own motion, is dropped; the part along it stays. `against_island` is
    True when it was pushed, False when it was not inside. Logs `island contact` on the tick
    the contact starts. Otherwise pure. Source: systems/ship.md, Rules, Islands.
    """
    moving: Hitbox = ship_hitbox(ship)
    if not ground.hitbox or not deeply_overlaps(moving, ground.hitbox):
        return replace(ship, against_island=False)
    push: _Push = _shortest_way_out(ship, moving, ground)
    vx, vy = _drop_speed_into_surface(ship, ground, push.direction)
    blocked = replace(
        ship,
        x=ship.x + push.distance * push.direction[0],
        y=ship.y + push.distance * push.direction[1],
        vx=vx,
        vy=vy,
        against_island=True,
    )
    if not ship.against_island:
        log.debug("island contact x=%.2f y=%.2f", blocked.x, blocked.y)
    return blocked


def _shortest_way_out(ship: Ship, moving: Hitbox, ground: Ground) -> _Push:
    """Return the shortest push that clears the ground and breaks no wall or the top line.

    A direction is skipped when its spot puts the ship past a side wall, or above the top line
    when it points up. A later direction wins only when shorter by more than SURFACE_TOLERANCE,
    so ties keep the earlier one. Straight down is never skipped, so a way always exists.
    Source: systems/ship.md, Rules, Islands, rule 2.
    """
    best: _Push | None = None
    for direction in push_directions(moving, ground.hitbox):
        distance: float = exit_distance(moving, ground.hitbox, direction)
        if not _spot_allowed(ship, direction, distance):
            continue
        if best is None or distance < best.distance - SURFACE_TOLERANCE:
            best = _Push(direction, distance)
    if best is None:
        raise RuntimeError("no way out of the ground: straight down must always be free")
    return best


def _spot_allowed(ship: Ship, direction: Direction, distance: float) -> bool:
    """True when pushing the ship `distance` px along `direction` keeps it inside the side
    walls and, for an upward push, at or below the top line.
    """
    x: float = ship.x + distance * direction[0]
    y: float = ship.y + distance * direction[1]
    if x - SHIP_W / 2 < 0 or x + SHIP_W / 2 > SCREEN_W:
        return False
    return not (direction[1] < 0 and y - SHIP_H / 2 < TOP_LINE_Y)


def _drop_speed_into_surface(ship: Ship, ground: Ground, normal: Direction) -> tuple[float, float]:
    """Return (vx, vy), px/tick, with the speed into the surface removed.

    Measured against the ground's motion: the relative speed r loses its part along `normal`
    (which points out of the island) only when it points into the surface (r . n < 0).
    Source: systems/ship.md, Rules, Islands, rule 4.
    """
    rx: float = ship.vx - ground.velocity_x
    ry: float = ship.vy - ground.velocity_y
    into: float = rx * normal[0] + ry * normal[1]
    if into >= 0:
        return ship.vx, ship.vy
    return (
        rx - into * normal[0] + ground.velocity_x,
        ry - into * normal[1] + ground.velocity_y,
    )


def _accelerate(vx: float, vy: float, thrust: Thrust) -> tuple[float, float]:
    """Steps 1 to 4: thrust, gravity, drag on vx, fall cap on vy. Returns (vx, vy), px/tick.

    Opposite keys cancel. No drag on vy, no cap on upward speed.
    Source: 04-ship.md, rules 2.1 to 2.4 and 7, Edge cases.
    """
    if thrust.left:
        vx -= THRUST_SIDE
    if thrust.right:
        vx += THRUST_SIDE
    if thrust.up:
        vy -= THRUST_UP
    if thrust.down:
        vy += THRUST_DOWN
    vy += GRAVITY
    vx *= DRAG_X
    return vx, min(vy, FALL_CAP)


def _clamp_to_walls(x: float, vx: float) -> tuple[float, float, Wall | None]:
    """Step 6: clamp an edge past a side wall onto it and zero vx. No bounce.

    Returns (x, vx, wall), wall None when no clamp happened.
    Source: 03-world-and-camera.md, rule 6; 01-vision.md, locked decision 3.
    """
    half_w: float = SHIP_W / 2
    if x - half_w < 0:
        return half_w, 0.0, "left"
    if x + half_w > SCREEN_W:
        return SCREEN_W - half_w, 0.0, "right"
    return x, vx, None


def _stop_at_top_line(y: float, vy: float) -> tuple[float, float, bool]:
    """Step 7, the top line as a ceiling.

    A top edge above TOP_LINE_Y is set onto it and vy becomes 0. Returns (y, vy, stopped).
    Source: 03-world-and-camera.md, rule 2; 04-ship.md, rule 2, step 7.
    """
    half_h: float = SHIP_H / 2
    if y - half_h < TOP_LINE_Y:
        return TOP_LINE_Y + half_h, 0.0, True
    return y, vy, False


def is_below_floor(ship: Ship) -> bool:
    """Step 8 check: True when the ship's top edge is at or past the floor. Pure, no logging.

    Used by `core.run` right after `step` to apply the fall.
    Source: 04-ship.md, rule 2.8; 03-world-and-camera.md, rule 5; systems/ship.md, Rules.
    """
    return ship.y - SHIP_H / 2 >= SCREEN_H


def ship_hitbox(ship: Ship) -> Hitbox:
    """Return the ship's inverted-T hitbox placed at its center, screen px. Pure, no logging.

    Source: systems/ship.md, Rules, Hitbox.
    """
    return place_hitbox(SHIP_HITBOX, ship.x, ship.y)
