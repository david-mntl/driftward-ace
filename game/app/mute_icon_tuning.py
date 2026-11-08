"""Load and check the mute icon values file.

Reads `tuning/mute_icon.json` once, at startup (`load_mute_icon_look`), in both run modes, after
the HUD rules (it needs the window and the play area). Checks every rule of
mute_icon.schema.json by hand (pygbag has no schema library), then the rules a schema can't
express, and builds `ui.mute_icon.MuteIconLook` from `margin` and `size`. The two colors are
checked and dropped: only tools/art/mute_icon.py reads them. Every field is required and no
default lives in code. A missing file raises FileNotFoundError; a bad one raises ValueError naming
the file and the field. Not a startup module: it imports ui, so only app.frame imports it, inside
the guard.

Source: docs/contracts/schemas/mute_icon.schema.json; docs/contracts/systems/mute-icon.md,
Interface and Rules 14, 15 and 17.
"""

import json
import logging
import re

import pygame

from app.drifters.checks import check_fields, check_integer
from app.tuning import TUNING_DIR
from core.world import SCREEN_H, SCREEN_W
from ui.hud_rules import HudRules
from ui.mute_icon import MuteIconLook

log = logging.getLogger(__name__)

MUTE_ICON_FILE: str = "mute_icon.json"
"""The mute icon file, in TUNING_DIR."""

_FILE_NAME: str = f"tuning/{MUTE_ICON_FILE}"

_FIELDS: frozenset[str] = frozenset(("margin", "size", "speaker_color", "slash_color"))

_COLOR_FIELDS: tuple[str, ...] = ("speaker_color", "slash_color")

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def load_mute_icon_look(hud_rules: HudRules) -> MuteIconLook:
    """Read and check tuning/mute_icon.json and build its look. Logs one INFO line.

    The icon's rectangle must lie inside the window and must not share a pixel with the play
    area's rectangle, else ValueError naming the file, `margin` and `size`.
    """
    text: str = (TUNING_DIR / MUTE_ICON_FILE).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{_FILE_NAME}: not valid JSON: {err}") from err
    fields: dict[str, object] = check_fields(_FILE_NAME, "", data, _FIELDS)
    look: MuteIconLook = MuteIconLook(
        margin=check_integer(_FILE_NAME, "margin", fields["margin"], 0),
        size=check_integer(_FILE_NAME, "size", fields["size"], 1),
    )
    for name in _COLOR_FIELDS:
        _check_color(name, fields[name])
    _check_corner(look, hud_rules)
    log.info("mute icon loaded margin=%d size=%d", look.margin, look.size)
    return look


def _check_color(field: str, value: object) -> None:
    """Raise unless value is a #rrggbb string."""
    if not isinstance(value, str) or not _HEX.match(value):
        raise ValueError(f"{_FILE_NAME}: {field} must be a color like #rrggbb")


def _check_corner(look: MuteIconLook, hud_rules: HudRules) -> None:
    """Raise unless the icon's rectangle is inside the window and clear of the play area."""
    window = hud_rules.window
    offset: int = look.margin + look.size
    icon: pygame.Rect = pygame.Rect(
        window.width - offset, window.height - offset, look.size, look.size
    )
    if not pygame.Rect(0, 0, window.width, window.height).contains(icon):
        raise ValueError(f"{_FILE_NAME}: margin and size put the icon outside the window")
    play_area: pygame.Rect = pygame.Rect(window.field_x, window.field_y, SCREEN_W, SCREEN_H)
    if icon.colliderect(play_area):
        raise ValueError(f"{_FILE_NAME}: margin and size put the icon over the play area")
