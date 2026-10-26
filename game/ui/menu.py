"""Menu screen: the title and the three items, the selected one marked.

Source: docs/contracts/systems/game-flow.md, Interface (ui/menu.py) and Presentation, Menu. The
view takes the selection as a plain value and only draws. It never fills the background, never
flips the display, never logs per frame, never catches an error and never reads the run mode, a
key or the focus. A stand-in until UI-03 and UI-04.
"""

import logging
from collections.abc import Mapping
from functools import cache
from types import MappingProxyType
from typing import Final

import pygame

from core.game_flow import MenuItem
from ui.screen_look import (
    SCREEN_TEXT_COLOR,
    SCREEN_TITLE_FONT_SIZE,
    SELECTION_MARKER,
    screen_font,
)

log = logging.getLogger(__name__)

MENU_TITLE_TEXT: Final[str] = "DRIFTWARD ACE"
"""Menu title. Scope report DRA-125, Values needed, Menu (stand-in until UI-03)."""

MENU_ITEM_FONT_SIZE: Final[int] = 24
"""Menu items' font size, default font, px. Scope report DRA-125, Values needed, Menu."""

MENU_ITEM_SPACING: Final[int] = 40
"""From one item's top to the next one's, px. Scope report DRA-125, Values needed, Menu."""

MENU_ITEM_TEXTS: Final[Mapping[MenuItem, str]] = MappingProxyType(
    {
        MenuItem.PLAY: "Play",
        MenuItem.INSTRUCTIONS: "Instructions",
        MenuItem.LEADERBOARD: "Leaderboard",
    }
)
"""Each item's label. Scope report DRA-125, Values needed, Menu; 02-game-flow.md, menu_items."""


def draw_menu(surface: pygame.Surface, selection: MenuItem) -> None:
    """Blit the title and the three items onto ``surface``, the marker on ``selection``. Units: px.

    Every line is centered across the width. The title is followed by one blank title line, then
    the items in ``MenuItem`` order, their tops ``MENU_ITEM_SPACING`` apart. The block, from the
    title's top to the last item's bottom (its top plus the item font's ``get_height()``), is
    centered vertically. Needs ``pygame.font`` initialized.
    """
    width, height = surface.get_size()
    title_line: int = screen_font(SCREEN_TITLE_FONT_SIZE).get_linesize()
    block_top: int = (height - _block_height(title_line)) // 2
    _blit_centered(surface, MENU_TITLE_TEXT, SCREEN_TITLE_FONT_SIZE, width, block_top)
    items_top: int = block_top + 2 * title_line
    for index, item in enumerate(MenuItem):
        top: int = items_top + index * MENU_ITEM_SPACING
        _blit_centered(surface, MENU_ITEM_TEXTS[item], MENU_ITEM_FONT_SIZE, width, top)
        if item is selection:
            _blit_marker(surface, MENU_ITEM_TEXTS[item], width, top)


def _block_height(title_line: int) -> int:
    """Return the block's height, px: title line, blank line, items to the last one's bottom."""
    last_gap: int = (len(MenuItem) - 1) * MENU_ITEM_SPACING
    return 2 * title_line + last_gap + screen_font(MENU_ITEM_FONT_SIZE).get_height()


def _blit_centered(surface: pygame.Surface, text: str, size: int, width: int, top: int) -> None:
    """Blit ``text`` at font ``size`` with its center on ``width // 2`` and its top at ``top``."""
    image: pygame.Surface = _render(text, size)
    surface.blit(image, image.get_rect(centerx=width // 2, top=top))


def _blit_marker(surface: pygame.Surface, label: str, width: int, top: int) -> None:
    """Blit the marker at ``top``, its right edge one space left of ``label``'s left edge."""
    label_left: int = _render(label, MENU_ITEM_FONT_SIZE).get_rect(centerx=width // 2).left
    space: int = screen_font(MENU_ITEM_FONT_SIZE).size(" ")[0]
    marker: pygame.Surface = _render(SELECTION_MARKER, MENU_ITEM_FONT_SIZE)
    surface.blit(marker, marker.get_rect(right=label_left - space, top=top))


@cache
def _render(text: str, size: int) -> pygame.Surface:
    """Return ``text`` rendered once at font ``size``, antialiased, in the screen text color."""
    return screen_font(size).render(text, True, SCREEN_TEXT_COLOR)
