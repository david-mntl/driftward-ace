"""The bot check: a ship flown with the arrow keys gets through the wave with zero hits.

09-waves.md, rule 7.3. The bot knows where every drifter will be on every tick (the tracks), so
it is a planner, not a player with reactions. From each start spot it tries every arrow-key
combination held for `decision_ticks`, drops each ship that is hit or falls past the floor, keeps
the first ship to reach each small cell of position and speed, and goes on with the
`beam_width` safest, spread over the screen. One ship
alive at the end is a pass. It flies the game's own ship step and the game's own hitboxes.

The tracks play each drifter with the ship held at the spawn, so a drifter that moves or hits
by where the ship is would be flown as if the ship stayed there. No drifter in the game does yet:
the chain lightning reads the ship only to place its warning, which never hits.
"""

import math
from dataclasses import dataclass

from checks import Context, Finding, Result, Status
from core.collision import (
    Box,
    Circle,
    Hitbox,
    Line,
    Shape,
    grow_hitbox,
    hitboxes_overlap,
)
from core.ship import (
    GRAVITY,
    SHIP_H,
    SHIP_W,
    THRUST_UP,
    Ship,
    Thrust,
    is_below_floor,
    ship_hitbox,
    step,
)
from core.world import SCREEN_H, SCREEN_W
from settings import BotConfig
from tracks import Track

ACTIONS: tuple[Thrust, ...] = tuple(
    Thrust(up=up, down=down, left=left, right=right)
    for up, down in ((False, False), (True, False), (False, True))
    for left, right in ((False, False), (True, False), (False, True))
)
"""Every arrow-key combination that does something different: opposite keys cancel."""

_Bounds = tuple[float, float, float, float]
"""left, top, right, bottom, px."""


@dataclass(frozen=True)
class Danger:
    """One hazard's hitbox on one tick."""

    track: Track
    hitbox: Hitbox
    """Placed, grown by the bot's margin."""
    bounds: _Bounds


@dataclass(frozen=True)
class Flight:
    """How the bot did from one start spot."""

    spot: str
    survived: bool
    end_tick: int
    """The tick the wave's last hazard is gone. The bot must live to here."""
    last_tick: int
    """The last tick a ship was alive on. end_tick on a pass."""
    last_ship: Ship
    """The safest ship on last_tick."""
    hit_by: tuple[str, ...] = ()
    """On a fail: the hazards that hit the last ships, most hits first."""


def timeline(tracks: list[Track], margin_px: float) -> list[list[Danger]]:
    """Every hazard hitbox on every tick from the wave's start to its last hazard's end."""
    dangers: dict[int, list[Danger]] = {}
    for track in tracks:
        for frame in track.frames:
            if not frame.hits:
                continue
            box: Hitbox = (
                grow_hitbox(frame.hitbox, margin_px) if margin_px else frame.hitbox
            )
            tick: int = track.start_tick + frame.age
            dangers.setdefault(tick, []).append(Danger(track, box, _hitbox_bounds(box)))
    end: int = max(dangers, default=0)
    return [dangers.get(tick, []) for tick in range(end + 1)]


def fly(spot: str, ship: Ship, dangers: list[list[Danger]], bot: BotConfig) -> Flight:
    """Search for a zero-hit path from `ship` to the end of `dangers`."""
    end: int = len(dangers) - 1
    ships: list[Ship] = [ship]
    tick: int = 0
    while tick < end:
        steps: int = min(bot.decision_ticks, end - tick)
        cells: dict[tuple[int, int, int, int], Ship] = {}
        hits: dict[str, int] = {}
        for start in ships:
            for action in ACTIONS:
                moved: Ship | None = _hold(start, action, tick, steps, dangers, hits)
                if moved is not None:
                    cells.setdefault(_cell(moved, bot), moved)
        if not cells:
            hit_by: tuple[str, ...] = tuple(
                name for name, _ in sorted(hits.items(), key=lambda item: -item[1])
            )
            return Flight(spot, False, end, tick, ships[0], hit_by)
        ships = _keep(list(cells.values()), dangers[tick + steps], bot)
        tick += steps
    return Flight(spot, True, end, end, ships[0])


def _hold(
    ship: Ship,
    action: Thrust,
    tick: int,
    steps: int,
    dangers: list[list[Danger]],
    hits: dict[str, int],
) -> Ship | None:
    """The ship after holding `action` for `steps` ticks, or None if it is hit or falls."""
    for offset in range(1, steps + 1):
        ship = step(ship, action)
        if is_below_floor(ship):
            hits["the floor"] = hits.get("the floor", 0) + 1
            return None
        hit: Danger | None = _hit(ship, dangers[tick + offset])
        if hit is not None:
            hits[hit.track.name] = hits.get(hit.track.name, 0) + 1
            return None
    return ship


def _hit(ship: Ship, dangers: list[Danger]) -> Danger | None:
    """The first hazard whose hitbox overlaps the ship's, or None."""
    left: float = ship.x - SHIP_W / 2
    right: float = ship.x + SHIP_W / 2
    top: float = ship.y - SHIP_H / 2
    bottom: float = ship.y + SHIP_H / 2
    box: Hitbox | None = None
    for danger in dangers:
        d_left, d_top, d_right, d_bottom = danger.bounds
        if d_right <= left or d_left >= right or d_bottom <= top or d_top >= bottom:
            continue
        box = box or ship_hitbox(ship)
        if hitboxes_overlap(box, danger.hitbox):
            return danger
    return None


