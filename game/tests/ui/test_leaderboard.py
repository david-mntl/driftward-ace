"""Leaderboard page tests: the title, the empty-list line, the rows and the footer.

Contract: docs/contracts/systems/game-flow.md, Interface (ui/leaderboard.py) and Presentation,
Leaderboard page and the shared items (Text, Lines and blank lines, Cache, Only draws). The texts
and the font sizes are stand-ins from scope report DRA-125, Values needed (Leaderboard page,
Footer); the GDD does not hold them until UI-03 and UI-04. From DRA-126 the page also shows one
row per saved entry: the row texts and look are stand-ins from scope report DRA-126, Values needed
(Leaderboard rows: 16 px, 24 px apart, the place `1.`, the nickname, the score grouped like SCORE,
`LV 3`) and docs/reports/DRA-126-away-log.md, Decisions, 5 (four columns, 24 px apart, the place and
the score right-aligned, the nickname and the level left-aligned).

Positions are read from the drawn pixels (`pygame.image.tobytes`), never from a font size. The page
is drawn on a black surface, so the ink is the text alone. Every text is compared with the same
text rendered here in the default font (`_reference`), and its place is worked out from the ink's
own offset in that render. The fonts' `get_linesize()` give the contract's rows (a blank line is
one body line), as in `test_game_over.py`. The footer's place is read from the instructions page,
which the contract names as its twin.
"""

from itertools import accumulate
from typing import NamedTuple

import pygame
import pytest

import ui.leaderboard as page_view
import ui.screen_look as look_view
from core.saves import ScoreEntry
from ui.instructions import draw_instructions
from ui.leaderboard import draw_leaderboard
from ui.screen_look import screen_font

SIZES: tuple[tuple[int, int], ...] = ((640, 480), (800, 600))
"""Surfaces drawn on: the canvas (03-world-and-camera.md, screen_w, screen_h (guess)) and a larger
one, so the centering is shown to follow the surface and not a constant."""

TITLE_TEXT: str = "LEADERBOARD"
TITLE_FONT_SIZE: int = 32
EMPTY_TEXT: str = "No scores yet."
BODY_FONT_SIZE: int = 16
"""Source: scope report DRA-125, Values needed, Leaderboard page: title 32 px, the line 16 px."""

FOOTER_TEXT: str = "Press Enter or Space to go back."
"""Source: scope report DRA-125, Values needed, Footer (16 px)."""

TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Source: scope report DRA-125, Values needed (white text)."""

GRAY: int = 60
"""A background below white, for the checks that show nothing fills the surface."""

TOLERANCE_PX: int = 1
"""Rects are placed by integer halves: a center, or a vertical middle, may be one px off."""

Band = tuple[int, int, int, int]
"""One line of ink: top row, bottom row, left column, right column, all inclusive."""


class _Ref(NamedTuple):
    """A text rendered here: its ink rectangle and where that sits in the render."""

    crop: tuple[bytes, ...]
    image_width: int
    image_height: int
    ink_left: int
    ink_top: int


def _surface(size: tuple[int, int], gray: int = 0) -> pygame.Surface:
    surface = pygame.Surface(size)
    surface.fill((gray, gray, gray))
    return surface


def _levels(surface: pygame.Surface) -> bytes:
    """The red level of every pixel, row by row. Every picture here is gray, so it is the level."""
    return pygame.image.tobytes(surface, "RGB")[::3]


def _bands(surface: pygame.Surface) -> list[Band]:
    """Each run of rows holding ink, with its ink columns."""
    width, height = surface.get_size()
    levels = _levels(surface)
    bands: list[Band] = []
    top: int | None = None
    for y in range(height + 1):
        inked = y < height and any(levels[y * width : (y + 1) * width])
        if inked and top is None:
            top = y
        elif not inked and top is not None:
            columns = [x for x in range(width) if any(levels[r * width + x] for r in range(top, y))]
            bands.append((top, y - 1, columns[0], columns[-1]))
            top = None
    return bands


def _crop(levels: bytes, width: int, band: Band) -> tuple[bytes, ...]:
    """The band's ink rectangle, one bytes row per pixel row."""
    top, bottom, left, right = band
    return tuple(levels[y * width + left : y * width + right + 1] for y in range(top, bottom + 1))


