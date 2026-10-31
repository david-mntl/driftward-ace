"""Load and check the background values file.

Reads `tuning/background.json` once, at startup (`load_background_rules`). Checks every rule of
background.schema.json by hand (pygbag has no schema library) and builds a BackgroundRules. A
field left out keeps its default from DEFAULTS. A missing file raises FileNotFoundError; a bad one
raises ValueError naming the file and the field. Never falls back for a missing file.
Not a startup module: it imports ui, so only app.frame imports it, inside the guard.

Source: docs/contracts/schemas/background.schema.json; 12-art-and-audio.md, background_numbers.
"""

import json
import logging
from pathlib import Path

from app.drifters.checks import check_fields, check_integer, is_number
from app.tuning import TUNING_DIR
from ui.background_view import BackgroundRules

log = logging.getLogger(__name__)

BACKGROUND_FILE: str = "background.json"

DEFAULTS: dict[str, int | float] = {
    "sway_loop_ticks": 900,
    "planet_count": 3,
    "planet_speed": 0.15,
    "planet_scale": 1.0,
    "river_light_count": 30,
    "river_light_loop_ticks": 900,
    "river_light_strength": 0.6,
    "swirl_count": 8,
    "swirl_loop_ticks": 480,
    "glow_height": 40,
    "glow_strength": 0.25,
}
"""Every field's default. All are guesses to tune after a frame-rate check in the browser build.
Source: 12-art-and-audio.md, background_numbers (guess)."""

_FIELDS: frozenset[str] = frozenset(DEFAULTS)


def load_background_rules() -> BackgroundRules:
    """Read and check the background values file and build its record. `{}` is valid."""
    name: str = f"tuning/{BACKGROUND_FILE}"
    text: str = (TUNING_DIR / Path(BACKGROUND_FILE)).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{name}: not valid JSON: {err}") from err
    fields: dict[str, object] = check_fields(name, "", data, _FIELDS, optional=_FIELDS)
    values: dict[str, object] = {**DEFAULTS, **fields}
    rules: BackgroundRules = BackgroundRules(
        sway_loop_ticks=check_integer(name, "sway_loop_ticks", values["sway_loop_ticks"], 1),
        planet_count=check_integer(name, "planet_count", values["planet_count"], 0),
        planet_speed=_number(name, "planet_speed", values, 0.0, None),
        planet_scale=_number(name, "planet_scale", values, 0.0, None, above=True),
        river_light_count=check_integer(name, "river_light_count", values["river_light_count"], 0),
        river_light_loop_ticks=check_integer(
            name, "river_light_loop_ticks", values["river_light_loop_ticks"], 1
        ),
        river_light_strength=_number(name, "river_light_strength", values, 0.0, 1.0),
        swirl_count=check_integer(name, "swirl_count", values["swirl_count"], 0),
        swirl_loop_ticks=check_integer(name, "swirl_loop_ticks", values["swirl_loop_ticks"], 1),
        glow_height=check_integer(name, "glow_height", values["glow_height"], 0),
        glow_strength=_number(name, "glow_strength", values, 0.0, 1.0),
    )
    log.info("background loaded %s", rules)
    return rules


def _number(
    name: str,
    key: str,
    values: dict[str, object],
    low: float,
    high: float | None,
    above: bool = False,
) -> float:
    """Return values[key] if it is a number from `low` up to `high` (None: no top), else raise.

    With `above`, `low` itself is not allowed.
    """
    value: object = values[key]
    too_low: bool = is_number(value) and (value <= low if above else value < low)
    too_high: bool = is_number(value) and high is not None and value > high
    if not is_number(value) or too_low or too_high:
        bound: str = f"> {low:g}" if above else f">= {low:g}"
        limit: str = f" and <= {high:g}" if high is not None else ""
        raise ValueError(f"{name}: {key} must be a number {bound}{limit}")
    return float(value)