def _keep(ships: list[Ship], dangers: list[Danger], bot: BotConfig) -> list[Ship]:
    """The `beam_width` ships to go on with, spread over the screen.

    Ships are grouped by `spread_px` square of the screen and by `spread_speed` of sideways speed.
    The safest ship of each group comes first, then the second safest of each, and so on, so some
    ships are always near, or racing toward, any way through.
    """
    scored = sorted(
        ((_score(ship, dangers, bot.safe_px), ship) for ship in ships),
        key=lambda item: item[0],
        reverse=True,
    )
    taken: dict[tuple[int, int, int], int] = {}
    ranked: list[tuple[int, int, Ship]] = []
    for order, (_, ship) in enumerate(scored):
        group = (
            math.floor(ship.x / bot.spread_px),
            math.floor(ship.y / bot.spread_px),
            round(ship.vx / bot.spread_speed),
        )
        turn: int = taken.get(group, 0)
        taken[group] = turn + 1
        ranked.append((turn, order, ship))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [ship for _, _, ship in ranked[: bot.beam_width]]


def _cell(ship: Ship, bot: BotConfig) -> tuple[int, int, int, int]:
    """Ships in the same cell count as the same ship: the search keeps the first to get there."""
    return (
        math.floor(ship.x / bot.cell_px),
        math.floor(ship.y / bot.cell_px),
        round(ship.vx / bot.cell_speed),
        round(ship.vy / bot.cell_speed),
    )


def _score(ship: Ship, dangers: list[Danger], safe_px: float) -> tuple[float, float]:
    """Higher is safer: room to the nearest hazard up to `safe_px`, then nearness to the middle.

    The floor counts as a hazard, nearer by how far the ship falls before full up thrust stops it.
    """
    falling: float = max(ship.vy, 0.0)
    stopping: float = falling * falling / (2 * (THRUST_UP - GRAVITY))
    room: float = min(safe_px, SCREEN_H - ship.y - SHIP_H / 2 - stopping)
    for danger in dangers:
        for shape in danger.hitbox:
            room = min(room, _distance(ship.x, ship.y, shape))
    middle: float = math.hypot(ship.x - SCREEN_W / 2, ship.y - SCREEN_H / 2)
    return (max(room, 0.0), -middle)


def _distance(x: float, y: float, shape: Shape) -> float:
    """Distance from a point to a placed shape's edge, px. 0 or less inside it."""
    if isinstance(shape, Circle):
        return math.hypot(x - shape.cx, y - shape.cy) - shape.r
    if isinstance(shape, Box):
        dx: float = max(abs(x - shape.cx) - shape.w / 2, 0.0)
        dy: float = max(abs(y - shape.cy) - shape.h / 2, 0.0)
        return math.hypot(dx, dy)
    return _segment_distance(x, y, shape) - shape.thickness / 2


def _segment_distance(x: float, y: float, line: Line) -> float:
    vx: float = line.bx - line.ax
    vy: float = line.by - line.ay
    length2: float = vx * vx + vy * vy
    t: float = 0.0
    if length2 > 0:
        t = max(0.0, min(1.0, ((x - line.ax) * vx + (y - line.ay) * vy) / length2))
    return math.hypot(x - (line.ax + t * vx), y - (line.ay + t * vy))


def _hitbox_bounds(hitbox: Hitbox) -> _Bounds:
    """The upright box around every shape of a placed hitbox."""
    parts: list[_Bounds] = []
    for shape in hitbox:
        if isinstance(shape, Circle):
            parts.append(
                (
                    shape.cx - shape.r,
                    shape.cy - shape.r,
                    shape.cx + shape.r,
                    shape.cy + shape.r,
                )
            )
        elif isinstance(shape, Box):
            half_w, half_h = shape.w / 2, shape.h / 2
            parts.append(
                (
                    shape.cx - half_w,
                    shape.cy - half_h,
                    shape.cx + half_w,
                    shape.cy + half_h,
                )
            )
        else:
            half: float = shape.thickness / 2
            parts.append(
                (
                    min(shape.ax, shape.bx) - half,
                    min(shape.ay, shape.by) - half,
                    max(shape.ax, shape.bx) + half,
                    max(shape.ay, shape.by) + half,
                )
            )
    return (
        min(p[0] for p in parts),
        min(p[1] for p in parts),
        max(p[2] for p in parts),
        max(p[3] for p in parts),
    )


def check_bot(ctx: Context) -> Result:
    """From every start spot the bot flies, it finds a path with zero hits to the wave's end."""
    bot: BotConfig = ctx.config.bot
    dangers: list[list[Danger]] = timeline(ctx.tracks, bot.margin_px)
    spots: tuple[str, ...] = bot.start_spots or tuple(ctx.ship_at)
    found: list[Finding] = []
    for spot in spots:
        flight: Flight = fly(spot, ctx.ship_at[spot], dangers, bot)
        if flight.survived:
            continue
        hazards: tuple[str, ...] = tuple(n for n in flight.hit_by if n != "the floor")
        found.append(
            Finding(
                f"from start spot '{spot}' every path is hit within {bot.decision_ticks} ticks "
                f"after tick {flight.last_tick}, by {', '.join(flight.hit_by[:3])}",
                flight.last_tick,
                ctx.px(flight.last_tick),
                (flight.last_ship.x, flight.last_ship.y),
                hazards[:3],
            )
        )
    margin: str = f", hitboxes grown {bot.margin_px:g} px" if bot.margin_px else ""
    note: str = (
        f"from {', '.join(spots)} to tick {len(dangers) - 1}; "
        f"{bot.decision_ticks}-tick choices, beam {bot.beam_width}{margin}"
    )
    status: Status = "FAIL" if found else "PASS"
    return Result("bot", "the bot finds a zero-hit path", status, tuple(found), note)
