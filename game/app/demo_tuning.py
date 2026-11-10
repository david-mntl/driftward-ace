"""Load and check the demo flight values file.

Reads `tuning/demo.json` once, at startup (`load_demo`), in both run modes, after the drifter
tuning (the coin's variant must exist) and the screens' rules (the caption's text role must
exist). Checks every field by hand (pygbag has no schema library), then the script with
`core.demo.check_demo_rules`, and returns the core `DemoRules` (None when `enabled` is false) and
the `ui.demo_view.DemoLook`. Every field is required and no default lives in code. A missing file
raises FileNotFoundError; a bad one raises ValueError naming the file and the field. Not a startup
module: it imports core and ui, so only app.frame imports it, inside the guard.

Source: docs/contracts/schemas/demo.schema.json; docs/contracts/systems/demo.md.
"""

import json
import logging
from typing import Final

from app.drifters.checks import (
    check_boolean,
    check_fields,
    check_integer,
    check_number,
    check_positive,
    is_number,
)
from app.tuning import TUNING_DIR
from core.demo import DemoRules, DemoStep, PilotRules, check_demo_rules
from core.drifters.base import DrifterType
from core.drifters.tuning import DrifterTuning
from core.ship import Thrust
from core.world import SCREEN_H, SCREEN_W
from ui.demo_view import DemoLook
from ui.screen_rules import ScreenRules

log = logging.getLogger(__name__)

DEMO_FILE: Final[str] = "demo.json"
"""The demo flight file, in TUNING_DIR."""

_FILE_NAME: Final[str] = f"tuning/{DEMO_FILE}"

_FIELDS: Final[frozenset[str]] = frozenset(
    (
        "enabled",
        "steps",
        "coin_step",
        "coin_type",
        "coin_variant",
        "fade_out_ticks",
        "pilot",
        "look",
    )
)

_STEP_FIELDS: Final[frozenset[str]] = frozenset(("keys", "ticks", "caption", "stand", "pilot_to"))

_PILOT_POSITIVE: Final[tuple[str, ...]] = ("gain", "max_speed", "band")
"""Autopilot fields that must be above 0."""

_PILOT_FIELDS: Final[frozenset[str]] = frozenset((*_PILOT_POSITIVE, "near_px", "near_speed"))

_ARROWS: Final[tuple[str, ...]] = ("up", "down", "left", "right")

_LOOK_INTEGERS: Final[dict[str, int]] = {
    "key_size": 1,
    "key_gap": 0,
    "key_radius": 0,
    "key_bottom": 0,
    "arrow_size": 1,
    "key_fade_ticks": 1,
    "press_depth": 0,
    "idle_fill_alpha": 0,
    "idle_border_alpha": 0,
    "lit_fill_alpha": 0,
    "caption_gap": 0,
    "caption_fade_ticks": 1,
    "caption_rise": 0,
    "skip_margin": 0,
    "fade_in_ticks": 0,
    "coin_ring_radius": 0,
    "coin_ring_pulse": 0,
    "coin_ring_period_ticks": 1,
    "coin_ring_alpha": 0,
    "start_ticks": 0,
    "start_pop_ticks": 1,
    "start_y": 0,
}
"""Each whole-number look field and its lowest value."""

_ALPHAS: Final[tuple[str, ...]] = (
    "idle_fill_alpha",
    "idle_border_alpha",
    "lit_fill_alpha",
    "coin_ring_alpha",
)

_LOOK_FIELDS: Final[frozenset[str]] = frozenset(
    (*_LOOK_INTEGERS, "caption_role", "skip_word", "start_text", "start_role", "start_scale")
)


def load_demo(
    tuning: DrifterTuning, screen_rules: ScreenRules
) -> tuple[DemoRules | None, DemoLook]:
    """Read and check tuning/demo.json. Return (the script, None when off; the look).

    Logs one INFO line.
    """
    text: str = (TUNING_DIR / DEMO_FILE).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{_FILE_NAME}: not valid JSON: {err}") from err
    fields: dict[str, object] = check_fields(_FILE_NAME, "", data, _FIELDS)
    enabled: bool = check_boolean(_FILE_NAME, "enabled", fields)
    look, key_fade_ticks = _look(fields["look"], screen_rules)
    rules: DemoRules = DemoRules(
        steps=_steps(fields["steps"]),
        coin_step=check_integer(_FILE_NAME, "coin_step", fields["coin_step"], 0),
        coin_type=_coin_type(fields["coin_type"]),
        coin_variant=_coin_variant(fields["coin_type"], fields["coin_variant"], tuning),
        fade_out_ticks=check_integer(_FILE_NAME, "fade_out_ticks", fields["fade_out_ticks"], 0),
        pilot=_pilot(fields["pilot"]),
        key_fade_ticks=key_fade_ticks,
    )
    try:
        check_demo_rules(rules)
    except ValueError as err:
        raise ValueError(f"{_FILE_NAME}: {err}") from err
    log.info(
        "demo loaded enabled=%s steps=%d ticks=%d",
        enabled,
        len(rules.steps),
        sum(demo_step.ticks for demo_step in rules.steps),
    )
    return (rules if enabled else None), look


def _steps(data: object) -> tuple[DemoStep, ...]:
    """Check the steps list and build each step."""
    if not isinstance(data, list) or not data:
        raise ValueError(f"{_FILE_NAME}: steps must be a non-empty list")
    return tuple(_step(f"steps[{index}]", item) for index, item in enumerate(data))


