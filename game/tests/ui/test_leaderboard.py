"""Leaderboard page tests: the title, the empty-list line and the footer.

Contract: docs/contracts/systems/game-flow.md, Interface (ui/leaderboard.py) and Presentation,
Leaderboard page and the shared items (Text, Lines and blank lines, Cache, Only draws). The texts
and the font sizes are stand-ins from scope report DRA-125, Values needed (Leaderboard page,
Footer); the GDD does not hold them until UI-03 and UI-04.

Positions are read from the drawn pixels (`pygame.image.tobytes`), never from a font size. The page
is drawn on a black surface, so the ink is the text alone. Every text is compared with the same
text rendered here in the default font (`_reference`), and its place is worked out from the ink's
own offset in that render. The fonts' `get_linesize()` give the contract's rows (a blank line is
one body line), as in `test_game_over.py`. The footer's place is read from the instructions page,
which the contract names as its twin.
"""

from typing import NamedTuple

import pygame
import pytest

import ui.leaderboard as page_view
import ui.screen_look as look_view
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
