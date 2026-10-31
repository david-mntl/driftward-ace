"""Pause box: a glass box with the word PAUSE and the ENTER and SPACE keys, centered.

Source: docs/contracts/systems/screens.md, Interface (ui/pause_box.py); 10-ui.md, `pause_box` and
`pause_look`. The view takes the surface and the look and only draws. It never fills the
background, never flips the display, never logs per frame, never catches an error and never reads
the run mode, a key or the focus.
"""

import logging
from typing import Final

import pygame

from ui.screen_look import PLAY_SIGN, ScreenLook

log = logging.getLogger(__name__)

PAUSE_TEXT: Final[str] = "PAUSE"
"""The box's word. 10-ui.md, pause_box (locked content)."""

PAUSE_KEYS: Final[tuple[str, ...]] = ("ENTER", "SPACE")
"""The keys that resume, shown under the word with a play sign. 10-ui.md, pause_box."""


def draw_pause_box(surface: pygame.Surface, look: ScreenLook) -> None:
    """Draw the box centered on ``surface``, then the word and the key caps centered in it. px.

    The word and the key row are one block, ``pause.gap`` apart, centered vertically in the box.
    Needs ``pygame.font`` initialized.
    """
    pause = look.rules.pause
    box: pygame.Rect = pygame.Rect(0, 0, pause.w, pause.h)
    box.center = surface.get_rect().center
    look.glass(surface, box, pause.blur)
    title_h: int = look.text_size(PAUSE_TEXT, "title")[1]
    top: int = box.centery - (title_h + pause.gap + look.rules.keycap.h) // 2
    look.blit_text(
        surface, PAUSE_TEXT, "title", look.palette["plating"], {"midtop": (box.centerx, top)}
    )
    look.blit_keys(
        surface, PAUSE_KEYS, PLAY_SIGN, {"midtop": (box.centerx, top + title_h + pause.gap)}
    )
