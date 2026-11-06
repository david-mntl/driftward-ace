"""Load and check the level-up values file.

Reads `tuning/level_up.json` once, at startup (`load_level_up`), in both run modes, after the HUD
rules (the HUD palette resolves the color keys). Checks every rule of level-up.schema.json by hand
(pygbag has no schema library), then the rules a schema can't express, and builds the core rules
(`core.level_up.LevelUpRules`) and the look records (`ui.level_up_rules.LevelUpLook`). Every field
is required and no default lives in code. A missing file raises FileNotFoundError; a bad one raises
ValueError naming the file and the field. Not a startup module: it imports ui, so only app.frame
imports it, inside the guard.

Source: docs/contracts/schemas/level-up.schema.json; docs/contracts/systems/level-up/tuning.md;
10-ui.md, rule 12.
"""

import json
import logging
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from app.drifters.checks import check_fields, check_integer, is_number
from app.tuning import TUNING_DIR
from core.level_up import LevelUpRules
from ui.hud_rules import HudRules
from ui.level_up_rules import (
    RGB,
    BandLook,
    BumpLook,
    FlyLook,
    GlintLook,
    HoldLook,
    LabelLook,
    LevelUpLook,
    NumberLook,
    PipsLook,
    PopLook,
    RingLook,
    StreakLook,
)

log = logging.getLogger(__name__)

LEVEL_UP_FILE: str = "level_up.json"

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

_Check = Callable[[str, str, object], int | float]
"""Checks one field and returns it as the int or float its record holds."""


def _tick(name: str, path: str, value: object) -> int:
    return check_integer(name, path, value, 0)


def _count(name: str, path: str, value: object) -> int:
    return check_integer(name, path, value, 1)


def _whole(name: str, path: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name}: {path} must be an integer")
    return value


def _at_least(minimum: int) -> _Check:
    def check(name: str, path: str, value: object) -> int:
        return check_integer(name, path, value, minimum)

    return check


def _alpha(name: str, path: str, value: object) -> int:
    number: int = check_integer(name, path, value, 0, "an integer from 0 to 255")
    if number > 255:
        raise ValueError(f"{name}: {path} must be an integer from 0 to 255")
    return number


def _above_zero(name: str, path: str, value: object) -> float:
    if not is_number(value) or value <= 0:
        raise ValueError(f"{name}: {path} must be a number > 0")
    return float(value)


def _zero_or_more(name: str, path: str, value: object) -> float:
    if not is_number(value) or value < 0:
        raise ValueError(f"{name}: {path} must be a number >= 0")
    return float(value)


def _share(name: str, path: str, value: object) -> float:
    if not is_number(value) or not 0 < value < 1:
        raise ValueError(f"{name}: {path} must be a number above 0 and below 1")
    return float(value)


def _above_one(name: str, path: str, value: object) -> float:
    if not is_number(value) or value <= 1:
        raise ValueError(f"{name}: {path} must be a number > 1")
    return float(value)


def _up_to_one(name: str, path: str, value: object) -> float:
    if not is_number(value) or not 0 < value <= 1:
        raise ValueError(f"{name}: {path} must be a number above 0 and at most 1")
    return float(value)


def _degrees(name: str, path: str, value: object) -> float:
    if not is_number(value) or not 0 <= value <= 89:
        raise ValueError(f"{name}: {path} must be a number from 0 to 89")
    return float(value)


