"""Leaderboard page: the title, the empty-list line and the footer.

Source: docs/contracts/systems/game-flow.md, Interface (ui/leaderboard.py) and Presentation,
Leaderboard page. The page is empty until DRA-126. The view takes nothing but the surface and only
draws. It never fills the background, never flips the display, never logs per frame, never catches
an error and never reads the run mode, a key or the focus. A stand-in until UI-03 and UI-04.
"""

import logging
from functools import cache
from typing import Final

import pygame

from ui.screen_look import (
    BACK_PROMPT_TEXT,
    SCREEN_BODY_FONT_SIZE,
    SCREEN_TEXT_COLOR,
    SCREEN_TITLE_FONT_SIZE,
    screen_font,
)

log = logging.getLogger(__name__)

LEADERBOARD_TITLE_TEXT: Final[str] = "LEADERBOARD"
"""Page title. Scope report DRA-125, Values needed, Leaderboard page (stand-in until UI-03)."""

LEADERBOARD_EMPTY_TEXT: Final[str] = "No scores yet."
"""The line an empty top 10 shows. Scope report DRA-125, Values needed, Leaderboard page."""


def draw_leaderboard(surface: pygame.Surface) -> None:
    """Blit the title, the empty-list line and the footer onto ``surface``. Units: px.

    The block is the title, a blank body line, then the empty-list line. It is centered vertically
    between the surface's top and the footer's top. The footer sits where the instructions page
    puts it: its top two body lines above the bottom. Needs ``pygame.font`` initialized.
    """
    width, height = surface.get_size()
    body_line: int = screen_font(SCREEN_BODY_FONT_SIZE).get_linesize()
    title_line: int = screen_font(SCREEN_TITLE_FONT_SIZE).get_linesize()
    footer_top: int = height - 2 * body_line
    top: int = (footer_top - (title_line + 2 * body_line)) // 2
    _blit_centered(surface, LEADERBOARD_TITLE_TEXT, SCREEN_TITLE_FONT_SIZE, width, top)
    top += title_line + body_line
    _blit_centered(surface, LEADERBOARD_EMPTY_TEXT, SCREEN_BODY_FONT_SIZE, width, top)
    _blit_centered(surface, BACK_PROMPT_TEXT, SCREEN_BODY_FONT_SIZE, width, footer_top)


def _blit_centered(surface: pygame.Surface, text: str, size: int, width: int, top: int) -> None:
    """Blit ``text`` at font ``size`` with its center on ``width // 2`` and its top at ``top``."""
    image: pygame.Surface = _render(text, size)
    surface.blit(image, image.get_rect(centerx=width // 2, top=top))


@cache
def _render(text: str, size: int) -> pygame.Surface:
    """Return ``text`` rendered once at font ``size``, antialiased, in the screen text color."""
    return screen_font(size).render(text, True, SCREEN_TEXT_COLOR)
