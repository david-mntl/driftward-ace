"""Leaderboard page tests: the title, the medal rows, the plain rows, the empty line and the footer.

Contract: docs/contracts/systems/screens.md, Interface (ui/leaderboard.py) and Presentation,
Leaderboard page; 10-ui.md, `leaderboard_look`. Every size and color is read from the real
tuning/screens.json through the `screen_rules` fixture, so a changed value moves the test with it.

Positions are read from the drawn pixels, never from a font size: the page is drawn on a black
surface, so a bright pixel is ink, and a rank color is found as the exact color of a corner bracket
(brackets are solid). Where a row sits is worked out from the contract (the table is centered
between the title band and the footer band as if it held ten rows).
"""

import dataclasses

import pygame
import pytest

from app.assets import load_screen_fonts
from core.saves import ScoreEntry
from ui.leaderboard import TOP_COUNT, draw_leaderboard
from ui.screen_look import ScreenLook
from ui.screen_rules import ScreenRules

SIZES: tuple[tuple[int, int], ...] = ((856, 518), (1000, 640))
"""Surfaces drawn on: the window (10-ui.md, window_screens) and a larger one, so the centering is
shown to follow the surface and not a constant."""

RANKS: tuple[str, ...] = ("rank_1", "rank_2", "rank_3")
INK_LEVEL: int = 100
"""A pixel with a channel above this is ink. The glass fill and the faint rule stay below it."""

NAMES: tuple[str, ...] = (
    "VEGA",
    "MOONDOG",
    "K-9",
    "ORBIT",
    "DAVID",
    "NOVA",
    "PIXEL",
    "ZED",
    "LUNA",
    "STARDUST*",
)
SCORES: tuple[int, ...] = (
    1204880,
    986420,
    812300,
    640150,
    598730,
    455210,
    391880,
    280440,
    176300,
    98650,
)
RIGHT_EDGE_TOLERANCE_PX: int = 4
"""Slack for a glyph's side bearing and the glow when a right edge is read from ink."""

FAINT_LEVEL: int = 8
"""Above this a pixel is more than the last medal row's faint glow reaching a plain row."""

CENTER_TOLERANCE_PX: int = 3
"""Slack for centering read from ink (glyph bearings, the trailing letter-spacing)."""


def _entries(count: int = 10, names: tuple[str, ...] = NAMES) -> list[ScoreEntry]:
    """``count`` entries in place order, scores falling, levels 9 down to 2."""
    return [
        ScoreEntry(nickname=names[i], score=SCORES[i], level_reached=max(9 - i, 2))
        for i in range(count)
    ]


def _page(
    look: ScreenLook, entries: list[ScoreEntry], size: tuple[int, int] = SIZES[0], gray: int = 0
) -> pygame.Surface:
    surface = pygame.Surface(size)
    surface.fill((gray, gray, gray))
    draw_leaderboard(surface, look, entries)
    return surface


def _table_top(rules: ScreenRules, size: tuple[int, int]) -> int:
    """Top of the first row: the ten-row table centered between the title band and the footer."""
    page = rules.leaderboard
    body_top = page.margin_top + page.head_h
    foot_top = size[1] - page.margin_bottom - page.foot_h
    tops = TOP_COUNT * page.top_h + (TOP_COUNT - 1) * page.top_gap
    table = tops + page.rest_gap + (10 - TOP_COUNT) * page.row_h
    return body_top + (foot_top - body_top - table) // 2


def _row_rect(rules: ScreenRules, size: tuple[int, int], place: int) -> pygame.Rect:
    """The box of place ``place`` (1 to 10): a medal row's panel, or a plain row's band."""
    page = rules.leaderboard
    left = (size[0] - page.table_w) // 2
    top = _table_top(rules, size)
    if place <= TOP_COUNT:
        return pygame.Rect(
            left, top + (place - 1) * (page.top_h + page.top_gap), page.table_w, page.top_h
        )
    first_plain = top + TOP_COUNT * page.top_h + (TOP_COUNT - 1) * page.top_gap + page.rest_gap
    return pygame.Rect(
        left, first_plain + (place - TOP_COUNT - 1) * page.row_h, page.table_w, page.row_h
    )


def _ink(surface: pygame.Surface, area: pygame.Rect, level: int = INK_LEVEL) -> pygame.Rect | None:
    """The rectangle of the bright pixels inside ``area``, in surface coordinates; None if none."""
    part = surface.subsurface(area.clip(surface.get_rect()))
    dark = pygame.mask.from_threshold(part, (0, 0, 0, 255), (level, level, level, 255))
    dark.invert()
    boxes = dark.get_bounding_rects()
    if not boxes:
        return None
    box = boxes[0].unionall(boxes[1:])
    return box.move(area.clip(surface.get_rect()).topleft)


