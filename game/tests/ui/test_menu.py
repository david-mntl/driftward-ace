"""Menu tests: the title, the three items in menu order, the marker on the selected one.

Contract: docs/contracts/systems/game-flow.md, Interface (ui/screen_look.py, ui/menu.py) and
Presentation, Menu and the shared items (Text, Lines and blank lines, Selection marker, Cache, Only
draws). The texts, the font sizes, the spacing and the marker are stand-ins from scope report
DRA-125, Values needed (Menu); the GDD does not hold them until UI-03 and UI-04.

Positions are read from the drawn pixels (`pygame.image.tobytes`), never from a font size. The
menu is drawn on a black surface, so the ink is the text alone. Every line is compared with the
same text rendered here in the default font (`_reference`), and each line's place is worked out
from the ink's own offset in that render. A label is measured on a picture where another item has
the marker, so the marker never touches the band being read. The fonts' `get_linesize()` and
`get_height()` give the contract's layout (one blank title line, the block's bottom), as in
`test_game_over.py`.
"""

from itertools import pairwise
from typing import NamedTuple

import pygame
import pytest

import ui.menu as menu_view
import ui.screen_look as look_view
from core.game_flow import MenuItem
from ui.menu import draw_menu
from ui.screen_look import screen_font

SIZES: tuple[tuple[int, int], ...] = ((640, 480), (800, 600))
"""Surfaces drawn on: the canvas (03-world-and-camera.md, screen_w, screen_h (guess)) and a larger
one, so the centering is shown to follow the surface and not a constant."""

TITLE_TEXT: str = "DRIFTWARD ACE"
TITLE_FONT_SIZE: int = 32
"""Source: scope report DRA-125, Values needed, Menu: title, 32 px."""

ITEMS: tuple[MenuItem, ...] = (MenuItem.PLAY, MenuItem.INSTRUCTIONS, MenuItem.LEADERBOARD)
"""Menu order, top first. Source: 02-game-flow.md, menu_items (locked)."""

LABELS: dict[MenuItem, str] = {
    MenuItem.PLAY: "Play",
    MenuItem.INSTRUCTIONS: "Instructions",
    MenuItem.LEADERBOARD: "Leaderboard",
}
ITEM_FONT_SIZE: int = 24
ITEM_SPACING: int = 40
"""Source: scope report DRA-125, Values needed, Menu: items at 24 px, 40 px apart."""

MARKER: str = ">"
"""Source: scope report DRA-125, Values needed, Menu: the selected item has `>` in front of it."""

TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Source: scope report DRA-125, Values needed (white text)."""

GRAY: int = 60
"""A background below white, for the checks that show nothing fills the surface."""

CENTER_TOLERANCE_PX: int = 1
"""A line's rect is placed by integer halves, so its center may be one px off the surface's."""

BLOCK_TOLERANCE_PX: int = 1
"""The block's top is an integer half, so its middle may be one px off the surface's."""

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


def _crop_at(levels: bytes, width: int, left: int, top: int, w: int, h: int) -> tuple[bytes, ...]:
    return tuple(levels[y * width + left : y * width + left + w] for y in range(top, top + h))


def _reference(text: str, size: int) -> _Ref:
    """``text`` in the default font at ``size``, white on black: its ink and the ink's offset."""
    image = pygame.font.Font(None, size).render(text, True, TEXT_COLOR)
    canvas = _surface(image.get_size())
    canvas.blit(image, (0, 0))
    band = _bands(canvas)[0]
    crop = _crop(_levels(canvas), canvas.get_width(), band)
    return _Ref(crop, image.get_width(), image.get_height(), band[2], band[0])


def _picture(selection: MenuItem, size: tuple[int, int], gray: int = 0) -> pygame.Surface:
    surface = _surface(size, gray)
    draw_menu(surface, selection)
    return surface


def _other(index: int) -> MenuItem:
    """An item that is not ``ITEMS[index]``, so that item is drawn with no marker."""
    return ITEMS[(index + 1) % len(ITEMS)]


