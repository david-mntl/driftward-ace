"""Instructions page tests: the title, six sections with an outline icon, and the footer.

Contract: docs/contracts/systems/game-flow.md, Interface (ui/instructions.py) and Presentation,
Instructions page and the shared items (Text, Lines and blank lines, Cache, Only draws). The texts,
the font sizes and the icon's size are stand-ins from scope report DRA-125, Values needed
(Instructions page, Footer); the GDD does not hold them until UI-03 and UI-04. The icon's outline
width comes from the contract (Presentation, Instructions page).

Positions are read from the drawn pixels (`pygame.image.tobytes`), never from a font size. The page
is drawn on a black surface, so the ink is the text and the icons alone. Every text is compared
with the same text rendered here in the default font (`_reference`), and its place is worked out
from the ink's own offset in that render. The fonts' `get_linesize()` give the contract's rows (a
blank line is one body line), as in `test_game_over.py`. A heading row's icon is found by its top
edge: the row's first ink row holds the icon alone, because the title is centered in the row.
"""

from itertools import combinations, pairwise
from typing import NamedTuple

import pygame
import pytest

import ui.instructions as page_view
import ui.screen_look as look_view
from ui.instructions import draw_instructions
from ui.screen_look import screen_font

SIZES: tuple[tuple[int, int], ...] = ((640, 480), (800, 600))
"""Surfaces drawn on: the canvas (03-world-and-camera.md, screen_w, screen_h (guess)) and a larger
one, so the centering is shown to follow the surface and not a constant."""

TITLE_TEXT: str = "HOW TO PLAY"
TITLE_FONT_SIZE: int = 32
BODY_FONT_SIZE: int = 16
"""Source: scope report DRA-125, Values needed, Instructions page: title 32 px, sections 16 px."""

SECTIONS: tuple[tuple[str, str], ...] = (
    ("FLY", "Arrows thrust. Let go and you keep drifting. Gravity never stops."),
    ("PAUSE", "Enter or Space pauses. Press it again to go on."),
    ("GRAZE", "Skim past a hazard without touching it to score points."),
    ("WARNING", "A warning shows where a hazard will come in. Get clear."),
    ("FALL", "Fall off the bottom and you lose a life."),
    ("COINS", "Coins are points. The good ones sit near danger."),
)
"""The six (title, line) pairs, in order. Source: scope report DRA-125, Values needed."""

ICON_SIZE: int = 16
"""Source: scope report DRA-125, Values needed: a 16 x 16 px white outline square."""

ICON_LINE_WIDTH: int = 1
"""Source: contract game-flow.md, Presentation, Instructions page: the plainest outline."""

FOOTER_TEXT: str = "Press Enter or Space to go back."
"""Source: scope report DRA-125, Values needed, Footer (16 px)."""

TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Source: scope report DRA-125, Values needed (white text)."""

GRAY: int = 60
"""A background below white, for the checks that show nothing fills the surface."""

TOLERANCE_PX: int = 1
"""Rects are placed by integer halves: a center, or a vertical middle, may be one px off."""

Band = tuple[int, int, int, int]
"""One run of ink: top row, bottom row, left column, right column, all inclusive."""


class _Ref(NamedTuple):
    """A text rendered here: its ink rectangle and where that sits in the render."""

    crop: tuple[bytes, ...]
    image_width: int
    image_height: int
    ink_left: int
    ink_top: int


class _Section(NamedTuple):
    """One section as drawn: the icon's top-left, and the title's and the line's ink."""

    icon_left: int
    icon_top: int
    title: Band
    line: Band


def _surface(size: tuple[int, int], gray: int = 0) -> pygame.Surface:
    surface = pygame.Surface(size)
    surface.fill((gray, gray, gray))
    return surface


def _levels(surface: pygame.Surface) -> bytes:
    """The red level of every pixel, row by row. Every picture here is gray, so it is the level."""
    return pygame.image.tobytes(surface, "RGB")[::3]


def _ink_bounds(levels: bytes, width: int, rows: range, columns: range) -> Band | None:
    """The ink inside a window of rows and columns, or None."""
    found = [(y, x) for y in rows for x in columns if levels[y * width + x]]
    if not found:
        return None
    ys = [y for y, _ in found]
    xs = [x for _, x in found]
    return min(ys), max(ys), min(xs), max(xs)


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


