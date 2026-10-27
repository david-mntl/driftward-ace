"""Pause box tests: a see-through dark box with PAUSE, both centered on the surface.

Contract: docs/contracts/systems/game-flow.md, Interface (ui/pause_box.py) and Presentation, Pause
box and the shared items (Text, Box, Only draws). The box's size, the title size, the text and the
fill's alpha are stand-ins from scope report DRA-125, Values needed (Pause box; the DRA-23 box
fill); the GDD does not hold them until UI-04.

Positions are read from the drawn pixels (`pygame.image.tobytes`), never from a font size or a
line height. On a black surface the box (black at alpha 90) adds no ink, so the ink is the text
alone.
"""

import pygame

from ui.pause_box import draw_pause_box

SURFACE_SIZE: tuple[int, int] = (640, 480)
"""Test surface. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

BOX_SIZE: tuple[int, int] = (320, 120)
"""Source: scope report DRA-125, Values needed, Pause box: the DRA-23 box size."""

BOX_ALPHA: int = 90
"""Fill alpha of 255, black. Source: scope report DRA-23, Game Over box, reused by DRA-125."""

TITLE_FONT_SIZE: int = 32
"""Default font, px. Source: scope report DRA-125, Values needed (every title)."""

PAUSE_TEXT: str = "PAUSE"
"""Source: 10-ui.md, pause_box (locked content); scope report DRA-125, Values needed."""

TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Source: scope report DRA-125, Values needed (white text)."""

BLACK: tuple[int, int, int] = (0, 0, 0)
"""Test surface fill. Source: 12-art-and-audio.md, placeholder_bg (guess)."""

GRAYS: tuple[int, ...] = (60, 130, 200)
"""Backgrounds the box is drawn over. Below white, so the text is always brighter than they are."""

BLEND_TOLERANCE: int = 1
"""SDL's alpha blend may be one level off the exact result."""

CENTER_TOLERANCE_PX: float = 1.0
"""Slack for glyph side bearings when centering is read from ink (one px on a 640 x 480 canvas)."""

Pixel = tuple[int, int]
Rect = tuple[int, int, int, int]
"""Left, top, right and bottom, all inclusive."""


def _surface(size: tuple[int, int] = SURFACE_SIZE, gray: int = 0) -> pygame.Surface:
    surface = pygame.Surface(size)
    surface.fill((gray, gray, gray))
    return surface


def _colors(surface: pygame.Surface) -> dict[Pixel, tuple[int, int, int]]:
    """Every pixel's color, keyed by (x, y)."""
    width, height = surface.get_size()
    data = pygame.image.tobytes(surface, "RGB")
    return {
        (x, y): (data[i], data[i + 1], data[i + 2])
        for y in range(height)
        for x, i in enumerate(range(y * width * 3, (y + 1) * width * 3, 3))
    }


def _bounds(pixels: set[Pixel]) -> Rect:
    xs = [x for x, _ in pixels]
    ys = [y for _, y in pixels]
    return min(xs), min(ys), max(xs), max(ys)


def _ink(surface: pygame.Surface) -> set[Pixel]:
    """The pixels that are not black."""
    return {pixel for pixel, color in _colors(surface).items() if color != BLACK}


def _reference_text() -> tuple[set[Pixel], dict[Pixel, tuple[int, int, int]]]:
    """PAUSE in the default font at the title size, white on black, ink moved to its own origin."""
    text = pygame.font.Font(None, TITLE_FONT_SIZE).render(PAUSE_TEXT, True, TEXT_COLOR)
    canvas = _surface(text.get_size())
    canvas.blit(text, (0, 0))
    colors = _colors(canvas)
    ink = {pixel for pixel, color in colors.items() if color != BLACK}
    left, top, _, _ = _bounds(ink)
    return (
        {(x - left, y - top) for x, y in ink},
        {(x - left, y - top): colors[(x, y)] for x, y in ink},
    )


