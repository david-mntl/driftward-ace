"""HUD: the meters flown, drawn top-left on top of the frame.

Source: docs/contracts/DRA-13/DRA-13-hud.md, Interface and Presentation. The view only draws.
It never fills, flips, logs per frame, catches an error, changes the scroll, or reads the run
mode or a key. The app passes ``below_overlay``.
"""

import logging
from functools import cache

import pygame

from core.scroll import Scroll
from ui.debug_overlay import overlay_text_bottom

log = logging.getLogger(__name__)

HUD_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Readout text color, RGB. Scope report DRA-13, temporary stand-in approved by the Director,
not in the GDD (UI-01 is TBD)."""

HUD_FONT_SIZE: int = 16
"""Readout text size, default font, px. Scope report DRA-13, temporary stand-in (readout text),
not in the GDD (UI-01 is TBD)."""

HUD_MARGIN: int = 4
"""Gap from the left edge to the text, px. Scope report DRA-13, HUD layout approved by the
Director, not in the GDD (UI-01 is TBD)."""

HUD_LINE_SPACING: int = 20
"""Distance between HUD line tops, px. Scope report DRA-13, HUD layout approved by the
Director, not in the GDD (UI-01 is TBD)."""

HUD_TOP: int = 4
"""Top of HUD line 1 in normal mode, px. Scope report DRA-13, HUD layout approved by the
Director, not in the GDD (UI-01 is TBD)."""

HUD_OVERLAY_GAP: int = 4
"""Gap between the overlay's text and HUD line 1 in debug mode, px. Scope report DRA-13, HUD
layout approved by the Director, not in the GDD (UI-01 is TBD)."""


def draw_hud(surface: pygame.Surface, scroll: Scroll, below_overlay: bool) -> None:
    """Draw ``<meters> m`` on HUD line 2, top-left at (HUD_MARGIN, hud_top + HUD_LINE_SPACING).

    ``hud_top`` is HUD_TOP, or the debug overlay's text bottom plus HUD_OVERLAY_GAP when
    ``below_overlay`` is True. Line 1 stays empty. Units: pixels.
    Needs ``pygame.font`` initialized.
    """
    hud_top: int = HUD_TOP
    if below_overlay:
        hud_top = overlay_text_bottom() + HUD_OVERLAY_GAP
    text: pygame.Surface = _hud_font().render(f"{scroll.meters} m", True, HUD_COLOR)
    surface.blit(text, (HUD_MARGIN, hud_top + HUD_LINE_SPACING))


@cache
def _hud_font() -> pygame.font.Font:
    """Return the HUD font, built on the first call and reused after.

    Default font at HUD_FONT_SIZE. Source: 15-tech-constraints.md, rule 5.
    """
    return pygame.font.Font(None, HUD_FONT_SIZE)
