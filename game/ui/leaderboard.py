"""Leaderboard page: the title, the top 3 as medal rows, places 4 to 10 as plain rows, the footer.

Source: docs/contracts/systems/screens.md, Interface (ui/leaderboard.py); 10-ui.md,
`leaderboard_page` and `leaderboard_look`. The view takes the surface, the look and the saved
entries and only draws. It never fills the background, never flips the display, never logs per
frame, never catches an error and never reads the run mode, a key or the focus.
"""

import logging
from collections.abc import Sequence
from functools import cache
from typing import Final

import pygame

from core.saves import ScoreEntry
from ui.score_text import group_digits
from ui.screen_look import ScreenLook, halo
from ui.screen_rules import RGB, LeaderboardRules

log = logging.getLogger(__name__)

LEADERBOARD_TITLE_TEXT: Final[str] = "LEADERBOARD"
"""Page title. 10-ui.md, leaderboard_look."""

LEADERBOARD_EMPTY_TEXT: Final[str] = "No scores yet."
"""The line an empty top 10 shows."""

LEVEL_LABEL: Final[str] = "LV"
"""Label before the level reached (``LV 3``). 10-ui.md, leaderboard_look."""

BACK_KEYS: Final[tuple[str, ...]] = ("ENTER", "SPACE")
"""The keys that go back to the menu, shown in the footer. 10-ui.md, instructions_text_and_look."""

BACK_WORD: Final[str] = "BACK"
"""The footer's word after the key caps. 10-ui.md, instructions_text_and_look."""

TOP_COUNT: Final[int] = 3
"""How many places are medal rows. 10-ui.md, leaderboard_look."""

TABLE_ROWS: Final[int] = 10
"""Rows of a full top 10. The block is centered as if it were always full, so rows never move."""

EMPTY_ALPHA: Final[int] = 166
"""Brightness of the empty-list line, 0..255: about 65%. Mock-up value, not in the GDD."""

PLACE_ALPHA: Final[int] = 128
"""Brightness of a plain row's place number, 0..255: about 50%. Mock-up value, not in the GDD."""

_VIEW_BOX: Final[int] = 32
"""Side of the square the medal pictures are drawn in, before they are scaled to ``medal_size``."""

_SUPERSAMPLE: Final[int] = 4
"""A medal is drawn this many times larger and shrunk, so its edges are smooth (art style)."""

_CROWN: Final[tuple[tuple[float, float], ...]] = (
    (3, 25),
    (1.5, 9),
    (10, 15.5),
    (16, 4),
    (22, 15.5),
    (30.5, 9),
    (29, 25),
)
"""The first place's crown outline in the 32 x 32 box."""

_RIBBON: Final[tuple[tuple[float, float], ...]] = ((9, 2), (16, 13), (23, 2))
"""The ribbon above a second or third place medal, in the 32 x 32 box."""


