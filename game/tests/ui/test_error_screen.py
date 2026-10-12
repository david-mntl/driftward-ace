"""Error screen tests. Contract: docs/contracts/systems/app.md, Presentation.

Positions are read from the drawn pixels, never from the font size. Every expected color
comes from the GDD.
"""

import pygame

from ui.error_screen import draw_error_screen
from ui.look import BACKGROUND

SURFACE_SIZE: tuple[int, int] = (640, 480)
"""Test surface. Source: task DRA-5-02 (03-world-and-camera.md, screen_w, screen_h)."""

PLACEHOLDER_BG: tuple[int, int, int] = (0, 0, 0)
"""Source: 12-art-and-audio.md, placeholder_bg (guess)."""

ERROR_TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Source: 10-ui.md, error_text_color (guess)."""

DETAIL: str = "ValueError: boom"
"""A debug-mode detail line, `<ErrorType>: <message>`. Source: 10-ui.md, error_debug_line."""

PREFILL: tuple[int, int, int] = (12, 200, 90)
"""Any color that isn't the background, to prove the fill replaces it. Test input only."""

CENTER_TOLERANCE_PX: float = 2.0
"""Slack for antialiasing and glyph side bearings when centering is read from ink."""

Band = tuple[int, int, int, int]
"""One line of ink: top row, bottom row, left column, right column, all inclusive."""


def _draw(detail: str | None) -> pygame.Surface:
    surface = pygame.Surface(SURFACE_SIZE)
    draw_error_screen(surface, detail)
    return surface


def _pixels(surface: pygame.Surface) -> list[list[tuple[int, int, int]]]:
    """Rows of RGB pixels, top to bottom."""
    width, height = surface.get_size()
    data = pygame.image.tobytes(surface, "RGB")
    return [
        [tuple(data[(y * width + x) * 3 : (y * width + x) * 3 + 3]) for x in range(width)]
        for y in range(height)
    ]


def _ink_bands(rows: list[list[tuple[int, int, int]]]) -> list[Band]:
    """Each run of rows holding a non-background pixel, with its ink columns."""
    has_ink = [any(p != BACKGROUND for p in row) for row in rows]
    bands: list[Band] = []
    top: int | None = None
    for y, ink in enumerate([*has_ink, False]):
        if ink and top is None:
            top = y
        elif not ink and top is not None:
            cols = [
                x
                for x in range(len(rows[0]))
                if any(rows[r][x] != BACKGROUND for r in range(top, y))
            ]
            bands.append((top, y - 1, cols[0], cols[-1]))
            top = None
    return bands


def _is_text_shade(pixel: tuple[int, int, int]) -> bool:
    """True if pixel is the background, the text color, or an antialiased blend of the two."""
    deltas = [fg - bg for fg, bg in zip(ERROR_TEXT_COLOR, PLACEHOLDER_BG, strict=True)]
    ref = max(range(3), key=lambda i: abs(deltas[i]))
    t = (pixel[ref] - PLACEHOLDER_BG[ref]) / deltas[ref]
    if not 0.0 <= t <= 1.0:
        return False
    return all(abs(pixel[i] - (PLACEHOLDER_BG[i] + t * deltas[i])) <= 1.0 for i in range(3))


def _assert_white_text(rows: list[list[tuple[int, int, int]]], band: Band) -> None:
    top, bottom, left, right = band
    ink = [rows[y][x] for y in range(top, bottom + 1) for x in range(left, right + 1)]
    assert ERROR_TEXT_COLOR in ink, f"no pixel of text color {ERROR_TEXT_COLOR} in {band}"
    bad = [p for p in ink if not _is_text_shade(p)]
    assert not bad, f"pixels that aren't text-color shades in {band}: {sorted(set(bad))[:5]}"


def _center_x(band: Band) -> float:
    return (band[2] + band[3]) / 2


def _center_y(band: Band) -> float:
    return (band[0] + band[1]) / 2


def test_error_screen_without_detail_shows_one_centered_white_line(
    pygame_headless: None,
) -> None:
    assert BACKGROUND == PLACEHOLDER_BG
    surface = _draw(None)
    rows = _pixels(surface)
    width, height = surface.get_size()

    bands = _ink_bands(rows)
    assert len(bands) == 1, f"expected one line of text, got bands {bands}"
    main = bands[0]
    top, bottom, left, right = main

    outside = [
        (x, y)
        for y in range(height)
        for x in range(width)
        if not (top <= y <= bottom and left <= x <= right) and rows[y][x] != PLACEHOLDER_BG
    ]
    assert not outside, f"non-background pixels outside the text: {outside[:5]}"
    _assert_white_text(rows, main)
    assert abs(_center_x(main) - (width - 1) / 2) <= CENTER_TOLERANCE_PX, main
    assert abs(_center_y(main) - (height - 1) / 2) <= CENTER_TOLERANCE_PX, main
    assert all(p == PLACEHOLDER_BG for row in rows[bottom + 1 :] for p in row)


def test_error_screen_with_detail_adds_a_centered_white_line_below(
    pygame_headless: None,
) -> None:
    plain_rows = _pixels(_draw(None))
    surface = _draw(DETAIL)
    rows = _pixels(surface)
    width = surface.get_width()

    plain_main = _ink_bands(plain_rows)[0]
    bands = _ink_bands(rows)
    assert len(bands) == 2, f"expected two lines of text, got bands {bands}"
    main, detail = bands

    assert main == plain_main, f"main line moved: {main} vs {plain_main}"
    assert rows[main[0] : main[1] + 1] == plain_rows[main[0] : main[1] + 1], "main line changed"
    assert detail[0] > main[1], f"detail {detail} not below main line {main}"
    _assert_white_text(rows, detail)
    assert abs(_center_x(detail) - (width - 1) / 2) <= CENTER_TOLERANCE_PX, detail


def test_error_screen_background_replaces_previous_content(pygame_headless: None) -> None:
    assert PREFILL != BACKGROUND
    surface = pygame.Surface(SURFACE_SIZE)
    surface.fill(PREFILL)
    draw_error_screen(surface, None)
    width, height = surface.get_size()
    for corner in [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]:
        assert tuple(surface.get_at(corner))[:3] == BACKGROUND, corner
