"""Error screen: shown once when an unexpected error stops the game.

Source: 10-ui.md, error_screen, error_text_font, error_layout, error_debug_line,
error_text_color, debug_text_font. The view only draws. It never reads the run mode,
never flips the display and never catches an error.
"""

import logging

import pygame

from ui.look import BACKGROUND

log = logging.getLogger(__name__)

MESSAGE: str = "Something broke. Reload the page."
"""Main line. Source: 10-ui.md, error_screen (guess)."""

MESSAGE_FONT_SIZE: int = 24
"""Main line font size, default font, px. Source: 10-ui.md, error_text_font (guess)."""

DETAIL_FONT_SIZE: int = 16
"""Detail line font size, default font, px. Source: 10-ui.md, debug_text_font (guess)."""

TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Text color, RGB. Source: 10-ui.md, error_text_color (guess)."""


def draw_error_screen(surface: pygame.Surface, detail: str | None) -> None:
    """Fill the surface with BACKGROUND and draw the error text centered on it.

    The main line is centered on the surface. If ``detail`` is a string, it is drawn
    centered horizontally, its top one main-font line-height below the main line's top,
    cut from the end until it fits the surface width. Units: pixels.
    Needs ``pygame.font`` initialized; raises if it isn't.
    """
    surface.fill(BACKGROUND)
    message_font: pygame.font.Font = pygame.font.Font(None, MESSAGE_FONT_SIZE)
    message: pygame.Surface = message_font.render(MESSAGE, True, TEXT_COLOR)
    message_rect: pygame.Rect = message.get_rect(center=surface.get_rect().center)
    surface.blit(message, message_rect)
    if detail is None:
        return
    detail_font: pygame.font.Font = pygame.font.Font(None, DETAIL_FONT_SIZE)
    fitted: str = _fit_to_width(detail, detail_font, surface.get_width())
    line: pygame.Surface = detail_font.render(fitted, True, TEXT_COLOR)
    line_top: int = message_rect.top + message_font.get_linesize()
    surface.blit(line, line.get_rect(centerx=surface.get_width() // 2, top=line_top))


def _fit_to_width(text: str, font: pygame.font.Font, max_width: int) -> str:
    """Return ``text`` cut from the end, one character at a time, until it fits ``max_width``.

    No ellipsis. Source: 10-ui.md, error_debug_line (guess).
    """
    fitted: str = text
    while fitted and font.size(fitted)[0] > max_width:
        fitted = fitted[:-1]
    if len(fitted) < len(text):
        log.debug("error detail cut from %s to %s characters", len(text), len(fitted))
    return fitted