def draw_leaderboard(
    surface: pygame.Surface, look: ScreenLook, entries: Sequence[ScoreEntry] = ()
) -> None:
    """Draw the title, the rows (or the empty-list line), the rulers and the footer. Units: px.

    Entry ``i`` is place ``i + 1``; the first three are medal rows, the rest plain rows. The title
    sits ``margin_top`` from the top. The table is ``table_w`` wide, centered across the width, and
    centered between the title band and the footer band as if it held ten rows. The footer's key
    caps are centered in a band ``foot_h`` tall, ``margin_bottom`` above the bottom. Needs
    ``pygame.font`` initialized.
    """
    rules: LeaderboardRules = look.rules.leaderboard
    width, height = surface.get_size()
    palette = look.palette
    look.blit_rulers(surface)
    look.blit_text(
        surface,
        LEADERBOARD_TITLE_TEXT,
        "title",
        palette["plating"],
        {"midtop": (width // 2, rules.margin_top)},
    )
    body_top: int = rules.margin_top + rules.head_h
    foot_top: int = height - rules.margin_bottom - rules.foot_h
    if entries:
        top: int = body_top + (foot_top - body_top - _table_height(rules)) // 2
        _draw_rows(surface, look, entries, top)
    else:
        look.blit_text(
            surface,
            LEADERBOARD_EMPTY_TEXT,
            "empty",
            palette["plating"],
            {"midtop": (width // 2, body_top + rules.empty_top)},
            glow=False,
            alpha=EMPTY_ALPHA,
        )
    look.blit_keys(
        surface,
        BACK_KEYS,
        BACK_WORD,
        {"center": (width // 2, foot_top + rules.foot_h // 2)},
    )


def _table_height(rules: LeaderboardRules) -> int:
    """Return the height of a full table, px: the top rows, the gap, the plain rows."""
    tops: int = TOP_COUNT * rules.top_h + (TOP_COUNT - 1) * rules.top_gap
    return tops + rules.rest_gap + (TABLE_ROWS - TOP_COUNT) * rules.row_h


def _draw_rows(
    surface: pygame.Surface, look: ScreenLook, entries: Sequence[ScoreEntry], top: int
) -> None:
    """Draw one row per entry from ``top``: medal rows first, then the plain rows."""
    rules: LeaderboardRules = look.rules.leaderboard
    left: int = (surface.get_width() - rules.table_w) // 2
    y: int = top
    for index, entry in enumerate(entries):
        place: int = index + 1
        if place <= TOP_COUNT:
            rect: pygame.Rect = pygame.Rect(left, y, rules.table_w, rules.top_h)
            _draw_top_row(surface, look, rect, place, entry)
            y += rules.top_h + (rules.top_gap if place < TOP_COUNT else rules.rest_gap)
        else:
            rect = pygame.Rect(left, y, rules.table_w, rules.row_h)
            _draw_plain_row(surface, look, rect, place, entry)
            y += rules.row_h


def _draw_top_row(
    surface: pygame.Surface, look: ScreenLook, rect: pygame.Rect, place: int, entry: ScoreEntry
) -> None:
    """Draw a medal row: a glass panel in the place's color, the medal, name, score and level."""
    rules: LeaderboardRules = look.rules.leaderboard
    palette = look.palette
    rank: RGB = palette[f"rank_{place}"]
    look.glass(surface, rect, rules.blur, rank)
    inner: pygame.Rect = rect.inflate(-2 * rules.pad_x, 0)
    medal: pygame.Surface = _medal(look, place)
    place_cell: pygame.Rect = pygame.Rect(inner.left, rect.top, rules.top_place_w, rect.height)
    surface.blit(medal, medal.get_rect(center=place_cell.center))
    _draw_cells(
        surface,
        look,
        inner,
        entry,
        (rules.top_place_w, rules.top_score_w),
        ("top_name", "top_score"),
        (palette["plating"], rank),
        glow=True,
    )


def _draw_plain_row(
    surface: pygame.Surface, look: ScreenLook, rect: pygame.Rect, place: int, entry: ScoreEntry
) -> None:
    """Draw a plain row: the dim place number, name, score and level, and a faint line under it."""
    rules: LeaderboardRules = look.rules.leaderboard
    palette = look.palette
    inner: pygame.Rect = rect.inflate(-2 * rules.pad_x, 0)
    look.blit_text(
        surface,
        str(place),
        "row",
        palette["plating"],
        {"midright": (inner.left + rules.place_w, rect.centery)},
        glow=False,
        alpha=PLACE_ALPHA,
    )
    _draw_cells(
        surface,
        look,
        inner,
        entry,
        (rules.place_w, rules.score_w),
        ("row", "row"),
        (palette["plating"], palette["plating"]),
        glow=False,
    )
    surface.blit(_rule(rect.width, palette["frame_lights"], rules.rule_alpha), rect.bottomleft)


def _draw_cells(
    surface: pygame.Surface,
    look: ScreenLook,
    inner: pygame.Rect,
    entry: ScoreEntry,
    widths: tuple[int, int],
    roles: tuple[str, str],
    colors: tuple[RGB, RGB],
    glow: bool,
) -> None:
    """Draw a row's name (left), score and level (both right-aligned) inside ``inner``.

    ``widths`` are the place cell's and the score cell's, ``roles`` and ``colors`` the name's and
    the score's.
    """
    rules: LeaderboardRules = look.rules.leaderboard
    palette = look.palette
    center: int = inner.centery
    level_right: int = inner.right
    score_right: int = level_right - rules.level_w - rules.column_gap
    look.blit_text(
        surface,
        entry.nickname,
        roles[0],
        colors[0],
        {"midleft": (inner.left + widths[0] + rules.column_gap, center)},
        glow,
    )
    look.blit_text(
        surface,
        group_digits(entry.score),
        roles[1],
        colors[1],
        {"midright": (score_right, center)},
        glow,
    )
    look.blit_text(
        surface,
        f"{LEVEL_LABEL} {entry.level_reached}",
        "level",
        palette["level"],
        {"midright": (level_right, center)},
        glow=False,
    )


@cache
def _rule(width: int, color: RGB, alpha: int) -> pygame.Surface:
    """Return the faint 1 px line under a plain row, ``width`` px wide."""
    line: pygame.Surface = pygame.Surface((width, 1), pygame.SRCALPHA)
    line.fill((*color, alpha))
    return line


@cache
def _medal(look: ScreenLook, place: int) -> pygame.Surface:
    """Return the medal picture of ``place``: a crown for 1st, a numbered medal on a ribbon for
    2nd and 3rd, in the place's color with the icon glow round it, ``medal_size`` px square before
    the glow. Drawn once at 4 times the size and shrunk."""
    rules: LeaderboardRules = look.rules.leaderboard
    rank: RGB = look.palette[f"rank_{place}"]
    big: int = _VIEW_BOX * _SUPERSAMPLE
    canvas: pygame.Surface = pygame.Surface((big, big), pygame.SRCALPHA)
    if place == 1:
        pygame.draw.polygon(canvas, rank, _scaled(_CROWN))
        base: pygame.Rect = pygame.Rect(
            3 * _SUPERSAMPLE, 26.5 * _SUPERSAMPLE, 26 * _SUPERSAMPLE, 3.2 * _SUPERSAMPLE
        )
        pygame.draw.rect(canvas, rank, base, border_radius=_SUPERSAMPLE)
    else:
        pygame.draw.lines(canvas, rank, False, _scaled(_RIBBON), 2 * _SUPERSAMPLE)
        center: tuple[int, int] = (16 * _SUPERSAMPLE, 20 * _SUPERSAMPLE)
        pygame.draw.circle(canvas, (*rank, 56), center, 10 * _SUPERSAMPLE)
        pygame.draw.circle(canvas, rank, center, 10 * _SUPERSAMPLE, 2 * _SUPERSAMPLE)
    medal: pygame.Surface = pygame.transform.smoothscale(canvas, (rules.medal_size,) * 2)
    if place != 1:
        scale: float = rules.medal_size / _VIEW_BOX
        number_center: tuple[int, int] = (round(16 * scale), round(20 * scale))
        look.blit_text(medal, str(place), "level", rank, {"center": number_center}, glow=False)
    glow = look.rules.glow
    if glow.icon_strength > 0:
        return halo(medal, glow.icon_radius, glow.icon_strength)
    return medal


def _scaled(points: tuple[tuple[float, float], ...]) -> list[tuple[float, float]]:
    """Return ``points`` of the 32 x 32 box in the supersampled canvas's px."""
    return [(x * _SUPERSAMPLE, y * _SUPERSAMPLE) for x, y in points]