_CHECKS: dict[str, dict[str, _Check]] = {
    "band": {
        "height": _at_least(2),
        "alpha": _alpha,
        "center_offset_y": _whole,
        "open_start": _tick,
        "open_end": _count,
        "close_start": _count,
        "close_end": _count,
        "close_glass_share": _share,
        "hairline_width": _count,
        "corner_tick_length": _tick,
    },
    "number": {
        "font_size": _at_least(8),
        "outline_width": _tick,
        "center_offset_y": _whole,
        "fall_start": _tick,
        "fall_end": _count,
        "fall_overshoot_px": _zero_or_more,
        "fall_peak_share": _share,
        "fall_stretch_x": _above_zero,
        "fall_stretch_y": _above_zero,
        "squash_ticks": _count,
        "squash_x": _above_zero,
        "squash_y": _above_zero,
        "pose_steps": _count,
    },
    "label": {
        "font_size": _at_least(6),
        "offset_y": _whole,
        "fade_in_start": _tick,
        "fade_in_end": _count,
        "spacing_wide": _tick,
        "spacing_normal": _tick,
        "spacing_steps": _count,
    },
    "hold": {"fade_out_start": _count, "fade_out_end": _count},
    "pips": {
        "size": _at_least(2),
        "pitch": _count,
        "offset_y": _whole,
        "start": _tick,
        "end": _count,
        "pop_ticks": _count,
        "flash_ticks": _count,
    },
    "ring": {
        "start_diameter": _above_zero,
        "end_diameter": _above_zero,
        "width": _count,
        "ticks": _count,
    },
    "streaks": {
        "count": _count,
        "ticks": _count,
        "length": _above_zero,
        "width": _count,
        "start_radius": _zero_or_more,
        "end_radius": _above_zero,
    },
    "glint": {
        "start": _tick,
        "end": _count,
        "frames": _count,
        "width": _count,
        "slant_degrees": _degrees,
        "strength": _up_to_one,
    },
    "bump": {"pixels": _tick, "ticks": _count, "peak_share": _share},
    "fly": {"start": _count, "arc_px": _zero_or_more, "steps": _count},
    "pop": {
        "ticks": _count,
        "start_scale": _above_one,
        "undershoot_scale": _up_to_one,
        "undershoot_share": _share,
        "flash_ticks": _count,
        "steps": _count,
        "bar_flash_ticks": _count,
        "box_flash_ticks": _count,
        "box_flash_width": _count,
        "box_corner_cut": _tick,
    },
}
"""Each look section: the check of every field, in the schema's order."""

COLOR_KEYS: tuple[str, ...] = (
    "glass",
    "hairline",
    "label",
    "number_top",
    "number_bottom",
    "number_outline",
    "ring",
    "streak",
    "glint",
    "pip_lit",
    "pip_unlit",
    "flash",
    "box_flash",
)
"""The 13 color keys of the schema's `colors` section."""

_TOP_FIELDS: frozenset[str] = frozenset({"level_up_rest", "arrival_tick", "banner_ticks", "colors"})


@dataclass(frozen=True, slots=True)
class _Loaded:
    """The file after the field checks: the three core numbers and the look."""

    rules: LevelUpRules
    look: LevelUpLook


def load_level_up(hud_rules: HudRules) -> tuple[LevelUpRules, LevelUpLook]:
    """Read and check the level-up values file; build the core rules and the look records."""
    name: str = f"tuning/{LEVEL_UP_FILE}"
    text: str = (TUNING_DIR / Path(LEVEL_UP_FILE)).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{name}: not valid JSON: {err}") from err
    loaded: _Loaded = _build(name, data, hud_rules.palette)
    _check_rules(name, loaded)
    log.info(
        "level up loaded level_up_rest=%d arrival_tick=%d banner_ticks=%d",
        loaded.rules.rest_ticks,
        loaded.rules.arrival_ticks,
        loaded.rules.banner_ticks,
    )
    return loaded.rules, loaded.look


def _build(name: str, data: object, palette: Mapping[str, RGB]) -> _Loaded:
    """Check every field of every section and build the records."""
    fields: dict[str, object] = check_fields(name, "", data, _TOP_FIELDS | _CHECKS.keys())
    rules: LevelUpRules = LevelUpRules(
        rest_ticks=check_integer(name, "level_up_rest", fields["level_up_rest"], 0),
        arrival_ticks=check_integer(name, "arrival_tick", fields["arrival_tick"], 1),
        banner_ticks=check_integer(name, "banner_ticks", fields["banner_ticks"], 1),
    )

    def section[T](record: Callable[..., T], key: str) -> T:
        return record(**_section_values(name, key, fields[key]))

    look: LevelUpLook = LevelUpLook(
        colors=_build_colors(name, fields["colors"], palette),
        band=section(BandLook, "band"),
        number=section(NumberLook, "number"),
        label=section(LabelLook, "label"),
        hold=section(HoldLook, "hold"),
        pips=section(PipsLook, "pips"),
        ring=section(RingLook, "ring"),
        streaks=section(StreakLook, "streaks"),
        glint=section(GlintLook, "glint"),
        bump=section(BumpLook, "bump"),
        fly=section(FlyLook, "fly"),
        pop=section(PopLook, "pop"),
    )
    return _Loaded(rules=rules, look=look)


def _section_values(name: str, section: str, data: object) -> dict[str, int | float]:
    """Check one section's fields, each by its own check, and return them by name."""
    checks: dict[str, _Check] = _CHECKS[section]
    fields: dict[str, object] = check_fields(name, section, data, frozenset(checks))
    return {key: check(name, f"{section}.{key}", fields[key]) for key, check in checks.items()}


