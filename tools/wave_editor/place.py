"""Place by position: the trigger and spawn spot that put a drifter on a chosen spot at a chosen moment.

    python tools/wave_editor/place.py <type> <x> <y> <seconds> [--variant V] [--invert]
        [--level N] [--ship L|C|R] [--wave FILE] [--seed N]

Plays the drifter alone with the game's own physics, the ship held still and the world scrolling
at the level's speed, like the editor's path trail. The drifter takes only the coordinates it is
placed by (CLICK_FIELDS), so the trigger, `at_px`, does the rest. A spot its path never passes at
that moment is refused, with the nearest spot it can reach and the miss in px. No pygame. Reads
the game, never changes it.
"""

import argparse
import functools
import json
import math
import multiprocessing
import os
import sys
from collections.abc import Callable, Iterable
from concurrent.futures import Future, ProcessPoolExecutor, TimeoutError
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

GAME_DIR: Path = Path(__file__).resolve().parents[2] / "game"
sys.path.insert(0, str(GAME_DIR))

from app.tuning import load_tuning
from core.drifters.base import DrifterType, Phase, TickContext, TouchEffect
from core.drifters.registry import drifter_class
from core.drifters.spawner import Placement, placement_seed, spawn_drifter
from core.drifters.tuning import DrifterTuning
from core.levels import LEVEL_COUNT, check_level
from core.scroll import scroll_speed
from core.ship import SPAWN_Y, Ship
from core.wave_files import SEAM_CLEAR_PX, _build_wave
from core.world import SCREEN_H, SCREEN_W

CLICK_FIELDS: dict[str, tuple[str, ...]] = {
    "meteorite": ("x",),
    "satellite": ("y",),
    "chain_lightning": ("x",),
    "fireball": ("x",),
    "coin": ("x", "y"),
    "floating_island": ("x",),
    "planet": ("x",),
    "ufo": ("y",),
    "electric_ball": ("x",),
}
"""Which coordinates of a mouse click a drifter takes. A meteorite falls from its x, a satellite
crosses at its y, a coin sits at both. A fireball enters along the top, at its x. An island and a
planet scroll in from the top at their x. A UFO crosses from a side at its y. An electric ball
falls from its x."""
FROM_TOP_FIELDS: dict[str, tuple[str, ...]] = {"coin": ("x",)}
"""Which coordinates a click sets when the drifter must come in from the top. A coin set at an x
and a y appears there; set at an x only it starts above the screen and slides down with the
scroll, so its path decides where it is and when."""
SHIP_X: dict[str, float] = {"L": 100.0, "C": 320.0, "R": 540.0}
"""Where the ship is held, by start spot, screen px. The same as the editor's ghost."""
CHECK_LEVEL: int = 8
"""The level used when none is given: the GDD's check_level (09-waves.md)."""
REACH_PX: float = 1.0
"""A spot past either end of the path counts as on it within this many px."""
MAX_AGE_TICKS: int = 1200
"""A drifter is followed this many ticks at most if it never leaves."""
PASSES: int = 3
"""Times the spawn coordinate is corrected, for a drifter whose path moves with it."""


@dataclass(frozen=True)
class Spot:
    """Where to place a drifter so it is on the target at the moment."""

    at_px: int
    """Trigger, px of scroll from the wave's start."""
    fields: dict[str, int]
    """The coordinates the placement takes (CLICK_FIELDS), screen px."""
    age: int
    """Ticks from the trigger to the moment."""
    off_px: float
    """Distance from the drifter's center to the target on that tick, px. A drifter moves in
    steps, so this is up to half a tick's move."""


class Cancelled(Exception):
    """The caller stopped the search (see the `cancel` argument of `place_in_wave`)."""