def _assert_line(levels: bytes, width: int, band: Band, ref: _Ref, what: str) -> None:
    """The band is exactly ``ref``'s ink and its render is centered across ``width``."""
    assert (band[1] - band[0] + 1, band[3] - band[2] + 1) == (len(ref.crop), len(ref.crop[0])), (
        f"{what}: the ink is not the text's size"
    )
    assert _crop(levels, width, band) == ref.crop, f"{what}: not the default font's render"
    rect_left = band[2] - ref.ink_left
    assert abs(2 * rect_left + ref.image_width - width) <= CENTER_TOLERANCE_PX, (
        f"{what}: not centered across {width}: rect left {rect_left}, "
        f"render width {ref.image_width}"
    )


def _label_places(size: tuple[int, int]) -> dict[MenuItem, tuple[int, int]]:
    """Each label's render rect, (left, top), read from a picture where it has no marker."""
    places: dict[MenuItem, tuple[int, int]] = {}
    for index, item in enumerate(ITEMS):
        band = _bands(_picture(_other(index), size))[1 + index]
        ref = _reference(LABELS[item], ITEM_FONT_SIZE)
        places[item] = (band[2] - ref.ink_left, band[0] - ref.ink_top)
    return places


def test_the_menu_shows_the_title_then_the_three_items_each_centered(
    pygame_headless: None,
) -> None:
    title_ref = _reference(TITLE_TEXT, TITLE_FONT_SIZE)
    for size in SIZES:
        width = size[0]
        for index, item in enumerate(ITEMS):
            surface = _picture(_other(index), size)
            bands = _bands(surface)
            assert len(bands) == 1 + len(ITEMS), f"{size=} {item}: lines of ink: {bands}"
            levels = _levels(surface)
            _assert_line(levels, width, bands[0], title_ref, f"{size=} title")
            label_ref = _reference(LABELS[item], ITEM_FONT_SIZE)
            _assert_line(levels, width, bands[1 + index], label_ref, f"{size=} {item}")


def test_the_items_are_the_spacing_apart_and_the_block_is_centered_down_the_surface(
    pygame_headless: None,
) -> None:
    title_line = pygame.font.Font(None, TITLE_FONT_SIZE).get_linesize()
    item_height = pygame.font.Font(None, ITEM_FONT_SIZE).get_height()
    title_ref = _reference(TITLE_TEXT, TITLE_FONT_SIZE)
    for size in SIZES:
        height = size[1]
        title_top = _bands(_picture(ITEMS[0], size))[0][0] - title_ref.ink_top
        places = _label_places(size)
        tops = [places[item][1] for item in ITEMS]
        # One blank title line under the title, then the items' tops the spacing apart.
        assert tops[0] == title_top + 2 * title_line, f"{size=}: first item at {tops[0]}"
        for upper, lower in pairwise(tops):
            assert lower - upper == ITEM_SPACING, f"{size=}: items at {tops}"
        # The block, the title's top to the last item's bottom, is centered down the surface.
        block_bottom = tops[-1] + item_height
        assert abs(title_top + block_bottom - height) <= BLOCK_TOLERANCE_PX, (
            f"{size=}: the block {title_top}..{block_bottom} is not centered on {height}"
        )


