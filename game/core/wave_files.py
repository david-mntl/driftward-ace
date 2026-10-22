"""The wave book's loader check: decoded wave and playlist files in, a checked WaveBook out.

`build_wave_book` takes the decoded JSON of every wave file and of the playlist, checks every rule
of their schemas by hand (pygbag has no schema library), spawns each placement once through the
real spawner, and builds the book. The first problem raises a ValueError that names the file and
the field. It never opens a file and logs nothing: the app reads, decodes and logs the load.

Source: docs/contracts/systems/waves.md, Interface and Rules, The wave files;
docs/contracts/schemas/wave.schema.json and playlist.schema.json.
"""

import logging
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final, TypeGuard

from core.drifters.base import Drifter, DrifterType, TouchEffect
from core.drifters.registry import drifter_class
from core.drifters.spawner import MAX_SEED, Placement, placement_seed, spawn_drifter
from core.drifters.tuning import DrifterTuning
from core.levels import FIRST_LEVEL, LEVEL_COUNT
from core.waves import LevelPlaylist, Wave, WaveBook, WaveKind, WavePlacement

log = logging.getLogger(__name__)

SEAM_CLEAR_PX: Final[float] = 120.0
"""A hazard may not trigger below this many px into its wave. Source: 09-waves.md, seam_clear
(locked)."""

NAME_PATTERN: Final[str] = r"^[a-z][a-z0-9_]*$"
"""Wave ids, drifter types and variant names. Source: wave.schema.json."""

WAVES_FOLDER: Final[str] = "waves"
"""How errors name the folder of the wave files."""

PLAYLIST_NAME: Final[str] = "playlist"
"""The playlist file's name, without .json."""

_NAME: Final[re.Pattern[str]] = re.compile(NAME_PATTERN)
_WAVE_FIELDS: Final[frozenset[str]] = frozenset(
    {"length_px", "kind", "min_level", "extra_rest_ticks", "placements"}
)
_PLACEMENT_FIELDS: Final[frozenset[str]] = frozenset(
    {"at_px", "type", "x", "y", "variant", "invert", "specialty", "as_level", "seed"}
)
_PLAYLIST_FIELDS: Final[frozenset[str]] = frozenset({"wave_zero", "levels"})
_LEVEL_FIELDS: Final[frozenset[str]] = frozenset({"fixed", "random_count"})
_KINDS: Final[tuple[str, ...]] = tuple(kind.value for kind in WaveKind)


@dataclass(frozen=True, slots=True)
class _Where:
    """A spot in a file: the file, and the path to the object being checked ("" for the root)."""

    file: str
    path: str = ""

    def error(self, problem: str) -> ValueError:
        """Return the error for a problem with the object at this spot."""
        spot: str = f"{self.file}: {self.path}: " if self.path else f"{self.file}: "
        return ValueError(spot + problem)

    def error_field(self, field: str, problem: str) -> ValueError:
        """Return the error for a problem with one field of the object at this spot."""
        name: str = f"{self.path}.{field}" if self.path else field
        return ValueError(f"{self.file}: {name} {problem}")


def build_wave_book(
    wave_documents: Mapping[str, object],
    playlist_document: object,
    tuning: DrifterTuning,
) -> WaveBook:
    """Check every wave file and the playlist, and return the wave book. Raises ValueError.

    `wave_documents` maps each wave id (its file name without .json) to its decoded JSON. The
    order of checks: every wave by id, then the playlist, then the pool checks, Level 1 to 8.
    Pure: no file, no log.
    """
    waves: dict[str, Wave] = {
        wave_id: _build_wave(wave_id, wave_documents[wave_id], tuning)
        for wave_id in sorted(wave_documents)
    }
    wave_zero: str
    playlists: tuple[LevelPlaylist, ...]
    wave_zero, playlists = _read_playlist(playlist_document)
    _check_named_waves(waves, wave_zero, playlists)
    book: WaveBook = WaveBook(waves=waves, wave_zero_id=wave_zero, playlists=playlists)
    _check_pools(book)
    return book