class Unreachable(ValueError):
    """The drifter's path never passes the target at that moment."""

    def __init__(
        self,
        reason: str,
        nearest: tuple[float, float] | None = None,
        miss_px: float = 0.0,
    ) -> None:
        self.nearest: tuple[float, float] | None = nearest
        """The nearest spot it can be on at that moment, screen px. None: none at all."""
        self.miss_px: float = miss_px
        """Distance from the target to `nearest`, px."""
        if nearest is not None:
            reason += f": nearest is {nearest[0]:.0f}, {nearest[1]:.0f}, {miss_px:.0f} px away"
        super().__init__(reason)


def place_at(
    what: Placement,
    target: tuple[float, float],
    moment: int,
    level: int,
    tuning: DrifterTuning,
    ship: Ship,
    cancel: Callable[[], bool] | None = None,
    pool: "ScanPool | None" = None,
    from_top: bool = False,
) -> Spot:
    """Find the trigger and spawn coordinates that put `what` on `target` at `moment`.

    `moment` is in ticks of scroll from the wave's start, at `level`. `what` gives the type,
    variant, invert and seed; its x and y are ignored. Of the spots on its path the one it
    reaches first after spawning wins. Raises Unreachable when the path never passes the
    target at that moment, ValueError when the game refuses the drifter. `cancel` is asked
    between the long steps of a slow search; True stops it with Cancelled. `pool` spreads a
    slow search over several processes; the result is the same without it. `from_top` makes a
    drifter that can be placed in the open (the coin) come in from the top instead: it takes
    only the coordinates of FROM_TOP_FIELDS and its trigger is worked out from its path.
    """
    name: str = what.drifter_type.value
    free: tuple[str, ...] | None = (FROM_TOP_FIELDS if from_top else {}).get(
        name, CLICK_FIELDS.get(name)
    )
    if free is None:
        raise Unreachable(f"{name} cannot be placed by position")
    spawn: dict[str, int] = {axis: round(target["xy".index(axis)]) for axis in free}
    last_age: int = moment - first_due_tick(_placed(what, spawn), level, tuning)

    def path_of(spawn: dict[str, int]) -> list[tuple[float, float] | None]:
        # Nothing reads past age last_age + 1 (the tick after the moment, for the step size).
        return _path(_placed(what, spawn), level, tuning, ship, last_age + 1)

    spawn, age = _by_shift(path_of, spawn, free, target, last_age)
    off: float | None = _landing(path_of(spawn), age, target)
    if off is None:
        scan = functools.partial(
            _scan_values, what, free[0], target, last_age, level, tuning, ship
        )
        spawn, age, off = _by_scan(path_of, free, target, last_age, scan, cancel, pool)
    return Spot(trigger_px(moment - age, level), spawn, age, off)


PathOf = Callable[[dict[str, int]], list[tuple[float, float] | None]]
"""The drifter's path (see `_path`) when placed at the given coordinates."""


def _by_shift(
    path_of: PathOf,
    spawn: dict[str, int],
    free: tuple[str, ...],
    target: tuple[float, float],
    last_age: int,
) -> tuple[dict[str, int], int]:
    """Move the spawn by the miss on the axes it sets, until it stops moving.

    Exact for a drifter whose path keeps its shape wherever it starts. Returns the last spawn
    the game took and the age at which it is nearest the target. A spawn the game refuses
    raises, unless it came from a correction.
    """
    found: tuple[dict[str, int], int] | None = None
    for _ in range(PASSES):
        try:
            path: list[tuple[float, float] | None] = path_of(spawn)
        except ValueError:
            if found is None:
                raise
            break
        age: int = _pick_age(path, free, target, last_age)
        found = (spawn, age)
        point: tuple[float, float] | None = path[age]
        assert point is not None
        moved: dict[str, int] = {
            axis: round(spawn[axis] + target[i] - point[i])
            for i, axis in enumerate("xy")
            if axis in free
        }
        if moved == spawn:
            break
        spawn = moved
    assert found is not None
    return found


