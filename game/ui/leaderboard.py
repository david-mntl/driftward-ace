"""Leaderboard page: the title, the rows or the empty-list line, and the footer.

Source: docs/contracts/systems/game-flow.md, Interface (ui/leaderboard.py) and Presentation,
Leaderboard page. The view takes the surface and the saved entries and only draws. It never fills
the background, never flips the display, never logs per frame, never catches an error and never
reads the run mode, a key or the focus. A stand-in until UI-03 and UI-04.
"""

import logging
from collections.abc import Sequence
from functools import cache
from itertools import accumulate
from typing import Final

import pygame

from core.saves import ScoreEntry
from ui.score_text import group_digits
from ui.screen_look import (
    BACK_PROMPT_TEXT,
    SCREEN_BODY_FONT_SIZE,
    SCREEN_TEXT_COLOR,
    SCREEN_TITLE_FONT_SIZE,
    screen_font,
)

log = logging.getLogger(__name__)

LEADERBOARD_TITLE_TEXT: Final[str] = "LEADERBOARD"
"""Page title. Scope report DRA-125, Values needed, Leaderboard page (stand-in until UI-03)."""

LEADERBOARD_EMPTY_TEXT: Final[str] = "No scores yet."
"""The line an empty top 10 shows. Scope report DRA-125, Values needed, Leaderboard page."""

PLACE_FORMAT: Final[str] = "{}."
"""The place cell, formatted with the place number (``1.``). Scope report DRA-126, Values needed,
Leaderboard rows."""

LEVEL_LABEL: Final[str] = "LV"
"""Label before the level reached (``LV 3``). Scope report DRA-126, Values needed, Leaderboard
rows."""

ROW_SPACING: Final[int] = 24
"""Px from one row's top to the next one's. Scope report DRA-126, Values needed, Leaderboard
rows (16 px text, 24 px apart)."""

COLUMN_GAP: Final[int] = 24
"""Px between two columns. docs/reports/DRA-126-away-log.md, Decisions, 5 (a stand-in, not in the
GDD)."""

_PLACE_COLUMN: Final[int] = 0
_SCORE_COLUMN: Final[int] = 2
_RIGHT_ALIGNED: Final[tuple[int, ...]] = (_PLACE_COLUMN, _SCORE_COLUMN)
"""The columns whose cells end on the column's right edge; the others start on its left edge."""


def draw_leaderboard(surface: pygame.Surface, entries: Sequence[ScoreEntry] = ()) -> None:
    """Blit the title, the rows (or the empty-list line) and the footer onto ``surface``. Units: px.

    Entry ``i`` is place ``i + 1``. The block is the title, a blank body line, then the rows, or
    the empty-list line when ``entries`` is empty. It is centered vertically between the surface's
    top and the footer's top. The footer sits where the instructions page puts it: its top two
    body lines above the bottom. Needs ``pygame.font`` initialized.
    """
    width, height = surface.get_size()
    body_line: int = screen_font(SCREEN_BODY_FONT_SIZE).get_linesize()
    title_line: int = screen_font(SCREEN_TITLE_FONT_SIZE).get_linesize()
    footer_top: int = height - 2 * body_line
    rows_height: int = body_line + (max(len(entries), 1) - 1) * ROW_SPACING
    top: int = (footer_top - (title_line + body_line + rows_height)) // 2
    _blit_centered(surface, LEADERBOARD_TITLE_TEXT, SCREEN_TITLE_FONT_SIZE, width, top)
    top += title_line + body_line
    if entries:
        _draw_rows(surface, entries, width, top)
    else:
        _blit_centered(surface, LEADERBOARD_EMPTY_TEXT, SCREEN_BODY_FONT_SIZE, width, top)
    _blit_centered(surface, BACK_PROMPT_TEXT, SCREEN_BODY_FONT_SIZE, width, footer_top)


def _draw_rows(
    surface: pygame.Surface, entries: Sequence[ScoreEntry], width: int, top: int
) -> None:
    """Blit one row per entry from ``top``, ``ROW_SPACING`` apart, the table centered on ``width``.

    Each column is as wide as its widest cell. The place and the score are right-aligned in their
    columns, the nickname and the level left-aligned.
    """
    rows: list[tuple[pygame.Surface, ...]] = [
        _row_cells(place, entry) for place, entry in enumerate(entries, start=1)
    ]
    widths: list[int] = [
        max(row[column].get_width() for row in rows) for column in range(len(rows[0]))
    ]
    lefts: list[int] = _column_lefts(widths, width)
    for index, row in enumerate(rows):
        _blit_row(surface, row, lefts, widths, top + index * ROW_SPACING)


def _blit_row(
    surface: pygame.Surface,
    row: Sequence[pygame.Surface],
    lefts: Sequence[int],
    widths: Sequence[int],
    top: int,
) -> None:
    """Blit each cell of ``row`` at ``top``, aligned inside its column."""
    for column, image in enumerate(row):
        right_edge: int = lefts[column] + widths[column]
        left: int = right_edge - image.get_width() if column in _RIGHT_ALIGNED else lefts[column]
        surface.blit(image, (left, top))


def _column_lefts(widths: Sequence[int], width: int) -> list[int]:
    """Return each column's left edge, px: the table centered on ``width``, ``COLUMN_GAP`` apart."""
    table_width: int = sum(widths) + (len(widths) - 1) * COLUMN_GAP
    start: int = (width - table_width) // 2
    steps: list[int] = [column_width + COLUMN_GAP for column_width in widths[:-1]]
    return [start, *(start + offset for offset in accumulate(steps))]


def _row_cells(place: int, entry: ScoreEntry) -> tuple[pygame.Surface, ...]:
    """Return the four cell images of one row: place, nickname, score, level (``LV 3``)."""
    texts: tuple[str, ...] = (
        PLACE_FORMAT.format(place),
        entry.nickname,
        group_digits(entry.score),
        f"{LEVEL_LABEL} {entry.level_reached}",
    )
    return tuple(_render(text, SCREEN_BODY_FONT_SIZE) for text in texts)


def _blit_centered(surface: pygame.Surface, text: str, size: int, width: int, top: int) -> None:
    """Blit ``text`` at font ``size`` with its center on ``width // 2`` and its top at ``top``."""
    image: pygame.Surface = _render(text, size)
    surface.blit(image, image.get_rect(centerx=width // 2, top=top))


@cache
def _render(text: str, size: int) -> pygame.Surface:
    """Return ``text`` rendered once at font ``size``, antialiased, in the screen text color."""
    return screen_font(size).render(text, True, SCREEN_TEXT_COLOR)
