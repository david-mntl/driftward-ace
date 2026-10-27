"""Instructions page: the title, six sections with a stand-in icon, and the footer.

Source: docs/contracts/systems/game-flow.md, Interface (ui/instructions.py) and Presentation,
Instructions page. The view takes nothing but the surface and only draws. It never fills the
background, never flips the display, never logs per frame, never catches an error and never reads
the run mode, a key or the focus. A stand-in until UI-03 and UI-04.
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

INSTRUCTIONS_TITLE_TEXT: Final[str] = "HOW TO PLAY"
"""Page title. Scope report DRA-125, Values needed, Instructions page (stand-in until UI-03)."""

INSTRUCTION_SECTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("FLY", "Arrows thrust. Let go and you keep drifting. Gravity never stops."),
    ("PAUSE", "Enter or Space pauses. Press it again to go on."),
    ("GRAZE", "Skim past a hazard without touching it to score points."),
    ("WARNING", "A warning shows where a hazard will come in. Get clear."),
    ("FALL", "Fall off the bottom and you lose a life."),
    ("COINS", "Coins are points. The good ones sit near danger."),
)
"""The six (title, line) pairs, in order. Scope report DRA-125, Values needed, Instructions page."""

ICON_SIZE: Final[int] = 16
"""The icon square's side, px. Scope report DRA-125, Values needed, Instructions page."""

ICON_LINE_WIDTH: Final[int] = 1
"""The icon's outline width, px: the plainest outline pygame draws. Contract: game-flow.md,
Presentation, Instructions page (stand-in until UI-03)."""


def draw_instructions(surface: pygame.Surface) -> None:
    """Blit the title, the six sections and the footer onto ``surface``. Units: px.

    Rows run from the block's top: title, a blank body line, then per section a heading row (icon,
    one space, title; centered together) and its line, with a blank body line between sections.
    The footer's top is two body lines above the bottom. The block, from the title's top to the
    last line's bottom, is centered vertically between the surface's top and the footer's top.
    Needs ``pygame.font`` initialized.
    """
    width, height = surface.get_size()
    body_line: int = screen_font(SCREEN_BODY_FONT_SIZE).get_linesize()
    heading_height: int = max(ICON_SIZE, body_line)
    footer_top: int = height - 2 * body_line
    top: int = (footer_top - _block_height(body_line, heading_height)) // 2
    _blit_centered(surface, INSTRUCTIONS_TITLE_TEXT, SCREEN_TITLE_FONT_SIZE, width, top)
    top += screen_font(SCREEN_TITLE_FONT_SIZE).get_linesize() + body_line
    for title, line in INSTRUCTION_SECTIONS:
        _draw_heading(surface, title, width, top, heading_height)
        top += heading_height
        _blit_centered(surface, line, SCREEN_BODY_FONT_SIZE, width, top)
        top += 2 * body_line
    _blit_centered(surface, BACK_PROMPT_TEXT, SCREEN_BODY_FONT_SIZE, width, footer_top)


def _block_height(body_line: int, heading_height: int) -> int:
    """Return the block's height, px: title, blank line, sections to the last line's bottom."""
    sections: int = len(INSTRUCTION_SECTIONS)
    section_rows: int = sections * (heading_height + body_line)
    blank_lines: int = 1 + (sections - 1)
    return (
        screen_font(SCREEN_TITLE_FONT_SIZE).get_linesize() + blank_lines * body_line + section_rows
    )


def _draw_heading(
    surface: pygame.Surface, title: str, width: int, top: int, row_height: int
) -> None:
    """Draw the icon and ``title`` in a row at ``top``, centered together, each centered in it."""
    image: pygame.Surface = _render(title, SCREEN_BODY_FONT_SIZE)
    space: int = screen_font(SCREEN_BODY_FONT_SIZE).size(" ")[0]
    left: int = (width - (ICON_SIZE + space + image.get_width())) // 2
    centery: int = top + row_height // 2
    icon: pygame.Rect = pygame.Rect(left, centery - ICON_SIZE // 2, ICON_SIZE, ICON_SIZE)
    pygame.draw.rect(surface, SCREEN_TEXT_COLOR, icon, ICON_LINE_WIDTH)
    surface.blit(image, image.get_rect(left=icon.right + space, centery=centery))


def _blit_centered(surface: pygame.Surface, text: str, size: int, width: int, top: int) -> None:
    """Blit ``text`` at font ``size`` with its center on ``width // 2`` and its top at ``top``."""
    image: pygame.Surface = _render(text, size)
    surface.blit(image, image.get_rect(centerx=width // 2, top=top))


@cache
def _render(text: str, size: int) -> pygame.Surface:
    """Return ``text`` rendered once at font ``size``, antialiased, in the screen text color."""
    return screen_font(size).render(text, True, SCREEN_TEXT_COLOR)