def _landing(
    path: list[tuple[float, float] | None], age: int, target: tuple[float, float]
) -> float | None:
    """The miss at `age`, px, if it is within half the drifter's move that tick. Else None."""
    point: tuple[float, float] | None = path[age] if age < len(path) else None
    if point is None:
        return None
    off: float = math.dist(point, target)
    step: float = max(
        (math.dist(point, near) for near in path[max(age - 1, 0) : age + 2] if near),
        default=0.0,
    )
    return off if off <= step / 2 + REACH_PX else None


def _by_scan(
    path_of: PathOf,
    free: tuple[str, ...],
    target: tuple[float, float],
    last_age: int,
    scan: "Callable[[Iterable[int]], Nearest | None]",
    cancel: Callable[[], bool] | None = None,
    pool: "ScanPool | None" = None,
) -> tuple[dict[str, int], int, float]:
    """Try every whole spawn coordinate across the screen and keep the nearest pass.

    For a drifter whose path changes with its start (a UFO weaves inside its band). Slower:
    one path per px, so `pool` may spread them over processes. Raises Unreachable with the
    nearest spot when none lands on the target.
    """
    axis: str = free[0]
    size: int = SCREEN_W if axis == "x" else SCREEN_H
    values: range = range(size + 1)
    found: Nearest | None = (
        pool.nearest(scan, values, cancel)
        if pool is not None
        else _serial_nearest(scan, values, cancel)
    )
    if found is None:
        raise Unreachable("too early: it cannot be on screen yet at this moment")
    distance, age, value = found
    path: list[tuple[float, float] | None] = path_of({axis: value})
    off: float | None = _landing(path, age, target)
    nearest: tuple[float, float] | None = path[age]
    if off is None and nearest is not None:
        raise Unreachable(
            "its path never passes that spot at this moment", nearest, distance
        )
    assert off is not None
    return {axis: value}, age, off


Nearest = tuple[float, int, int]
"""The closest a drifter comes to the target: (distance px, age in ticks, spawn coordinate)."""

CHUNK_VALUES: int = 8
"""Spawn coordinates searched between two looks at the cancel flag."""


def _scan_values(
    what: Placement,
    axis: str,
    target: tuple[float, float],
    last_age: int,
    level: int,
    tuning: DrifterTuning,
    ship: Ship,
    values: Iterable[int],
) -> Nearest | None:
    """The nearest pass to `target` over the spawn coordinates in `values`, ages up to
    `last_age`. The first of equal passes wins. Top level so a worker process can run it."""
    best: Nearest | None = None
    for value in values:
        try:
            path: list[tuple[float, float] | None] = _path(
                _placed(what, {axis: value}), level, tuning, ship, last_age + 1
            )
        except ValueError:
            continue
        for age, point in enumerate(path[: last_age + 1]):
            if point is not None:
                distance: float = math.dist(point, target)
                if best is None or distance < best[0]:
                    best = (distance, age, value)
    return best


def _closer(best: Nearest | None, other: Nearest | None) -> Nearest | None:
    """The nearer of two results; on a tie `best`, the one from lower coordinates."""
    if other is not None and (best is None or other[0] < best[0]):
        return other
    return best


def _chunks(values: range) -> list[range]:
    return [
        values[start : start + CHUNK_VALUES]
        for start in range(0, len(values), CHUNK_VALUES)
    ]


def _serial_nearest(
    scan: "Callable[[Iterable[int]], Nearest | None]",
    values: range,
    cancel: Callable[[], bool] | None,
) -> Nearest | None:
    best: Nearest | None = None
    for chunk in _chunks(values):
        if cancel is not None and cancel():
            raise Cancelled
        best = _closer(best, scan(chunk))
    return best


