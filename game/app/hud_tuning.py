"""Load and check the HUD values file.

Reads `tuning/hud.json` once, at startup (`load_hud_rules`), before the window opens, because the
window's size is in it. Checks every rule of hud.schema.json by hand (pygbag has no schema library)
and builds a HudRules. Every field is required and no default lives in code. A missing file raises
FileNotFoundError; a bad one raises ValueError naming the file and the field. Not a startup module:
it imports ui, so only app.frame imports it, inside the guard.

Source: docs/contracts/schemas/hud.schema.json; docs/contracts/systems/hud.md, Interface; 10-ui.md,
rule 12.
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
from core.run import LIVES_START
from core.world import SCREEN_H, SCREEN_W
from ui.hud_rules import BREAK_LOOKS, PALETTE_KEYS, RGB, HudRules

log = logging.getLogger(__name__)

HUD_FILE: str = "hud.json"

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

_AT_LEAST_ONE: frozenset[str] = frozenset(
    {
        "window.width",
        "window.height",
        "panel.width",
        "frame.pillar_width",
        "frame.sheen_rows",
        "score.tile_count",
        "score.tile_w",
        "score.tile_h",
        "score.tile_pitch",
        "score.tile_top",
        "score.bar_w",
        "score.bar_h",
        "score.bar_segments",
        "score.bar_step",
        "hearts.cell_w",
        "hearts.cell_h",
        "level.bars",
        "level.bar_w",
        "level.bar_pitch",
        "level.bar_base_h",
        "level.tier_mid",
        "level.tier_high",
        "graze.radius",
        "graze.inner_radius",
        "graze.wedge_radius",
        "graze.count_limit",
        "motion.sweep_ticks",
        "motion.sweep_frames",
        "motion.scan_ticks",
        "motion.scan_w",
        "motion.beat_ticks",
        "motion.beat_steps",
        "motion.break_ticks",
        "motion.bump_ticks",
        "motion.ring_ticks",
        "motion.ring_frames",
        "motion.ring_radius",
        "fonts.label_size",
        "fonts.value_size",
        "fonts.tile_size",
        "fonts.graze_size",
        "fonts.level_size",
    }
)
"""Integer fields that must be 1 or more. Every other integer must be 0 or more."""

_SHARES: frozenset[str] = frozenset(
    {
        "frame.spill",
        "fonts.label_mix",
        "fonts.value_mix",
        "level.tier_mid_mix",
    }
)
"""Float fields that must lie in 0..1."""

_SHARES_ABOVE_ZERO: frozenset[str] = frozenset(
    {"motion.beat_peak_at", "motion.beat_end_at", "motion.bump_peak_at"}
)
"""Float fields that must lie above 0 and up to 1."""

_AT_LEAST_ONE_FLOAT: frozenset[str] = frozenset({"motion.beat_scale", "motion.bump_scale"})
"""Float fields that must be 1 or more (a size multiple that only grows)."""

_ABOVE_ZERO: frozenset[str] = frozenset(
    {"frame.light_radius", "panel.scale", "motion.ring_from", "motion.ring_to"}
)
"""Float fields that must be above 0."""


def load_hud_rules() -> HudRules:
    """Read and check the HUD values file and build its records."""
    name: str = f"tuning/{HUD_FILE}"
    text: str = (TUNING_DIR / Path(HUD_FILE)).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{name}: not valid JSON: {err}") from err
    rules: HudRules = _build(HudRules, name, "", data)
    _check_rules(name, rules)
    log.info(
        "hud loaded window=%dx%d panel_x=%d",
        rules.window.width,
        rules.window.height,
        rules.panel.x,
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
        return check_integer(name, path, value, 1 if path in _AT_LEAST_ONE else 0)
    if hint is float:
        return _check_float(name, path, value)
    raise TypeError(f"{name}: {path}: no check for type {hint!r}")


def _convert_generic(name: str, path: str, value: object, hint: types.GenericAlias) -> object:
    """Check a tuple type: a fixed-size list of ints, a list of those, the break keys or the

    palette.
    """
    origin: object = typing.get_origin(hint)
    args: tuple[object, ...] = typing.get_args(hint)
    if origin is collections.abc.Mapping:
        return _convert_palette(name, path, value)
    if origin is tuple and args and args[-1] is Ellipsis:
        if not isinstance(value, list) or not value:
            raise ValueError(f"{name}: {path} must be a non-empty array")
        item: object = args[0]
        return tuple(_convert(name, f"{path}[{i}]", entry, item) for i, entry in enumerate(value))
    if origin is tuple:
        if not isinstance(value, list) or len(value) != len(args):
            raise ValueError(f"{name}: {path} must be an array of {len(args)} items")
        return tuple(
            _convert(name, f"{path}[{i}]", entry, kind)
            for i, (entry, kind) in enumerate(zip(value, args, strict=True))
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


def _check_float(name: str, path: str, value: object) -> float:
    """Return value as a float if it is a number in the range its path needs, else raise."""
    if not is_number(value):
        raise ValueError(f"{name}: {path} must be a number")
    number: float = float(value)
    if path in _SHARES and not 0.0 <= number <= 1.0:
        raise ValueError(f"{name}: {path} must be a number from 0 to 1")
    if path in _SHARES_ABOVE_ZERO and not 0.0 < number <= 1.0:
        raise ValueError(f"{name}: {path} must be a number above 0 and up to 1")
    if path in _AT_LEAST_ONE_FLOAT and number < 1.0:
        raise ValueError(f"{name}: {path} must be a number >= 1")
    if path in _ABOVE_ZERO and number <= 0.0:
        raise ValueError(f"{name}: {path} must be a number > 0")
    if number < 0.0:
        raise ValueError(f"{name}: {path} must be a number >= 0")
    return number


def _check_rules(name: str, rules: HudRules) -> None:
    """Check what a single field can't: the palette, the break keys, and fields that depend on each

    other.
    """
    _check_palette(name, rules.palette)
    _check_geometry(name, rules)
    if rules.window.dim_alpha > 255:
        raise ValueError(f"{name}: window.dim_alpha must be an integer from 0 to 255")
    if len(rules.hearts.slots) != LIVES_START:
        raise ValueError(f"{name}: hearts.slots must hold one center per life ({LIVES_START})")
    if rules.level.tier_mid > rules.level.tier_high:
        raise ValueError(f"{name}: level.tier_mid must be <= level.tier_high")
    if rules.motion.beat_peak_at >= rules.motion.beat_end_at:
        raise ValueError(f"{name}: motion.beat_peak_at must be below motion.beat_end_at")
    if rules.motion.scan_from > rules.motion.scan_to:
        raise ValueError(f"{name}: motion.scan_from must be <= motion.scan_to")
    _check_break_keys(name, rules.motion.break_keys)


def _check_geometry(name: str, rules: HudRules) -> None:
    """Raise unless the play area, panel and frame fit the window and the bar segments have width.

    A bad number would otherwise fail deep inside pygame with no field named.
    """
    window, panel = rules.window, rules.panel
    if window.field_x + SCREEN_W > window.width or window.field_y + SCREEN_H > window.height:
        raise ValueError(
            f"{name}: window.field_x and window.field_y must leave room for the "
            f"{SCREEN_W}x{SCREEN_H} play area inside window.width and window.height"
        )
    if panel.x + panel.width > window.width:
        raise ValueError(f"{name}: panel.x + panel.width must be <= window.width")
    frame_width: int = panel.x + rules.frame.pillar_width
    if frame_width > window.width or frame_width < window.field_x + SCREEN_W:
        raise ValueError(
            f"{name}: panel.x + frame.pillar_width must reach past the play area "
            "and fit window.width"
        )
    score = rules.score
    if score.bar_w <= (score.bar_segments - 1) * score.bar_gap:
        raise ValueError(
            f"{name}: score.bar_gap is too wide for score.bar_w and score.bar_segments"
        )


def _check_palette(name: str, palette: object) -> None:
    """Raise unless the palette holds exactly PALETTE_KEYS, each a #rrggbb text."""
    if not isinstance(palette, dict):
        raise ValueError(f"{name}: palette must be an object")
    for key in PALETTE_KEYS:
        if key not in palette:
            raise ValueError(f"{name}: palette.{key} is missing")
    for key in palette:
        if key not in PALETTE_KEYS:
            raise ValueError(f"{name}: palette.{key} is not a known field")


def _check_break_keys(name: str, keys: tuple[tuple[float, float, str], ...]) -> None:
    """Raise unless the keys start at 0, end at 1, never go back, and name known looks."""
    if len(keys) < 2:
        raise ValueError(f"{name}: motion.break_keys must hold at least 2 keys")
    shares: list[float] = [key[0] for key in keys]
    if shares[0] != 0.0 or shares[-1] != 1.0 or shares != sorted(shares):
        raise ValueError(f"{name}: motion.break_keys shares must rise from 0 to 1")
    for index, (_, brightness, look) in enumerate(keys):
        if not 0.0 <= brightness <= 1.0:
            raise ValueError(f"{name}: motion.break_keys[{index}] brightness must be 0 to 1")
        if look not in BREAK_LOOKS:
            raise ValueError(
                f"{name}: motion.break_keys[{index}] look must be one of {BREAK_LOOKS}"
            )