def test_the_marker_is_only_left_of_the_selected_item_at_its_rows(
    pygame_headless: None,
) -> None:
    space = pygame.font.Font(None, ITEM_FONT_SIZE).size(" ")[0]
    item_height = pygame.font.Font(None, ITEM_FONT_SIZE).get_height()
    marker_ref = _reference(MARKER, ITEM_FONT_SIZE)
    marker_h, marker_w = len(marker_ref.crop), len(marker_ref.crop[0])
    for size in SIZES:
        width = size[0]
        places = _label_places(size)
        levels = {item: _levels(_picture(item, size)) for item in ITEMS}
        for item in ITEMS:
            label_left, label_top = places[item]
            label_ink_left = label_left + _reference(LABELS[item], ITEM_FONT_SIZE).ink_left
            for other in ITEMS:
                if other is item:
                    continue
                # What the marker adds: the pixels that are brighter with `item` selected.
                added = [
                    (i % width, i // width)
                    for i, (now, before) in enumerate(zip(levels[item], levels[other], strict=True))
                    if now > before
                ]
                assert added, f"{size=} {item}: no marker"
                assert {y for _, y in added} <= set(range(label_top, label_top + item_height)), (
                    f"{size=} {item}: marker ink outside the item's rows"
                )
                assert max(x for x, _ in added) < label_ink_left, (
                    f"{size=} {item}: marker ink not left of the label"
                )
                # One marker, in the label's font, its top on the label's top and its right edge
                # one space left of the label's left edge.
                expected_left = label_left - space - marker_ref.image_width + marker_ref.ink_left
                expected_top = label_top + marker_ref.ink_top
                bounds = (
                    min(x for x, _ in added),
                    min(y for _, y in added),
                    max(x for x, _ in added),
                    max(y for _, y in added),
                )
                assert bounds == (
                    expected_left,
                    expected_top,
                    expected_left + marker_w - 1,
                    expected_top + marker_h - 1,
                ), f"{size=} {item}: marker ink at {bounds}"
                assert (
                    _crop_at(levels[item], width, expected_left, expected_top, marker_w, marker_h)
                    == marker_ref.crop
                ), f"{size=} {item}: the marker is not {MARKER!r} in the label's font"


def test_the_labels_do_not_move_with_the_selection(pygame_headless: None) -> None:
    title_ref = _reference(TITLE_TEXT, TITLE_FONT_SIZE)
    for size in SIZES:
        width = size[0]
        places = _label_places(size)
        title_band = _bands(_picture(ITEMS[0], size))[0]
        for selection in ITEMS:
            levels = _levels(_picture(selection, size))
            assert _crop(levels, width, title_band) == title_ref.crop, f"{size=}: title moved"
            for item in ITEMS:
                ref = _reference(LABELS[item], ITEM_FONT_SIZE)
                left, top = places[item]
                got = _crop_at(
                    levels,
                    width,
                    left + ref.ink_left,
                    top + ref.ink_top,
                    len(ref.crop[0]),
                    len(ref.crop),
                )
                assert got == ref.crop, f"{size=} {selection=}: {item} moved or changed"


def test_the_menu_draws_the_same_pixels_twice_and_changes_nothing_but_the_surface(
    pygame_headless: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # Fonts are built once per size and kept.
    for font_size in (TITLE_FONT_SIZE, ITEM_FONT_SIZE):
        assert screen_font(font_size) is screen_font(font_size)
    texts_before = dict(menu_view.MENU_ITEM_TEXTS)
    caplog.set_level(0)
    for selection in ITEMS:
        first = pygame.image.tobytes(_picture(selection, SIZES[0]), "RGB")
        second = pygame.image.tobytes(_picture(selection, SIZES[0]), "RGB")
        assert first == second, f"{selection}: two draws, two pictures"
        # Nothing fills the background: every pixel with no ink stays the background's.
        on_gray = pygame.image.tobytes(_picture(selection, SIZES[0], gray=GRAY), "RGB")
        assert all(
            bright == GRAY for ink, bright in zip(first, on_gray, strict=True) if ink == 0
        ), f"{selection}: the draw changed pixels with no ink"
        # The same surface size in and out, and the one call is all it takes.
        surface = _picture(selection, SIZES[1])
        assert surface.get_size() == SIZES[1]
    assert caplog.records == [], "the view logged"
    assert dict(menu_view.MENU_ITEM_TEXTS) == texts_before
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

    for module in (menu_view, look_view):
        monkeypatch.setattr(module, "screen_font", counting, raising=False)
    for selection in ITEMS * 2:
        _picture(selection, SIZES[0])
    assert renders == [], f"rendered again on later frames: {renders}"
