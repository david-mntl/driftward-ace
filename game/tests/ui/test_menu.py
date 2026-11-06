"""Menu tests: the title, the three items in menu order, the lit one, the hint and the rulers.

Contract: docs/contracts/systems/screens.md, Interface (ui/menu.py) and Presentation, Menu;
10-ui.md, `menu_screen`, `menu_look` and `menu_hint`. Every size and color is read from the real
tuning/screens.json through the `screen_rules` fixture.

Positions are read from the drawn pixels, never from a font size: the menu is drawn on a black
surface, so a bright pixel is ink. The lit (selected) item has pale text and cyan brackets; the
others are dim, so a pale pixel (every channel above ``LIT_LEVEL``) marks the lit item only.
"""

from itertools import pairwise

import pygame
import pytest

from core.game_flow import MenuItem
from ui.menu import MENU_HINT_TEXT, draw_menu
from ui.screen_look import ScreenLook
from ui.screen_rules import ScreenRules

SIZES: tuple[tuple[int, int], ...] = ((856, 518), (640, 480), (1000, 700))
"""Surfaces drawn on: the window (10-ui.md, window_screens), the play-area size and a larger one,
so the centering is shown to follow the surface and not a constant."""

ITEMS: tuple[MenuItem, ...] = (MenuItem.PLAY, MenuItem.INSTRUCTIONS, MenuItem.LEADERBOARD)
"""Menu order, top first. Source: 02-game-flow.md, menu_items (locked)."""

INK_LEVEL: int = 60
"""A pixel with a channel above this is ink."""

LIT_LEVEL: int = 200
"""A pixel with every channel above this is the lit item's pale text."""

CENTER_TOLERANCE_PX: int = 3
"""Slack for centering read from ink (glyph bearings, the trailing letter-spacing)."""


def _menu(
    look: ScreenLook,
    selection: MenuItem,
    size: tuple[int, int] = SIZES[0],
    gray: int = 0,
) -> pygame.Surface:
    surface = pygame.Surface(size)
    surface.fill((gray, gray, gray))
    draw_menu(surface, look, selection)
    return surface


def _ink(surface: pygame.Surface, area: pygame.Rect, level: int = INK_LEVEL) -> pygame.Rect | None:
    """The rectangle of the bright pixels inside ``area``, in surface coordinates; None if none."""
    clipped = area.clip(surface.get_rect())
    dark = pygame.mask.from_threshold(
        surface.subsurface(clipped), (0, 0, 0, 255), (level, level, level, 255)
    )
    dark.invert()
    boxes = dark.get_bounding_rects()
    if not boxes:
        return None
    return boxes[0].unionall(boxes[1:]).move(clipped.topleft)


def _lit_count(surface: pygame.Surface, area: pygame.Rect) -> int:
    """How many pixels inside ``area`` are pale: every channel above ``LIT_LEVEL``."""
    part = surface.subsurface(area.clip(surface.get_rect()))
    pale = pygame.mask.from_threshold(part, (255, 255, 255, 255), (255 - LIT_LEVEL,) * 3 + (255,))
    return pale.count()


def _rows(surface: pygame.Surface) -> list[tuple[int, int]]:
    """Each run of pixel rows holding ink between the rulers: top row and bottom row."""
    rulers_w = 30
    width, height = surface.get_size()
    area = pygame.Rect(rulers_w, 0, width - 2 * rulers_w, height)
    bands: list[tuple[int, int]] = []
    start: int | None = None
    for y in range(height + 1):
        row = pygame.Rect(area.left, y, area.width, 1)
        inked = y < height and _ink(surface, row) is not None
        if inked and start is None:
            start = y
        elif not inked and start is not None:
            bands.append((start, y - 1))
            start = None
    return bands