def _body_line() -> int:
    """One body line's height: the font's line size (contract: Lines and blank lines)."""
    return pygame.font.Font(None, BODY_FONT_SIZE).get_linesize()


def _row_height() -> int:
    """A heading row's height: the taller of the icon and a body line."""
    return max(ICON_SIZE, _body_line())


def _page(size: tuple[int, int], gray: int = 0) -> pygame.Surface:
    surface = _surface(size, gray)
    draw_instructions(surface)
    return surface


def _sections(surface: pygame.Surface) -> tuple[Band, list[_Section], Band]:
    """The title's ink, each section, and the footer's ink, read from the pixels."""
    width = surface.get_width()
    levels = _levels(surface)
    bands = _bands(surface)
    assert len(bands) == len(SECTIONS) + 2, f"runs of ink: {bands}"
    row_height = _row_height()
    sections: list[_Section] = []
    for band in bands[1:-1]:
        top = band[0]
        # The first ink row of a heading row is the icon's top edge alone.
        edge = [x for x in range(width) if levels[top * width + x]]
        icon_left = edge[0]
        assert edge == list(range(icon_left, icon_left + ICON_SIZE)), f"icon top edge: {edge}"
        title = _ink_bounds(
            levels, width, range(top, top + row_height), range(icon_left + ICON_SIZE, width)
        )
        line = _ink_bounds(levels, width, range(top + row_height, band[1] + 1), range(width))
        assert title is not None, f"row at {top}: no title"
        assert line is not None, f"row at {top}: no line"
        sections.append(_Section(icon_left, top, title, line))
    return bands[0], sections, bands[-1]


def _rects_of(title: Band, sections: list[_Section], footer: Band) -> list[tuple[str, pygame.Rect]]:
    """The ink rectangle of every element on the page, named."""

    def rect(band: Band) -> pygame.Rect:
        return pygame.Rect(band[2], band[0], band[3] - band[2] + 1, band[1] - band[0] + 1)

    rects = [("page title", rect(title))]
    for index, section in enumerate(sections):
        icon = pygame.Rect(section.icon_left, section.icon_top, ICON_SIZE, ICON_SIZE)
        rects.append((f"icon {index}", icon))
        rects.append((f"heading {index}", rect(section.title)))
        rects.append((f"line {index}", rect(section.line)))
    rects.append(("footer", rect(footer)))
    return rects