def test_pause_box_is_its_size_centered_darker_and_see_through(pygame_headless: None) -> None:
    left = (SURFACE_SIZE[0] - BOX_SIZE[0]) // 2
    top = (SURFACE_SIZE[1] - BOX_SIZE[1]) // 2
    expected_box = (left, top, left + BOX_SIZE[0] - 1, top + BOX_SIZE[1] - 1)
    results: dict[int, dict[Pixel, tuple[int, int, int]]] = {}
    on_black = _surface()
    draw_pause_box(on_black)
    text_bounds = _bounds(_ink(on_black))
    for gray in GRAYS:
        surface = _surface(gray=gray)
        draw_pause_box(surface)
        colors = _colors(surface)
        results[gray] = colors
        background = (gray, gray, gray)
        changed = {pixel for pixel, color in colors.items() if color != background}
        assert _bounds(changed) == expected_box, f"{gray=}: the box is not {BOX_SIZE} centered"
        shaded = round(gray * (255 - BOX_ALPHA) / 255)
        corner_colors = [
            colors[(expected_box[0], expected_box[1])],
            colors[(expected_box[2], expected_box[1])],
            colors[(expected_box[0], expected_box[3])],
            colors[(expected_box[2], expected_box[3])],
        ]
        for color in corner_colors:
            assert color[0] == color[1] == color[2] < gray, f"{gray=}: {color} is not darker"
            assert abs(color[0] - shaded) <= BLEND_TOLERANCE, f"{gray=}: {color} not {shaded}"
        # Off the text, the box is that one darker gray and nothing is drawn outside it: a
        # filled box with no border.
        text_left, text_top, text_right, text_bottom = text_bounds
        for pixel, color in colors.items():
            inside = expected_box[0] <= pixel[0] <= expected_box[2]
            inside = inside and expected_box[1] <= pixel[1] <= expected_box[3]
            on_text = text_left <= pixel[0] <= text_right and text_top <= pixel[1] <= text_bottom
            if not inside:
                assert color == background, f"{gray=} {pixel}: ink outside the box"
            elif not on_text:
                assert abs(color[0] - shaded) <= BLEND_TOLERANCE, f"{gray=} {pixel}: {color}"
                assert color[0] == color[1] == color[2], f"{gray=} {pixel}: {color} not gray"
    # See-through: the same box over two backgrounds gives two results, each from its background.
    first, second = GRAYS[0], GRAYS[-1]
    assert results[first][(left, top)] != results[second][(left, top)]


def test_pause_text_is_centered_on_the_box_center(pygame_headless: None) -> None:
    reference_ink, reference_colors = _reference_text()
    ref_width = max(x for x, _ in reference_ink) + 1
    ref_height = max(y for _, y in reference_ink) + 1
    for size in (SURFACE_SIZE, (800, 600), (1000, 700)):
        surface = _surface(size)
        draw_pause_box(surface)
        colors = _colors(surface)
        ink = {pixel for pixel, color in colors.items() if color != BLACK}
        assert ink, f"{size=}: nothing drawn on black but the box adds no ink"
        left, top, right, bottom = _bounds(ink)
        assert (right - left + 1, bottom - top + 1) == (ref_width, ref_height), (
            f"{size=}: the ink is not the word {PAUSE_TEXT!r} at the title size"
        )
        assert {(x - left, y - top): colors[(x, y)] for x, y in ink} == reference_colors, (
            f"{size=}: the word's pixels are not the antialiased default-font render"
        )
        center_x = size[0] // 2
        box_center_y = (size[1] - BOX_SIZE[1]) // 2 + BOX_SIZE[1] // 2
        assert abs((left + right) / 2 - (center_x - 0.5)) <= CENTER_TOLERANCE_PX, (
            f"{size=}: text not centered across the box: {left}..{right}"
        )
        assert abs((top + bottom) / 2 - (box_center_y - 0.5)) <= 2.0, (
            f"{size=}: text not centered down the box: {top}..{bottom}, box center {box_center_y}"
        )
        # The box and its text sit in the same place relative to the surface's center.
    small = _surface(SURFACE_SIZE)
    large = _surface((800, 600))
    draw_pause_box(small)
    draw_pause_box(large)
    shift_x, shift_y = (800 - SURFACE_SIZE[0]) // 2, (600 - SURFACE_SIZE[1]) // 2
    small_colors = _colors(small)
    large_colors = _colors(large)
    for (x, y), color in small_colors.items():
        assert large_colors[(x + shift_x, y + shift_y)] == color, f"({x}, {y}) moved with the size"


def test_pause_box_on_a_black_surface_leaves_the_text_as_the_only_ink(
    pygame_headless: None,
) -> None:
    surface = _surface()
    draw_pause_box(surface)
    left = (SURFACE_SIZE[0] - BOX_SIZE[0]) // 2
    top = (SURFACE_SIZE[1] - BOX_SIZE[1]) // 2
    ink = _ink(surface)
    ink_left, ink_top, ink_right, ink_bottom = _bounds(ink)
    assert ink_left > left, "text touches the box's left side"
    assert ink_right < left + BOX_SIZE[0] - 1, "text touches the box's right side"
    assert ink_top > top, "text touches the box's top edge"
    assert ink_bottom < top + BOX_SIZE[1] - 1, "text touches the box's bottom edge"
    # The same word twice in a row draws the same picture (the cache serves it unchanged).
    again = _surface()
    draw_pause_box(again)
    assert pygame.image.tobytes(again, "RGB") == pygame.image.tobytes(surface, "RGB")
