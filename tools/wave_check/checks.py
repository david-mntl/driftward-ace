"""The wave_check checks of part 1: placement sanity, telegraph, coin near a hazard, coin
inside an island, seam.

Each check takes a `Context` (the wave, the level, the tuning and every drifter's track) and
returns a `Result` with a status and findings. A finding names the tick, the scroll distance, the
position and the drifters involved. The bot check (zero-hit path) is in `bot.py` and runs on its
own (`--bot`). The gap check is not built yet.
"""

from dataclasses import dataclass, field
from typing import Literal

from core.collision import Hitbox, grow_hitbox, hitboxes_overlap
from core.drifters.base import DrifterType, Phase, TouchEffect, scale_timer
from core.drifters.registry import drifter_class
from core.drifters.tuning import DrifterTuning
from core.levels import FIRST_LEVEL, timer_mult
from core.scroll import scroll_speed
from core.ship import SHIP_W, Ship, ship_hitbox
from core.ship import spawn as ship_spawn
from core.waves import Wave
from settings import Config
from tracks import Frame, Track

Status = Literal["PASS", "FAIL", "SKIP"]


@dataclass(frozen=True)
class Finding:
    """One thing a check found."""

    message: str
    tick: int | None = None
    px: float | None = None
    pos: tuple[float, float] | None = None
    drifters: tuple[str, ...] = ()


@dataclass(frozen=True)
class Result:
    name: str
    title: str
    status: Status
    findings: tuple[Finding, ...] = ()
    note: str = ""


@dataclass
class Context:
    wave: Wave
    level: int
    tuning: DrifterTuning
    config: Config
    tracks: list[Track]
    ship_at: dict[str, Ship] = field(default_factory=dict)
    """The ship at each start spot."""

    @property
    def speed(self) -> float:
        return scroll_speed(self.level)

    def px(self, tick: int) -> float:
        return round(tick * self.speed, 1)


def _is_hazard(track: Track) -> bool:
    # Anything that is not a pickup. A blocker (the floating island) counts as a hazard here,
    # though it never hurts (09-waves.md, rule 7).
    return track.effect is not TouchEffect.COLLECT


def _is_island(track: Track) -> bool:
    # The drifter the ship stands on: the one whose touch blocks.
    return track.effect is TouchEffect.BLOCK


def _result(name: str, title: str, findings: list[Finding], note: str = "") -> Result:
    return Result(name, title, "FAIL" if findings else "PASS", tuple(findings), note)


# ---- placement sanity -------------------------------------------------------------------


def check_placements(ctx: Context) -> Result:
    """Every drifter enters the screen, and no hazard turns active on top of the ship."""
    found: list[Finding] = []
    for track in ctx.tracks:
        first: Frame = track.frames[0]
        if not track.entered:
            found.append(
                Finding(
                    f"{track.name} never enters the screen",
                    track.start_tick,
                    track.item.at_px,
                    (first.x, first.y),
                    (track.name,),
                )
            )
        if not _is_hazard(track):
            continue
        active: Frame | None = next(
            (f for f in track.frames if f.phase is Phase.ACTIVE), None
        )
        if active is None:
            continue
        for spot, ship in ctx.ship_at.items():
            if hitboxes_overlap(active.hitbox, ship_hitbox(ship)):
                found.append(
                    Finding(
                        f"{track.name} turns active on the ship at start spot '{spot}'",
                        track.start_tick + active.age,
                        track.item.at_px,
                        (active.x, active.y),
                        (track.name,),
                    )
                )
    return _result(
        "placement",
        "placement: enters the screen, not on the ship",
        found,
        "a UFO outside its band is refused by the game's loader",
    )


# ---- telegraph --------------------------------------------------------------------------


def _telegraph(
    tuning: DrifterTuning, level: int, drifter_type: DrifterType
) -> tuple[int, str] | None:
    """The drifter's telegraph at `level` before the game's floor, ticks, with its sum.

    None when the drifter says it has no telegraph. An entry warning is not a telegraph
    (07-drifters.md rule 9).
    """
    base: int | None = drifter_class(drifter_type).telegraph_ticks(
        tuning.drifters[drifter_type].extra
    )
    if base is None:
        return None
    use: int = level if tuning.switches.timer_scaling else FIRST_LEVEL
    mult: float = timer_mult(use)
    return scale_timer(base, mult), f"{base} x {mult:g}"


def check_telegraph(ctx: Context) -> Result:
    """Every telegraph lasts at least telegraph_min ticks at this level, before the game's floor."""
    minimum: int = ctx.tuning.hazards.telegraph_min_ticks
    found: list[Finding] = []
    seen: set[str] = set()
    plain: set[DrifterType] = set()
    for track in ctx.tracks:
        drifter_type: DrifterType = track.item.placement.drifter_type
        if drifter_type in seen or drifter_type in plain:
            continue
        telegraph: tuple[int, str] | None = _telegraph(ctx.tuning, ctx.level, drifter_type)
        if telegraph is None:
            plain.add(drifter_type)
            continue
        seen.add(drifter_type)
        ticks, how = telegraph
        if ticks < minimum:
            found.append(
                Finding(
                    f"{drifter_type.value} charge is {ticks} ticks at level {ctx.level} "
                    f"({how}), under telegraph_min {minimum}",
                    track.start_tick,
                    track.item.at_px,
                    drifters=(track.name,),
                )
            )
    note: str = f"telegraph_min {minimum} ticks; checked: {', '.join(sorted(t.value for t in seen)) or 'none in this wave'}"
    return _result("telegraph", f"telegraph >= {minimum} ticks", found, note)


