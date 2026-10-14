"""HUD layout tests. Contract: docs/contracts/systems/hud.md, Rules and Presentation.

Positions are read from the drawn pixels, never from a font size or a line height. The HUD
and the debug overlay must never overlap (Director, scope report DRA-13, Decision log). The
hearts show the lives left (scope report DRA-23, Values needed).
"""

import pygame

from core.run import Run
from core.scroll import Scroll
from core.ship import spawn
from ui.debug_overlay import draw_debug_overlay, overlay_text_bottom
from ui.hud import (
    HEART_COLOR,
    HEART_GAP,
    HEART_MARGIN,
    HEART_SIZE,
    HUD_COLOR,
    HUD_LINE_SPACING,
    HUD_MARGIN,
    HUD_OVERLAY_GAP,
    HUD_TOP,
    draw_hud,
)

SURFACE_SIZE: tuple[int, int] = (640, 480)
"""Test surface. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

SCREEN_H: int = 480
"""Source: 03-world-and-camera.md, screen_h (guess)."""

TOP_LINE_RATIO: float = 0.35
"""Source: 03-world-and-camera.md, top_line_ratio (locked)."""

TOP_LINE_ROW: int = int(SCREEN_H * TOP_LINE_RATIO)
"""Row 168 of the overlay's top line. Source: 03-world-and-camera.md, rule 2."""

FLOOR_ROW: int = SCREEN_H - 1
"""Row 479 of the overlay's floor line. Source: 03-world-and-camera.md, rule 3."""

BLACK: tuple[int, int, int] = (0, 0, 0)
"""Test surface fill. Source: 12-art-and-audio.md, placeholder_bg (guess)."""

OVERLAY_GREEN: tuple[int, int, int] = (0, 255, 0)
"""Source: 10-ui.md, debug_overlay_color (guess)."""

WHITE: tuple[int, int, int] = (255, 255, 255)
"""Readout color. Source: scope report DRA-13, temporary stand-in."""

# Scope report DRA-13, HUD layout (approved by the Director, not in the GDD).
assert HUD_COLOR == WHITE
assert (HUD_MARGIN, HUD_LINE_SPACING, HUD_TOP, HUD_OVERLAY_GAP) == (4, 20, 4, 4)

# Scope report DRA-23, Values needed (hearts, approved by the Director, not in the GDD).
assert HEART_COLOR == WHITE
assert (HEART_SIZE, HEART_GAP, HEART_MARGIN) == (24, 8, 8)

SCROLL = Scroll(ticks=130, scrolled_ticks=100)
"""100 scrolled ticks, 11 m: a multi-digit readout with width."""

SLOT_LEFTS: tuple[int, ...] = (608, 576, 544)
"""Box left column of slots 0, 1 and 2, slot 0 the rightmost. Source: systems/hud.md,
Presentation (640 - 8 - 24 - i * 32), scope report DRA-23, Values needed."""

HEART_TOP: int = 8
"""Box top row of every heart. Source: scope report DRA-23, Values needed (8 px from the top)."""

HEART_AREA_LEFT: int = 536
"""Left column of the hearts area: the leftmost box minus the margin. Source: systems/hud.md,
Presentation."""

HEART_AREA_ROWS: int = 40
"""Rows 0 to 39 of the hearts area. Source: task DRA-23-05, test 2."""

Pixels = list[list[tuple[int, int, int]]]


def _pixels(surface: pygame.Surface) -> Pixels:
    width, height = surface.get_size()
    data = pygame.image.tobytes(surface, "RGB")
    row_len = width * 3
    return [
        [(data[i], data[i + 1], data[i + 2]) for i in range(y * row_len, (y + 1) * row_len, 3)]
        for y in range(height)
    ]


def _blank() -> pygame.Surface:
    surface = pygame.Surface(SURFACE_SIZE)
    surface.fill(BLACK)
    return surface


def _run(lives: int) -> Run:
    return Run(ship=spawn(), scroll=SCROLL, lives=lives)


def _hud(below_overlay: bool, lives: int = 0) -> Pixels:
    """The HUD on a black surface. The readout tests use 0 lives: only the readout is white."""
    surface = _blank()
    draw_hud(surface, _run(lives), below_overlay)
    return _pixels(surface)


def _overlay() -> Pixels:
    surface = _blank()
    draw_debug_overlay(surface, spawn())
    return _pixels(surface)


def _ink(rows: Pixels, ignore_rows: tuple[int, ...] = ()) -> list[tuple[int, int]]:
    """(x, y) of every non-black pixel outside ignore_rows."""
    return [
        (x, y)
        for y, row in enumerate(rows)
        if y not in ignore_rows
        for x, p in enumerate(row)
        if p != BLACK
    ]


def _white(rows: Pixels) -> list[tuple[int, int]]:
    return [(x, y) for y, row in enumerate(rows) for x, p in enumerate(row) if p == WHITE]


def test_hud_normal_layout_leaves_line_one_empty(pygame_headless: None) -> None:
    rows = _hud(below_overlay=False)
    ink = _ink(rows)
    assert _white(rows), "no white readout pixel drawn"
    first_row = HUD_TOP + HUD_LINE_SPACING
    top = min(y for _, y in ink)
    left = min(x for x, _ in ink)
    assert top >= first_row, f"ink above HUD line 2: row {top}"
    assert left >= HUD_MARGIN, f"ink left of the margin: column {left}"
    assert not [1 for _, y in ink if y < first_row], "something drawn on HUD line 1"