def _count(
    surface: pygame.Surface, area: pygame.Rect, color: tuple[int, int, int], tolerance: int = 1
) -> int:
    """How many pixels inside ``area`` are ``color``, each channel within ``tolerance``."""
    part = surface.subsurface(area.clip(surface.get_rect()))
    level = (tolerance, tolerance, tolerance, 255)
    return pygame.mask.from_threshold(part, (*color, 255), level).count()


def _rows_differing(first: pygame.Surface, second: pygame.Surface) -> tuple[int, int] | None:
    """The first and last pixel row where the two pictures differ; None if they are the same."""
    width, height = first.get_size()
    a = pygame.image.tobytes(first, "RGB")
    b = pygame.image.tobytes(second, "RGB")
    rows = [
        y
        for y in range(height)
        if a[y * width * 3 : (y + 1) * width * 3] != b[y * width * 3 : (y + 1) * width * 3]
    ]
    return (rows[0], rows[-1]) if rows else None


def test_title_is_in_the_head_band_and_centered(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    page = screen_rules.leaderboard
    for size in SIZES:
        surface = _page(look, _entries(), size)
        band = pygame.Rect(40, 0, size[0] - 80, page.margin_top + page.head_h)
        ink = _ink(surface, band, 150)
        assert ink is not None, f"{size}: no title ink in the head band"
        assert abs(ink.centerx - size[0] / 2) <= CENTER_TOLERANCE_PX, f"{size}: title off center"
        assert ink.top >= page.margin_top - 4, f"{size}: title is above its margin"


def test_medal_rows_have_rank_colored_corner_brackets(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    out = screen_rules.glass.bracket_out
    colors = [screen_rules.palette[key] for key in RANKS]
    assert len(set(colors)) == 3, "the three rank colors must differ"
    for size in SIZES:
        surface = _page(look, _entries(), size)
        for place, color in enumerate(colors, start=1):
            rect = _row_rect(screen_rules, size, place)
            corners = [
                (rect.left - out, rect.top - out),
                (rect.right + out - 1, rect.top - out),
            ]
            if place == TOP_COUNT:
                # The next medal row's glow lies over the bottom corners above it, so only the
                # last medal row's bottom corners are exactly the rank color.
                corners += [
                    (rect.left - out, rect.bottom + out - 1),
                    (rect.right + out - 1, rect.bottom + out - 1),
                ]
            for corner in corners:
                assert tuple(surface.get_at(corner))[:3] == color, (
                    f"{size}: place {place} has no {color} bracket at {corner}"
                )


def test_plain_rows_have_no_brackets(look: ScreenLook, screen_rules: ScreenRules) -> None:
    out = screen_rules.glass.bracket_out
    cyan = screen_rules.palette["frame_lights"]
    surface = _page(look, _entries())
    for place in range(TOP_COUNT + 1, 11):
        rect = _row_rect(screen_rules, SIZES[0], place)
        corner = (rect.left - out, rect.top - out)
        assert tuple(surface.get_at(corner))[:3] != cyan, f"place {place} has a bracket"


def test_medal_rows_are_taller_than_plain_rows_and_set_apart(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    page = screen_rules.leaderboard
    assert page.top_h > page.row_h
    assert page.rest_gap > 0
    third = _row_rect(screen_rules, SIZES[0], 3)
    fourth = _row_rect(screen_rules, SIZES[0], 4)
    assert fourth.top - third.bottom == page.rest_gap
    second = _row_rect(screen_rules, SIZES[0], 2)
    assert second.top - _row_rect(screen_rules, SIZES[0], 1).bottom == page.top_gap
    assert fourth.height == page.row_h
    assert third.height == page.top_h


def test_plain_rows_have_a_faint_line_under_them(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    surface = _page(look, _entries())
    for place in range(TOP_COUNT + 1, 11):
        rect = _row_rect(screen_rules, SIZES[0], place)
        x = rect.left + 2
        assert max(surface.get_at((x, rect.bottom))[:3]) > FAINT_LEVEL, f"place {place}: no line"
        # The row above ends with its line on this row's first pixel row.
        for y in range(rect.top + 1, rect.bottom):
            assert max(surface.get_at((x, y))[:3]) <= FAINT_LEVEL, f"place {place}: ink at row {y}"


def test_entry_i_is_place_i_plus_1(look: ScreenLook, screen_rules: ScreenRules) -> None:
    base = _page(look, _entries())
    for index in range(10):
        names = list(NAMES)
        names[index] = "ZZZZ"
        changed = _page(look, _entries(names=tuple(names)))
        span = _rows_differing(base, changed)
        rect = _row_rect(screen_rules, SIZES[0], index + 1)
        assert span is not None, f"place {index + 1}: its name draws nothing"
        message = (
            f"place {index + 1}: its name changed rows {span}, outside {rect.top}..{rect.bottom}"
        )
        assert rect.top - 2 <= span[0], message
        assert span[1] <= rect.bottom + 2, message


def test_all_ten_rows_fit_between_the_title_and_the_footer(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    page = screen_rules.leaderboard
    for size in SIZES:
        surface = _page(look, _entries(), size)
        first = _row_rect(screen_rules, size, 1)
        last = _row_rect(screen_rules, size, 10)
        assert first.top >= page.margin_top + page.head_h, f"{size}: the table touches the title"
        assert last.bottom <= size[1] - page.margin_bottom - page.foot_h, f"{size}: touches footer"
        assert _ink(surface, last, 150) is not None, f"{size}: the tenth row is empty"


def test_fewer_entries_leave_the_rows_where_they_are(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    full = _page(look, _entries())
    three = _page(look, _entries(3))
    first = _row_rect(screen_rules, SIZES[0], 1)
    third = _row_rect(screen_rules, SIZES[0], 3)
    page = screen_rules.leaderboard
    area = pygame.Rect(
        0, first.top - 20, SIZES[0][0] - 60, third.bottom + page.rest_gap - first.top + 20
    )
    assert full.subsurface(area).get_buffer().raw == three.subsurface(area).get_buffer().raw
    fourth = _row_rect(screen_rules, SIZES[0], 4)
    assert _ink(three, pygame.Rect(100, fourth.top, 650, 200), 60) is None


def test_scores_end_on_one_edge(look: ScreenLook, screen_rules: ScreenRules) -> None:
    page = screen_rules.leaderboard
    surface = _page(look, _entries())
    rect = _row_rect(screen_rules, SIZES[0], 1)
    score_right = rect.right - page.pad_x - page.level_w - page.column_gap
    for place in range(1, 11):
        row = _row_rect(screen_rules, SIZES[0], place)
        area = pygame.Rect(score_right - 200, row.top, 200 + page.column_gap // 2, row.height)
        wide = score_right - (page.top_score_w if place <= TOP_COUNT else page.score_w)
        ink = _ink(
            surface, pygame.Rect(max(area.left, wide), row.top, area.right - wide, row.height), 150
        )
        assert ink is not None, f"place {place}: no score ink"
        assert score_right - RIGHT_EDGE_TOLERANCE_PX <= ink.right <= score_right, (
            f"place {place}: score ends at {ink.right}, not {score_right}"
        )


def test_table_is_centered(look: ScreenLook, screen_rules: ScreenRules) -> None:
    rank = screen_rules.palette["rank_1"]
    for size in SIZES:
        surface = _page(look, _entries(), size)
        row = _row_rect(screen_rules, size, 1)
        area = row.inflate(60, 12)
        pixels = pygame.mask.from_threshold(
            surface.subsurface(area.clip(surface.get_rect())), (*rank, 255), (1, 1, 1, 255)
        ).get_bounding_rects()
        left = min(box.left for box in pixels) + area.left
        right = max(box.right for box in pixels) + area.left
        assert abs((left + right) / 2 - size[0] / 2) <= 1, f"{size}: the table is off center"


def test_each_medal_row_has_a_medal_in_its_rank_color(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    page = screen_rules.leaderboard
    surface = _page(look, _entries())
    shapes = []
    for place, key in enumerate(RANKS, start=1):
        row = _row_rect(screen_rules, SIZES[0], place)
        cell = pygame.Rect(row.left + page.pad_x, row.top, page.top_place_w, row.height)
        assert _count(surface, cell, screen_rules.palette[key], 30) >= 20, (
            f"place {place}: no medal"
        )
        ink = _ink(surface, cell, 150)
        assert ink is not None, f"place {place}: no medal ink"
        assert cell.contains(ink), f"place {place}: medal leaves its cell"
        shapes.append(pygame.image.tobytes(surface.subsurface(cell), "RGB"))
    assert len(set(shapes)) == 3, "the three medals must not look the same"


def test_plain_rows_have_no_medal(look: ScreenLook, screen_rules: ScreenRules) -> None:
    page = screen_rules.leaderboard
    surface = _page(look, _entries())
    for place in range(TOP_COUNT + 1, 11):
        row = _row_rect(screen_rules, SIZES[0], place)
        number = pygame.Rect(row.left + page.pad_x, row.top, page.place_w, row.height)
        ink = _ink(surface, number, 40)
        assert ink is not None, f"place {place}: no number"
        assert ink.width <= 2 * 12, f"place {place}: more than a number"
        assert _count(surface, number, screen_rules.palette["rank_1"]) == 0


def test_empty_list_shows_the_line_and_no_rows(look: ScreenLook, screen_rules: ScreenRules) -> None:
    page = screen_rules.leaderboard
    for size in SIZES:
        surface = _page(look, [], size)
        body_top = page.margin_top + page.head_h
        foot_top = size[1] - page.margin_bottom - page.foot_h
        line = _ink(surface, pygame.Rect(100, body_top, size[0] - 200, foot_top - body_top), 60)
        assert line is not None, f"{size}: the empty list says nothing"
        assert line.top >= body_top + page.empty_top - 4, f"{size}: the line is above its place"
        assert abs(line.centerx - size[0] / 2) <= CENTER_TOLERANCE_PX, f"{size}: line off center"
        assert line.height < page.top_h, f"{size}: more than one line of text"
        for key in RANKS:
            whole = surface.get_rect()
            assert _count(surface, whole, screen_rules.palette[key]) == 0, f"{size}: a medal row"


def test_footer_shows_the_back_keys_centered(look: ScreenLook, screen_rules: ScreenRules) -> None:
    page = screen_rules.leaderboard
    cyan = screen_rules.palette["frame_lights"]
    for size in SIZES:
        surface = _page(look, _entries(), size)
        band = pygame.Rect(
            100, size[1] - page.margin_bottom - page.foot_h, size[0] - 200, page.foot_h
        )
        ink = _ink(surface, band, 60)
        assert ink is not None, f"{size}: no footer"
        assert abs(ink.centerx - size[0] / 2) <= CENTER_TOLERANCE_PX, f"{size}: footer off center"
        assert _count(surface, band, cyan, 40) > 0, f"{size}: the key caps are not cyan"


def test_nothing_is_drawn_outside_the_table_but_the_rulers(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    rulers = screen_rules.rulers
    for size in SIZES:
        surface = _page(look, _entries(), size)
        left = (size[0] - screen_rules.leaderboard.table_w) // 2
        side = pygame.Rect(
            rulers.inset_x + rulers.w + 1, 0, left - 8 - (rulers.inset_x + rulers.w + 1), size[1]
        )
        assert _ink(surface, side) is None, f"{size}: ink between the ruler and the table"
        assert _ink(surface, pygame.Rect(0, 0, rulers.inset_x + rulers.w, size[1])) is not None, (
            f"{size}: no ruler"
        )


def test_the_page_never_fills_the_background(look: ScreenLook) -> None:
    surface = _page(look, _entries(), gray=60)
    for point in ((3, 3), (50, 200), (SIZES[0][0] - 4, 300)):
        assert surface.get_at(point)[:3] == (60, 60, 60), f"{point} was painted over"


def test_redraw_is_the_same_picture(look: ScreenLook) -> None:
    first = pygame.image.tobytes(_page(look, _entries()), "RGB")
    assert pygame.image.tobytes(_page(look, _entries()), "RGB") == first


def test_blur_flag_is_read_from_the_values(look: ScreenLook, screen_rules: ScreenRules) -> None:
    """With blur on, the glass blurs what is behind it; off (the shipped value), it leaves it."""
    assert screen_rules.leaderboard.blur is False
    blurred_rules = dataclasses.replace(
        screen_rules, leaderboard=dataclasses.replace(screen_rules.leaderboard, blur=True)
    )
    blurred = ScreenLook(blurred_rules, load_screen_fonts(blurred_rules))
    plain = pygame.Surface(SIZES[0])
    plain.fill((90, 90, 90))
    for x in range(0, SIZES[0][0], 6):
        pygame.draw.line(plain, (200, 60, 60), (x, 0), (x, SIZES[0][1]))
    first = plain.copy()
    second = plain.copy()
    draw_leaderboard(first, look, _entries())
    draw_leaderboard(second, blurred, _entries())
    assert pygame.image.tobytes(first, "RGB") != pygame.image.tobytes(second, "RGB")


@pytest.mark.parametrize("size", [(640, 480), (1000, 700)])
def test_other_surface_sizes_draw_without_error(look: ScreenLook, size: tuple[int, int]) -> None:
    surface = _page(look, _entries(), size)
    assert _ink(surface, surface.get_rect(), 150) is not None


def test_one_and_three_entries_draw_inside_the_window_with_their_rank_colors(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    for count in (1, 3):
        surface = _page(look, _entries(count))
        assert _ink(surface, surface.get_rect()) is not None
    three = _page(look, _entries(3))
    found = {
        rank: any(
            tuple(three.get_at((x, y))[:3]) == screen_rules.palette[rank]
            for x in range(0, three.get_width(), 1)
            for y in range(100, 280, 1)
        )
        for rank in ("rank_1", "rank_2", "rank_3")
    }
    assert all(found.values()), found