def _build_colors(name: str, data: object, palette: Mapping[str, RGB]) -> dict[str, RGB]:
    """Check the colors section and resolve each key to RGB."""
    fields: dict[str, object] = check_fields(name, "colors", data, frozenset(COLOR_KEYS))
    return {key: _resolve_color(name, f"colors.{key}", fields[key], palette) for key in COLOR_KEYS}


def _resolve_color(name: str, path: str, value: object, palette: Mapping[str, RGB]) -> RGB:
    """Return `#rrggbb` or a HUD palette key as RGB, else raise."""
    if not isinstance(value, str):
        raise ValueError(f"{name}: {path} must be a string")
    if _HEX.match(value):
        return (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16))
    if value in palette:
        return palette[value]
    raise ValueError(f"{name}: {path} '{value}' is not a hex color or a HUD palette key")


def _check_rules(name: str, loaded: _Loaded) -> None:
    """Check the rules a field can't: the order of the ticks across fields and sections."""
    rules, look = loaded.rules, loaded.look
    if rules.rest_ticks > 0:
        _need(
            name,
            rules.arrival_ticks < rules.banner_ticks,
            "arrival_tick must be below banner_ticks",
        )
        _need(
            name,
            rules.banner_ticks <= rules.rest_ticks,
            "banner_ticks must be at most level_up_rest",
        )
    _check_pop(name, rules, look)
    _check_band(name, rules, look)
    _check_number(name, look)
    _check_label_and_pips(name, rules, look)
    _need(
        name,
        look.glint.start < look.glint.end <= look.hold.fade_out_start,
        "glint.start must be below glint.end, and glint.end at most hold.fade_out_start",
    )
    _need(name, look.fly.start < rules.arrival_ticks, "fly.start must be below arrival_tick")
    _need(
        name,
        look.ring.start_diameter < look.ring.end_diameter,
        "ring.start_diameter must be below ring.end_diameter",
    )
    _need(
        name,
        look.streaks.start_radius < look.streaks.end_radius,
        "streaks.start_radius must be below streaks.end_radius",
    )


def _check_pop(name: str, rules: LevelUpRules, look: LevelUpLook) -> None:
    """The pop fits the banner's life and is as long as each of its flashes."""
    pop = look.pop
    _need(
        name,
        rules.arrival_ticks + pop.ticks <= rules.banner_ticks,
        "arrival_tick + pop.ticks must be at most banner_ticks",
    )
    for flash in ("flash_ticks", "bar_flash_ticks", "box_flash_ticks"):
        _need(name, getattr(pop, flash) <= pop.ticks, f"pop.{flash} must be at most pop.ticks")


def _check_band(name: str, rules: LevelUpRules, look: LevelUpLook) -> None:
    """The band opens, then closes, and is closed by the arrival."""
    band = look.band
    _need(
        name,
        band.open_start < band.open_end <= band.close_start < band.close_end <= rules.arrival_ticks,
        "band must satisfy open_start < open_end <= close_start < close_end <= arrival_tick",
    )


def _check_number(name: str, look: LevelUpLook) -> None:
    """The fall, the squash and what the landing starts are over before the flight."""
    number = look.number
    _need(
        name, number.fall_start < number.fall_end, "number.fall_start must be below number.fall_end"
    )
    _need(
        name,
        number.fall_end + number.squash_ticks <= look.fly.start,
        "number.fall_end + number.squash_ticks must be at most fly.start",
    )
    landing: int = max(look.ring.ticks, look.streaks.ticks, look.bump.ticks)
    _need(
        name,
        number.fall_end + landing <= look.fly.start,
        "number.fall_end + max(ring.ticks, streaks.ticks, bump.ticks) must be at most fly.start",
    )


def _check_label_and_pips(name: str, rules: LevelUpRules, look: LevelUpLook) -> None:
    """The label and the pips fade in and out inside the hold."""
    label, hold, pips = look.label, look.hold, look.pips
    _need(
        name,
        label.fade_in_start
        < label.fade_in_end
        <= hold.fade_out_start
        < hold.fade_out_end
        <= rules.arrival_ticks,
        "label.fade_in_* and hold.fade_out_* must satisfy fade_in_start < fade_in_end <= "
        "fade_out_start < fade_out_end <= arrival_tick",
    )
    _need(
        name,
        pips.start < pips.end <= hold.fade_out_start,
        "pips.start must be below pips.end, and pips.end at most hold.fade_out_start",
    )
    _need(
        name,
        pips.pop_ticks <= pips.end - pips.start,
        "pips.pop_ticks must be at most pips.end - pips.start",
    )


def _need(name: str, ok: bool, message: str) -> None:
    """Raise ValueError naming the file unless `ok`."""
    if not ok:
        raise ValueError(f"{name}: {message}")
