"""The wave files' load check: `build_wave_book` accepts a good set and refuses every bad one.

Contract: docs/contracts/systems/waves.md, Interface (`game/core/wave_files.py`, the shapes
`game/core/waves.py` builds), Rules (The wave files, Logging); docs/contracts/schemas/
wave.schema.json and playlist.schema.json; systems/drifters.md, Interface (`placement_seed`,
`MAX_SEED`) and Rules (Spawner, Placement seed; UFO, Born). Tasks: docs/contracts/DRA-76/tasks/
DRA-76-08-qa-engineer.md and docs/contracts/DRA-104/tasks/DRA-104-06-qa-engineer.md (the seed, the
UFO). One test per behavior they list. The good set is the test-only JSON in `wave_files/`, read
here with `json`; each refusal is that set with the edits of one row made. A UFO goes in by an
edit that sets a wave's whole `placements` list (`with_placements`), so the good set stays as it is.
The tuning records are built here from the GDD values below, never read from game/tuning/ or
game/waves/, and no expected number is imported from the code under test.
"""

import copy
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import pytest

from core.collision import Box, Circle
from core.drifters.base import DrifterType
from core.drifters.coin import Coin, CoinTypeExtra, CoinVariantExtra
from core.drifters.meteorite import Meteorite
from core.drifters.satellite import Satellite, SatelliteVariantExtra
from core.drifters.spawner import Placement, placement_seed
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.drifters.ufo import Ufo, UfoTypeExtra
from core.wave_files import build_wave_book
from core.waves import LevelPlaylist, WaveBook, WaveKind, WavePlacement

type Json = Any

FOLDER: Final[Path] = Path(__file__).parent / "wave_files"
"""The test-only wave files and playlist, to the two schemas. Never read by the game."""

LEVELS: Final[int] = 8
"""Source: 08-difficulty.md, level table (locked)."""

SEAM_CLEAR: Final[float] = 120.0
"""px of scroll. Source: 09-waves.md, seam_clear (locked)."""

LOGGER: Final[str] = "core.wave_files"
"""Logger name. Source: waves.md, Rules, Logging."""

SPEED_RATIO: Final[float] = 0.75
WARNING_TICKS: Final[int] = 30
"""Fixed test values, not the live tuning file. The load check never reads either."""

CRYSTAL_W: Final[int] = 12
CRYSTAL_H: Final[int] = 20
BODY_H: Final[int] = 10
RING_W: Final[int] = 22
RING_H: Final[int] = 8
"""px. Source: drifters/04-coin.md, Values (guess)."""

DISC_W: Final[float] = 40.0
DISC_H: Final[float] = 10.0
DOME_R: Final[float] = 9.0
UFO_SPEED_RATIO: Final[float] = 0.3
BAND_TOP: Final[float] = 188.0
BAND_BOTTOM: Final[float] = 440.0
"""px. Source: drifters/07-ufo.md, size, hitbox, speed_ratio and band (guess)."""

MAX_SEED_VALUE: Final[int] = 4_294_967_295
"""A seed's largest value, 2^32 - 1. Source: waves.md, Rules, The wave files (Placement)."""

POINTS: Final[dict[str, int]] = {"common": 50, "rare": 100}
"""Source: 06-scoring.md, coin_points (common 50 locked, rare 100 guess)."""

SIZES: Final[dict[str, tuple[float, float]]] = {
    "small": (20, 10),
    "medium": (28, 14),
    "big": (40, 20),
}
"""Meteorite variant to (width, hitbox radius), px. Source: drifters/01-meteorite.md (guess)."""