class ScanPool:
    """Worker processes for the slow scan, started on first use and kept for the next one.

    Spreads the spawn coordinates over the cores and keeps the answer of the serial search:
    chunks are merged in order. If the processes cannot start or break, the search runs here
    instead, and keeps doing so.
    """

    def __init__(self, workers: int | None = None) -> None:
        self._workers: int = workers or max(1, min((os.cpu_count() or 1) - 1, 6))
        self._pool: ProcessPoolExecutor | None = None
        self._broken: bool = self._workers < 2

    def nearest(
        self,
        scan: "Callable[[Iterable[int]], Nearest | None]",
        values: range,
        cancel: Callable[[], bool] | None = None,
    ) -> Nearest | None:
        """`scan` over `values` split across the workers. Raises Cancelled if `cancel` says so."""
        if self._broken:
            return _serial_nearest(scan, values, cancel)
        futures: list[Future[Nearest | None]] = []
        try:
            if self._pool is None:
                self._pool = ProcessPoolExecutor(
                    max_workers=self._workers,
                    mp_context=multiprocessing.get_context("spawn"),
                )
            futures = [self._pool.submit(scan, chunk) for chunk in _chunks(values)]
            best: Nearest | None = None
            for future in futures:
                best = _closer(best, self._wait(future, cancel))
        except Cancelled:
            for future in futures:
                future.cancel()
            raise
        except Exception:  # noqa: BLE001 - a broken pool must only slow the search down
            self._broken = True
            self.close()
            return _serial_nearest(scan, values, cancel)
        return best

    @staticmethod
    def _wait(
        future: "Future[Nearest | None]", cancel: Callable[[], bool] | None
    ) -> Nearest | None:
        while True:
            if cancel is not None and cancel():
                raise Cancelled
            try:
                return future.result(timeout=0.05)
            except TimeoutError:
                continue

    def close(self) -> None:
        """Stop the workers. A search still running is dropped."""
        if self._pool is not None:
            self._pool.shutdown(wait=False, cancel_futures=True)
            self._pool = None


def _placed(what: Placement, spawn: dict[str, int]) -> Placement:
    """`what` at the spawn coordinates in `spawn`; an axis left out keeps its own."""
    return replace(what, x=spawn.get("x", what.x), y=spawn.get("y", what.y))


def first_due_tick(what: Placement, level: int, tuning: DrifterTuning) -> int:
    """The earliest tick of scroll a placement may come due: past the seam for all but a coin.

    The game's loader lets a floating island in the seam, but wave_check counts it as a hazard
    there (09-waves.md, rule 7), so it waits too.
    """
    least: float = 0.0
    if spawn_drifter(what, level, tuning).effect_on_touch() is not TouchEffect.COLLECT:
        least = SEAM_CLEAR_PX
    tick: int = max(1, math.ceil(least / scroll_speed(level)))
    while trigger_px(tick, level) < least:
        tick += 1
    return tick


def trigger_px(tick: int, level: int) -> int:
    """The whole px trigger that comes due on scroll tick `tick` (from 1) at `level`.

    The game makes a trigger due on the first tick the scroll reaches it, so any trigger in
    ((tick - 1) x speed, tick x speed] works. The scroll moves more than 1 px a tick, so a whole
    one is always in there.
    """
    return math.floor(round(tick * scroll_speed(level), 6))


def _path(
    what: Placement,
    level: int,
    tuning: DrifterTuning,
    ship: Ship,
    ticks: int = MAX_AGE_TICKS,
) -> list[tuple[float, float] | None]:
    """The drifter's center per tick from its trigger, None while it is not ACTIVE.

    Stops after `ticks` ticks at most. A caller that only reads up to some age passes that age
    plus the one tick after it, so the rest is never played."""
    ctx: TickContext = TickContext(ship=ship, scroll_step_px=scroll_speed(level))
    drifter = spawn_drifter(what, level, tuning).settle_warning(ctx)
    points: list[tuple[float, float] | None] = []
    for _ in range(min(ticks, MAX_AGE_TICKS) + 1):
        active: bool = drifter.phase is Phase.ACTIVE
        points.append((drifter.x, drifter.y) if active else None)
        drifter = drifter.update(ctx).mark_entered()
        if drifter.phase is Phase.GONE or (
            drifter.has_entered and not drifter.is_partly_on_screen()
        ):
            break
    return points


