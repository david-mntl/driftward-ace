"""Version label: the game's version as small dim text in the window's bottom-left corner.

Source: docs/contracts/systems/screens.md, Interface (ui/version_label.py) and Presentation;
10-ui.md, `version_label`. Drawn on the menu and the full-window pages only, never during a run.
The view only draws: it never fills, flips, logs or reads a key.
"""

import logging
from typing import Final

import pygame

from ui.screen_look import ScreenLook

log = logging.getLogger(__name__)

VERSION_PREFIX: Final[str] = "v"
"""Put before the number, so 1.0.0 shows as v1.0.0."""


def draw_version(surface: pygame.Surface, look: ScreenLook, version: str) -> None:
    """Draw ``version`` (such as ``1.0.0``) as ``v1.0.0`` in the bottom-left corner of ``surface``.

    Role ``hint``, plating at ``version.text_alpha``, no glow. The text's left edge sits
    ``margin_left`` px from the left edge and its bottom ``margin_bottom`` px above the bottom.
    """
    rules = look.rules.version
    look.blit_text(
        surface,
        f"{VERSION_PREFIX}{version}",
        "hint",
        look.palette["plating"],
        {"bottomleft": (rules.margin_left, surface.get_height() - rules.margin_bottom)},
        glow=False,
        alpha=rules.text_alpha,
    )