# ---- coins ------------------------------------------------------------------------------


def _center_distance(a: Frame, b: Frame) -> float:
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def check_coins(ctx: Context) -> Result:
    """Every coin comes within coin_near of a hazard's hitbox while both are on screen."""
    near: float = ctx.config.coin_near_ship_widths * SHIP_W
    hazards: list[Track] = [t for t in ctx.tracks if _is_hazard(t)]
    found: list[Finding] = []
    coins: int = 0
    for coin in (t for t in ctx.tracks if not _is_hazard(t)):
        coins += 1
        closest: tuple[float, Track] | None = None
        met: bool = False
        for frame in coin.frames:
            if not frame.visible or not frame.hitbox:
                continue
            reach: Hitbox = grow_hitbox(frame.hitbox, near)
            tick: int = coin.start_tick + frame.age
            for hazard in hazards:
                other: Frame | None = _frame_at(hazard, tick)
                if other is None or not other.hitbox or not other.visible:
                    continue
                if hitboxes_overlap(reach, other.hitbox):
                    met = True
                    break
                gap: float = _center_distance(frame, other)
                if closest is None or gap < closest[0]:
                    closest = (gap, hazard)
            if met:
                break
        if not met:
            first: Frame = coin.frames[0]
            why: str = (
                f"nearest hazard centre {closest[0]:.0f} px away ({closest[1].name})"
                if closest
                else "no hazard is on screen at the same time"
            )
            found.append(
                Finding(
                    f"{coin.name} never comes within {near:g} px of a hazard: {why}",
                    coin.start_tick,
                    coin.item.at_px,
                    (first.x, first.y),
                    (coin.name, *((closest[1].name,) if closest else ())),
                )
            )
    note: str = (
        f"{coins} coin(s), limit {near:g} px from the coin's hitbox to a hazard's"
    )
    return _result("coin_near", "every coin near a hazard", found, note)


def check_coin_in_island(ctx: Context) -> Result:
    """No coin sits inside a floating island. Touching an island's edge from outside passes."""
    islands: list[Track] = [t for t in ctx.tracks if _is_island(t)]
    found: list[Finding] = []
    for coin in (t for t in ctx.tracks if not _is_hazard(t)):
        for frame in coin.frames:
            if not frame.hitbox:
                continue
            tick: int = coin.start_tick + frame.age
            inside: Track | None = next(
                (
                    island
                    for island in islands
                    if (other := _frame_at(island, tick)) is not None
                    and other.hitbox
                    and hitboxes_overlap(frame.hitbox, other.hitbox)
                ),
                None,
            )
            if inside is not None:
                found.append(
                    Finding(
                        f"{coin.name} sits inside {inside.name}",
                        tick,
                        ctx.px(tick),
                        (frame.x, frame.y),
                        (coin.name, inside.name),
                    )
                )
                break
    note: str = f"{len(islands)} island(s)"
    return _result("coin_in_island", "no coin inside an island", found, note)


def _frame_at(track: Track, tick: int) -> Frame | None:
    """The track's frame on `tick` counted from the wave's start, or None if it is not alive."""
    age: int = tick - track.start_tick
    return track.frames[age] if 0 <= age < len(track.frames) else None


# ---- seam -------------------------------------------------------------------------------


def check_seam(ctx: Context) -> Result:
    """No hazard is on screen in the wave's first seam_clear px. A warning counts."""
    clear: float = ctx.config.seam_clear_px
    found: list[Finding] = []
    for track in ctx.tracks:
        if not _is_hazard(track):
            continue
        first_px: float = ctx.px(track.start_tick)
        if first_px < clear:
            found.append(
                Finding(
                    f"{track.name} is on screen at {first_px:g} px, inside the first {clear:g} px",
                    track.start_tick,
                    first_px,
                    (track.frames[0].x, track.frames[0].y),
                    (track.name,),
                )
            )
    return _result("seam", f"seam clear {clear:g} px at the start", found)


# ---- running them -----------------------------------------------------------------------

NOT_YET: tuple[Result, ...] = (
    Result(
        "gap",
        "gap >= gap_min along the bot's path",
        "SKIP",
        note="not built yet",
    ),
    Result(
        "bot",
        "the bot finds a zero-hit path",
        "SKIP",
        note="runs on its own: wave_check.py --bot",
    ),
    Result("lava", "lava walls", "SKIP", note="lava is not defined yet"),
    Result(
        "notes",
        "per-drifter notes",
        "SKIP",
        note="floating island: coin inside is its own check; planet: measured from its body; "
        "UFO: band checked by the game's loader; "
        "gaps and the bot's island and planet physics are not built",
    ),
)


def run_checks(ctx: Context) -> list[Result]:
    """Every check, in report order."""
    return [
        check_placements(ctx),
        check_telegraph(ctx),
        check_coins(ctx),
        check_coin_in_island(ctx),
        check_seam(ctx),
        *NOT_YET,
    ]


def ships_at_spots(config: Config) -> dict[str, Ship]:
    """The ship at each start spot: the game's spawn, moved to the spot's x."""
    base: Ship = ship_spawn()
    return {
        name: Ship(x=x, y=base.y, vx=0.0, vy=0.0)
        for name, x in config.start_spots.items()
    }