def _pick_age(
    path: list[tuple[float, float] | None],
    free: tuple[str, ...],
    target: tuple[float, float],
    last_age: int,
) -> int:
    """The first age, up to `last_age`, at which the path passes the target on the axis the
    placement can't set (at most one; none for a coin). Raises Unreachable with the nearest
    such spot when there is none."""
    fixed: list[int] = [i for i, axis in enumerate("xy") if axis not in free]

    def residual(age: int) -> float | None:
        point: tuple[float, float] | None = path[age] if age < len(path) else None
        if point is None or age > last_age:
            return None
        return sum(point[i] - target[i] for i in fixed)

    ages: list[int] = [age for age in range(len(path)) if residual(age) is not None]
    if not ages:
        raise Unreachable("too early: it cannot be on screen yet at this moment")
    for age in ages:
        here: float | None = residual(age)
        after: float | None = residual(age + 1)
        assert here is not None
        if abs(here) <= REACH_PX:
            return age
        if after is not None and here * after <= 0:
            return age if abs(here) <= abs(after) else age + 1
    best: int = min(ages, key=lambda age: abs(residual(age) or 0.0))
    point: tuple[float, float] | None = path[best]
    assert point is not None
    nearest: tuple[float, float] = (
        point[0] if 0 in fixed else target[0],
        point[1] if 1 in fixed else target[1],
    )
    raise Unreachable(
        "its path never passes that spot at this moment",
        nearest,
        math.dist(nearest, target),
    )


def seed_for(
    what: Placement, wave_id: str, placements: list[Any], at_px: float
) -> Placement:
    """`what` with the default seed it gets when added at `at_px` to `placements` (sorted).

    The game seeds a seeded drifter left without one from the wave id and its index. A drifter
    that is not seeded, or one that already has a seed, comes back as it is.
    """
    if what.seed is not None or not drifter_class(what.drifter_type).seeded:
        return what
    index: int = sum(
        1
        for item in placements
        if isinstance(item, dict) and float(item.get("at_px", 0)) <= at_px
    )
    return replace(what, seed=placement_seed(wave_id, index))


def place_in_wave(
    what: Placement,
    target: tuple[float, float],
    moment: int,
    level: int,
    tuning: DrifterTuning,
    ship: Ship,
    wave_id: str,
    placements: list[Any],
    cancel: Callable[[], bool] | None = None,
    pool: ScanPool | None = None,
    from_top: bool = False,
) -> Spot:
    """`place_at` for a placement added to a wave, with the default seed it will get there.

    The seed hangs on the index, the index on the trigger, so a seeded drifter is placed again
    until the two agree.
    """
    speed: float = scroll_speed(level)
    seeded: Placement = seed_for(what, wave_id, placements, moment * speed)
    spot: Spot = place_at(
        seeded, target, moment, level, tuning, ship, cancel, pool, from_top
    )
    for _ in range(PASSES):
        again: Placement = seed_for(what, wave_id, placements, spot.at_px)
        if again == seeded:
            break
        seeded = again
        spot = place_at(
            seeded, target, moment, level, tuning, ship, cancel, pool, from_top
        )
    return spot


def placement_item(what: Placement, spot: Spot) -> dict[str, Any]:
    """The wave file's placement object for `spot`."""
    item: dict[str, Any] = {
        "at_px": spot.at_px,
        "type": what.drifter_type.value,
        **spot.fields,
    }
    if what.variant:
        item["variant"] = what.variant
    if what.invert:
        item["invert"] = True
    if what.seed is not None:
        item["seed"] = what.seed
    return item


