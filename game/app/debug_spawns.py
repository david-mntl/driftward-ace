"""The debug test spawn list: a file the Director edits by hand, played in a loop in debug mode.

Reads `tuning/debug_spawns.json` once at startup, in debug mode only, checks every rule of its
schema by hand, then checks every row by spawning it once. Its `play` chooses what debug mode
plays: these rows, or the normal waves. The rows in play (every row, or only
one drifter type's) are spread evenly over one loop of `loop_ticks`, which repeats. A temporary
stand-in kept in the scope reports, not in the GDD. Not a wave: no wave file, no wave clock, no
picker.
Not a startup module: it imports core.drifters, so only app.frame imports it, inside the guard.

Source: docs/contracts/systems/app.md, Interface and Rules, Debug test spawn list;
docs/contracts/schemas/debug-spawn-list.schema.json; scope report DRA-39, Limits and Values needed.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from app.tuning import _fields, _is_number, _read_json
from core.drifters.base import DrifterType
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning

log = logging.getLogger(__name__)

SPAWN_LIST_FILE: str = "debug_spawns.json"
"""The spawn list file, in app.tuning.TUNING_DIR, read at call time."""

ALL_ROWS: str = "all"
"""The mode that plays every row."""

PLAY_LIST: str = "list"
"""play: the rows play and the run has no waves. Source: schemas/debug-spawn-list.schema.json."""

PLAY_WAVES: str = "waves"
"""play: the normal waves play and no row is placed."""

DEFAULT_PLAY: str = PLAY_LIST
"""play when the file leaves it out. Source: scope report DRA-76, Not in GDD (Director)."""

DEFAULT_MODE: str = ALL_ROWS
"""Mode when the file leaves it out. Source: scope report DRA-39, Values needed (stand-in)."""

DEFAULT_LOOP_TICKS: int = 180
"""Loop length when the file leaves it out, ticks (3 s). Source: scope report DRA-39, Values
needed (stand-in, kept from DRA-29)."""

_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
"""Drifter type, mode and variant names. Source: debug-spawn-list.schema.json."""

_LIST_FIELDS: frozenset[str] = frozenset({"play", "mode", "loop_ticks", "rows"})
_LIST_OPTIONAL: frozenset[str] = frozenset({"play", "mode", "loop_ticks"})
_ROW_FIELDS: frozenset[str] = frozenset({"type", "x", "y", "variant", "invert", "speed"})
_ROW_OPTIONAL: frozenset[str] = frozenset({"x", "y", "variant", "invert", "speed"})


@dataclass(frozen=True, slots=True)
class DebugSpawnList:
    """The checked list, ready to play."""

    play: str
    """PLAY_LIST or PLAY_WAVES: what debug mode plays."""

    mode: str
    """"all" or a DrifterType value."""

    loop_ticks: int
    """Length of one loop, ticks, >= 1."""

    schedule: tuple[tuple[int, Placement], ...]
    """(offset within the loop, placement) for each row in play, in file order.

    Offsets from 0 to loop_ticks - 1.
    """


def load_debug_spawns(tuning: DrifterTuning) -> DebugSpawnList:
    """Read and check the spawn list file and every row, then build the schedule.

    Every row, in play or not, is spawned once at Level 1 and thrown away, so a row its drifter
    refuses raises here. Raises ValueError naming the file and the field on any problem; a
    missing file raises FileNotFoundError as it is.
    """
    name, data = _read_json(Path(SPAWN_LIST_FILE))
    fields: dict[str, object] = _fields(name, "", data, _LIST_FIELDS, optional=_LIST_OPTIONAL)
    play: str = _play(name, fields.get("play", DEFAULT_PLAY))
    mode: str = _mode(name, fields.get("mode", DEFAULT_MODE))
    loop_ticks: int = _loop_ticks(name, fields.get("loop_ticks", DEFAULT_LOOP_TICKS))
    rows: object = fields["rows"]
    if not isinstance(rows, list):
        raise ValueError(f"{name}: rows must be a list")
    placements: list[Placement] = [
        _row(name, f"rows[{index}]", row, tuning) for index, row in enumerate(rows)
    ]
    in_play: list[Placement] = [
        placement
        for placement in placements
        if mode == ALL_ROWS or placement.drifter_type.value == mode
    ]
    count: int = len(in_play)
    schedule: tuple[tuple[int, Placement], ...] = tuple(
        ((index * loop_ticks) // count, placement) for index, placement in enumerate(in_play)
    )
    log.info(
        "debug spawns loaded mode=%s rows=%d loop_ticks=%d play=%s", mode, count, loop_ticks, play
    )
    return DebugSpawnList(play=play, mode=mode, loop_ticks=loop_ticks, schedule=schedule)


def debug_spawns_due(spawn_list: DebugSpawnList, ticks: int) -> tuple[Placement, ...]:
    """Return the placements due on this tick of play, in schedule order.

    ticks is run.scroll.ticks after the tick: 1 on the first tick of play. () when ticks < 1.
    Otherwise every placement whose offset is (ticks - 1) % spawn_list.loop_ticks.
    """
    if ticks < 1:
        return ()
    offset: int = (ticks - 1) % spawn_list.loop_ticks
    return tuple(placement for due, placement in spawn_list.schedule if due == offset)


def _type_names() -> str:
    """Return the DrifterType values as a comma-separated list, for error messages."""
    return ", ".join(drifter_type.value for drifter_type in DrifterType)


def _drifter_type(value: object) -> DrifterType | None:
    """Return the DrifterType whose value is `value`, or None."""
    for drifter_type in DrifterType:
        if drifter_type.value == value:
            return drifter_type
    return None


def _play(name: str, value: object) -> str:
    """Return play if it is "list" or "waves", else raise."""
    if value not in (PLAY_LIST, PLAY_WAVES):
        raise ValueError(f'{name}: play must be "{PLAY_LIST}" or "{PLAY_WAVES}"')
    return str(value)


def _mode(name: str, value: object) -> str:
    """Return the mode if it is "all" or a drifter type value, else raise."""
    if value != ALL_ROWS and _drifter_type(value) is None:
        raise ValueError(f'{name}: mode must be "{ALL_ROWS}" or a drifter type ({_type_names()})')
    return str(value)


def _loop_ticks(name: str, value: object) -> int:
    """Return loop_ticks if it is an int >= 1 (never a bool), else raise."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name}: loop_ticks must be an integer >= 1")
    return value


