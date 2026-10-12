"""Ship state and its one-tick physics step.

The step runs on the fixed 60 Hz tick: thrust, gravity, drag, fall cap, move, side walls,
then two TEMPORARY DRA-6 stand-ins, the top-line stop and the floor respawn. It never
mutates its input, never reads frame time, randomness or the run mode.

Source: docs/contracts/DRA-6/DRA-6-ship.md, Interface and Rules.
"""

import logging
from dataclasses import dataclass
from typing import Literal

from core.world import SCREEN_H, SCREEN_W, TOP_LINE_Y

log = logging.getLogger(__name__)

SHIP_W: int = 32
"""Ship width, px. Source: 04-ship.md, ship_w (guess)."""

SHIP_H: int = 32
"""Ship height, px. Source: 04-ship.md, ship_h (guess)."""

GRAVITY: float = 0.16
"""Added to vy every tick, px/tick². Source: 04-ship.md, gravity (guess)."""

THRUST_SIDE: float = 0.42
"""Left or right thrust, px/tick². Source: 04-ship.md, thrust_side (guess)."""

THRUST_UP: float = 0.42
"""Up thrust, px/tick². Source: 04-ship.md, thrust_up (guess)."""

THRUST_DOWN: float = 0.42
"""Down thrust, px/tick². Source: 04-ship.md, thrust_down (guess)."""

DRAG_X: float = 0.94
"""Multiplies vx every tick. Source: 04-ship.md, drag_x (guess)."""

FALL_CAP: float = 5.5
"""Highest downward speed, px/tick. Source: 04-ship.md, fall_cap (guess)."""

SPAWN_X: float = 320.0
"""Spawn center x, px. Source: 03-world-and-camera.md, ship_start (guess);
05-lives-and-damage.md, fall_respawn (locked)."""

SPAWN_Y: float = 240.0
"""Spawn center y, px. Source: 03-world-and-camera.md, ship_start (guess);
05-lives-and-damage.md, fall_respawn (locked)."""

Wall = Literal["left", "right"]


@dataclass(frozen=True)
class Thrust:
    """Which arrow keys are held this tick."""

    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False


@dataclass(frozen=True)
class Ship:
    """Ship state after a tick. Screen px, y down. x and y are the ship's center."""

    x: float
    y: float
    vx: float
    vy: float
    wall: Wall | None = None
    at_top_line: bool = False


def spawn() -> Ship:
    """Return the ship at (SPAWN_X, SPAWN_Y), at rest, touching nothing.

    Source: 03-world-and-camera.md, ship_start; 05-lives-and-damage.md, fall_respawn.
    """
    return Ship(x=SPAWN_X, y=SPAWN_Y, vx=0.0, vy=0.0)


def step(ship: Ship, thrust: Thrust) -> Ship:
    """Advance the ship one 60 Hz tick and return the new ship. Never mutates the input.

    Pure apart from DEBUG event logging on `core.ship`: a line when wall or top-line
    contact starts, and one on each respawn. No line on a tick where nothing happened.
    Source: 04-ship.md, rule 2 (tick order); DRA-6-ship.md, Rules and Logging.
    """
    vx, vy = _accelerate(ship.vx, ship.vy, thrust)
    x: float = ship.x + vx
    y: float = ship.y + vy
    x, vx, wall = _clamp_to_walls(x, vx)
    y, vy, at_top_line = _stop_at_top_line(y, vy)
    moved = Ship(x=x, y=y, vx=vx, vy=vy, wall=wall, at_top_line=at_top_line)
    _log_contact_starts(ship, moved)
    if _is_below_floor(moved):
        log.debug("respawn from x=%.2f y=%.2f", moved.x, moved.y)
        return spawn()
    return moved


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
    """Step 7, TEMPORARY for DRA-6 until the camera exists.

    A top edge above TOP_LINE_Y is set onto it and vy becomes 0. Returns (y, vy, stopped).
    Source: scope report DRA-6, Limits; 03-world-and-camera.md, rule 2.
    """
    half_h: float = SHIP_H / 2
    if y - half_h < TOP_LINE_Y:
        return TOP_LINE_Y + half_h, 0.0, True
    return y, vy, False


def _is_below_floor(ship: Ship) -> bool:
    """Step 8 check, TEMPORARY for DRA-6 until lives exist: the top edge is at or past the floor.

    Source: scope report DRA-6, Limits; 03-world-and-camera.md, rule 5.
    """
    return ship.y - SHIP_H / 2 >= SCREEN_H


def _log_contact_starts(before: Ship, after: Ship) -> None:
    """Log a wall hit or a top-line stop only on the tick the contact starts.

    Source: DRA-6-ship.md, Rules, Logging.
    """
    if after.wall is not None and after.wall != before.wall:
        log.debug("wall hit side=%s x=%.2f y=%.2f", after.wall, after.x, after.y)
    if after.at_top_line and not before.at_top_line:
        log.debug("top line stop x=%.2f y=%.2f", after.x, after.y)