def _is_string(value: object) -> TypeGuard[str]:
    return isinstance(value, str)


def _is_name(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and _NAME.fullmatch(value) is not None


def _is_boolean(value: object) -> TypeGuard[bool]:
    return isinstance(value, bool)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_kind(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and value in _KINDS


def _is_number(value: object) -> TypeGuard[float]:
    """Return True for a finite int or float. A bool is not a number.

    An int too large to become a float is not finite for this purpose, so it is refused.
    """
    if not isinstance(value, int | float) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _is_positive_number(value: object) -> TypeGuard[float]:
    return _is_number(value) and value > 0


def _is_non_negative_number(value: object) -> TypeGuard[float]:
    return _is_number(value) and value >= 0


def _is_integer(value: object) -> TypeGuard[int]:
    """Return True for an int. A bool is not an integer."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_non_negative_integer(value: object) -> TypeGuard[int]:
    return _is_integer(value) and value >= 0


def _is_seed(value: object) -> TypeGuard[int]:
    return _is_integer(value) and 0 <= value <= MAX_SEED


def _is_level(value: object) -> TypeGuard[int]:
    return _is_integer(value) and FIRST_LEVEL <= value <= LEVEL_COUNT


def _checked[T](
    where: _Where,
    data: Mapping[str, object],
    field: str,
    test: Callable[[object], TypeGuard[T]],
    needs: str,
) -> T:
    """Return the required `field` of `data`, or raise unless `test` accepts it."""
    value: object = data.get(field)
    if not test(value):
        raise where.error_field(field, f"must be {needs}")
    return value


def _checked_optional[T](
    where: _Where,
    data: Mapping[str, object],
    field: str,
    test: Callable[[object], TypeGuard[T]],
    needs: str,
) -> T | None:
    """Return the optional `field` of `data`: None when left out, else as `_checked`."""
    if field not in data:
        return None
    return _checked(where, data, field, test, needs)


def _as_object(where: _Where, document: object, noun: str) -> Mapping[str, object]:
    """Return `document` as a JSON object, or raise."""
    if not isinstance(document, dict):
        raise where.error(f"must be {noun}")
    return document


def _refuse_unknown_fields(
    where: _Where, data: Mapping[str, object], known: frozenset[str]
) -> None:
    """Raise for the first field of `data`, in file order, that is not in `known`."""
    for field in data:
        if field not in known:
            raise where.error(f"unknown field '{field}'")


def _build_wave(wave_id: str, document: object, tuning: DrifterTuning) -> Wave:
    """Check one wave file and return its Wave."""
    file: str = f"{WAVES_FOLDER}/{wave_id}.json"
    where: _Where = _Where(file)
    if not _NAME.fullmatch(wave_id):
        raise where.error(f"the file name must match {NAME_PATTERN}")
    data: Mapping[str, object] = _as_object(where, document, "a JSON object")
    _refuse_unknown_fields(where, data, _WAVE_FIELDS)
    length_px: float = _checked(where, data, "length_px", _is_positive_number, "a number > 0")
    kind: WaveKind = WaveKind(_checked(where, data, "kind", _is_kind, '"fixed" or "pool"'))
    items: list[object] = _checked(where, data, "placements", _is_list, "a list")
    min_level: int | None = _read_min_level(where, data, kind)
    extra_rest_ticks: int | None = _checked_optional(
        where, data, "extra_rest_ticks", _is_non_negative_integer, "an integer >= 0"
    )
    placements: list[WavePlacement] = [
        _build_placement(wave_id, index, item, tuning) for index, item in enumerate(items)
    ]
    _check_one_path_per_seed(file, placements)
    placements.sort(key=lambda wave_placement: wave_placement.at_px)
    return Wave(
        wave_id=wave_id,
        length_px=float(length_px),
        kind=kind,
        min_level=min_level,
        extra_rest_ticks=0 if extra_rest_ticks is None else extra_rest_ticks,
        placements=tuple(placements),
    )


def _read_min_level(where: _Where, data: Mapping[str, object], kind: WaveKind) -> int | None:
    """Return a pool wave's min_level. Raise if a pool wave has none or a fixed wave has one."""
    if kind is WaveKind.FIXED:
        if "min_level" in data:
            raise where.error_field("min_level", "is only for a pool wave")
        return None
    if "min_level" not in data:
        raise where.error_field("min_level", "is required for a pool wave")
    level_range: str = f"from {FIRST_LEVEL} to {LEVEL_COUNT}"
    return _checked(where, data, "min_level", _is_level, f"an integer {level_range}")


def _build_placement(
    wave_id: str, index: int, item: object, tuning: DrifterTuning
) -> WavePlacement:
    """Check one placement, spawn it once as a test, and return it with its trigger.

    `index` is the placement's place in the file's list. A seeded drifter that the file gives no
    seed gets `placement_seed(wave_id, index)`.
    """
    where: _Where = _Where(f"{WAVES_FOLDER}/{wave_id}.json", f"placements[{index}]")
    data: Mapping[str, object] = _as_object(where, item, "an object")
    _refuse_unknown_fields(where, data, _PLACEMENT_FIELDS)
    at_px: float = _checked(where, data, "at_px", _is_non_negative_number, "a number >= 0")
    drifter_type: DrifterType = _read_drifter_type(where, data)
    variant: str | None = _checked_optional(
        where, data, "variant", _is_name, f"a string matching {NAME_PATTERN}"
    )
    invert: bool | None = _checked_optional(where, data, "invert", _is_boolean, "a boolean")
    as_level: int | None = _checked_optional(
        where, data, "as_level", _is_level, f"an integer from {FIRST_LEVEL} to {LEVEL_COUNT}"
    )
    seed: int | None = _checked_optional(
        where, data, "seed", _is_seed, f"an integer from 0 to {MAX_SEED}"
    )
    if seed is None and drifter_class(drifter_type).seeded:
        seed = placement_seed(wave_id, index)
    placement: Placement = Placement(
        drifter_type,
        x=_checked_optional(where, data, "x", _is_number, "a number"),
        y=_checked_optional(where, data, "y", _is_number, "a number"),
        variant=variant,
        as_level=as_level,
        specialty_enabled=_checked_optional(where, data, "specialty", _is_boolean, "a boolean"),
        invert=bool(invert),
        seed=seed,
    )
    _check_spawns_clear_of_seam(where, placement, at_px, tuning)
    return WavePlacement(at_px=float(at_px), placement=placement)


def _check_one_path_per_seed(file: str, placements: list[WavePlacement]) -> None:
    """Raise for the first placement, by file index, whose seed an earlier one already uses.

    Source: drifters/07-ufo.md, seed (two UFOs in one wave never share a path).
    """
    first_user: dict[int, int] = {}
    for index, wave_placement in enumerate(placements):
        seed: int | None = wave_placement.placement.seed
        if seed is None:
            continue
        if seed in first_user:
            where: _Where = _Where(file, f"placements[{index}]")
            raise where.error(f"seed {seed} is already used by placements[{first_user[seed]}]")
        first_user[seed] = index


def _read_drifter_type(where: _Where, data: Mapping[str, object]) -> DrifterType:
    """Return the placement's drifter type, or raise listing the types in enum order."""
    name: str = _checked(where, data, "type", _is_string, "a string")
    try:
        return DrifterType(name)
    except ValueError as error:
        known: str = ", ".join(drifter_type.value for drifter_type in DrifterType)
        problem: str = f"'{name}' is not a drifter type ({known})"
        raise where.error_field("type", problem) from error


def _check_spawns_clear_of_seam(
    where: _Where, placement: Placement, at_px: float, tuning: DrifterTuning
) -> None:
    """Spawn `placement` once at the first level, and refuse a hazard inside the seam.

    Whatever the spawner raises is raised again as a ValueError naming the placement.
    """
    try:
        drifter: Drifter = spawn_drifter(placement, FIRST_LEVEL, tuning)
    except ValueError as error:
        raise where.error(str(error)) from error
    if drifter.effect_on_touch() is TouchEffect.HIT and at_px < SEAM_CLEAR_PX:
        raise where.error(
            f"a hazard ({placement.drifter_type.value}) at {at_px:g} px "
            f"is inside the first {SEAM_CLEAR_PX:g} px"
        )


def _read_playlist(document: object) -> tuple[str, tuple[LevelPlaylist, ...]]:
    """Check the playlist file's shape and return Wave 0's id and the level playlists."""
    where: _Where = _Where(f"{WAVES_FOLDER}/{PLAYLIST_NAME}.json")
    data: Mapping[str, object] = _as_object(where, document, "a JSON object")
    _refuse_unknown_fields(where, data, _PLAYLIST_FIELDS)
    wave_zero: str = _checked(where, data, "wave_zero", _is_string, "a string")
    levels: object = data.get("levels")
    if not _is_list(levels) or len(levels) != LEVEL_COUNT:
        raise where.error_field("levels", f"must be a list of exactly {LEVEL_COUNT} levels")
    return wave_zero, tuple(
        _read_level(where.file, index, level) for index, level in enumerate(levels)
    )


def _read_level(file: str, index: int, level: object) -> LevelPlaylist:
    """Check one level of the playlist and return its LevelPlaylist."""
    where: _Where = _Where(file, f"levels[{index}]")
    data: Mapping[str, object] = _as_object(where, level, "an object")
    _refuse_unknown_fields(where, data, _LEVEL_FIELDS)
    fixed: list[object] = _checked(where, data, "fixed", _is_list, "a list")
    for position, wave_id in enumerate(fixed):
        if not _is_string(wave_id):
            raise where.error_field(f"fixed[{position}]", "must be a string")
    random_count: int = _checked(
        where, data, "random_count", _is_non_negative_integer, "an integer >= 0"
    )
    return LevelPlaylist(fixed=tuple(str(wave_id) for wave_id in fixed), random_count=random_count)


def _check_named_waves(
    waves: Mapping[str, Wave], wave_zero: str, playlists: tuple[LevelPlaylist, ...]
) -> None:
    """Raise unless `wave_zero` and every fixed entry name a wave."""
    root: _Where = _Where(f"{WAVES_FOLDER}/{PLAYLIST_NAME}.json")
    if wave_zero not in waves:
        raise root.error_field("wave_zero", f"names '{wave_zero}', which is not a wave")
    for index, playlist in enumerate(playlists):
        where: _Where = _Where(root.file, f"levels[{index}]")
        for position, wave_id in enumerate(playlist.fixed):
            if wave_id not in waves:
                problem: str = f"names '{wave_id}', which is not a wave"
                raise where.error_field(f"fixed[{position}]", problem)


def _check_pools(book: WaveBook) -> None:
    """Raise unless every random slot can be filled and a pool wave can play at Level 8."""
    for level in range(FIRST_LEVEL, LEVEL_COUNT + 1):
        random_count: int = book.playlists[level - 1].random_count
        if random_count > 0 and not book.pool_ids(level):
            raise _Where(f"{WAVES_FOLDER}/{PLAYLIST_NAME}.json").error(
                f"levels[{level - 1}] (level {level}) has random_count {random_count} "
                f"but no pool wave with min_level <= {level}"
            )
    if not book.pool_ids(LEVEL_COUNT):
        raise _Where(WAVES_FOLDER).error(f"no pool wave can play at level {LEVEL_COUNT}")