def _row(name: str, path: str, data: object, tuning: DrifterTuning) -> Placement:
    """Check one row against the schema, build its Placement and spawn it once to check it.

    x and y are both optional: the drifter's own start position refuses a missing coordinate it
    needs, through the load-time spawn. Source: app.md, Rules, Debug test spawn list (DRA-56).
    """
    fields: dict[str, object] = _fields(name, path, data, _ROW_FIELDS, optional=_ROW_OPTIONAL)
    drifter_type: DrifterType | None = _drifter_type(fields["type"])
    if drifter_type is None:
        raise ValueError(f"{name}: {path}.type must be a drifter type ({_type_names()})")
    placement = Placement(
        drifter_type,
        x=_coordinate(name, path, fields, "x"),
        y=_coordinate(name, path, fields, "y"),
        variant=_variant(name, path, fields),
        invert=_invert(name, path, fields),
        speed=_speed(name, path, fields),
    )
    try:
        spawn_drifter(placement, 1, tuning)
    except ValueError as err:
        raise ValueError(f"{name}: {path}: {err}") from err
    return placement


def _coordinate(name: str, path: str, fields: dict[str, object], key: str) -> float | None:
    """Return a row's x or y as a float, None when left out. Raise unless it is a number."""
    if key not in fields:
        return None
    value: object = fields[key]
    if not _is_number(value):
        raise ValueError(f"{name}: {path}.{key} must be a number")
    return float(value)


def _variant(name: str, path: str, fields: dict[str, object]) -> str | None:
    """Return a row's variant name, None when left out. Raise unless it is a valid name."""
    if "variant" not in fields:
        return None
    value: object = fields["variant"]
    if not isinstance(value, str) or not _NAME.fullmatch(value):
        raise ValueError(f"{name}: {path}.variant must be a string matching {_NAME.pattern}")
    return value


def _invert(name: str, path: str, fields: dict[str, object]) -> bool:
    """Return a row's invert, False when left out. Raise unless it is a boolean."""
    value: object = fields.get("invert", False)
    if not isinstance(value, bool):
        raise ValueError(f"{name}: {path}.invert must be a boolean")
    return value


def _speed(name: str, path: str, fields: dict[str, object]) -> float | None:
    """Return a row's Level 1 speed, px/tick, None when left out. Raise unless it is > 0."""
    if "speed" not in fields:
        return None
    value: object = fields["speed"]
    if not _is_number(value) or value <= 0:
        raise ValueError(f"{name}: {path}.speed must be a number > 0")
    return float(value)
