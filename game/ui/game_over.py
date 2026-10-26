"""Game-over screen: a see-through box with GAME OVER, the score, and RETRY above MENU.

Source: docs/contracts/systems/game-flow.md, Interface (ui/game_over.py) and Presentation,
Game-over screen. The views take plain values (the score, the selection) and only draw. They never
fill the background, never flip the display, never log per frame, never catch an error and never
read the run mode, a key or the focus. A stand-in until UI-04.
"""

import logging
from dataclasses import dataclass
from functools import cache, lru_cache
from typing import Final

import pygame

from core.game_flow import GameOverChoice
from ui.score_text import score_text
from ui.screen_look import (
    SCREEN_BODY_FONT_SIZE,
    SCREEN_BOX_COLOR,
    SCREEN_TEXT_COLOR,
    SCREEN_TITLE_FONT_SIZE,
    SELECTION_MARKER,
    screen_font,
)

log = logging.getLogger(__name__)

BOX_SIZE: tuple[int, int] = (320, 160)
"""Box width and height, px. Scope report DRA-125, Values needed, Game-over screen: the DRA-23 box
grown to 320 x 160 (stand-in until UI-04)."""

TITLE_TEXT: str = "GAME OVER"
"""Title line, the only message until DRA-126. Scope report DRA-125, Values needed, Game-over
screen; 10-ui.md, game_over_message."""

RETRY_TEXT: Final[str] = "RETRY"
"""First choice's label. Scope report DRA-125, Values needed, Game-over screen; 02-game-flow.md,
game_over_choices (locked)."""

MENU_TEXT: Final[str] = "MENU"
"""Second choice's label. Scope report DRA-125, Values needed, Game-over screen; 02-game-flow.md,
game_over_choices (locked)."""

_CHOICE_TEXTS: Final[dict[GameOverChoice, str]] = {
    GameOverChoice.RETRY: RETRY_TEXT,
    GameOverChoice.MENU: MENU_TEXT,
}


@dataclass(frozen=True, slots=True)
class _Layout:
    """Where the box and the four lines sit on one surface, px.

    ``box_left`` and ``box_top`` are the box's top-left; the other tops are the four lines' tops.
    """

    box_left: int
    box_top: int
    title_top: int
    score_top: int
    retry_top: int
    menu_top: int


def draw_game_over(surface: pygame.Surface) -> None:
    """Blit the box and the title onto ``surface``, centered. Units: pixels.

    The box top-left is ``((width - box_width) // 2, (height - box_height) // 2)``. The title,
    at the title size, is centered across the width in the first line's place. The other three
    places stay empty. Needs ``pygame.font`` initialized.
    """
    layout: _Layout = _layout(surface.get_size())
    surface.blit(_box(), (layout.box_left, layout.box_top))
    _blit_centered(surface, _title(), layout.title_top)


def draw_final_score(surface: pygame.Surface, score: int) -> None:
    """Blit the score line onto ``surface``, in the second line's place, centered.

    ``score`` is a whole number >= 0, trusted. The text is ``score_text(score)`` at the body
    size, however long it is. The place is worked out from ``surface.get_size()`` as
    ``draw_game_over`` does. Needs ``pygame.font`` initialized.
    """
    layout: _Layout = _layout(surface.get_size())
    _blit_centered(surface, _score_line(score), layout.score_top)


def draw_game_over_choices(surface: pygame.Surface, selection: GameOverChoice) -> None:
    """Blit RETRY and MENU onto ``surface`` in the third and fourth places, the marker on one.

    Both labels are centered at the body size and never move with ``selection``. The marker is
    in the same font, with the label's top, its right edge one space left of the label's left
    edge. The place is worked out from ``surface.get_size()`` as ``draw_game_over`` does. Needs
    ``pygame.font`` initialized.
    """
    layout: _Layout = _layout(surface.get_size())
    tops: dict[GameOverChoice, int] = {
        GameOverChoice.RETRY: layout.retry_top,
        GameOverChoice.MENU: layout.menu_top,
    }
    for choice in GameOverChoice:
        label: pygame.Surface = _label(_CHOICE_TEXTS[choice])
        _blit_centered(surface, label, tops[choice])
        if choice is selection:
            _blit_marker(surface, label, tops[choice])


def _layout(size: tuple[int, int]) -> _Layout:
    """Return the box origin and the four tops for a surface of ``size``.

    The block (title line + score line + RETRY line, then the MENU font's ``get_height()``) is
    centered vertically in the box. Lines are stacked by their fonts' ``get_linesize()``.
    """
    width, height = size
    box_left: int = (width - BOX_SIZE[0]) // 2
    box_top: int = (height - BOX_SIZE[1]) // 2
    title_line: int = screen_font(SCREEN_TITLE_FONT_SIZE).get_linesize()
    body_line: int = screen_font(SCREEN_BODY_FONT_SIZE).get_linesize()
    block: int = title_line + 2 * body_line + screen_font(SCREEN_BODY_FONT_SIZE).get_height()
    title_top: int = box_top + (BOX_SIZE[1] - block) // 2
    score_top: int = title_top + title_line
    retry_top: int = score_top + body_line
    return _Layout(box_left, box_top, title_top, score_top, retry_top, retry_top + body_line)


def _blit_centered(surface: pygame.Surface, image: pygame.Surface, top: int) -> None:
    """Blit ``image`` with its center on the surface's ``width // 2`` and its top at ``top``."""
    surface.blit(image, image.get_rect(centerx=surface.get_width() // 2, top=top))


def _blit_marker(surface: pygame.Surface, label: pygame.Surface, top: int) -> None:
    """Blit the marker at ``top``, its right edge one space left of the centered ``label``."""
    label_left: int = label.get_rect(centerx=surface.get_width() // 2).left
    space: int = screen_font(SCREEN_BODY_FONT_SIZE).size(" ")[0]
    marker: pygame.Surface = _label(SELECTION_MARKER)
    surface.blit(marker, marker.get_rect(right=label_left - space, top=top))


@cache
def _box() -> pygame.Surface:
    """Return the box surface, filled once with ``SCREEN_BOX_COLOR``, no border."""
    box: pygame.Surface = pygame.Surface(BOX_SIZE, pygame.SRCALPHA)
    box.fill(SCREEN_BOX_COLOR)
    return box


@cache
def _title() -> pygame.Surface:
    """Return ``TITLE_TEXT`` rendered once at the title size, antialiased."""
    return screen_font(SCREEN_TITLE_FONT_SIZE).render(TITLE_TEXT, True, SCREEN_TEXT_COLOR)


@cache
def _label(text: str) -> pygame.Surface:
    """Return ``text`` rendered once at the body size, antialiased."""
    return screen_font(SCREEN_BODY_FONT_SIZE).render(text, True, SCREEN_TEXT_COLOR)


@lru_cache(maxsize=1)
def _score_line(score: int) -> pygame.Surface:
    """Return the score line rendered for ``score``, antialiased.

    Holds the last score only: the score is frozen while the screen shows, so it renders once.
    """
    return screen_font(SCREEN_BODY_FONT_SIZE).render(score_text(score), True, SCREEN_TEXT_COLOR)
