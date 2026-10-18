"""Game Over box tests. Contract: docs/contracts/systems/run.md, Interface and Presentation.

Positions are read from the drawn pixels, never from a font size or a line height. The box is
black at alpha 90, so on a black surface it adds no ink: the ink is the text alone.
"""

import pygame

from ui.game_over import draw_final_score, draw_game_over

SURFACE_SIZE: tuple[int, int] = (640, 480)
"""Test surface. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

BOX_SIZE: tuple[int, int] = (320, 120)
"""Source: systems/run.md, Presentation, Box (BOX_SIZE 320 x 120)."""

BOX_LEFT: int = (SURFACE_SIZE[0] - BOX_SIZE[0]) // 2
"""Source: systems/run.md, Presentation, Box: (width - 320) // 2 = 160."""

BOX_TOP: int = (SURFACE_SIZE[1] - BOX_SIZE[1]) // 2
"""Source: systems/run.md, Presentation, Box: (height - 120) // 2 = 180."""

SCORE_FONT_SIZE: int = 16
"""Source: systems/run.md, Presentation, Score (default font at 16 px)."""

BLACK: tuple[int, int, int] = (0, 0, 0)
"""Test surface fill. Source: 12-art-and-audio.md, placeholder_bg (guess)."""

SCORES: tuple[int, ...] = (0, 999, 1234, 1234567)
"""A short and a long score, with and without a separator, for the centering checks."""

CENTER_TOLERANCE_PX: float = 2.0
"""Slack for antialiasing and glyph side bearings when centering is read from ink."""

Pixels = list[list[tuple[int, int, int]]]
Band = tuple[int, int, int, int]
"""One line of ink: top row, bottom row, left column, right column, all inclusive."""


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


def _box_only() -> Pixels:
    surface = _blank()
    draw_game_over(surface)
    return _pixels(surface)


def _box_with_score(score: int) -> Pixels:
    surface = _blank()
    draw_game_over(surface)
    draw_final_score(surface, score)
    return _pixels(surface)


def _bands(rows: Pixels) -> list[Band]:
    """Each run of rows holding a non-black pixel, with its ink columns."""
    has_ink = [any(p != BLACK for p in row) for row in rows]
    bands: list[Band] = []
    top: int | None = None
    for y, ink in enumerate([*has_ink, False]):
        if ink and top is None:
            top = y
        elif not ink and top is not None:
            cols = [
                x for x in range(len(rows[0])) if any(rows[r][x] != BLACK for r in range(top, y))
            ]
            bands.append((top, y - 1, cols[0], cols[-1]))
            top = None
    return bands


def _band_pixels(rows: Pixels, band: Band) -> Pixels:
    top, bottom, _, _ = band
    return rows[top : bottom + 1]


def _reference_size(score_text: str) -> tuple[int, int]:
    """Ink width and height of ``score_text`` in the default font at 16 px, white on black."""
    font = pygame.font.Font(None, SCORE_FONT_SIZE)
    text = font.render(score_text, True, (255, 255, 255))
    canvas = pygame.Surface(text.get_size())
    canvas.fill(BLACK)
    canvas.blit(text, (0, 0))
    (top, bottom, left, right) = _bands(_pixels(canvas))[0]
    return right - left + 1, bottom - top + 1


def _expected_text(score: int) -> str:
    """The score's text worked out here, groups of three split by a space (hud.md)."""
    digits = f"{score:,}".replace(",", " ")
    return f"SCORE {digits}"


def _center_x(band: Band) -> float:
    return (band[2] + band[3]) / 2


def test_game_over_with_score_shows_three_centered_lines_in_the_box(
    pygame_headless: None,
) -> None:
    for score in SCORES:
        rows = _box_with_score(score)
        bands = _bands(rows)
        assert len(bands) == 3, f"{score=}: expected three lines, got {bands}"
        title, line, prompt = bands
        assert title[1] < line[0] < line[1] < prompt[0], f"{score=}: lines out of order {bands}"
        for band in bands:
            top, bottom, left, right = band
            box_bottom = BOX_TOP + BOX_SIZE[1]
            box_right = BOX_LEFT + BOX_SIZE[0]
            assert top >= BOX_TOP, f"{score=}: {band} above the box"
            assert bottom < box_bottom, f"{score=}: {band} below the box"
            assert left >= BOX_LEFT, f"{score=}: {band} left of the box"
            assert right < box_right, f"{score=}: {band} right of the box"
            center = SURFACE_SIZE[0] / 2 - 0.5
            assert abs(_center_x(band) - center) <= CENTER_TOLERANCE_PX, f"{score=}: {band}"
        width, height = _reference_size(_expected_text(score))
        assert (line[3] - line[2] + 1, line[1] - line[0] + 1) == (width, height), (
            f"{score=}: middle line is not the text {_expected_text(score)!r}: {line}"
        )


def test_game_over_only_the_score_line_changes_with_the_score(pygame_headless: None) -> None:
    short = _box_with_score(0)
    long = _box_with_score(1234567)
    assert short != long, "the score did not change the picture"
    bands_short = _bands(short)
    bands_long = _bands(long)
    assert len(bands_short) == len(bands_long) == 3
    # The score line's rows: from its top to its bottom, whichever score is taller.
    line_top = min(bands_short[1][0], bands_long[1][0])
    line_bottom = max(bands_short[1][1], bands_long[1][1])
    for y in range(SURFACE_SIZE[1]):
        if line_top <= y <= line_bottom:
            continue
        assert short[y] == long[y], f"row {y} outside the score line changed with the score"
    assert bands_short[0] == bands_long[0], "title moved with the score"
    assert bands_short[2] == bands_long[2], "prompt moved with the score"


def test_game_over_alone_leaves_the_score_line_place_empty(pygame_headless: None) -> None:
    alone = _box_only()
    with_score = _box_with_score(1234567)
    alone_bands = _bands(alone)
    with_bands = _bands(with_score)
    assert len(alone_bands) == 2, f"expected title and prompt, got {alone_bands}"
    title, prompt = alone_bands
    assert title == with_bands[0], "title moved when the score line was added"
    assert prompt == with_bands[2], "prompt moved when the score line was added"
    assert _band_pixels(alone, title) == _band_pixels(with_score, title)
    assert _band_pixels(alone, prompt) == _band_pixels(with_score, prompt)
    score_line = with_bands[1]
    assert title[1] < score_line[0] < score_line[1] < prompt[0]
    for y in range(title[1] + 1, prompt[0]):
        assert all(p == BLACK for p in alone[y]), f"ink in the score line's place, row {y}"
