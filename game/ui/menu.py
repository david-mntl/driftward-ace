"""Menu screen: the title, the three items with the selected one lit and bracketed, the hint.

Source: docs/contracts/systems/screens.md, Interface (ui/menu.py); 10-ui.md, `menu_screen`,
`menu_look` and `menu_hint`. The view takes the look and the selection as a plain value and only
draws. It never fills the background, never flips the display, never logs per frame, never catches
an error and never reads the run mode, a key or the focus.
"""

import logging
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

import pygame

from core.game_flow import MenuItem
from ui.screen_look import ScreenLook

log = logging.getLogger(__name__)

MENU_TITLE_TEXT: Final[str] = "DRIFTWARD ACE"
"""Menu title."""

MENU_HINT_TEXT: Final[str] = "Up & Down to choose. Enter to start."
"""The line under the items. 10-ui.md, menu_hint."""

MENU_ITEM_TEXTS: Final[Mapping[MenuItem, str]] = MappingProxyType(
    {
        MenuItem.PLAY: "PLAY",
        MenuItem.INSTRUCTIONS: "INSTRUCTIONS",
        MenuItem.LEADERBOARD: "LEADERBOARD",
    }
)
"""Each item's label, in capitals like RETRY and MENU. 02-game-flow.md, menu_items."""

HINT_ALPHA: Final[int] = 153
"""Brightness of the hint line, 0..255: about 60%, like the other key hints. Mock-up value."""


def draw_menu(surface: pygame.Surface, look: ScreenLook, selection: MenuItem) -> None:
    """Draw the title, the three items, the hint and the rulers onto ``surface``. Units: px.

    The title, ``title_gap``, then the items (``item_w`` by ``item_h``, ``item_gap`` apart, in
    ``MenuItem`` order) are one block, centered on both axes. ``selection`` is lit and bracketed,
    the others dim. The hint is centered, ``hint_bottom`` px above the bottom edge. Needs
    ``pygame.font`` initialized.
    """
    rules = look.rules.menu
    width, height = surface.get_size()
    palette = look.palette
    look.blit_rulers(surface)
    title_h: int = look.text_size(MENU_TITLE_TEXT, "menu_title")[1]
    count: int = len(MenuItem)
    block: int = title_h + rules.title_gap + count * rules.item_h + (count - 1) * rules.item_gap
    top: int = (height - block) // 2
    look.blit_text(
        surface,
        MENU_TITLE_TEXT,
        "menu_title",
        palette["plating"],
        {"midtop": (width // 2, top)},
    )
    items_top: int = top + title_h + rules.title_gap
    for index, item in enumerate(MenuItem):
        rect: pygame.Rect = pygame.Rect(0, 0, rules.item_w, rules.item_h)
        rect.midtop = (width // 2, items_top + index * (rules.item_h + rules.item_gap))
        state: str = "selected" if item is selection else "dim"
        look.blit_choice(surface, MENU_ITEM_TEXTS[item], rect, "menu_item", state)
    look.blit_text(
        surface,
        MENU_HINT_TEXT,
        "hint",
        palette["plating"],
        {"midbottom": (width // 2, height - rules.hint_bottom)},
        glow=False,
        alpha=HINT_ALPHA,
    )