def test_hud_never_overlaps_the_debug_overlay(pygame_headless: None) -> None:
    overlay = _ink(_overlay(), ignore_rows=(TOP_LINE_ROW, FLOOR_ROW))
    hud = _white(_hud(below_overlay=True))
    assert overlay, "no overlay text drawn"
    assert hud, "no white readout pixel drawn"
    lowest_overlay = max(y for _, y in overlay)
    highest_hud = min(y for _, y in hud)
    assert highest_hud > lowest_overlay, f"HUD row {highest_hud} not below overlay {lowest_overlay}"


def test_hud_keeps_the_gap_below_the_overlay(pygame_headless: None) -> None:
    overlay = _ink(_overlay(), ignore_rows=(TOP_LINE_ROW, FLOOR_ROW))
    hud = _white(_hud(below_overlay=True))
    bottom = overlay_text_bottom()
    assert bottom > max(y for _, y in overlay), "overlay_text_bottom is not below the overlay text"
    assert min(y for _, y in hud) >= bottom + HUD_OVERLAY_GAP + HUD_LINE_SPACING


def test_hud_does_not_jump_when_the_overlay_is_hidden(pygame_headless: None) -> None:
    overlay_only = _overlay()
    covered = _blank()
    draw_debug_overlay(covered, spawn())
    draw_hud(covered, _run(0), True)
    covered_rows = _pixels(covered)
    hidden_rows = _hud(below_overlay=True)
    overlay_pixels = set(_ink(overlay_only))
    for y, row in enumerate(hidden_rows):
        for x, pixel in enumerate(row):
            if (x, y) not in overlay_pixels:
                assert covered_rows[y][x] == pixel, f"HUD pixel differs at {(x, y)}"
    assert _white(hidden_rows), "no white readout pixel drawn"


def test_hud_stays_above_the_top_line(pygame_headless: None) -> None:
    for below_overlay in (False, True):
        hud = _white(_hud(below_overlay))
        assert hud, f"no white readout pixel drawn, below_overlay={below_overlay}"
        lowest = max(y for _, y in hud)
        assert lowest < TOP_LINE_ROW, f"HUD row {lowest} reaches the top line, {below_overlay=}"


def _box_white(rows: Pixels, left: int) -> list[tuple[int, int]]:
    """White (x, y) inside the heart box whose top-left is (left, HEART_TOP)."""
    return [
        (x, y)
        for y in range(HEART_TOP, HEART_TOP + HEART_SIZE)
        for x in range(left, left + HEART_SIZE)
        if rows[y][x] == WHITE
    ]


def _box_pixels(rows: Pixels, left: int) -> Pixels:
    return [rows[y][left : left + HEART_SIZE] for y in range(HEART_TOP, HEART_TOP + HEART_SIZE)]


def test_hud_draws_one_heart_per_life(pygame_headless: None) -> None:
    for lives in (3, 2, 1, 0):
        rows = _hud(below_overlay=False, lives=lives)
        filled = {SLOT_LEFTS[slot] for slot in range(lives)}
        for left in SLOT_LEFTS:
            has_white = bool(_box_white(rows, left))
            assert has_white == (left in filled), f"{lives=}: box at {left}, white={has_white}"
        inside = {
            (x, y)
            for left in filled
            for x in range(left, left + HEART_SIZE)
            for y in range(HEART_TOP, HEART_TOP + HEART_SIZE)
        }
        stray = [
            (x, y)
            for (x, y) in _white(rows)
            if x >= HEART_AREA_LEFT and y < HEART_AREA_ROWS and (x, y) not in inside
        ]
        assert not stray, f"{lives=}: white pixels outside the filled boxes, first {stray[:3]}"


def test_hud_lost_life_removes_the_leftmost_heart_only(pygame_headless: None) -> None:
    three = _hud(below_overlay=False, lives=3)
    two = _hud(below_overlay=False, lives=2)
    for left in SLOT_LEFTS[:2]:
        assert _box_white(three, left), f"no heart at {left} with 3 lives"
        assert _box_pixels(two, left) == _box_pixels(three, left), f"heart at {left} changed"
    assert not _box_white(two, SLOT_LEFTS[2]), "leftmost heart still drawn with 2 lives"


def test_hud_hearts_ignore_the_overlay(pygame_headless: None) -> None:
    def hearts(below_overlay: bool) -> Pixels:
        return [row[HEART_AREA_LEFT:] for row in _hud(below_overlay, lives=3)]

    normal = hearts(below_overlay=False)
    debug = hearts(below_overlay=True)
    assert any(WHITE in row for row in normal), "no heart drawn"
    assert normal == debug, "hearts moved with below_overlay"
    heart_pixels = {
        (x, y)
        for y, row in enumerate(_hud(below_overlay=True, lives=3))
        for x, p in enumerate(row)
        if x >= HEART_AREA_LEFT and p == WHITE
    }
    overlay_text = {
        (x, y)
        for y, row in enumerate(_overlay())
        for x, p in enumerate(row)
        if p == OVERLAY_GREEN and y not in (TOP_LINE_ROW, FLOOR_ROW)
    }
    assert overlay_text, "no overlay text drawn"
    assert not heart_pixels & overlay_text, "a heart pixel shares a place with overlay text"
