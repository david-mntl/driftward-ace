"""Pause box: a see-through black box with the word PAUSE, centered.

Source: docs/contracts/systems/game-flow.md, Interface (ui/pause_box.py) and Presentation, Pause
box. The view takes nothing but the surface and only draws. It never fills the background, never
flips the display, never logs per frame, never catches an error and never reads the run mode, a
key or the focus. A stand-in until UI-04.
"""

import logging
from functools import cache
from typing import Final

import pygame

from ui.screen_look import (
    SCREEN_BOX_COLOR,
    SCREEN_TEXT_COLOR,
    SCREEN_TITLE_FONT_SIZE,
    screen_font,
)

log = logging.getLogger(__name__)

PAUSE_BOX_SIZE: Final[tuple[int, int]] = (320, 120)
"""Box width and height, px. Scope report DRA-125, Values needed, Pause box: the DRA-23 box size
(stand-in until UI-04)."""

PAUSE_TEXT: Final[str] = "PAUSE"
"""The box's word. Scope report DRA-125, Values needed, Pause box; 10-ui.md, pause_box (locked
content)."""


def draw_pause_box(surface: pygame.Surface) -> None:
    """Blit the box and ``PAUSE_TEXT`` onto ``surface``, both centered. Units: px.

    The box's top-left is ``((width - box_width) // 2, (height - box_height) // 2)``. The text, at
    the title size, has its rect centered on the box's center. The fill is see-through, so what is
    on ``surface`` shows through. Needs ``pygame.font`` initialized.
    """
    width, height = surface.get_size()
    box: pygame.Surface = _box()
    box_rect: pygame.Rect = box.get_rect(
        topleft=((width - PAUSE_BOX_SIZE[0]) // 2, (height - PAUSE_BOX_SIZE[1]) // 2)
    )
    surface.blit(box, box_rect)
    text: pygame.Surface = _text()
    surface.blit(text, text.get_rect(center=box_rect.center))


@cache
def _box() -> pygame.Surface:
    """Return the box surface, filled once with ``SCREEN_BOX_COLOR``, no border."""
    box: pygame.Surface = pygame.Surface(PAUSE_BOX_SIZE, pygame.SRCALPHA)
    box.fill(SCREEN_BOX_COLOR)
    return box


@cache
def _text() -> pygame.Surface:
    """Return ``PAUSE_TEXT`` rendered once at the title size, antialiased."""
    return screen_font(SCREEN_TITLE_FONT_SIZE).render(PAUSE_TEXT, True, SCREEN_TEXT_COLOR)