def _reference(text: str, size: int) -> _Ref:
    """``text`` in the default font at ``size``, white on black: its ink and the ink's offset."""
    image = pygame.font.Font(None, size).render(text, True, TEXT_COLOR)
    canvas = _surface(image.get_size())
    canvas.blit(image, (0, 0))
    band = _bands(canvas)[0]
    crop = _crop(_levels(canvas), canvas.get_width(), band)
    return _Ref(crop, image.get_width(), image.get_height(), band[2], band[0])


def _page(size: tuple[int, int], gray: int = 0) -> pygame.Surface:
    surface = _surface(size, gray)
    draw_leaderboard(surface)
    return surface


def _assert_line(levels: bytes, width: int, band: Band, ref: _Ref, what: str) -> None:
    """The band is exactly ``ref``'s ink and its render is centered across ``width``."""
    assert (band[1] - band[0] + 1, band[3] - band[2] + 1) == (len(ref.crop), len(ref.crop[0])), (
        f"{what}: the ink is not the text's size"
    )
    assert _crop(levels, width, band) == ref.crop, f"{what}: not the default font's render"
    rect_left = band[2] - ref.ink_left
    assert abs(2 * rect_left + ref.image_width - width) <= TOLERANCE_PX, (
        f"{what}: not centered across {width}: rect left {rect_left}, "
        f"render width {ref.image_width}"
    )


def test_the_leaderboard_shows_the_title_the_empty_line_and_the_footer_centered(
    pygame_headless: None,
) -> None:
    title_ref = _reference(TITLE_TEXT, TITLE_FONT_SIZE)
    empty_ref = _reference(EMPTY_TEXT, BODY_FONT_SIZE)
    footer_ref = _reference(FOOTER_TEXT, BODY_FONT_SIZE)
    title_line = pygame.font.Font(None, TITLE_FONT_SIZE).get_linesize()
    body_line = pygame.font.Font(None, BODY_FONT_SIZE).get_linesize()
    for size in SIZES:
        width, height = size
        surface = _page(size)
        bands = _bands(surface)
        assert len(bands) == 3, f"{size=}: lines of ink: {bands}"
        levels = _levels(surface)
        title, empty, footer = bands
        _assert_line(levels, width, title, title_ref, f"{size=} title")
        _assert_line(levels, width, empty, empty_ref, f"{size=} empty line")
        _assert_line(levels, width, footer, footer_ref, f"{size=} footer")
        # The title, one blank body line, then the empty-list line.
        title_top = title[0] - title_ref.ink_top
        assert empty[0] - empty_ref.ink_top == title_top + title_line + body_line, (
            f"{size=}: the empty line is not one blank line under the title"
        )
        # That block is centered between the surface's top and the footer's top.
        footer_top = height - 2 * body_line
        block_bottom = empty[0] - empty_ref.ink_top + body_line
        assert abs(title_top + block_bottom - footer_top) <= TOLERANCE_PX, (
            f"{size=}: the block {title_top}..{block_bottom} is not centered above {footer_top}"
        )


def test_the_footer_is_on_the_same_rows_as_the_instructions_page(pygame_headless: None) -> None:
    for size in SIZES:
        width, _ = size
        leaderboard = _page(size)
        instructions = _surface(size)
        draw_instructions(instructions)
        footer = _bands(leaderboard)[-1]
        assert footer == _bands(instructions)[-1], f"{size=}: the footer is not in the same place"
        assert _crop(_levels(leaderboard), width, footer) == _crop(
            _levels(instructions), width, footer
        ), f"{size=}: the footer's pixels differ from the instructions page's"


