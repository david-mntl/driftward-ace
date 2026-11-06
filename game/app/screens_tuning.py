"""Load and check the screens values file.

Reads `tuning/screens.json` once, at startup (`load_screen_rules`). Checks every rule of
screens.schema.json by hand (pygbag has no schema library) and builds a ScreenRules. Every field is
required and no default lives in code. A missing file raises FileNotFoundError; a bad one raises
ValueError naming the file and the field. Not a startup module: it imports ui, so only app.frame
imports it, inside the guard.

Source: docs/contracts/schemas/screens.schema.json; docs/contracts/systems/screens.md, Interface;
10-ui.md, rule 12.
"""

import collections.abc
import dataclasses
import json
import logging
import re
import types
import typing
from collections.abc import Callable
from pathlib import Path

from app.drifters.checks import check_fields, check_integer, is_number
from app.tuning import TUNING_DIR
from ui.screen_rules import FONT_ROLES, PALETTE_KEYS, RGB, ScreenRules

log = logging.getLogger(__name__)

SCREENS_FILE: str = "screens.json"

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

_AT_LEAST_ONE_SUFFIXES: tuple[str, ...] = ("_size", "_w", "_h", "_pitch")
"""A whole number whose name ends like this must be 1 or more. Any other one is 0 or more."""

_AT_LEAST_ONE: frozenset[str] = frozenset(
    {"w", "h", "size", "glass.blur_down", "instructions.columns"}
)
"""Whole numbers that must be 1 or more whatever their name (a field's name or its full path)."""


def load_screen_rules() -> ScreenRules:
    """Read and check the screens values file and build its records."""
    name: str = f"tuning/{SCREENS_FILE}"
    text: str = (TUNING_DIR / Path(SCREENS_FILE)).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{name}: not valid JSON: {err}") from err
    rules: ScreenRules = _build(ScreenRules, name, "", data)
    _check_rules(name, rules)
    log.info(
        "screens loaded %d palette colors, %d font roles",
        len(rules.palette),
        len(rules.fonts.roles),
    )
    return rules


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
    """Check `value` against the type `hint` and return it, as the tuples and floats the records

    use.
    """
    if isinstance(hint, types.GenericAlias):
        return _convert_generic(name, path, value, hint)
    if isinstance(hint, typing.TypeAliasType):
        return _convert(name, path, value, hint.__value__)
    if dataclasses.is_dataclass(hint) and isinstance(hint, type):
        return _build(hint, name, path, value)
    if hint is bool:
        if not isinstance(value, bool):
            raise ValueError(f"{name}: {path} must be a boolean")
        return value
    if hint is str:
        if not isinstance(value, str):
            raise ValueError(f"{name}: {path} must be a string")
        return value
    if hint is int:
        return _check_int(name, path, value)
    if hint is float:
        return _check_float(name, path, value)
    raise TypeError(f"{name}: {path}: no check for type {hint!r}")


def _convert_generic(name: str, path: str, value: object, hint: types.GenericAlias) -> object:
    """Check the palette or a non-empty array of records."""
    origin: object = typing.get_origin(hint)
    args: tuple[object, ...] = typing.get_args(hint)
    if origin is collections.abc.Mapping:
        return _convert_palette(name, path, value)
    if origin is tuple and args and args[-1] is Ellipsis:
        if not isinstance(value, list) or not value:
            raise ValueError(f"{name}: {path} must be a non-empty array")
        return tuple(
            _convert(name, f"{path}[{i}]", entry, args[0]) for i, entry in enumerate(value)
        )
    raise TypeError(f"{name}: {path}: no check for type {hint!r}")


def _convert_palette(name: str, path: str, value: object) -> dict[str, RGB]:
    """Check an object of #rrggbb texts and return it as RGB tuples, key by key."""
    if not isinstance(value, dict):
        raise ValueError(f"{name}: {path} must be an object")
    colors: dict[str, RGB] = {}
    for key, text in value.items():
        if not isinstance(text, str) or not _HEX.match(text):
            raise ValueError(f"{name}: {path}.{key} must be a color like #rrggbb")
        colors[str(key)] = (int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16))
    return colors


def _check_int(name: str, path: str, value: object) -> int:
    """Return a whole number in the range its name says, else raise."""
    key: str = path.rsplit(".", 1)[-1]
    one: bool = (
        path in _AT_LEAST_ONE or key in _AT_LEAST_ONE or key.endswith(_AT_LEAST_ONE_SUFFIXES)
    )
    minimum: int = 1 if one else 0
    number: int = check_integer(name, path, value, minimum)
    if key.endswith("_alpha") and number > 255:
        raise ValueError(f"{name}: {path} must be an integer from 0 to 255")
    return number


def _check_float(name: str, path: str, value: object) -> float:
    """Return a number >= 0 (0 to 1 for a ``*_strength``), else raise."""
    if not is_number(value):
        raise ValueError(f"{name}: {path} must be a number")
    number: float = float(value)
    if path.endswith("_strength") and not 0.0 <= number <= 1.0:
        raise ValueError(f"{name}: {path} must be a number from 0 to 1")
    if number < 0.0:
        raise ValueError(f"{name}: {path} must be a number >= 0")
    return number


def _check_rules(name: str, rules: ScreenRules) -> None:
    """Check what a single field can't: the palette keys, the font roles and the layout that
    depends on other fields."""
    for key in PALETTE_KEYS:
        if key not in rules.palette:
            raise ValueError(f"{name}: palette.{key} is missing")
    for key in rules.palette:
        if key not in PALETTE_KEYS:
            raise ValueError(f"{name}: palette.{key} is not a known field")
    _check_roles(name, rules)
    if rules.rulers.major_pitch % rules.rulers.minor_pitch:
        raise ValueError(f"{name}: rulers.major_pitch must be a multiple of rulers.minor_pitch")
    over = rules.game_over
    if over.picker_w < over.w or over.picker_h < over.h:
        raise ValueError(f"{name}: game_over.picker_w and picker_h must be >= w and h")


def _check_roles(name: str, rules: ScreenRules) -> None:
    """Raise unless fonts.roles names every role in FONT_ROLES once and no other."""
    names: list[str] = [role.name for role in rules.fonts.roles]
    for index, role in enumerate(names):
        if role not in FONT_ROLES:
            raise ValueError(f"{name}: fonts.roles[{index}].name must be one of {FONT_ROLES}")
        if names.count(role) > 1:
            raise ValueError(f"{name}: fonts.roles names {role} more than once")
    for role in FONT_ROLES:
        if role not in names:
            raise ValueError(f"{name}: fonts.roles has no {role}")
    for index, entry in enumerate(rules.fonts.roles):
        if entry.size < 1:
            raise ValueError(f"{name}: fonts.roles[{index}].size must be 1 or more")
