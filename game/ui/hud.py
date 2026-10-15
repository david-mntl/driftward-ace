"""HUD: the meters flown top-left and the lives as hearts top-right, on top of the frame.

Source: docs/contracts/systems/hud.md, Interface and Presentation. The view only draws.
It never fills, flips, logs per frame, catches an error, changes the run, or reads the run
mode or a key. The app passes ``below_overlay``.
"""

import logging
from functools import cache

import pygame

from core.run import Run
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

HEART_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Heart color, RGB. Scope report DRA-23, hearts, temporary stand-in approved by the Director,
not in the GDD (UI-01 and UI-02 are TBD)."""

HEART_SIZE: int = 24
"""Heart width and height, px. Scope report DRA-23, hearts, temporary stand-in approved by the
Director, not in the GDD (UI-01 and UI-02 are TBD)."""

HEART_GAP: int = 8
"""Gap between two hearts, px. Scope report DRA-23, hearts, temporary stand-in approved by the
Director, not in the GDD (UI-01 and UI-02 are TBD)."""

HEART_MARGIN: int = 8
"""Gap from the top and right edges to the hearts, px. Scope report DRA-23, hearts, temporary
stand-in approved by the Director, not in the GDD (UI-01 and UI-02 are TBD)."""


def draw_hud(surface: pygame.Surface, run: Run, below_overlay: bool) -> None:
    """Draw the meters readout top-left and one heart per life top-right. Units: pixels.

    The readout is ``<meters> m`` on HUD line 2, top-left at (HUD_MARGIN, hud_top +
    HUD_LINE_SPACING). ``hud_top`` is HUD_TOP, or the debug overlay's text bottom plus
    HUD_OVERLAY_GAP when ``below_overlay`` is True. Line 1 stays empty. The hearts do not
    depend on ``below_overlay``. Needs ``pygame.font`` initialized.
    """
    hud_top: int = HUD_TOP
    if below_overlay:
        hud_top = overlay_text_bottom() + HUD_OVERLAY_GAP
    text: pygame.Surface = _hud_font().render(f"{run.scroll.meters} m", True, HUD_COLOR)
    surface.blit(text, (HUD_MARGIN, hud_top + HUD_LINE_SPACING))
    _draw_hearts(surface, run.lives)


def _draw_hearts(surface: pygame.Surface, lives: int) -> None:
    """Blit one heart into each of slots 0 to ``lives - 1``, slot 0 being the rightmost.

    Slot ``i`` has its box top-left at (width - HEART_MARGIN - HEART_SIZE - i * (HEART_SIZE +
    HEART_GAP), HEART_MARGIN), so a lost life empties the leftmost heart and the others stay.
    """
    heart: pygame.Surface = _heart()
    first_left: int = surface.get_width() - HEART_MARGIN - HEART_SIZE
    for slot in range(lives):
        surface.blit(heart, (first_left - slot * (HEART_SIZE + HEART_GAP), HEART_MARGIN))


@cache
def _heart() -> pygame.Surface:
    """Return the heart, built on the first call and reused after.

    A HEART_SIZE square SRCALPHA surface holding two round lobes on top and a point at the
    bottom center, in HEART_COLOR. The shape reaches the left and right columns and the bottom
    row. Source: hud.md, Presentation, Hearts; 15-tech-constraints.md, rule 5.
    """
    last: int = HEART_SIZE - 1
    radius: int = HEART_SIZE // 4
    lobe_y: int = radius
    shoulder_y: int = radius + 1
    middle: int = HEART_SIZE // 2
    heart: pygame.Surface = pygame.Surface((HEART_SIZE, HEART_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(heart, HEART_COLOR, (radius, lobe_y), radius)
    pygame.draw.circle(heart, HEART_COLOR, (HEART_SIZE - radius, lobe_y), radius)
    point: list[tuple[int, int]] = [
        (0, shoulder_y),
        (last, shoulder_y),
        (middle, last),
        (middle - 1, last),
    ]
    pygame.draw.polygon(heart, HEART_COLOR, point)
    return heart


@cache
def _hud_font() -> pygame.font.Font:
    """Return the HUD font, built on the first call and reused after.

    Default font at HUD_FONT_SIZE. Source: 15-tech-constraints.md, rule 5.
    """
    return pygame.font.Font(None, HUD_FONT_SIZE)