def test_the_leaderboard_draws_the_same_pixels_twice_and_changes_nothing_but_the_surface(
    pygame_headless: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    texts_before = (page_view.LEADERBOARD_TITLE_TEXT, page_view.LEADERBOARD_EMPTY_TEXT)
    caplog.set_level(0)
    for size in SIZES:
        first = pygame.image.tobytes(_page(size), "RGB")
        second = pygame.image.tobytes(_page(size), "RGB")
        assert first == second, f"{size=}: two draws, two pictures"
        # Nothing fills the background: every pixel with no ink stays the background's.
        on_gray = pygame.image.tobytes(_page(size, gray=GRAY), "RGB")
        assert all(
            bright == GRAY for ink, bright in zip(first, on_gray, strict=True) if ink == 0
        ), f"{size=}: the draw changed pixels with no ink"
        assert _page(size).get_size() == size
    assert caplog.records == [], "the view logged"
    assert texts_before == (page_view.LEADERBOARD_TITLE_TEXT, page_view.LEADERBOARD_EMPTY_TEXT)
    # Every fixed text is rendered once, on the first draw: after that, no render per frame.
    renders: list[str] = []

    class CountingFont:
        def __init__(self, font: pygame.font.Font) -> None:
            self._font = font

        def render(self, text: str, antialias: bool, color: tuple[int, int, int]) -> pygame.Surface:
            renders.append(text)
            return self._font.render(text, antialias, color)

        def __getattr__(self, name: str) -> object:
            return getattr(self._font, name)

    def counting(size: int) -> CountingFont:
        return CountingFont(screen_font(size))

    for module in (page_view, look_view):
        monkeypatch.setattr(module, "screen_font", counting, raising=False)
    for _ in range(3):
        _page(SIZES[0])
    assert renders == [], f"rendered again on later frames: {renders}"


# DRA-126: the rows. Contract: game-flow.md, Interface (ui/leaderboard.py) and Presentation,
# Leaderboard page (Filled, Row cells, Columns).

ROW_SPACING: int = 24
"""Px from one row's top to the next one's. Source: scope report DRA-126, Values needed
(Leaderboard rows: 16 px, 24 px apart)."""

COLUMN_GAP: int = 24
"""Px between two columns. Source: docs/reports/DRA-126-away-log.md, Decisions, 5."""

LEVEL_LABEL: str = "LV"
"""The label before the level reached (`LV 3`). Source: scope report DRA-126, Values needed."""


def _entry(nickname: str, score: int, level: int) -> ScoreEntry:
    return ScoreEntry(nickname=nickname, score=score, level_reached=level)


FIVE: tuple[ScoreEntry, ...] = (
    _entry("ACE", 1234567, 3),
    _entry("ZZZZZZZZZZ", 90000, 8),
    _entry(" A B", 999, 1),
    _entry("M", 5, 4),
    _entry("NEO.-_!?*", 0, 2),
)
"""Five entries in the order a list holds them, #1 first. Different widths in every column: a
nickname of one letter and of ten, one with blanks (a leading and an inner one, drawn as spaces),
scores from 0 to seven digits, levels 1 to 8."""

TEN: tuple[ScoreEntry, ...] = tuple(
    _entry(name, score, level)
    for name, score, level in (
        ("ONE", 100000000, 8),
        ("TWO", 12345678, 7),
        ("THREE", 1000000, 6),
        ("FOUR", 123456, 5),
        ("FIVE", 12345, 5),
        ("SIX", 9999, 4),
        ("SEVEN", 1000, 3),
        ("EIGHT", 999, 2),
        ("NINE", 10, 1),
        ("TEN", 0, 1),
    )
)
"""A full top 10: the tenth place has two digits, so the place column is wider than for nine."""

ONE: tuple[ScoreEntry, ...] = (_entry("SOLO", 42, 1),)


def _cell_texts(place: int, entry: ScoreEntry) -> tuple[str, str, str, str]:
    """The four cells of a row as the contract lists them: the place (`1.`), the nickname as
    saved, the score grouped like SCORE with no label, the level (`LV 3`)."""
    digits = f"{entry.score:,}".replace(",", " ")
    return f"{place}.", entry.nickname, digits, f"{LEVEL_LABEL} {entry.level_reached}"


def _expected_page(
    size: tuple[int, int], entries: tuple[ScoreEntry, ...], title_top: int, start: int
) -> bytes:
    """The page built here, cell by cell: the title and the footer centered, each row's four cells
    in columns as wide as their widest cell, ``COLUMN_GAP`` apart, the table's left edge at
    ``start``, the place and score right-aligned and the nickname and level left-aligned."""
    width, height = size
    body = pygame.font.Font(None, BODY_FONT_SIZE)
    title = pygame.font.Font(None, TITLE_FONT_SIZE)
    surface = _surface(size)

    def centered(text: str, font: pygame.font.Font, top: int) -> None:
        image = font.render(text, True, TEXT_COLOR)
        surface.blit(image, image.get_rect(centerx=width // 2, top=top))

    centered(TITLE_TEXT, title, title_top)
    centered(FOOTER_TEXT, body, height - 2 * body.get_linesize())
    rows = [_cell_texts(place, entry) for place, entry in enumerate(entries, start=1)]
    widths = [max(body.size(row[column])[0] for row in rows) for column in range(4)]
    lefts = [start, *(start + offset for offset in accumulate(w + COLUMN_GAP for w in widths[:3]))]
    first_row = title_top + title.get_linesize() + body.get_linesize()
    for index, row in enumerate(rows):
        for column, text in enumerate(row):
            image = body.render(text, True, TEXT_COLOR)
            right_aligned = column in (0, 2)
            left = lefts[column] + (widths[column] - image.get_width() if right_aligned else 0)
            surface.blit(image, (left, first_row + index * ROW_SPACING))
    return pygame.image.tobytes(surface, "RGB")


def _drawn(size: tuple[int, int], entries: tuple[ScoreEntry, ...], gray: int = 0) -> pygame.Surface:
    surface = _surface(size, gray)
    draw_leaderboard(surface, entries)
    return surface


@pytest.mark.parametrize("entries", [ONE, FIVE, TEN], ids=["one", "five", "ten"])
def test_the_leaderboard_with_entries_has_one_row_per_entry_in_four_aligned_columns(
    pygame_headless: None, entries: tuple[ScoreEntry, ...]
) -> None:
    body = pygame.font.Font(None, BODY_FONT_SIZE)
    title = pygame.font.Font(None, TITLE_FONT_SIZE)
    title_ref = _reference(TITLE_TEXT, TITLE_FONT_SIZE)
    for size in SIZES:
        width, height = size
        tag = f"{size=} {len(entries)} entries"
        surface = _drawn(size, entries)
        data = pygame.image.tobytes(surface, "RGB")
        bands = _bands(surface)
        # The title, one band per row (24 px apart, 16 px text: they never touch) and the footer.
        assert len(bands) == len(entries) + 2, f"{tag}: lines of ink: {bands}"
        title_band, footer = bands[0], bands[-1]
        # The block, from the title's top to the last row's bottom, is centered above the footer.
        title_top = title_band[0] - title_ref.ink_top
        footer_top = height - 2 * body.get_linesize()
        rows_height = body.get_linesize() + (len(entries) - 1) * ROW_SPACING
        block = title.get_linesize() + body.get_linesize() + rows_height
        assert abs(2 * title_top + block - footer_top) <= TOLERANCE_PX, (
            f"{tag}: the block is not centered above the footer: top {title_top}"
        )
        # Row i, entry i, place i + 1: the whole picture is the one built cell by cell here.
        rows = [_cell_texts(place, entry) for place, entry in enumerate(entries, start=1)]
        table = sum(max(body.size(row[c])[0] for row in rows) for c in range(4)) + 3 * COLUMN_GAP
        starts = ((width - table) // 2, (width - table + 1) // 2)
        candidates = [_expected_page(size, entries, title_top, start) for start in starts]
        assert data in candidates, f"{tag}: not the table of four aligned columns, centered"
        # The footer is the instructions page's footer, in the same place.
        instructions = _surface(size)
        draw_instructions(instructions)
        assert footer == _bands(instructions)[-1], f"{tag}: the footer moved"
        # The rows are ROW_SPACING apart: each row's ink top is row 0's plus i x 24 px (a cell's own
        # glyphs may stand a row or two higher, so the band tops are read within 2 px).
        row_tops = [band[0] for band in bands[1:-1]]
        for index, top in enumerate(row_tops):
            assert abs(top - (row_tops[0] + index * ROW_SPACING)) <= 2, (
                f"{tag}: row {index} is not {ROW_SPACING} px under the one above: {row_tops}"
            )


def test_the_leaderboard_with_entries_puts_each_cell_in_its_column_by_its_alignment(
    pygame_headless: None,
) -> None:
    # The place and the score end on their column's right edge, the nickname and the level start on
    # its left edge, whatever the other rows hold. Read from a page whose rows differ in width.
    body = pygame.font.Font(None, BODY_FONT_SIZE)
    rows = [_cell_texts(place, entry) for place, entry in enumerate(TEN, start=1)]
    size = SIZES[0]
    surface = _drawn(size, TEN)
    levels = _levels(surface)
    width = size[0]
    bands = _bands(surface)[1:-1]
    # Per column, the row's ink inside the column's own horizontal range.
    widths = [max(body.size(row[c])[0] for row in rows) for c in range(4)]
    table = sum(widths) + 3 * COLUMN_GAP
    start = (width - table) // 2
    lefts = [start, *(start + offset for offset in accumulate(w + COLUMN_GAP for w in widths[:3]))]
    for index, (band, row) in enumerate(zip(bands, rows, strict=True)):
        for column, text in enumerate(row):
            ref = _reference(text, BODY_FONT_SIZE)
            right_aligned = column in (0, 2)
            cell_left = lefts[column] + (
                widths[column] - body.size(text)[0] if right_aligned else 0
            )
            ink_left = cell_left + ref.ink_left
            top, bottom = band[0], band[1]
            assert _crop_rows(levels, width, ink_left, top, bottom, ref), (
                f"row {index} column {column} {text!r}: not at its place"
            )


def _crop_rows(levels: bytes, width: int, left: int, top: int, bottom: int, ref: _Ref) -> bool:
    """True when ``ref``'s ink rectangle is in ``levels`` with its left column at ``left`` and its
    rows ending inside ``top`` to ``bottom`` (the row's band)."""
    height = len(ref.crop)
    for y in range(top, bottom - height + 2):
        got = tuple(
            levels[(y + r) * width + left : (y + r) * width + left + len(ref.crop[0])]
            for r in range(height)
        )
        if got == ref.crop:
            return True
    return False


def test_the_leaderboard_with_no_entries_is_the_dra_125_page(pygame_headless: None) -> None:
    for size in SIZES:
        default = pygame.image.tobytes(_page(size), "RGB")
        assert pygame.image.tobytes(_drawn(size, ()), "RGB") == default, f"{size=}: ()"
        empty_list = _surface(size)
        draw_leaderboard(empty_list, [])
        assert pygame.image.tobytes(empty_list, "RGB") == default, f"{size=}: []"
        bands = _bands(_page(size))
        assert len(bands) == 3, f"{size=}: not the title, the empty line and the footer: {bands}"
        levels = _levels(_page(size))
        _assert_line(levels, size[0], bands[1], _reference(EMPTY_TEXT, BODY_FONT_SIZE), "empty")


def test_the_footer_of_the_filled_page_is_the_instructions_footer(pygame_headless: None) -> None:
    for size in SIZES:
        width, _ = size
        instructions = _surface(size)
        draw_instructions(instructions)
        footer = _bands(instructions)[-1]
        for entries in (ONE, FIVE, TEN):
            page = _drawn(size, entries)
            assert _bands(page)[-1] == footer, f"{size=} {len(entries)}: the footer moved"
            assert _crop(_levels(page), width, footer) == _crop(
                _levels(instructions), width, footer
            ), f"{size=} {len(entries)}: the footer's pixels differ"


def test_the_filled_leaderboard_draws_the_same_pixels_twice_and_changes_nothing_but_the_surface(
    pygame_headless: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(0)
    entries_before = tuple(
        ScoreEntry(nickname=e.nickname, score=e.score, level_reached=e.level_reached) for e in TEN
    )
    texts_before = (page_view.PLACE_FORMAT, page_view.LEVEL_LABEL, page_view.ROW_SPACING)
    for size in SIZES:
        for entries in (ONE, FIVE, TEN):
            first = pygame.image.tobytes(_drawn(size, entries), "RGB")
            second = pygame.image.tobytes(_drawn(size, entries), "RGB")
            assert first == second, f"{size=} {len(entries)}: two draws, two pictures"
            # Nothing fills the background: every pixel with no ink stays the background's.
            on_gray = pygame.image.tobytes(_drawn(size, entries, gray=GRAY), "RGB")
            assert all(
                bright == GRAY for ink, bright in zip(first, on_gray, strict=True) if ink == 0
            ), f"{size=} {len(entries)}: the draw changed pixels with no ink"
            assert _drawn(size, entries).get_size() == size
    assert caplog.records == [], "the view logged"
    assert entries_before == TEN, "the draw changed the entries"
    assert texts_before == (page_view.PLACE_FORMAT, page_view.LEVEL_LABEL, page_view.ROW_SPACING)
    # Every cell text is rendered once and kept: the draws above warmed the caches, and after that
    # no render per frame for a text already rendered.
    renders: list[str] = []

    class CountingFont:
        def __init__(self, font: pygame.font.Font) -> None:
            self._font = font

        def render(self, text: str, antialias: bool, color: tuple[int, int, int]) -> pygame.Surface:
            renders.append(text)
            return self._font.render(text, antialias, color)

        def __getattr__(self, name: str) -> object:
            return getattr(self._font, name)

    def counting(size: int) -> CountingFont:
        return CountingFont(pygame.font.Font(None, size))

    for module in (page_view, look_view):
        monkeypatch.setattr(module, "screen_font", counting, raising=False)
    for _ in range(3):
        for entries in (ONE, FIVE, TEN):
            _drawn(SIZES[0], entries)
    assert renders == [], f"rendered again on later frames: {renders}"
