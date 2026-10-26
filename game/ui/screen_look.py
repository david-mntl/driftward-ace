"""The stand-in look the screens share: text color, sizes, marker, box color and fonts.

Source: docs/contracts/systems/game-flow.md, Interface (ui/screen_look.py) and Presentation. Every
value is a scope report DRA-125, Values needed, stand-in approved by the Director and not in the
GDD, until UI-03 and UI-04. Each one is its own constant, so those features replace them one by
one. Imports pygame only.
"""

import logging
from functools import cache
from typing import Final

import pygame

log = logging.getLogger(__name__)

SCREEN_TEXT_COLOR: Final[tuple[int, int, int]] = (255, 255, 255)
"""Text color, RGB. Scope report DRA-125, Values needed: white text (stand-in until UI-04)."""

SCREEN_TITLE_FONT_SIZE: Final[int] = 32
"""Every title's font size, default font, px: the menu's, the pages', PAUSE and GAME OVER. Scope
report DRA-125, Values needed (stand-in until UI-04)."""

SCREEN_BODY_FONT_SIZE: Final[int] = 16
"""Body font size, default font, px: the pages' sections, lines and footer, and the game-over
lines. Scope report DRA-125, Values needed (stand-in until UI-04)."""

SELECTION_MARKER: Final[str] = ">"
"""Drawn in front of the selected item. Scope report DRA-125, Values needed (stand-in until
UI-04)."""

SCREEN_BOX_COLOR: Final[tuple[int, int, int, int]] = (0, 0, 0, 90)
"""Pause and game-over box fill, RGBA: black at alpha 90 of 255, about 35%. Scope report DRA-23,
Game Over box, reused by scope report DRA-125, Values needed (stand-in until UI-04)."""

BACK_PROMPT_TEXT: Final[str] = "Press Enter or Space to go back."
"""Footer of the instructions and leaderboard pages. Scope report DRA-125, Values needed (stand-in
until UI-03)."""


@cache
def screen_font(size: int) -> pygame.font.Font:
    """Return the default font at ``size`` px, built on the first call for that size and kept.

    Needs ``pygame.font`` initialized. Source: 15-tech-constraints.md, rule 5.
    """
    return pygame.font.Font(None, size)
