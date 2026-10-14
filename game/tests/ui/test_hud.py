"""HUD layout tests. Contract: docs/contracts/systems/hud.md, Rules.

Positions are read from the drawn pixels, never from a font size or a line height. The HUD
and the debug overlay must never overlap (Director, scope report DRA-13, Decision log).
"""

import pygame

from core.scroll import Scroll
from core.ship import spawn
from ui.debug_overlay import draw_debug_overlay, overlay_text_bottom
from ui.hud import HUD_COLOR, HUD_LINE_SPACING, HUD_MARGIN, HUD_OVERLAY_GAP, HUD_TOP, draw_hud

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

SCROLL = Scroll(ticks=130, scrolled_ticks=100)
"""100 scrolled ticks, 11 m: a multi-digit readout with width."""

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


def _hud(below_overlay: bool) -> Pixels:
    surface = _blank()
    draw_hud(surface, SCROLL, below_overlay)
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
    draw_hud(covered, SCROLL, True)
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