# ---- command line -----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args: argparse.Namespace = _parser().parse_args(argv)
    try:
        check_level(args.level)
        what: Placement = Placement(
            drifter_type=DrifterType(args.type),
            variant=args.variant,
            invert=args.invert,
            seed=args.seed,
        )
        wave_id, wave, tuning = _load(args.wave)
    except (ValueError, OSError) as err:
        print(f"place: {err}", file=sys.stderr)
        return 2
    moment: int = round(args.seconds * 60)
    target: tuple[float, float] = (args.x, args.y)
    ship: Ship = Ship(x=SHIP_X[args.ship], y=SPAWN_Y, vx=0.0, vy=0.0)
    placements: list[Any] = list(wave.get("placements", [])) if wave else []
    if wave is None and what.seed is None and drifter_class(what.drifter_type).seeded:
        print(
            f"place: {args.type} needs --seed, or --wave for its default seed",
            file=sys.stderr,
        )
        return 2
    if wave is not None and moment * scroll_speed(args.level) > float(
        wave["length_px"]
    ):
        print("place: the moment is past the wave's end", file=sys.stderr)
        return 2
    try:
        spot: Spot = place_in_wave(
            what, target, moment, args.level, tuning, ship, wave_id, placements
        )
        item: dict[str, Any] = placement_item(what, spot)
        trial: dict[str, Any] = (
            {**wave, "placements": [*placements, item]}
            if wave is not None
            else {
                "length_px": max(spot.at_px, 1),
                "kind": "fixed",
                "placements": [item],
            }
        )
        _build_wave(wave_id, trial, tuning)
    except Unreachable as err:
        print(
            f"refused: {args.type} at {args.x:g}, {args.y:g} at {args.seconds:g} s: {err}"
        )
        return 1
    except ValueError as err:
        print(f"refused: the game does not take it: {err}")
        return 1
    print(
        f"{args.type} on {args.x:g}, {args.y:g} at {args.seconds:g} s (Level {args.level}): "
        f"at_px {spot.at_px}, {spot.age} ticks after its trigger, {spot.off_px:.1f} px off"
    )
    print(json.dumps(item))
    return 0


def _load(path: str | None) -> tuple[str, dict[str, Any] | None, DrifterTuning]:
    """The wave id, the wave and the tuning: the file's sandbox layers over production, or
    production alone when there is no file."""
    if path is None:
        return "place", None, load_tuning()
    from bench import load_merged
    from doc import Doc

    doc: Doc = Doc.open(Path(path).resolve())
    if doc.wave is None:
        raise ValueError(f"{path}: has no wave")
    return doc.wave_id, doc.wave, load_merged(doc)[0]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="place.py",
        description="The trigger and spawn spot that put a drifter on a spot at a moment.",
    )
    parser.add_argument("type", choices=sorted(CLICK_FIELDS), help="drifter type")
    parser.add_argument("x", type=float, help="target x, screen px")
    parser.add_argument("y", type=float, help="target y, screen px, y down")
    parser.add_argument(
        "seconds", type=float, help="moment, seconds into the wave at the level"
    )
    parser.add_argument(
        "--variant", help="variant name; default: the drifter's default"
    )
    parser.add_argument("--invert", action="store_true", help="the mirrored drifter")
    parser.add_argument(
        "--level",
        type=int,
        default=CHECK_LEVEL,
        choices=range(1, LEVEL_COUNT + 1),
        metavar=f"1..{LEVEL_COUNT}",
        help=f"level the moment is at; default {CHECK_LEVEL}",
    )
    parser.add_argument(
        "--ship",
        choices=sorted(SHIP_X),
        default="C",
        help="where the ship is held; default C",
    )
    parser.add_argument(
        "--wave",
        help="a wave or sandbox file: its tuning layers, length and default seeds",
    )
    parser.add_argument("--seed", type=int, help="a seeded drifter's seed (the UFO)")
    return parser


if __name__ == "__main__":
    sys.exit(main())