def _step(path: str, data: object) -> DemoStep:
    """Check one step and build it."""
    fields: dict[str, object] = check_fields(_FILE_NAME, path, data, _STEP_FIELDS)
    keys: object = fields["keys"]
    if (
        not isinstance(keys, list)
        or any(key not in _ARROWS for key in keys)
        or len(set(keys)) != len(keys)
    ):
        raise ValueError(f"{_FILE_NAME}: {path}.keys must list distinct arrows of {_ARROWS}")
    caption: object = fields["caption"]
    if caption is not None and (not isinstance(caption, str) or not caption.strip()):
        raise ValueError(f"{_FILE_NAME}: {path}.caption must be text or null")
    stand: object = fields["stand"]
    if not isinstance(stand, bool):
        raise ValueError(f"{_FILE_NAME}: {path}.stand must be a boolean")
    return DemoStep(
        keys=Thrust(**{arrow: arrow in keys for arrow in _ARROWS}),
        ticks=check_integer(_FILE_NAME, f"{path}.ticks", fields["ticks"], 1),
        caption=caption,
        stand=stand,
        pilot_to=_spot(f"{path}.pilot_to", fields["pilot_to"]),
    )


def _spot(path: str, value: object) -> tuple[float, float] | None:
    """Return the [x, y] spot inside the play area, None for null, else raise."""
    if value is None:
        return None
    if (
        not isinstance(value, list)
        or len(value) != 2
        or not all(is_number(number) for number in value)
        or not 0 <= value[0] <= SCREEN_W
        or not 0 <= value[1] <= SCREEN_H
    ):
        raise ValueError(
            f"{_FILE_NAME}: {path} must be null or [x, y] inside {SCREEN_W} x {SCREEN_H}"
        )
    return float(value[0]), float(value[1])


def _pilot(data: object) -> PilotRules:
    """Check the autopilot object and build it."""
    fields: dict[str, object] = check_fields(_FILE_NAME, "pilot", data, _PILOT_FIELDS)
    positive: dict[str, float] = {
        name: check_positive(_FILE_NAME, f"pilot.{name}", fields[name]) for name in _PILOT_POSITIVE
    }
    near: dict[str, float] = {}
    for name in ("near_px", "near_speed"):
        value: float = check_number(_FILE_NAME, f"pilot.{name}", fields[name])
        if value < 0:
            raise ValueError(f"{_FILE_NAME}: pilot.{name} must be a number >= 0")
        near[name] = value
    return PilotRules(**positive, **near)


def _coin_type(value: object) -> DrifterType:
    """Return the drifter type named `value`, else raise. Whether it is a pickup is checked by
    `core.demo.start_demo`."""
    names: list[str] = [member.value for member in DrifterType]
    if not isinstance(value, str) or value not in names:
        raise ValueError(f"{_FILE_NAME}: coin_type must be one of {names}")
    return DrifterType(value)


def _coin_variant(type_name: object, value: object, tuning: DrifterTuning) -> str:
    """Return the variant name if the coin type's tuning has it, else raise."""
    coin = tuning.drifters.get(_coin_type(type_name))
    names: list[str] = sorted(coin.variants) if coin is not None else []
    if not isinstance(value, str) or value not in names:
        raise ValueError(f"{_FILE_NAME}: coin_variant must be one of {names}")
    return value


def _look(data: object, screen_rules: ScreenRules) -> tuple[DemoLook, int]:
    """Check the look object. Return the look and `key_fade_ticks`, which the core glow uses."""
    fields: dict[str, object] = check_fields(_FILE_NAME, "look", data, _LOOK_FIELDS)
    numbers: dict[str, int] = {
        name: check_integer(_FILE_NAME, f"look.{name}", fields[name], minimum)
        for name, minimum in _LOOK_INTEGERS.items()
    }
    for name in _ALPHAS:
        if numbers[name] > 255:
            raise ValueError(f"{_FILE_NAME}: look.{name} must be 0 to 255")
    key_fade_ticks: int = numbers.pop("key_fade_ticks")
    scale: object = fields["start_scale"]
    if not is_number(scale) or scale < 1:
        raise ValueError(f"{_FILE_NAME}: look.start_scale must be a number >= 1")
    look: DemoLook = DemoLook(
        caption_role=_role("caption_role", fields, screen_rules),
        skip_word=_text("skip_word", fields),
        start_text=_text("start_text", fields),
        start_role=_role("start_role", fields, screen_rules),
        start_scale=float(scale),
        **numbers,
    )
    return look, key_fade_ticks


def _role(name: str, fields: dict[str, object], screen_rules: ScreenRules) -> str:
    """Return look field `name` if it is a screens text role, else raise."""
    roles: list[str] = [role.name for role in screen_rules.fonts.roles]
    role: object = fields[name]
    if not isinstance(role, str) or role not in roles:
        raise ValueError(f"{_FILE_NAME}: look.{name} must be one of {roles}")
    return role


def _text(name: str, fields: dict[str, object]) -> str:
    """Return look field `name` if it is text that is not blank, else raise."""
    word: object = fields[name]
    if not isinstance(word, str) or not word.strip():
        raise ValueError(f"{_FILE_NAME}: look.{name} must be text")
    return word