def _item_ink(look: ScreenLook, size: tuple[int, int]) -> list[pygame.Rect]:
    """The ink of each item, found from the bands between the title and the hint."""
    surface = _menu(look, MenuItem.PLAY, size)
    bands = _rows(surface)
    assert len(bands) == 5, f"{size}: expected title, 3 items and hint, got bands {bands}"
    return [
        _ink(surface, pygame.Rect(30, top, size[0] - 60, bottom - top + 1))
        or pygame.Rect(0, 0, 0, 0)
        for top, bottom in bands[1:4]
    ]


def test_three_items_between_the_title_and_the_hint_in_menu_order(look: ScreenLook) -> None:
    for size in SIZES:
        items = _item_ink(look, size)
        assert [i.top for i in items] == sorted(i.top for i in items), f"{size}: items out of order"
        # With the last item selected, the first two are dim: PLAY is shorter than INSTRUCTIONS.
        surface = _menu(look, MenuItem.LEADERBOARD, size)
        areas = [pygame.Rect(30, i.top - 6, size[0] - 60, i.height + 12) for i in items]
        dim = [_ink(surface, area) for area in areas[:2]]
        assert dim[0] is not None
        assert dim[1] is not None
        assert dim[0].width < dim[1].width, f"{size}: PLAY is not shorter than INSTRUCTIONS"


def test_title_is_above_the_items_and_centered(look: ScreenLook) -> None:
    for size in SIZES:
        surface = _menu(look, MenuItem.PLAY, size)
        bands = _rows(surface)
        title = _ink(
            surface, pygame.Rect(30, bands[0][0], size[0] - 60, bands[0][1] - bands[0][0] + 1)
        )
        assert title is not None
        assert abs(title.centerx - size[0] / 2) <= CENTER_TOLERANCE_PX, f"{size}: title off center"
        assert bands[0][1] < bands[1][0], f"{size}: the title touches the first item"


def test_items_are_centered_and_evenly_spaced(look: ScreenLook, screen_rules: ScreenRules) -> None:
    menu = screen_rules.menu
    for size in SIZES:
        items = _item_ink(look, size)
        for item in items:
            assert abs(item.centerx - size[0] / 2) <= CENTER_TOLERANCE_PX, f"{size}: off center"
        steps = [b.centery - a.centery for a, b in pairwise(items)]
        assert all(abs(step - (menu.item_h + menu.item_gap)) <= 3 for step in steps), (
            f"{size}: item steps {steps}, expected {menu.item_h + menu.item_gap}"
        )


def test_block_is_centered_vertically(look: ScreenLook, screen_rules: ScreenRules) -> None:
    menu = screen_rules.menu
    for size in SIZES:
        surface = _menu(look, MenuItem.PLAY, size)
        bands = _rows(surface)
        # The block runs from the title's top to the last item's bottom edge (its box, not its ink).
        last = _item_ink(look, size)[-1]
        bottom = last.centery + menu.item_h // 2
        middle = (bands[0][0] + bottom) / 2
        assert abs(middle - size[1] / 2) <= 10, f"{size}: block middle {middle}, not {size[1] / 2}"


def test_exactly_the_selected_item_is_lit(look: ScreenLook) -> None:
    for size in SIZES:
        spots = _item_ink(look, size)
        areas = [pygame.Rect(30, s.top - 6, size[0] - 60, s.height + 12) for s in spots]
        for selection in ITEMS:
            surface = _menu(look, selection, size)
            lit = [_lit_count(surface, area) for area in areas]
            index = ITEMS.index(selection)
            assert lit[index] > 0, f"{size}: {selection} is not lit"
            assert all(count == 0 for i, count in enumerate(lit) if i != index), (
                f"{size}: {selection} selected but lit counts are {lit}"
            )