def test_the_page_has_the_title_then_six_sections_each_an_icon_a_title_and_a_line(
    pygame_headless: None,
) -> None:
    title_ref = _reference(TITLE_TEXT, TITLE_FONT_SIZE)
    footer_ref = _reference(FOOTER_TEXT, BODY_FONT_SIZE)
    space = pygame.font.Font(None, BODY_FONT_SIZE).size(" ")[0]
    row_height = _row_height()
    assert page_view.INSTRUCTION_SECTIONS == SECTIONS
    assert page_view.ICON_SIZE == ICON_SIZE
    assert page_view.ICON_LINE_WIDTH == ICON_LINE_WIDTH
    for size in SIZES:
        width, height = size
        surface = _page(size)
        levels = _levels(surface)
        title, sections, footer = _sections(surface)
        # The page title and the footer: the texts, centered.
        for band, ref, what in ((title, title_ref, "title"), (footer, footer_ref, "footer")):
            assert _crop(levels, width, band) == ref.crop, f"{size=} {what}: not the render"
            rect_left = band[2] - ref.ink_left
            assert abs(2 * rect_left + ref.image_width - width) <= TOLERANCE_PX, (
                f"{size=} {what}: not centered across {width}"
            )
        assert len(sections) == len(SECTIONS)
        for index, ((name, line), section) in enumerate(zip(SECTIONS, sections, strict=True)):
            what = f"{size=} section {index} {name}"
            # The icon: a square outline of the icon's size, width 1, nothing inside it.
            left, top = section.icon_left, section.icon_top
            for y in range(ICON_SIZE):
                for x in range(ICON_SIZE):
                    on_edge = min(x, y, ICON_SIZE - 1 - x, ICON_SIZE - 1 - y) < ICON_LINE_WIDTH
                    expected = 255 if on_edge else 0
                    got = levels[(top + y) * width + left + x]
                    assert got == expected, f"{what}: icon pixel ({x}, {y}) is {got}"
            # Its title, one space right of the icon, in the body font.
            heading_ref = _reference(name, BODY_FONT_SIZE)
            assert _crop(levels, width, section.title) == heading_ref.crop, f"{what}: title"
            assert section.title[2] == left + ICON_SIZE + space + heading_ref.ink_left, (
                f"{what}: the title is not one space right of the icon"
            )
            # The icon and the title are centered together across the width.
            together = ICON_SIZE + space + heading_ref.image_width
            assert abs(2 * left + together - width) <= TOLERANCE_PX, f"{what}: heading off center"
            # Each is centered vertically in the row.
            title_top = section.title[0] - heading_ref.ink_top
            assert abs(title_top - top - (row_height - heading_ref.image_height) // 2) <= (
                TOLERANCE_PX
            ), f"{what}: the title is not centered in its row"
            # Its line, under the heading row, centered.
            line_ref = _reference(line, BODY_FONT_SIZE)
            assert _crop(levels, width, section.line) == line_ref.crop, f"{what}: line"
            assert section.line[0] - line_ref.ink_top == top + row_height, (
                f"{what}: the line is not directly under its heading row"
            )
            line_left = section.line[2] - line_ref.ink_left
            assert abs(2 * line_left + line_ref.image_width - width) <= TOLERANCE_PX, (
                f"{what}: the line is not centered"
            )
        # Every row is inside the surface and no two overlap.
        surface_rect = pygame.Rect(0, 0, width, height)
        rects = _rects_of(title, sections, footer)
        for name, rect in rects:
            assert surface_rect.contains(rect), f"{size=} {name} {rect} is not inside the surface"
        for (first, one), (second, two) in combinations(rects, 2):
            assert not one.colliderect(two), f"{size=} {first} {one} overlaps {second} {two}"


def test_the_rows_are_one_under_the_other_with_blank_lines_and_the_block_is_centered(
    pygame_headless: None,
) -> None:
    title_line = pygame.font.Font(None, TITLE_FONT_SIZE).get_linesize()
    body_line = _body_line()
    row_height = _row_height()
    title_ref = _reference(TITLE_TEXT, TITLE_FONT_SIZE)
    for size in SIZES:
        height = size[1]
        title, sections, footer = _sections(_page(size))
        title_top = title[0] - title_ref.ink_top
        tops = [section.icon_top for section in sections]
        # The title, a blank line, then the first heading row.
        assert tops[0] == title_top + title_line + body_line, f"{size=}: first row at {tops[0]}"
        # Heading row, line row, then a blank line, for each section.
        for upper, lower in pairwise(tops):
            assert lower - upper == row_height + 2 * body_line, f"{size=}: rows at {tops}"
        # The block, the title's top to the last line's bottom, is centered between the surface's
        # top and the footer's top.
        footer_top = height - 2 * body_line
        block_bottom = tops[-1] + row_height + body_line
        assert abs(title_top + block_bottom - footer_top) <= TOLERANCE_PX, (
            f"{size=}: the block {title_top}..{block_bottom} is not centered above {footer_top}"
        )
        assert footer[0] > block_bottom, f"{size=}: the footer is inside the block"


def test_the_footer_is_near_the_bottom_with_one_blank_line_under_it(
    pygame_headless: None,
) -> None:
    body_line = _body_line()
    footer_ref = _reference(FOOTER_TEXT, BODY_FONT_SIZE)
    for size in SIZES:
        width, height = size
        surface = _page(size)
        _, _, footer = _sections(surface)
        # The footer's line sits two body lines above the bottom: its own line, then one blank.
        assert footer[0] - footer_ref.ink_top == height - 2 * body_line, f"{size=}: footer row"
        levels = _levels(surface)
        blank = levels[(height - body_line) * width :]
        assert not any(blank), f"{size=}: ink in the last body line"
        assert footer[1] < height - body_line, f"{size=}: the footer reaches the blank line"


def test_the_instructions_draw_the_same_pixels_twice_and_change_nothing_but_the_surface(
    pygame_headless: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    sections_before = tuple(page_view.INSTRUCTION_SECTIONS)
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
    assert tuple(page_view.INSTRUCTION_SECTIONS) == sections_before
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