def make_tuning() -> DrifterTuning:
    """Build the meteorite, satellite, coin and UFO tuning from the GDD values above."""
    coin_extra: CoinTypeExtra = CoinTypeExtra(
        body_height=BODY_H,
        ring_width=RING_W,
        ring_height=RING_H,
        glint_size=2,
        glint_left=3,
        glint_top=3,
        popup_ticks=60,
        popup_rise_per_tick=0.5,
    )
    ufo_extra: UfoTypeExtra = UfoTypeExtra(
        weave_change_ticks_min=60,
        weave_change_ticks_max=96,
        weave_step_min=40.0,
        weave_step_max=120.0,
        weave_speed_max=1.6,
        weave_turn=0.1,
        band_top=BAND_TOP,
        band_bottom=BAND_BOTTOM,
    )
    # Importing the four classes registers them with the spawner; their types key the tuning.
    return DrifterTuning(
        drifters={
            Meteorite.drifter_type: DrifterTypeTuning(
                variants={
                    name: VariantTuning(width=width, height=width, hitbox=(Circle(0, 0, radius),))
                    for name, (width, radius) in SIZES.items()
                },
                default_variant="medium",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
            Satellite.drifter_type: DrifterTypeTuning(
                variants={
                    "flat": VariantTuning(
                        width=60,
                        height=20,
                        hitbox=(Box(0, 0, 40, 12),),
                        extra=SatelliteVariantExtra(angle_degrees=0.0),
                    )
                },
                default_variant="flat",
                speed_ratio=SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
            ),
            Coin.drifter_type: DrifterTypeTuning(
                variants={
                    name: VariantTuning(
                        width=CRYSTAL_W,
                        height=CRYSTAL_H,
                        hitbox=(Box(0.0, 0.0, float(CRYSTAL_W), float(BODY_H)),),
                        extra=CoinVariantExtra(points=points, glint=name == "rare"),
                    )
                    for name, points in POINTS.items()
                },
                default_variant="common",
                speed_ratio=0.0,
                entry_warning_ticks=0,
                extra=coin_extra,
            ),
            Ufo.drifter_type: DrifterTypeTuning(
                variants={
                    "standard": VariantTuning(
                        width=DISC_W,
                        height=DISC_H,
                        hitbox=(Box(0.0, 0.0, DISC_W, DISC_H), Circle(0.0, -DISC_H / 2, DOME_R)),
                        extra=None,
                    )
                },
                default_variant="standard",
                speed_ratio=UFO_SPEED_RATIO,
                entry_warning_ticks=WARNING_TICKS,
                extra=ufo_extra,
            ),
        },
        switches=PlaytestSwitches(),
    )


TUNING: Final[DrifterTuning] = make_tuning()


class _Removed:
    """Marks an edit that takes a field, or a whole file, out."""


REMOVE: Final[_Removed] = _Removed()


@dataclass(frozen=True)
class Edit:
    """One change to the good set: set (or remove) the value at `path` inside one document.

    `target` is a wave id or "playlist". An empty `path` sets or removes the whole document.
    """

    target: str
    path: tuple[str | int, ...]
    value: object


@dataclass(frozen=True)
class Refusal:
    """One bad set: the edits, the start of the error, and a word the message must hold."""

    name: str
    edits: tuple[Edit, ...]
    prefix: str
    needle: str = ""
    spawn: bool = False


def good_set() -> tuple[dict[str, Json], Json]:
    """Read the good set: every wave file by id, and the playlist."""
    waves: dict[str, Json] = {}
    playlist: Json = None
    for path in sorted(FOLDER.glob("*.json")):
        document: Json = json.loads(path.read_text(encoding="utf-8"))
        if path.stem == "playlist":
            playlist = document
        else:
            waves[path.stem] = document
    assert playlist is not None
    return waves, playlist


def edited(*edits: Edit) -> tuple[dict[str, Json], Json]:
    """Return the good set with `edits` applied, in order."""
    waves, playlist = good_set()
    for edit in edits:
        if not edit.path:
            if edit.target == "playlist":
                playlist = copy.deepcopy(edit.value)
            elif isinstance(edit.value, _Removed):
                del waves[edit.target]
            else:
                waves[edit.target] = copy.deepcopy(edit.value)
            continue
        node: Json = playlist if edit.target == "playlist" else waves[edit.target]
        for key in edit.path[:-1]:
            node = node[key]
        if isinstance(edit.value, _Removed):
            del node[edit.path[-1]]
        else:
            node[edit.path[-1]] = copy.deepcopy(edit.value)
    return waves, playlist


def build(*edits: Edit) -> WaveBook:
    """Build the book from the good set with `edits` applied."""
    waves, playlist = edited(*edits)
    return build_wave_book(waves, playlist, TUNING)


def label(value: object) -> str:
    """A short name for a bad value in a test id."""
    return "missing" if isinstance(value, _Removed) else repr(value)


def field_rows(
    target: str, path: tuple[str | int, ...], prefix: str, values: tuple[object, ...]
) -> list[Refusal]:
    """One refusal per bad value of one field. The error must start with `prefix`."""
    where: str = ".".join(str(step) for step in path)
    return [
        Refusal(f"{target}.{where}={label(value)}", (Edit(target, path, value),), prefix)
        for value in values
    ]


def wave_field(wave_id: str, field: str, values: tuple[object, ...]) -> list[Refusal]:
    """Refusals for a wave file's own field."""
    return field_rows(wave_id, (field,), f"waves/{wave_id}.json: {field}", values)


def placement_field(
    wave_id: str, index: int, field: str, values: tuple[object, ...]
) -> list[Refusal]:
    """Refusals for one field of one placement."""
    prefix: str = f"waves/{wave_id}.json: placements[{index}].{field}"
    return field_rows(wave_id, ("placements", index, field), prefix, values)


def level_field(index: int, field: str, values: tuple[object, ...]) -> list[Refusal]:
    """Refusals for one field of one playlist level."""
    prefix: str = f"waves/playlist.json: levels[{index}].{field}"
    return field_rows("playlist", ("levels", index, field), prefix, values)


def ufo_row(at_px: float = 200, y: float | None = 300, **fields: object) -> dict[str, Json]:
    """One UFO placement of a wave file. `y` None leaves it out; `fields` adds `seed` and so on."""
    row: dict[str, Json] = {"at_px": at_px, "type": "ufo"}
    if y is not None:
        row["y"] = y
    row.update(fields)
    return row


def rock_row(at_px: float = 500) -> dict[str, Json]:
    """One meteorite placement, a hazard that carries no seed."""
    return {"at_px": at_px, "type": "meteorite", "x": 200}


def with_placements(*rows: dict[str, Json], wave_id: str = "l1_a") -> Edit:
    """The edit that sets a wave's whole placement list, in the order given (the file's order)."""
    return Edit(wave_id, ("placements",), list(rows))


def ufos_in(book: WaveBook, wave_id: str = "l1_a") -> list[WavePlacement]:
    """The wave's UFO placements, in the book's order (sorted by trigger)."""
    return [
        p for p in book.waves[wave_id].placements if p.placement.drifter_type is DrifterType.UFO
    ]


NOT_A_NUMBER: Final[tuple[object, ...]] = ("10", True, False, None, [], {})
NOT_AN_INTEGER: Final[tuple[object, ...]] = (1.5, "2", True, None, [])
NOT_A_STRING: Final[tuple[object, ...]] = (5, None, True, [])
NOT_A_BOOLEAN: Final[tuple[object, ...]] = ("yes", 1, 0, None)
NOT_A_NAME: Final[tuple[object, ...]] = (5, "", "Big", "bad-name", "1x", True)
NOT_AN_OBJECT: Final[tuple[object, ...]] = ([], "text", 5, None)
BAD_SEEDS: Final[tuple[object, ...]] = (
    -1,
    MAX_SEED_VALUE + 1,
    2**64,
    1.5,
    -0.5,
    True,
    False,
    "5",
    None,
    [],
    {},
)
NO_LEVELS: Final[tuple[object, ...]] = (
    REMOVE,
    {},
    "text",
    None,
    [],
    [{"fixed": [], "random_count": 0}] * 7,
)

REFUSALS: Final[list[Refusal]] = [
    # A bad wave id. The wave with this key is a copy of a good one, so only the key is wrong.
    *[
        Refusal(
            f"wave id {key!r}",
            (Edit(key, (), good_set()[0]["l1_b"]),),
            f"waves/{key}.json: the file name must match ^[a-z][a-z0-9_]*$",
        )
        for key in ("Bad_Id", "1abc", "has-dash", "", "_x", "L1")
    ],
    # A wave or a placement that isn't an object.
    *[
        Refusal(
            f"wave l1_b is {label(value)}",
            (Edit("l1_b", (), value),),
            "waves/l1_b.json: ",
            needle="object",
        )
        for value in (*NOT_AN_OBJECT, [{"length_px": 1}])
    ],
    *[
        Refusal(
            f"placement 1 of wave_0 is {label(value)}",
            (Edit("wave_0", ("placements", 1), value),),
            "waves/wave_0.json: placements[1]",
            needle="object",
        )
        for value in NOT_AN_OBJECT
    ],
    # An unknown field, speed on a placement included.
    Refusal(
        "wave field speed",
        (Edit("l1_a", ("speed",), 3.0),),
        "waves/l1_a.json: unknown field 'speed'",
    ),
    Refusal(
        "wave field id", (Edit("l1_a", ("id",), "l1_a"),), "waves/l1_a.json: unknown field 'id'"
    ),
    Refusal(
        "placement field speed",
        (Edit("l1_a", ("placements", 0, "speed"), 3.0),),
        "waves/l1_a.json: placements[0]: unknown field 'speed'",
    ),
    Refusal(
        "placement field on coin",
        (Edit("wave_0", ("placements", 1, "size"), 4),),
        "waves/wave_0.json: placements[1]: unknown field 'size'",
    ),
    Refusal(
        "playlist field",
        (Edit("playlist", ("name",), "x"),),
        "waves/playlist.json: unknown field 'name'",
    ),
    Refusal(
        "level field",
        (Edit("playlist", ("levels", 2, "name"), "x"),),
        "waves/playlist.json: levels[2]",
        needle="unknown field 'name'",
    ),
    # Each required wave field missing, and each type or range broken.
    *wave_field("l1_a", "length_px", (REMOVE,)),
    *[
        Refusal(
            f"l1_a.length_px={label(value)}",
            (Edit("l1_a", ("length_px",), value),),
            "waves/l1_a.json: length_px must be a number > 0",
        )
        for value in (0, 0.0, -1, -0.5, *NOT_A_NUMBER)
    ],
    *wave_field("l1_a", "kind", (REMOVE, "other", "Fixed", "", 1, None, True, [])),
    *wave_field("l1_a", "placements", (REMOVE, {}, "text", 5, None)),
    # min_level: missing on a pool wave, present on a fixed one, and broken.
    Refusal(
        "pool without min_level",
        (Edit("l1_b", ("min_level",), REMOVE),),
        "waves/l1_b.json: min_level is required for a pool wave",
    ),
    Refusal(
        "fixed with min_level",
        (Edit("l1_a", ("min_level",), 1),),
        "waves/l1_a.json: min_level is only for a pool wave",
    ),
    Refusal(
        "fixed with min_level null",
        (Edit("l1_a", ("min_level",), None),),
        "waves/l1_a.json: min_level is only for a pool wave",
    ),
    *wave_field("l1_b", "min_level", (0, -1, 9, 100, *NOT_AN_INTEGER)),
    *wave_field("l1_a", "extra_rest_ticks", (-1, *NOT_AN_INTEGER)),
    # Each required placement field missing, and each type or range broken.
    *placement_field("wave_0", 2, "at_px", (REMOVE,)),
    *[
        Refusal(
            f"wave_0.placements.2.at_px={label(value)}",
            (Edit("wave_0", ("placements", 2, "at_px"), value),),
            "waves/wave_0.json: placements[2].at_px must be a number >= 0",
        )
        for value in (-1, -0.001, *NOT_A_NUMBER)
    ],
    *placement_field("wave_0", 2, "type", (REMOVE, 5, None, True, [])),
    *[
        Refusal(
            f"placement type {value!r}",
            (Edit("wave_0", ("placements", 2, "type"), value),),
            f"waves/wave_0.json: placements[2].type '{value}' is not a drifter type "
            "(meteorite, satellite, chain_lightning, fireball, coin, floating_island, planet, ufo)",
        )
        for value in ("comet", "Meteorite", "UFO", "")
    ],
    *placement_field("wave_0", 2, "x", ("5", True, False, None, [])),
    *placement_field("l1_a", 0, "y", ("5", True, False, None, [])),
    *placement_field("wave_0", 2, "variant", NOT_A_NAME),
    *placement_field("wave_0", 2, "invert", NOT_A_BOOLEAN),
    *placement_field("wave_0", 2, "specialty", NOT_A_BOOLEAN),
    *placement_field("wave_0", 2, "as_level", (0, -1, 9, 100, *NOT_AN_INTEGER)),
    # What the load-time spawn refuses, named by the placement and keeping the cause.
    Refusal(
        "unknown variant",
        (Edit("l1_a", ("placements", 1, "variant"), "huge"),),
        "waves/l1_a.json: placements[1]: unknown variant 'huge' for drifter type 'meteorite'",
        spawn=True,
    ),
    Refusal(
        "unknown variant on the coin",
        (Edit("wave_0", ("placements", 1, "variant"), "huge"),),
        "waves/wave_0.json: placements[1]: unknown variant 'huge' for drifter type 'coin'",
        spawn=True,
    ),
    Refusal(
        "meteorite without x",
        (Edit("wave_0", ("placements", 3, "x"), REMOVE),),
        "waves/wave_0.json: placements[3]: meteorite placement needs x",
        spawn=True,
    ),
    Refusal(
        "satellite without y",
        (Edit("l1_a", ("placements", 0, "y"), REMOVE),),
        "waves/l1_a.json: placements[0]: satellite placement needs y",
        spawn=True,
    ),
    Refusal(
        "invert on a meteorite",
        (Edit("wave_0", ("placements", 2, "invert"), True),),
        "waves/wave_0.json: placements[2]: meteorite has no invert",
        spawn=True,
    ),
    Refusal(
        "invert on a coin",
        (Edit("wave_0", ("placements", 1, "invert"), True),),
        "waves/wave_0.json: placements[1]: coin has no invert",
        spawn=True,
    ),
    Refusal(
        "specialty on a meteorite",
        (Edit("wave_0", ("placements", 2, "specialty"), True),),
        "waves/wave_0.json: placements[2]: meteorite has no specialty",
        spawn=True,
    ),
    Refusal(
        "specialty on a satellite",
        (Edit("l1_a", ("placements", 0, "specialty"), True),),
        "waves/l1_a.json: placements[0]: satellite has no specialty",
        spawn=True,
    ),
    Refusal(
        "specialty on a coin",
        (Edit("wave_0", ("placements", 1, "specialty"), True),),
        "waves/wave_0.json: placements[1]: coin has no specialty",
        spawn=True,
    ),
    # The seed field: an integer from 0 to MAX_SEED, on any placement (the range is checked first).
    *[
        Refusal(
            f"placement seed={label(value)}",
            (Edit("wave_0", ("placements", 2, "seed"), value),),
            "waves/wave_0.json: placements[2].seed must be an integer from 0 to 4294967295",
        )
        for value in BAD_SEEDS
    ],
    # What the load-time spawn refuses about a seed or a UFO, named by the placement.
    *[
        Refusal(
            f"seed on {name}",
            (Edit(wave_id, ("placements", index, "seed"), 5),),
            f"waves/{wave_id}.json: placements[{index}]: {name} has no seed",
            spawn=True,
        )
        for name, wave_id, index in (("meteorite", "wave_0", 2), ("coin", "wave_0", 1))
    ],
    Refusal(
        "seed on a satellite",
        (Edit("l1_a", ("placements", 0, "seed"), 0),),
        "waves/l1_a.json: placements[0]: satellite has no seed",
        spawn=True,
    ),
    *[
        Refusal(
            f"ufo at y {y:g}",
            (with_placements(rock_row(), ufo_row(y=y)),),
            f"waves/l1_a.json: placements[1]: ufo placement y {y:g} is outside its band 188 to 440",
            spawn=True,
        )
        for y in (0, 100, 187.5, 187.99, 440.01, 440.5, 480)
    ],
    # Two UFOs in one wave never share a seed, given or default. The later one, by the file's
    # order and not the trigger's, is named with the earlier.
    Refusal(
        "two ufos with the same given seed",
        (
            with_placements(
                ufo_row(at_px=500, seed=7), rock_row(), ufo_row(at_px=200, seed=8), ufo_row(seed=7)
            ),
        ),
        "waves/l1_a.json: placements[3]: seed 7 is already used by placements[0]",
    ),
    Refusal(
        "the later ufo is the one in the file after the first, whatever its trigger",
        (with_placements(ufo_row(at_px=500, seed=7), ufo_row(at_px=130, seed=7)),),
        "waves/l1_a.json: placements[1]: seed 7 is already used by placements[0]",
    ),
    Refusal(
        "three ufos with one seed name the first",
        (with_placements(ufo_row(seed=0), ufo_row(seed=1), ufo_row(seed=0), ufo_row(seed=0)),),
        "waves/l1_a.json: placements[2]: seed 0 is already used by placements[0]",
    ),
    Refusal(
        "a given seed equal to an earlier default seed",
        (with_placements(ufo_row(), ufo_row(seed=placement_seed("l1_a", 0))),),
        f"waves/l1_a.json: placements[1]: seed {placement_seed('l1_a', 0)} is already used by "
        "placements[0]",
    ),
    Refusal(
        "a default seed equal to an earlier given seed",
        (with_placements(rock_row(), ufo_row(seed=placement_seed("l1_a", 2)), ufo_row()),),
        f"waves/l1_a.json: placements[2]: seed {placement_seed('l1_a', 2)} is already used by "
        "placements[1]",
    ),
    # The playlist: shape, and the number of levels.
    *[
        Refusal(
            f"playlist is {label(value)}",
            (Edit("playlist", (), value),),
            "waves/playlist.json: ",
            needle="object",
        )
        for value in NOT_AN_OBJECT
    ],
    *field_rows(
        "playlist", ("wave_zero",), "waves/playlist.json: wave_zero", (REMOVE, *NOT_A_STRING)
    ),
    *[
        Refusal(
            f"playlist levels={label(value)}",
            (Edit("playlist", ("levels",), value),),
            "waves/playlist.json: levels must be a list of exactly 8 levels",
        )
        for value in NO_LEVELS
    ],
    Refusal(
        "playlist with 9 levels",
        (Edit("playlist", ("levels",), [{"fixed": [], "random_count": 0}] * 9),),
        "waves/playlist.json: levels must be a list of exactly 8 levels",
    ),
    Refusal(
        "playlist with 7 levels",
        (Edit("playlist", ("levels", 7), REMOVE),),
        "waves/playlist.json: levels must be a list of exactly 8 levels",
    ),
    *[
        Refusal(
            f"level 2 is {label(value)}",
            (Edit("playlist", ("levels", 1), value),),
            "waves/playlist.json: levels[1]",
            needle="object",
        )
        for value in NOT_AN_OBJECT
    ],
    *level_field(2, "fixed", (REMOVE, {}, "l1_a", 5, None)),
    *[
        Refusal(
            f"level fixed entry {label(value)}",
            (Edit("playlist", ("levels", 0, "fixed", 0), value),),
            "waves/playlist.json: levels[0].fixed[0]",
        )
        for value in NOT_A_STRING
    ],
    *[
        Refusal(
            f"levels.2.random_count={label(value)}",
            (Edit("playlist", ("levels", 2, "random_count"), value),),
            "waves/playlist.json: levels[2].random_count must be an integer >= 0",
        )
        for value in (REMOVE, -1, *NOT_AN_INTEGER)
    ],
    # A named wave that is not there.
    Refusal(
        "wave_zero names no wave",
        (Edit("playlist", ("wave_zero",), "wave_00"),),
        "waves/playlist.json: wave_zero names 'wave_00', which is not a wave",
    ),
    Refusal(
        "fixed entry names no wave",
        (Edit("playlist", ("levels", 0, "fixed"), ["l1_a", "l1_c"]),),
        "waves/playlist.json: levels[0].fixed[1] names 'l1_c', which is not a wave",
    ),
    Refusal(
        "fixed entry names the playlist",
        (Edit("playlist", ("levels", 4, "fixed"), ["playlist"]),),
        "waves/playlist.json: levels[4].fixed[0] names 'playlist', which is not a wave",
    ),
    # A level with random slots and no pool wave allowed at it.
    Refusal(
        "no pool wave at level 1",
        (Edit("l1_b", ("min_level",), 3),),
        "waves/playlist.json: levels[0] (level 1) has random_count 1 "
        "but no pool wave with min_level <= 1",
    ),
    Refusal(
        "no pool wave at level 2",
        (Edit("l1_b", ("min_level",), 3), Edit("playlist", ("levels", 0, "random_count"), 0)),
        "waves/playlist.json: levels[1] (level 2) has random_count 2 "
        "but no pool wave with min_level <= 2",
    ),
    # No pool wave at Level 8, whatever the playlists say.
    Refusal(
        "no pool wave at level 8",
        (
            Edit("l1_b", (), REMOVE),
            Edit("l3_pool", (), REMOVE),
            Edit("l8_pool", (), REMOVE),
            *[Edit("playlist", ("levels", n, "random_count"), 0) for n in range(LEVELS)],
        ),
        "waves: no pool wave can play at level 8",
    ),
]


@pytest.mark.parametrize("refusal", REFUSALS, ids=[refusal.name for refusal in REFUSALS])
def test_a_bad_set_raises_value_error_naming_the_file_and_the_problem(refusal: Refusal) -> None:
    with pytest.raises(ValueError, match=r"^waves") as raised:
        build(*refusal.edits)
    message: str = str(raised.value)
    assert message.startswith(refusal.prefix), message
    assert refusal.needle in message, message
    if refusal.spawn:
        assert isinstance(raised.value.__cause__, ValueError)


def test_the_good_set_builds_a_book() -> None:
    book: WaveBook = build()
    # Ids come from the keys, in id order.
    assert list(book.waves) == ["l1_a", "l1_b", "l3_pool", "l8_pool", "wave_0"]
    for wave_id, wave in book.waves.items():
        assert wave.wave_id == wave_id
    assert book.wave_zero_id == "wave_0"
    # Eight playlists, Level 1 first, each fixed list a tuple.
    assert book.playlists == (
        LevelPlaylist(fixed=("l1_a",), random_count=1),
        LevelPlaylist(fixed=(), random_count=2),
        LevelPlaylist(fixed=("l1_a", "l1_a"), random_count=0),
        LevelPlaylist(fixed=("l1_a",), random_count=1),
        LevelPlaylist(fixed=(), random_count=1),
        LevelPlaylist(fixed=("l1_a",), random_count=2),
        LevelPlaylist(fixed=("l1_a",), random_count=0),
        LevelPlaylist(fixed=("l1_a",), random_count=1),
    )
    assert len(book.playlists) == LEVELS
    # Lengths and triggers are floats, written as integers or not in the files.
    for wave in book.waves.values():
        assert type(wave.length_px) is float
        for wave_placement in wave.placements:
            assert type(wave_placement.at_px) is float
            assert wave_placement.placement.speed is None
    assert [wave.length_px for wave in book.waves.values()] == [
        900.5,
        800.0,
        1000.0,
        2000.25,
        1320.0,
    ]
    # Kind and min_level: a pool wave has one, a fixed wave has None.
    assert [(wave.kind, wave.min_level) for wave in book.waves.values()] == [
        (WaveKind.FIXED, None),
        (WaveKind.POOL, 1),
        (WaveKind.POOL, 3),
        (WaveKind.POOL, 8),
        (WaveKind.FIXED, None),
    ]
    # The extra rest is 0 when the file leaves it out, and as written when it doesn't.
    assert [wave.extra_rest_ticks for wave in book.waves.values()] == [30, 0, 0, 12, 0]
    assert all(type(wave.extra_rest_ticks) is int for wave in book.waves.values())
    # Placements sorted by trigger, a tie kept in file order (x 20 before x 10 at 300 px).
    assert book.waves["wave_0"].placements == (
        WavePlacement(at_px=0.0, placement=Placement(DrifterType.COIN, x=320, variant="rare")),
        WavePlacement(at_px=150.5, placement=Placement(DrifterType.METEORITE, x=30)),
        WavePlacement(
            at_px=300.0, placement=Placement(DrifterType.METEORITE, x=20, variant="small")
        ),
        WavePlacement(at_px=300.0, placement=Placement(DrifterType.METEORITE, x=10)),
        WavePlacement(at_px=600.0, placement=Placement(DrifterType.METEORITE, x=100)),
    )
    assert book.waves["l1_a"].placements == (
        WavePlacement(at_px=50.0, placement=Placement(DrifterType.COIN, x=100, y=60)),
        WavePlacement(
            at_px=120.0,
            placement=Placement(DrifterType.SATELLITE, y=200, variant="flat", invert=True),
        ),
        WavePlacement(
            at_px=400.0,
            placement=Placement(
                DrifterType.METEORITE, x=500, variant="big", as_level=3, specialty_enabled=False
            ),
        ),
    )
    assert book.waves["l1_b"].placements == ()
    # The slots: the fixed ids, then None for each random slot.
    assert [book.level_slots(level) for level in range(1, LEVELS + 1)] == [
        ("l1_a", None),
        (None, None),
        ("l1_a", "l1_a"),
        ("l1_a", None),
        (None,),
        ("l1_a", None, None),
        ("l1_a",),
        ("l1_a", None),
    ]
    # The pool ids per level: min_level 1, 3 and 8, sorted by id.
    pools: list[tuple[str, ...]] = [book.pool_ids(level) for level in range(1, LEVELS + 1)]
    assert pools == [
        ("l1_b",),
        ("l1_b",),
        ("l1_b", "l3_pool"),
        ("l1_b", "l3_pool"),
        ("l1_b", "l3_pool"),
        ("l1_b", "l3_pool"),
        ("l1_b", "l3_pool"),
        ("l1_b", "l3_pool", "l8_pool"),
    ]


@pytest.mark.parametrize(
    ("wave_id", "index", "drifter_name"),
    [("wave_0", 0, "meteorite"), ("l1_a", 0, "satellite")],
    ids=["meteorite", "satellite"],
)
def test_a_hazard_below_120_px_is_refused_and_one_at_120_px_is_accepted(
    wave_id: str, index: int, drifter_name: str
) -> None:
    path: tuple[str | int, ...] = ("placements", index, "at_px")
    for at_px in (0, 0.0, 50, 100, 119.5, 119.99):
        with pytest.raises(ValueError, match=r"^waves") as raised:
            build(Edit(wave_id, path, at_px))
        assert str(raised.value) == (
            f"waves/{wave_id}.json: placements[{index}]: a hazard ({drifter_name}) at {at_px:g} px "
            f"is inside the first 120 px"
        )
    for at_px in (120, 120.0, 120.5, 600):
        book: WaveBook = build(Edit(wave_id, path, at_px))
        triggers: list[float] = [p.at_px for p in book.waves[wave_id].placements]
        assert float(at_px) in triggers
    assert SEAM_CLEAR == 120.0


@pytest.mark.parametrize("at_px", [0, 0.0, 1, 50.5, 119.99, 120, 3000], ids=repr)
def test_a_coin_triggers_anywhere_even_below_120_px(at_px: float) -> None:
    for wave_id, index in (("wave_0", 1), ("l1_a", 2)):
        book: WaveBook = build(Edit(wave_id, ("placements", index, "at_px"), at_px))
        wave_placements: tuple[WavePlacement, ...] = book.waves[wave_id].placements
        coins: list[WavePlacement] = [
            p for p in wave_placements if p.placement.drifter_type is DrifterType.COIN
        ]
        assert [p.at_px for p in coins] == [float(at_px)]


def test_the_unknown_type_message_lists_every_type_in_enum_order_ending_planet_ufo() -> None:
    with pytest.raises(ValueError, match=r"^waves") as raised:
        build(Edit("wave_0", ("placements", 2, "type"), "comet"))
    assert str(raised.value) == (
        "waves/wave_0.json: placements[2].type 'comet' is not a drifter type "
        "(meteorite, satellite, chain_lightning, fireball, coin, floating_island, planet, ufo)"
    )
    assert str(raised.value).endswith("planet, ufo)")
    # `ufo` is a type now: it is no longer refused as one.
    book: WaveBook = build(with_placements(ufo_row()))
    assert [p.placement.drifter_type for p in ufos_in(book)] == [DrifterType.UFO]


@pytest.mark.parametrize("seed", [0, 1, 7, 2**31, MAX_SEED_VALUE - 1, MAX_SEED_VALUE], ids=repr)
def test_a_seed_from_0_to_max_seed_is_accepted_and_kept(seed: int) -> None:
    book: WaveBook = build(with_placements(ufo_row(seed=seed)))
    assert [p.placement.seed for p in ufos_in(book)] == [seed]
    assert type(ufos_in(book)[0].placement.seed) is int


def test_a_seed_below_0_above_max_seed_or_not_an_integer_is_refused_with_its_message() -> None:
    message: str = "waves/l1_a.json: placements[0].seed must be an integer from 0 to 4294967295"
    for seed in (-1, MAX_SEED_VALUE + 1, 1.5, True, False):
        with pytest.raises(ValueError, match=r"^waves") as raised:
            build(with_placements(ufo_row(seed=seed)))
        assert str(raised.value) == message, seed


def test_a_ufo_with_no_seed_gets_the_placement_seed_of_its_wave_and_file_index() -> None:
    # File order: a meteorite (0), a UFO at 400 (1), a UFO at 150 (2), a UFO at 300 with a seed (3),
    # a meteorite (4). Sorted by trigger the UFOs come as 2, 3, 1: the index is the file's.
    rows: tuple[dict[str, Json], ...] = (
        rock_row(500),
        ufo_row(at_px=400),
        ufo_row(at_px=150),
        ufo_row(at_px=300, seed=99),
        rock_row(250),
    )
    book: WaveBook = build(with_placements(*rows))
    found: list[WavePlacement] = ufos_in(book)
    assert [p.at_px for p in found] == [150.0, 300.0, 400.0]
    assert [p.placement.seed for p in found] == [
        placement_seed("l1_a", 2),
        99,
        placement_seed("l1_a", 1),
    ]
    # Every drifter that has no seed keeps None.
    others: list[WavePlacement] = [
        p for p in book.waves["l1_a"].placements if p.placement.drifter_type is not DrifterType.UFO
    ]
    assert len(others) == 2
    assert [p.placement.seed for p in others] == [None, None]
    # The wave id is part of the default: the same index in another wave is another seed.
    other: WaveBook = build(with_placements(*rows, wave_id="l1_b"))
    assert ufos_in(other, "l1_b")[0].placement.seed == placement_seed("l1_b", 2)
    assert placement_seed("l1_b", 2) != placement_seed("l1_a", 2)
    for found_seed in (p.placement.seed for p in found):
        assert found_seed is not None
        assert 0 <= found_seed <= MAX_SEED_VALUE


def test_the_good_set_keeps_every_seed_at_none() -> None:
    book: WaveBook = build()
    for wave in book.waves.values():
        for wave_placement in wave.placements:
            assert wave_placement.placement.seed is None


def test_a_seed_on_a_drifter_that_has_none_and_a_ufo_outside_its_band_are_refused() -> None:
    cases: tuple[tuple[Edit, str], ...] = (
        (
            Edit("wave_0", ("placements", 2, "seed"), 5),
            "waves/wave_0.json: placements[2]: meteorite has no seed",
        ),
        (
            Edit("l1_a", ("placements", 0, "seed"), 5),
            "waves/l1_a.json: placements[0]: satellite has no seed",
        ),
        (
            Edit("wave_0", ("placements", 1, "seed"), 5),
            "waves/wave_0.json: placements[1]: coin has no seed",
        ),
        (
            with_placements(rock_row(), rock_row(), ufo_row(y=100)),
            "waves/l1_a.json: placements[2]: ufo placement y 100 is outside its band 188 to 440",
        ),
    )
    for edit, message in cases:
        with pytest.raises(ValueError, match=r"^waves") as raised:
            build(edit)
        assert str(raised.value) == message
        assert isinstance(raised.value.__cause__, ValueError)
    # The band's two ends are inside it.
    for y in (BAND_TOP, BAND_BOTTOM, 300):
        book: WaveBook = build(with_placements(ufo_row(y=y)))
        assert len(ufos_in(book)) == 1


def test_one_seed_twice_in_a_wave_is_refused_and_in_two_waves_it_loads() -> None:
    # Given seeds: the later one in the file is named, with the earlier.
    with pytest.raises(ValueError, match=r"^waves") as raised:
        build(with_placements(ufo_row(at_px=500, seed=7), rock_row(), ufo_row(at_px=200, seed=7)))
    assert str(raised.value) == (
        "waves/l1_a.json: placements[2]: seed 7 is already used by placements[0]"
    )
    # A given seed that is another UFO's default seed.
    default: int = placement_seed("l1_a", 0)
    with pytest.raises(ValueError, match=r"^waves") as raised:
        build(with_placements(ufo_row(), ufo_row(seed=default)))
    assert str(raised.value) == (
        f"waves/l1_a.json: placements[1]: seed {default} is already used by placements[0]"
    )
    # Different seeds in one wave load, including a default next to a given one.
    book: WaveBook = build(with_placements(ufo_row(seed=7), ufo_row(), ufo_row(seed=8)))
    assert len({p.placement.seed for p in ufos_in(book)}) == 3
    # The same seed in two different waves loads, and each wave keeps it.
    both: WaveBook = build(
        with_placements(ufo_row(seed=7), wave_id="l1_a"),
        with_placements(ufo_row(seed=7), wave_id="l1_b"),
    )
    assert [p.placement.seed for p in ufos_in(both, "l1_a")] == [7]
    assert [p.placement.seed for p in ufos_in(both, "l1_b")] == [7]
    # A meteorite never counts: no placement but a UFO has a seed to share.
    mixed: WaveBook = build(with_placements(rock_row(), ufo_row(seed=7), rock_row(300)))
    assert [p.placement.seed for p in ufos_in(mixed)] == [7]


def test_a_ufo_below_120_px_is_refused_and_one_at_120_px_is_accepted() -> None:
    for at_px in (0, 0.0, 50, 100, 119.5, 119.99):
        with pytest.raises(ValueError, match=r"^waves") as raised:
            build(with_placements(rock_row(), ufo_row(at_px=at_px)))
        assert str(raised.value) == (
            f"waves/l1_a.json: placements[1]: a hazard (ufo) at {at_px:g} px is inside the first "
            f"120 px"
        )
    for at_px in (120, 120.0, 120.5, 600):
        book: WaveBook = build(with_placements(rock_row(), ufo_row(at_px=at_px)))
        assert [p.at_px for p in ufos_in(book)] == [float(at_px)]
    assert SEAM_CLEAR == 120.0


def test_what_is_not_checked_at_load_is_accepted() -> None:
    # A placement past the wave's length (a hazard at 5000 px in a 1320 px wave).
    past: WaveBook = build(Edit("wave_0", ("placements", 0, "at_px"), 5000))
    assert past.waves["wave_0"].length_px == 1320.0
    assert past.waves["wave_0"].placements[-1].at_px == 5000.0
    # A level with no slots.
    empty: WaveBook = build(Edit("playlist", ("levels", 6), {"fixed": [], "random_count": 0}))
    assert empty.level_slots(7) == ()
    assert empty.playlists[6] == LevelPlaylist(fixed=(), random_count=0)
    # A pool wave in a fixed list.
    pooled: WaveBook = build(Edit("playlist", ("levels", 0, "fixed"), ["l1_b"]))
    assert pooled.playlists[0].fixed == ("l1_b",)
    assert pooled.level_slots(1) == ("l1_b", None)
    # A hazard that is not a meteorite in Wave 0.
    hazard: WaveBook = build(
        Edit("wave_0", ("placements", 2, "type"), "satellite"),
        Edit("wave_0", ("placements", 2, "y"), 200),
        Edit("wave_0", ("placements", 2, "variant"), "flat"),
    )
    kinds: list[DrifterType] = [p.placement.drifter_type for p in hazard.waves["wave_0"].placements]
    assert DrifterType.SATELLITE in kinds


def test_build_wave_book_logs_nothing(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger=LOGGER)
    build()
    with pytest.raises(ValueError, match=r"^waves"):
        build(Edit("l1_a", ("length_px",), 0))
    assert [record for record in caplog.records if record.name.startswith(LOGGER)] == []
