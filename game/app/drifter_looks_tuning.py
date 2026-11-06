"""Load and check the drifter looks file, and set the sprites up for the views.

Reads `tuning/drifter_looks.json` once, at startup (`load_drifter_looks`), and builds a
DrifterLooks. Every field is required and no default lives in code. A missing file raises
FileNotFoundError; a bad one raises ValueError naming the file and the field.
`install_drifter_looks` then loads every strip and builds every image the game will draw, once
the display is open, so no spawn builds an image mid-run. Not a startup module: it imports ui, so
only app.frame (and the wave editor) import it, inside the guard.

Source: 12-art-and-audio.md, rules 3, 9, 10 and 13; 15-tech-constraints.md, rule 5.
"""

import dataclasses
import json
import logging
import time
import types
import typing
from collections.abc import Callable
from enum import Enum
from pathlib import Path

from app.drifters.checks import check_fields, check_integer
from app.tuning import TUNING_DIR
from core.drifters.tuning import DrifterTuning
from ui.drifters.looks import DrifterLooks
from ui.drifters.preload import warm_sprites
from ui.drifters.sprites import Sprites, install_sprites, sprites_folder

log = logging.getLogger(__name__)

LOOKS_FILE: str = "drifter_looks.json"

_ZERO_OK: frozenset[str] = frozenset({"fireball.art_head_center"})
"""Integer fields that may be 0, besides color channels. Every other integer must be 1 or more."""

_RGB_MAX: int = 255
"""The largest channel of a color."""


def load_drifter_looks() -> DrifterLooks:
    """Read and check the drifter looks file and build its records."""
    name: str = f"tuning/{LOOKS_FILE}"
    text: str = (TUNING_DIR / Path(LOOKS_FILE)).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{name}: not valid JSON: {err}") from err
    looks: DrifterLooks = _build(DrifterLooks, name, "", data)
    log.info(
        "drifter looks loaded strips=%d grounds=%d dim_steps=%d",
        len(looks.strips()),
        len(looks.floating_island.looks),
        looks.dim_steps,
    )
    return looks


def install_drifter_looks(tuning: DrifterTuning) -> Sprites:
    """Load the looks and every strip, build every image the game will draw, and install them.

    Call it once, after the display is open and the drifter tuning is loaded. A missing sprite
    file raises FileNotFoundError (from pygame); a strip whose size does not fit its rule raises
    ValueError naming the file.
    """
    started: float = time.perf_counter()
    looks: DrifterLooks = load_drifter_looks()
    sprites: Sprites = Sprites(looks, sprites_folder(), warm_levels=(_rehit_level(looks, tuning),))
    warm_sprites(sprites, tuning)
    install_sprites(sprites)
    log.info("drifter sprites ready in %.0f ms", (time.perf_counter() - started) * 1000)
    return sprites


def _rehit_level(looks: DrifterLooks, tuning: DrifterTuning) -> int:
    """Return the brightness level a drifter draws at during its re-hit cooldown."""
    return min(looks.dim_steps, max(0, round(tuning.hazards.rehit_dim * looks.dim_steps)))


def _build[T](cls: Callable[..., T], name: str, path: str, data: object) -> T:
    """Build the frozen record `cls` from the object `data`, converting each field by its type."""
    hints: dict[str, object] = typing.get_type_hints(cls)
    fields: dict[str, object] = check_fields(name, path, data, frozenset(hints))
    values: dict[str, object] = {}
    for key, hint in hints.items():
        where: str = f"{path}.{key}" if path else key
        values[key] = _convert(name, where, fields[key], hint)
    return cls(**values)


def _convert(name: str, path: str, value: object, hint: object) -> object:
    """Check `value` against the type `hint` and return it as the record field's type."""
    if isinstance(hint, types.GenericAlias):
        return _convert_generic(name, path, value, hint)
    if isinstance(hint, type) and issubclass(hint, Enum):
        return _convert_enum(name, path, value, hint)
    if dataclasses.is_dataclass(hint) and isinstance(hint, type):
        return _build(hint, name, path, value)
    if hint is str:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name}: {path} must be a non-empty string")
        return value
    if hint is int:
        return check_integer(name, path, value, _minimum(path))
    raise TypeError(f"{name}: {path}: no check for type {hint!r}")


def _minimum(path: str) -> int:
    """Return the least an integer at `path` may be: 0 for a color channel or a `_ZERO_OK` field.

    A tuple element's path ends in `[n]`; the field is the path before it.
    """
    field: str = path.split("[")[0]
    return 0 if field in _ZERO_OK or field.endswith("color") else 1


def _convert_enum(name: str, path: str, value: object, hint: type[Enum]) -> Enum:
    """Return the member of `hint` whose value is the text `value`, else raise."""
    for member in hint:
        if member.value == value:
            return member
    options: str = ", ".join(f"'{member.value}'" for member in hint)
    raise ValueError(f"{name}: {path} must be one of {options}")


def _convert_generic(name: str, path: str, value: object, hint: types.GenericAlias) -> object:
    """Check a tuple type: a list of records, strings, or a fixed list of ints (a color)."""
    origin: object = typing.get_origin(hint)
    args: tuple[object, ...] = typing.get_args(hint)
    if origin is not tuple:
        raise TypeError(f"{name}: {path}: no check for type {hint!r}")
    if args and args[-1] is Ellipsis:
        if not isinstance(value, list) or not value:
            raise ValueError(f"{name}: {path} must be a non-empty array")
        return tuple(
            _convert(name, f"{path}[{i}]", entry, args[0]) for i, entry in enumerate(value)
        )
    if not isinstance(value, list) or len(value) != len(args):
        raise ValueError(f"{name}: {path} must be an array of {len(args)} items")
    items: tuple[object, ...] = tuple(
        _convert(name, f"{path}[{i}]", entry, kind)
        for i, (entry, kind) in enumerate(zip(value, args, strict=True))
    )
    if path.endswith("color") and any(
        isinstance(channel, int) and channel > _RGB_MAX for channel in items
    ):
        raise ValueError(f"{name}: {path} channels must be 0 to {_RGB_MAX}")
    return items
