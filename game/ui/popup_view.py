"""Points popup: the text a pickup leaves where it was collected, rising until it ends.

Source: docs/contracts/systems/run.md, Interface and Presentation, Points popup. The view reads
only the popup it is given. It never fills, flips, logs per frame, catches an error, changes the
popup, or reads the run mode or a key. The app draws each popup in ``run.popups``, in order.
"""

import logging
from functools import cache
from typing import Final

import pygame

from core.popup import PointsPopup

log = logging.getLogger(__name__)

POPUP_COLOR: Final[tuple[int, int, int]] = (255, 80, 150)
"""Popup text color, RGB. drifters/04-coin.md, popup_color (guess)."""

POPUP_FONT_SIZE: Final[int] = 16
"""Popup text size, default font, px. Scope report DRA-62, Limits: the HUD's font size."""


def popup_text(points: int) -> str:
    """Return ``+`` and the points' digits, e.g. ``+50``. ``points`` is a whole number >= 0."""
    return f"+{points}"


def draw_points_popup(surface: pygame.Surface, popup: PointsPopup) -> None:
    """Blit the popup's text centered on ``(round(popup.x), round(popup.y))``. Units: pixels.

    Needs ``pygame.font`` initialized. The place comes from core; nothing is moved here.
    """
    text: pygame.Surface = _popup_surface(popup.points)
    center: tuple[int, int] = (round(popup.x), round(popup.y))
    surface.blit(text, text.get_rect(center=center))


@cache
def _popup_surface(points: int) -> pygame.Surface:
    """Return the text for ``points``, rendered once per value and kept.

    Source: run.md, Presentation, Points popup, Cache; 15-tech-constraints.md, rule 5.
    """
    return _popup_font().render(popup_text(points), True, POPUP_COLOR)


@cache
def _popup_font() -> pygame.font.Font:
    """Return the popup font, built on the first call and reused after.

    Default font at POPUP_FONT_SIZE. Source: 15-tech-constraints.md, rule 5.
    """
    return pygame.font.Font(None, POPUP_FONT_SIZE)
