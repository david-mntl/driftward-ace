"""Game-over screen: a see-through box with a message, the score, an optional name picker, and
RETRY above MENU.

Source: docs/contracts/systems/game-flow.md, Interface (ui/game_over.py) and Presentation,
Game-over screen. The views take plain values (the message, the score, the picker, the selection)
and only draw. They never fill the background, never flip the display, never log per frame, never
catch an error and never read the run mode, a key or the focus. A stand-in until UI-04.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache, lru_cache
from itertools import accumulate
from types import MappingProxyType
from typing import Final

import pygame

from core.game_flow import GameOverChoice
from core.saves import BLANK, NICKNAME_CHARACTERS, GameOverMessage, NamePicker
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
"""Box width and height without the picker, px. Scope report DRA-125, Values needed, Game-over
screen: the DRA-23 box grown to 320 x 160 (stand-in until UI-04)."""

PICKER_BOX_SIZE: Final[tuple[int, int]] = (400, 280)
"""Box width and height with the picker, px. Scope report DRA-126, Values needed, Game-over screen
with the picker: box 400 x 280 (stand-in until UI-04)."""

PICKER_FONT_SIZE: Final[int] = 24
"""Font size of the slots' characters, default font, px. Scope report DRA-126, Values needed,
Game-over screen with the picker: 24 px characters (stand-in until UI-04)."""

PICKER_HINT_TEXT: Final[str] = "Up/Down: letter   Left/Right: slot   Enter: save"
"""The line under the slots while picking. Scope report DRA-126, Values needed, Game-over screen
with the picker (stand-in until UI-04)."""

INACTIVE_TEXT_COLOR: Final[tuple[int, int, int]] = (128, 128, 128)
"""RETRY and MENU before the save, RGB grey. Scope report DRA-126, Values needed, Game-over screen
with the picker (stand-in until UI-04)."""

SLOT_UNDERLINE_COLOR: Final[tuple[int, int, int]] = (128, 128, 128)
"""Every slot's underline, RGB grey. Scope report DRA-126, Values needed, Picker slots (stand-in
until UI-04)."""

CURSOR_COLOR: Final[tuple[int, int, int]] = (255, 255, 255)
"""The outline on the cursor's slot, RGB white. Scope report DRA-126, Values needed, Picker slots
(stand-in until UI-04)."""

SLOT_LINE_WIDTH: Final[int] = 1
"""The underline's and the outline's width, px. docs/reports/DRA-126-away-log.md, Decisions, 4:
the plainest line pygame draws (stand-in until UI-04)."""

MESSAGE_TEXTS: Final[Mapping[GameOverMessage, str]] = MappingProxyType(
    {
        GameOverMessage.NEW_BEST_SCORE: "NEW BEST SCORE",
        GameOverMessage.TOP_3: "TOP 3",
        GameOverMessage.TOP_10: "TOP 10",
        GameOverMessage.GAME_OVER: "GAME OVER",
    }
)
"""The first line, by message. 10-ui.md, game_over_message (locked)."""

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
    """Where the box and the six lines sit on one surface, px.

    ``box_left`` and ``box_top`` are the box's top-left; the other tops are the lines' tops. Without
    the picker the slot row and the hint have no height: their tops equal ``retry_top``.
    """

    box_size: tuple[int, int]
    box_left: int
    box_top: int
    message_top: int
    score_top: int
    slots_top: int
    hint_top: int
    retry_top: int
    menu_top: int


def draw_game_over(
    surface: pygame.Surface,
    message: GameOverMessage = GameOverMessage.GAME_OVER,
    picker_shown: bool = False,
) -> None:
    """Blit the box and the message onto ``surface``, centered. Units: pixels.

    The box is ``PICKER_BOX_SIZE`` when ``picker_shown`` and ``BOX_SIZE`` otherwise, its top-left
    ``((width - box_width) // 2, (height - box_height) // 2)``. ``MESSAGE_TEXTS[message]``, at the
    title size, is centered across the width in the first line's place. The other lines' places
    stay empty. Needs ``pygame.font`` initialized.
    """
    layout: _Layout = _layout(surface.get_size(), picker_shown)
    surface.blit(_box(layout.box_size), (layout.box_left, layout.box_top))
    _blit_centered(surface, _message(message), layout.message_top)


def draw_final_score(surface: pygame.Surface, score: int, picker_shown: bool = False) -> None:
    """Blit the score line onto ``surface``, in the second line's place, centered.

    ``score`` is a whole number >= 0, trusted. The text is ``score_text(score)`` at the body
    size, however long it is. The place is worked out from ``surface.get_size()`` and
    ``picker_shown`` as ``draw_game_over`` does. Needs ``pygame.font`` initialized.
    """
    layout: _Layout = _layout(surface.get_size(), picker_shown)
    _blit_centered(surface, _score_line(score), layout.score_top)


def draw_name_picker(surface: pygame.Surface, picker: NamePicker, picking: bool) -> None:
    """Blit the slot row and, while ``picking``, the cursor's outline and the hint.

    Draws in the picker layout's third and fourth places, so it is called with the picker
    layout's other functions (``picker_shown`` True). Each slot is a cell with its character, a
    grey underline, and a white outline on ``picker.cursor`` only while ``picking``. After the
    save (``picking`` False) the slots stay as picked, and the outline and the hint places stay
    empty. Needs ``pygame.font`` initialized.
    """
    layout: _Layout = _layout(surface.get_size(), True)
    cells: list[pygame.Rect] = _slot_cells(surface.get_width(), layout.slots_top, len(picker.slots))
    for cell, character in zip(cells, picker.slots, strict=True):
        _blit_character(surface, character, cell)
    for cell in cells:
        surface.fill(SLOT_UNDERLINE_COLOR, _underline(cell))
    if not picking:
        return
    pygame.draw.rect(surface, CURSOR_COLOR, cells[picker.cursor], SLOT_LINE_WIDTH)
    _blit_centered(surface, _hint(), layout.hint_top)


def draw_game_over_choices(
    surface: pygame.Surface,
    selection: GameOverChoice,
    picker_shown: bool = False,
    active: bool = True,
) -> None:
    """Blit RETRY and MENU onto ``surface`` in the last two places, the marker on one.

    Both labels are centered at the body size and never move with ``selection``. While ``active``
    they are white and the marker is in the same font, with the label's top, its right edge one
    space left of the label's left edge. While not ``active`` (the picker still takes the keys)
    both are ``INACTIVE_TEXT_COLOR`` and no marker is drawn. The place is worked out from
    ``surface.get_size()`` and ``picker_shown`` as ``draw_game_over`` does. Needs ``pygame.font``
    initialized.
    """
    layout: _Layout = _layout(surface.get_size(), picker_shown)
    tops: dict[GameOverChoice, int] = {
        GameOverChoice.RETRY: layout.retry_top,
        GameOverChoice.MENU: layout.menu_top,
    }
    color: tuple[int, int, int] = SCREEN_TEXT_COLOR if active else INACTIVE_TEXT_COLOR
    for choice in GameOverChoice:
        label: pygame.Surface = _label(_CHOICE_TEXTS[choice], color)
        _blit_centered(surface, label, tops[choice])
        if active and choice is selection:
            _blit_marker(surface, label, tops[choice])


def _layout(size: tuple[int, int], picker_shown: bool) -> _Layout:
    """Return the box origin and the line tops for a surface of ``size``.

    The block (message, score, [slot row, hint,] RETRY line heights, then the MENU font's
    ``get_height()``) is centered vertically in the box. Lines are stacked by their fonts'
    ``get_linesize()``; the slot row and the hint have height 0 without the picker.
    """
    width, height = size
    box_size: tuple[int, int] = PICKER_BOX_SIZE if picker_shown else BOX_SIZE
    title_line: int = screen_font(SCREEN_TITLE_FONT_SIZE).get_linesize()
    body_line: int = screen_font(SCREEN_BODY_FONT_SIZE).get_linesize()
    slots_line: int = screen_font(PICKER_FONT_SIZE).get_linesize() if picker_shown else 0
    hint_line: int = body_line if picker_shown else 0
    heights: list[int] = [title_line, body_line, slots_line, hint_line, body_line]
    block: int = sum(heights) + screen_font(SCREEN_BODY_FONT_SIZE).get_height()
    box_left: int = (width - box_size[0]) // 2
    box_top: int = (height - box_size[1]) // 2
    message_top: int = box_top + (box_size[1] - block) // 2
    tops: list[int] = [message_top, *(message_top + h for h in accumulate(heights))]
    return _Layout(box_size, box_left, box_top, *tops)


def _slot_cells(surface_width: int, top: int, count: int) -> list[pygame.Rect]:
    """Return ``count`` cells side by side, one space apart, centered on ``surface_width // 2``.

    Every cell is as wide as the widest character of ``NICKNAME_CHARACTERS`` and as tall as the
    slot row, and its top is ``top``.
    """
    font: pygame.font.Font = screen_font(PICKER_FONT_SIZE)
    cell_width: int = _cell_width()
    gap: int = font.size(" ")[0]
    row: pygame.Rect = pygame.Rect(0, top, count * cell_width + (count - 1) * gap, 0)
    row.centerx = surface_width // 2
    return [
        pygame.Rect(row.left + i * (cell_width + gap), top, cell_width, font.get_linesize())
        for i in range(count)
    ]


def _underline(cell: pygame.Rect) -> pygame.Rect:
    """Return the cell's bottom ``SLOT_LINE_WIDTH`` rows, its full width."""
    return pygame.Rect(cell.left, cell.bottom - SLOT_LINE_WIDTH, cell.width, SLOT_LINE_WIDTH)


def _blit_character(surface: pygame.Surface, character: str, cell: pygame.Rect) -> None:
    """Blit ``character`` centered across ``cell``, its top on the cell top. A blank draws none."""
    if character == BLANK:
        return
    image: pygame.Surface = _picker_character(character)
    surface.blit(image, image.get_rect(centerx=cell.centerx, top=cell.top))


def _blit_centered(surface: pygame.Surface, image: pygame.Surface, top: int) -> None:
    """Blit ``image`` with its center on the surface's ``width // 2`` and its top at ``top``."""
    surface.blit(image, image.get_rect(centerx=surface.get_width() // 2, top=top))


def _blit_marker(surface: pygame.Surface, label: pygame.Surface, top: int) -> None:
    """Blit the marker at ``top``, its right edge one space left of the centered ``label``."""
    label_left: int = label.get_rect(centerx=surface.get_width() // 2).left
    space: int = screen_font(SCREEN_BODY_FONT_SIZE).size(" ")[0]
    marker: pygame.Surface = _label(SELECTION_MARKER, SCREEN_TEXT_COLOR)
    surface.blit(marker, marker.get_rect(right=label_left - space, top=top))


@cache
def _box(size: tuple[int, int]) -> pygame.Surface:
    """Return the box surface of ``size``, filled once with ``SCREEN_BOX_COLOR``, no border."""
    box: pygame.Surface = pygame.Surface(size, pygame.SRCALPHA)
    box.fill(SCREEN_BOX_COLOR)
    return box


@cache
def _message(message: GameOverMessage) -> pygame.Surface:
    """Return ``MESSAGE_TEXTS[message]`` rendered once at the title size, antialiased."""
    return screen_font(SCREEN_TITLE_FONT_SIZE).render(
        MESSAGE_TEXTS[message], True, SCREEN_TEXT_COLOR
    )


@cache
def _label(text: str, color: tuple[int, int, int]) -> pygame.Surface:
    """Return ``text`` rendered once at the body size in ``color``, antialiased."""
    return screen_font(SCREEN_BODY_FONT_SIZE).render(text, True, color)


def _hint() -> pygame.Surface:
    """Return ``PICKER_HINT_TEXT`` rendered once at the body size, antialiased."""
    return _label(PICKER_HINT_TEXT, SCREEN_TEXT_COLOR)


@cache
def _picker_character(character: str) -> pygame.Surface:
    """Return ``character`` rendered once at the picker size in ``SCREEN_TEXT_COLOR``."""
    return screen_font(PICKER_FONT_SIZE).render(character, True, SCREEN_TEXT_COLOR)


@cache
def _cell_width() -> int:
    """Return the widest character of ``NICKNAME_CHARACTERS`` at the picker size, px."""
    font: pygame.font.Font = screen_font(PICKER_FONT_SIZE)
    return max(font.size(character)[0] for character in NICKNAME_CHARACTERS)


@lru_cache(maxsize=1)
def _score_line(score: int) -> pygame.Surface:
    """Return the score line rendered for ``score``, antialiased.

    Holds the last score only: the score is frozen while the screen shows, so it renders once.
    """
    return screen_font(SCREEN_BODY_FONT_SIZE).render(score_text(score), True, SCREEN_TEXT_COLOR)