def test_selected_item_has_cyan_brackets_and_the_others_do_not(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    cyan = screen_rules.palette["frame_lights"]
    spots = _item_ink(look, SIZES[0])
    areas = [pygame.Rect(30, s.top - 6, SIZES[0][0] - 60, s.height + 12) for s in spots]
    for selection in ITEMS:
        surface = _menu(look, selection)
        counts = [
            pygame.mask.from_threshold(
                surface.subsurface(area), (*cyan, 255), (40, 40, 40, 255)
            ).count()
            for area in areas
        ]
        index = ITEMS.index(selection)
        assert counts[index] > 0, f"{selection}: no cyan brackets"
        assert all(c == 0 for i, c in enumerate(counts) if i != index), f"cyan elsewhere: {counts}"


def test_changing_the_selection_changes_only_the_two_items(look: ScreenLook) -> None:
    size = SIZES[0]
    spots = _item_ink(look, size)
    first = _menu(look, MenuItem.PLAY)
    second = _menu(look, MenuItem.INSTRUCTIONS)
    width = size[0]
    a = pygame.image.tobytes(first, "RGB")
    b = pygame.image.tobytes(second, "RGB")
    changed = [
        y
        for y in range(size[1])
        if a[y * width * 3 : (y + 1) * width * 3] != b[y * width * 3 : (y + 1) * width * 3]
    ]
    assert changed, "the selection did not move"
    message = f"rows {changed[0]}..{changed[-1]} changed, outside the first two items"
    assert spots[0].top - 12 <= changed[0], message
    assert changed[-1] <= spots[1].bottom + 12, message


def test_hint_is_the_last_line_and_centered(look: ScreenLook, screen_rules: ScreenRules) -> None:
    menu = screen_rules.menu
    assert MENU_HINT_TEXT == "Up & Down to choose. Enter to start."
    for size in SIZES:
        surface = _menu(look, MenuItem.PLAY, size)
        bands = _rows(surface)
        hint = _ink(
            surface, pygame.Rect(30, bands[-1][0], size[0] - 60, bands[-1][1] - bands[-1][0] + 1)
        )
        assert hint is not None
        assert hint.bottom <= size[1] - menu.hint_bottom, f"{size}: the hint is too low"
        assert hint.bottom >= size[1] - menu.hint_bottom - 6, f"{size}: the hint is too high"
        assert abs(hint.centerx - size[0] / 2) <= CENTER_TOLERANCE_PX, f"{size}: hint off center"
        assert bands[-1][0] > bands[-2][1], f"{size}: the hint touches the last item"


def test_rulers_are_drawn_and_nothing_else_is_near_the_sides(
    look: ScreenLook, screen_rules: ScreenRules
) -> None:
    rulers = screen_rules.rulers
    for size in SIZES:
        surface = _menu(look, MenuItem.PLAY, size)
        assert _ink(surface, pygame.Rect(0, 0, rulers.inset_x + rulers.w, size[1])) is not None
        assert (
            _ink(
                surface,
                pygame.Rect(
                    size[0] - rulers.inset_x - rulers.w, 0, rulers.inset_x + rulers.w, size[1]
                ),
            )
            is not None
        )
        free = pygame.Rect(rulers.inset_x + rulers.w + 1, 0, 80, size[1])
        assert _ink(surface, free) is None, f"{size}: ink between the ruler and the content"


def test_the_menu_never_fills_the_background(look: ScreenLook) -> None:
    surface = _menu(look, MenuItem.PLAY, gray=60)
    for point in ((3, 3), (50, 200), (SIZES[0][0] - 4, 300)):
        assert surface.get_at(point)[:3] == (60, 60, 60), f"{point} was painted over"


def test_redraw_is_the_same_picture(look: ScreenLook) -> None:
    first = pygame.image.tobytes(_menu(look, MenuItem.LEADERBOARD), "RGB")
    assert pygame.image.tobytes(_menu(look, MenuItem.LEADERBOARD), "RGB") == first


@pytest.mark.parametrize("selection", ITEMS)
def test_every_selection_draws(look: ScreenLook, selection: MenuItem) -> None:
    assert _ink(_menu(look, selection), pygame.Rect(0, 0, *SIZES[0])) is not None
