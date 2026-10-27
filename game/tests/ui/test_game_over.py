"""Game-over screen tests: the box, the title, the score line, and RETRY above MENU.

Contract: docs/contracts/systems/game-flow.md, Interface (ui/game_over.py) and Presentation,
Game-over screen and the shared items (Text, Lines and blank lines, Selection marker, Box, Cache,
Only draws). The box's size, the texts, the font sizes, the marker and the fill's alpha are
stand-ins from scope report DRA-125, Values needed (Game-over screen; the DRA-23 box fill and the
DRA-61 score line); the GDD does not hold them until UI-04.

From DRA-126 the screen also has the message by place and, with the picker, a larger box with six
lines (the message, the score, ten slots, the hint, RETRY and MENU). The picker's size, font, hint,
greys and line width are stand-ins from scope report DRA-126, Values needed (Game-over screen with
the picker, Picker slots) and docs/reports/DRA-126-away-log.md, Decisions, 4; the messages are
10-ui.md, game_over_message (locked); the GDD does not hold the look until UI-04.

Positions are read from the drawn pixels (`pygame.image.tobytes`), never from a font size or a
line height. On a black 640 x 480 surface the box (black at alpha 90) adds no ink, so the ink is
the text alone. The score line's text is written here from the contract's examples (groups of
three split by a space), never taken from `score_text`.
"""

import dataclasses
from itertools import pairwise
from typing import NamedTuple

import pygame
import pytest

import ui.game_over as view
import ui.screen_look as look_view
from core.game_flow import GameOverChoice
from core.saves import GameOverMessage, NamePicker
from ui.game_over import (
    draw_final_score,
    draw_game_over,
    draw_game_over_choices,
    draw_name_picker,
)

SURFACE_SIZE: tuple[int, int] = (640, 480)
"""Test surface. Source: 03-world-and-camera.md, screen_w, screen_h (guess)."""

BOX_SIZE: tuple[int, int] = (320, 160)
"""Source: scope report DRA-125, Values needed, Game-over screen: the DRA-23 box grown."""

BOX_LEFT: int = (SURFACE_SIZE[0] - BOX_SIZE[0]) // 2
"""Source: game-flow.md, Presentation, Box: (width - box_width) // 2 = 160."""

BOX_TOP: int = (SURFACE_SIZE[1] - BOX_SIZE[1]) // 2
"""Source: game-flow.md, Presentation, Box: (height - box_height) // 2 = 160."""

BOX_ALPHA: int = 90
"""Fill alpha of 255, black. Source: scope report DRA-23, Game Over box, reused by DRA-125."""

TITLE_FONT_SIZE: int = 32
"""Default font, px. Source: scope report DRA-125, Values needed (every title)."""

BODY_FONT_SIZE: int = 16
"""Default font, px. Source: scope report DRA-125, Values needed (the game-over lines)."""

TITLE_TEXT: str = "GAME OVER"
"""Source: scope report DRA-125, Values needed; 10-ui.md, game_over_message (GAME OVER only)."""

RETRY_TEXT: str = "RETRY"
MENU_TEXT: str = "MENU"
"""Source: scope report DRA-125, Values needed; 02-game-flow.md, game_over_choices (locked)."""

TEXT_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Source: scope report DRA-125, Values needed (white text)."""

BLACK: tuple[int, int, int] = (0, 0, 0)
"""Test surface fill. Source: 12-art-and-audio.md, placeholder_bg (guess)."""

SCORES: tuple[int, ...] = (0, 999, 1234, 1234567)
"""A short and a long score, with and without a separator, for the checks that vary the score."""

CENTER_TOLERANCE_PX: float = 2.0
"""Slack for antialiasing and glyph side bearings when centering is read from ink."""

BLOCK_TOLERANCE_PX: float = 3.0
"""Slack for the glyphs' own space above and below their ink when the block's centering is read
from ink: the title's caps start lower in their line than MENU's end."""

MARKER_ROW_SLACK_PX: int = 2
"""Rows a marker's ink may stand above or below its label's ink (the glyph '>' hangs a row)."""

MARKER_GAP_SLACK_PX: int = 4
"""Px the marker's ink may stand beyond one space from its label (both glyphs' side bearings)."""

BLEND_TOLERANCE: int = 1
"""SDL's alpha blend may be one level off the exact result."""

Band = tuple[int, int, int, int]
"""One line of ink: top row, bottom row, left column, right column, all inclusive."""


def _surface(size: tuple[int, int] = SURFACE_SIZE, gray: int = 0) -> pygame.Surface:
    surface = pygame.Surface(size)
    surface.fill((gray, gray, gray))
    return surface


def _red_channel(surface: pygame.Surface) -> bytes:
    """The red level of every pixel, row by row. Every picture here is gray, so it is the level."""
    return pygame.image.tobytes(surface, "RGB")[::3]


def _bands(surface: pygame.Surface) -> list[Band]:
    """Each run of rows holding ink, with its ink columns."""
    width, height = surface.get_size()
    levels = _red_channel(surface)
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


def _crop(surface: pygame.Surface, band: Band) -> tuple[bytes, ...]:
    """The band's ink rectangle, one bytes row per pixel row."""
    width = surface.get_width()
    levels = _red_channel(surface)
    top, bottom, left, right = band
    return tuple(levels[y * width + left : y * width + right + 1] for y in range(top, bottom + 1))


def _reference(text: str, size: int) -> tuple[bytes, ...]:
    """The ink rectangle of ``text`` in the default font at ``size``, white on black."""
    image = pygame.font.Font(None, size).render(text, True, TEXT_COLOR)
    canvas = _surface(image.get_size())
    canvas.blit(image, (0, 0))
    return _crop(canvas, _bands(canvas)[0])


def _expected_text(score: int) -> str:
    """The score's text worked out here, groups of three split by a space (hud.md)."""
    digits = f"{score:,}".replace(",", " ")
    return f"SCORE {digits}"


def _center_x(band: Band) -> float:
    return (band[2] + band[3]) / 2


def _full(
    score: int,
    selection: GameOverChoice = GameOverChoice.RETRY,
    size: tuple[int, int] = SURFACE_SIZE,
    gray: int = 0,
) -> pygame.Surface:
    surface = _surface(size, gray)
    draw_game_over(surface)
    draw_final_score(surface, score)
    draw_game_over_choices(surface, selection)
    return surface


def _choices(selection: GameOverChoice) -> pygame.Surface:
    surface = _surface()
    draw_game_over_choices(surface, selection)
    return surface


def test_game_over_box_is_its_size_centered_darker_and_see_through(pygame_headless: None) -> None:
    expected = (
        BOX_LEFT,
        BOX_TOP,
        BOX_LEFT + BOX_SIZE[0] - 1,
        BOX_TOP + BOX_SIZE[1] - 1,
    )
    corners = [(expected[0], expected[1]), (expected[2], expected[1])]
    corners += [(expected[0], expected[3]), (expected[2], expected[3])]
    seen: dict[int, int] = {}
    for gray in (60, 130, 200):
        background = gray
        shaded = round(gray * (255 - BOX_ALPHA) / 255)
        for name, surface in (
            ("box alone", _surface(gray=gray)),
            ("all three calls", _full(1234567, gray=gray)),
        ):
            if name == "box alone":
                draw_game_over(surface)
            width = surface.get_width()
            levels = _red_channel(surface)
            changed = [
                (i % width, i // width) for i, level in enumerate(levels) if level != background
            ]
            xs = [x for x, _ in changed]
            ys = [y for _, y in changed]
            assert (min(xs), min(ys), max(xs), max(ys)) == expected, (
                f"{gray=} {name}: the changed pixels are not the {BOX_SIZE} box centered"
            )
            for x, y in corners:
                level = levels[y * width + x]
                assert level < background, f"{gray=} {name}: corner {(x, y)} is not darker"
                assert abs(level - shaded) <= BLEND_TOLERANCE, f"{gray=} {name}: {level}"
            seen[gray] = levels[expected[1] * width + expected[0]]
    assert len(set(seen.values())) == 3, "the box did not let each background through"
    # The box is centered from the surface's own size, not placed at one spot.
    for width, height in ((800, 600), (1000, 700)):
        surface = _surface((width, height), gray=130)
        draw_game_over(surface)
        levels = _red_channel(surface)
        changed = [(i % width, i // width) for i, level in enumerate(levels) if level != 130]
        xs = [x for x, _ in changed]
        ys = [y for _, y in changed]
        left = (width - BOX_SIZE[0]) // 2
        top = (height - BOX_SIZE[1]) // 2
        assert (min(xs), min(ys), max(xs), max(ys)) == (
            left,
            top,
            left + BOX_SIZE[0] - 1,
            top + BOX_SIZE[1] - 1,
        ), f"{width}x{height}: the box is not centered"


def test_game_over_draws_four_centered_lines_stacked_in_the_box(pygame_headless: None) -> None:
    expected_columns = {
        "title": _reference(TITLE_TEXT, TITLE_FONT_SIZE),
        "retry": _reference(RETRY_TEXT, BODY_FONT_SIZE),
        "menu": _reference(MENU_TEXT, BODY_FONT_SIZE),
    }
    for score in SCORES:
        for selection in GameOverChoice:
            surface = _full(score, selection)
            bands = _bands(surface)
            assert len(bands) == 4, f"{score=} {selection=}: not four lines (no prompt): {bands}"
            title, line, retry, menu = bands
            tops_and_bottoms = [(title[1], line[0]), (line[1], retry[0]), (retry[1], menu[0])]
            for above_bottom, below_top in tops_and_bottoms:
                assert above_bottom < below_top, f"{score=} {selection=}: out of order {bands}"
            for band in bands:
                top, bottom, left, right = band
                assert top >= BOX_TOP, f"{score=}: {band} above the box"
                assert bottom < BOX_TOP + BOX_SIZE[1], f"{score=}: {band} below the box"
                assert left >= BOX_LEFT, f"{score=}: {band} left of the box"
                assert right < BOX_LEFT + BOX_SIZE[0], f"{score=}: {band} right of the box"
            # Centered across the width. The selected label has its marker in its band, so its
            # center is read from the picture where the other choice is selected.
            for band in (title, line):
                center = SURFACE_SIZE[0] / 2 - 0.5
                assert abs(_center_x(band) - center) <= CENTER_TOLERANCE_PX, f"{score=}: {band}"
            # The block, title top to MENU bottom, is centered in the box.
            gap_above = title[0] - BOX_TOP
            gap_below = BOX_TOP + BOX_SIZE[1] - 1 - menu[1]
            assert abs(gap_above - gap_below) <= BLOCK_TOLERANCE_PX, (
                f"{score=} {selection=}: block not centered in the box: {gap_above} above, "
                f"{gap_below} below"
            )
            # Each line is its text at its size.
            assert _crop(surface, title) == expected_columns["title"], f"{score=}: title"
            assert _crop(surface, line) == _reference(_expected_text(score), BODY_FONT_SIZE), (
                f"{score=}: the second line is not {_expected_text(score)!r} at the body size"
            )
        # The labels, with the marker left out, are centered like every line.
        for band_index, text in ((2, "retry"), (3, "menu")):
            other = GameOverChoice.MENU if band_index == 2 else GameOverChoice.RETRY
            bands = _bands(_full(score, other))
            band = bands[band_index]
            assert abs(_center_x(band) - (SURFACE_SIZE[0] / 2 - 0.5)) <= CENTER_TOLERANCE_PX
            assert _crop(_full(score, other), band) == expected_columns[text], f"{text}"


def _ink_top_in_line(text: str, size: int) -> int:
    """Rows from the top of a rendered line to the top of its ink, read from the pixels."""
    image = pygame.font.Font(None, size).render(text, True, TEXT_COLOR)
    canvas = _surface(image.get_size())
    canvas.blit(image, (0, 0))
    return _bands(canvas)[0][0]


def test_game_over_lines_are_stacked_with_no_gap_and_the_block_is_centered(
    pygame_headless: None,
) -> None:
    title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
    body_font = pygame.font.Font(None, BODY_FONT_SIZE)
    title_line = title_font.get_linesize()
    body_line = body_font.get_linesize()
    block = title_line + body_line + body_line + body_font.get_height()
    title_top = BOX_TOP + (BOX_SIZE[1] - block) // 2
    score_top = title_top + title_line
    line_tops = (title_top, score_top, score_top + body_line, score_top + 2 * body_line)
    for score in (0, 1234567):
        texts = (
            (TITLE_TEXT, TITLE_FONT_SIZE),
            (_expected_text(score), BODY_FONT_SIZE),
            (RETRY_TEXT, BODY_FONT_SIZE),
            (MENU_TEXT, BODY_FONT_SIZE),
        )
        # A label is measured in the picture where the other choice has the marker, so the
        # marker's ink does not reach into its band.
        retry_bands = _bands(_full(score, GameOverChoice.MENU))
        menu_bands = _bands(_full(score, GameOverChoice.RETRY))
        bands = (retry_bands[0], retry_bands[1], retry_bands[2], menu_bands[3])
        for index, (band, top, (text, size)) in enumerate(
            zip(bands, line_tops, texts, strict=True)
        ):
            assert band[0] == top + _ink_top_in_line(text, size), (
                f"{score=} line {index}: ink top {band[0]}, expected {top} + the text's own offset"
            )


def test_game_over_marker_is_left_of_the_selected_choice_only(pygame_headless: None) -> None:
    on_retry = _choices(GameOverChoice.RETRY)
    on_menu = _choices(GameOverChoice.MENU)
    width = SURFACE_SIZE[0]
    # Without the marker each label is where it is: RETRY's rows in the MENU picture and MENU's
    # rows in the RETRY picture are labels alone.
    bands_on_menu = _bands(on_menu)
    bands_on_retry = _bands(on_retry)
    assert len(bands_on_menu) == len(bands_on_retry) == 2
    retry_label = bands_on_menu[0]
    menu_label = bands_on_retry[1]
    assert _crop(on_menu, retry_label) == _reference(RETRY_TEXT, BODY_FONT_SIZE)
    assert _crop(on_retry, menu_label) == _reference(MENU_TEXT, BODY_FONT_SIZE)
    # The pixels that differ between the two pictures are the two markers and nothing else, so
    # the labels do not move with the selection.
    space = pygame.font.Font(None, BODY_FONT_SIZE).size(" ")[0]
    levels_retry = _red_channel(on_retry)
    levels_menu = _red_channel(on_menu)
    changed = [
        (i % width, i // width)
        for i in range(len(levels_retry))
        if levels_retry[i] != levels_menu[i]
    ]
    assert changed, "the marker did not move with the selection"
    boundary = (retry_label[1] + menu_label[0]) / 2
    for selected, label, other_label, markers in (
        ("RETRY", retry_label, menu_label, [p for p in changed if p[1] < boundary]),
        ("MENU", menu_label, retry_label, [p for p in changed if p[1] > boundary]),
    ):
        assert markers, f"{selected}: no marker ink"
        marker_left = min(x for x, _ in markers)
        marker_right = max(x for x, _ in markers)
        assert marker_right < label[2], f"{selected}: the marker is not left of the label"
        gap = label[2] - marker_right
        assert gap <= space + MARKER_GAP_SLACK_PX, f"{selected}: the marker is {gap} px from it"
        assert marker_left >= label[2] - 40, f"{selected}: marker ink far left of the label"
        rows = [y for _, y in markers]
        assert min(rows) >= label[0] - MARKER_ROW_SLACK_PX, f"{selected}: marker above its row"
        assert max(rows) <= label[1] + MARKER_ROW_SLACK_PX, f"{selected}: marker below its row"
        assert max(rows) < other_label[0] or min(rows) > other_label[1], (
            f"{selected}: the marker reaches into the other choice's rows"
        )


def test_game_over_each_function_alone_draws_only_its_own_lines(pygame_headless: None) -> None:
    for score in SCORES:
        full = _full(score)
        full_bands = _bands(full)
        title_band, score_band, retry_band, menu_band = full_bands
        full_levels = _red_channel(full)
        width = SURFACE_SIZE[0]

        box_only = _surface()
        draw_game_over(box_only)
        score_only = _surface()
        draw_final_score(score_only, score)
        choices_only = _surface()
        draw_game_over_choices(choices_only, GameOverChoice.RETRY)

        assert _bands(box_only) == [title_band], f"{score=}: draw_game_over is not the title alone"
        assert _bands(score_only) == [score_band], f"{score=}: draw_final_score is not its line"
        assert _bands(choices_only)[0][:2] == (retry_band[0], retry_band[1])
        assert _bands(choices_only)[1][0] == menu_band[0]
        assert len(_bands(choices_only)) == 2

        # Together the three alone pictures are the full picture, line for line: the lines'
        # rows never share a pixel, so the levels add up to the full picture's.
        alone_levels = [
            _red_channel(box_only),
            _red_channel(score_only),
            _red_channel(choices_only),
        ]
        first, last = title_band[0], menu_band[1]
        for y in range(SURFACE_SIZE[1]):
            row = slice(y * width, (y + 1) * width)
            if not first <= y <= last:
                assert not any(full_levels[row]), f"{score=}: ink outside the block, row {y}"
                continue
            rows = (levels[row] for levels in alone_levels)
            summed = bytes(sum(column) for column in zip(*rows, strict=True))
            assert summed == full_levels[row], f"{score=}: row {y} differs alone and together"


def test_game_over_only_the_score_line_changes_with_the_score_and_the_same_score_repeats(
    pygame_headless: None,
) -> None:
    pictures = {score: _full(score) for score in SCORES}
    for score in SCORES:
        # The same score drawn again, on a fresh surface and after other scores, is the same
        # picture: the one-slot cache cannot serve a stale line.
        again = _full(score)
        assert _red_channel(again) == _red_channel(pictures[score]), f"{score=}: not repeatable"
    width = SURFACE_SIZE[0]
    short = pictures[0]
    for score in SCORES[1:]:
        long = pictures[score]
        assert _red_channel(short) != _red_channel(long), f"{score=}: the score changed nothing"
        bands_short = _bands(short)
        bands_long = _bands(long)
        assert len(bands_short) == len(bands_long) == 4
        top = min(bands_short[1][0], bands_long[1][0])
        bottom = max(bands_short[1][1], bands_long[1][1])
        levels_short = _red_channel(short)
        levels_long = _red_channel(long)
        for y in range(SURFACE_SIZE[1]):
            if top <= y <= bottom:
                continue
            row = slice(y * width, (y + 1) * width)
            assert levels_short[row] == levels_long[row], f"{score=}: row {y} changed"
        for index in (0, 2, 3):
            assert bands_short[index][:2] == bands_long[index][:2], f"{score=}: line {index} moved"
            assert _crop(short, bands_short[index]) == _crop(long, bands_long[index])


def test_game_over_lines_keep_their_place_relative_to_the_surface_center(
    pygame_headless: None,
) -> None:
    small = _full(1234567)
    large_size = (800, 600)
    large = _full(1234567, size=large_size)
    shift_x = (large_size[0] - SURFACE_SIZE[0]) // 2
    shift_y = (large_size[1] - SURFACE_SIZE[1]) // 2
    small_bands = _bands(small)
    large_bands = _bands(large)
    assert len(large_bands) == 4
    for small_band, large_band in zip(small_bands, large_bands, strict=True):
        assert large_band == (
            small_band[0] + shift_y,
            small_band[1] + shift_y,
            small_band[2] + shift_x,
            small_band[3] + shift_x,
        ), "a line is not placed from the surface's own size"
        assert _crop(large, large_band) == _crop(small, small_band)


# DRA-126: the message by place, the picker layout, the cells, the cursor and the hint, the
# grey RETRY and MENU, and the screen after the save. Contract: game-flow.md, Interface
# (ui/game_over.py, "DRA-126: what saves add and change") and Presentation, Game-over screen.

PICKER_BOX_SIZE: tuple[int, int] = (400, 280)
"""Source: scope report DRA-126, Values needed, Game-over screen with the picker (box 400 x 280)."""

PICKER_FONT_SIZE: int = 24
"""Source: scope report DRA-126, Values needed (the 10 slots with 24 px characters)."""

HINT_TEXT: str = "Up/Down: letter   Left/Right: slot   Enter: save"
"""Source: scope report DRA-126, Values needed (the hint at 16 px)."""

GREY: int = 128
"""RETRY and MENU before the save and every slot's underline, as a gray level. Source: scope report
DRA-126, Values needed (grey (128, 128, 128))."""

SLOT_COUNT: int = 10
"""Source: 11-save-data.md, nickname_length and nickname_input (locked)."""

CHARACTERS: str = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_!?*"
"""The blank, A to Z, 0 to 9, then `. - _ ! ? *`. Source: 11-save-data.md, nickname_chars (locked)
and nickname_char_order (guess)."""

MESSAGE_TEXTS: dict[GameOverMessage, str] = {
    GameOverMessage.NEW_BEST_SCORE: "NEW BEST SCORE",
    GameOverMessage.TOP_3: "TOP 3",
    GameOverMessage.TOP_10: "TOP 10",
    GameOverMessage.GAME_OVER: "GAME OVER",
}
"""Source: 10-ui.md, game_over_message (locked): #1 NEW BEST SCORE, #2-3 TOP 3, #4-10 TOP 10, off
the list GAME OVER."""

SIZES: tuple[tuple[int, int], ...] = ((640, 480), (800, 600))
"""Surfaces drawn on: the canvas and a larger one, so the layout follows the surface."""

TOLERANCE_PX: int = 1
"""Rects are placed by integer halves: a center may be one px off."""

PICKER_SCORE: int = 1234567
"""A score with groups, drawn in the picker scenes."""


class _Ref(NamedTuple):
    """A text rendered here: its ink rectangle and where that sits in the render."""

    crop: tuple[bytes, ...]
    image_width: int
    ink_left: int
    ink_top: int


class _Lines(NamedTuple):
    """The box and the top of every line, worked out from the contract's layout and the fonts."""

    box: pygame.Rect
    message: int
    score: int
    slots: int
    hint: int
    retry: int
    menu: int
    slot_line: int


def _ink_ref(text: str, size: int, level: int = 255) -> _Ref:
    """``text`` in the default font at ``size`` in gray ``level``: its ink and the ink's offset."""
    image = pygame.font.Font(None, size).render(text, True, (level, level, level))
    canvas = _surface(image.get_size())
    canvas.blit(image, (0, 0))
    bands = _bands(canvas)
    # A glyph such as ``!`` or ``?`` has more than one run of ink rows: take them all.
    box = (bands[0][0], bands[-1][1], min(b[2] for b in bands), max(b[3] for b in bands))
    return _Ref(_crop(canvas, box), image.get_width(), box[2], box[0])


def _lines(size: tuple[int, int], picker: bool) -> _Lines:
    """The contract's layout: lines stacked by their fonts' ``get_linesize()``, the block (its
    last line is the MENU font's ``get_height()``) centered vertically in the box."""
    title = pygame.font.Font(None, TITLE_FONT_SIZE)
    body = pygame.font.Font(None, BODY_FONT_SIZE)
    slot_line = pygame.font.Font(None, PICKER_FONT_SIZE).get_linesize() if picker else 0
    hint_line = body.get_linesize() if picker else 0
    heights = [title.get_linesize(), body.get_linesize(), slot_line, hint_line, body.get_linesize()]
    block = sum(heights) + body.get_height()
    box_size = PICKER_BOX_SIZE if picker else BOX_SIZE
    box = pygame.Rect((size[0] - box_size[0]) // 2, (size[1] - box_size[1]) // 2, *box_size)
    tops = [box.top + (box_size[1] - block) // 2]
    for height in heights:
        tops.append(tops[-1] + height)
    message, score, slots, hint, retry, menu = tops
    return _Lines(box, message, score, slots, hint, retry, menu, slot_line)


def _picker(name: str = "", cursor: int = 0) -> NamePicker:
    return NamePicker(slots=tuple(name.ljust(SLOT_COUNT)), cursor=cursor)


def _scene(
    picker_shown: bool,
    message: GameOverMessage = GameOverMessage.GAME_OVER,
    score: int = PICKER_SCORE,
    picker: NamePicker | None = None,
    picking: bool = False,
    selection: GameOverChoice = GameOverChoice.RETRY,
    size: tuple[int, int] = SURFACE_SIZE,
    gray: int = 0,
) -> pygame.Surface:
    """The screen as the app draws it: box and message, score, picker, then RETRY and MENU
    (white with the marker once the picker is not taking the keys)."""
    surface = _surface(size, gray)
    draw_game_over(surface, message, picker_shown)
    draw_final_score(surface, score, picker_shown)
    if picker is not None:
        draw_name_picker(surface, picker, picking)
    draw_game_over_choices(surface, selection, picker_shown, not picking)
    return surface


def _box_of_changes(surface: pygame.Surface, gray: int) -> tuple[int, int, int, int]:
    """Left, top, right and bottom (inclusive) of every pixel that is not ``gray``."""
    width = surface.get_width()
    levels = _red_channel(surface)
    changed = [i for i, level in enumerate(levels) if level != gray]
    xs = [i % width for i in changed]
    ys = [i // width for i in changed]
    return min(xs), min(ys), max(xs), max(ys)


def _check_line(
    surface: pygame.Surface, band: Band, ref: _Ref, top: int, what: str, centered: bool = True
) -> None:
    """The band is ``ref``'s ink exactly, its ink top is ``top`` plus the text's own offset, and
    its render is centered across the surface."""
    assert _crop(surface, band) == ref.crop, f"{what}: not the default font's render"
    assert band[0] == top + ref.ink_top, f"{what}: ink top {band[0]}, line top {top}"
    if centered:
        rect_left = band[2] - ref.ink_left
        assert abs(2 * rect_left + ref.image_width - surface.get_width()) <= TOLERANCE_PX, (
            f"{what}: not centered: rect left {rect_left}, render width {ref.image_width}"
        )


def test_game_over_without_the_picker_draws_each_message_in_the_title_place(
    pygame_headless: None,
) -> None:
    for size in SIZES:
        lines = _lines(size, picker=False)
        reference = _scene(False, size=size)
        base_alone = _surface(size)
        draw_game_over(base_alone)
        for message, text in MESSAGE_TEXTS.items():
            tag = f"{size=} {message}"
            alone = _surface(size)
            draw_game_over(alone, message)
            bands = _bands(alone)
            assert len(bands) == 1, f"{tag}: not one line of ink: {bands}"
            _check_line(alone, bands[0], _ink_ref(text, TITLE_FONT_SIZE), lines.message, tag)
            assert _box_of_changes(_scene(False, message, size=size, gray=60), 60) == (
                lines.box.left,
                lines.box.top,
                lines.box.right - 1,
                lines.box.bottom - 1,
            ), f"{tag}: the box is not the DRA-125 box"
            # Every other line stays: the picture differs from the GAME OVER one in the title's
            # rows alone.
            width = size[0]
            levels, base = _red_channel(_scene(False, message, size=size)), _red_channel(reference)
            title_rows = range(
                min(bands[0][0], _bands(base_alone)[0][0]),
                max(bands[0][1], _bands(base_alone)[0][1]) + 1,
            )
            for y in range(size[1]):
                if y not in title_rows:
                    row = slice(y * width, (y + 1) * width)
                    assert levels[row] == base[row], f"{tag}: row {y} differs from GAME OVER's"


def test_the_dra_125_calls_draw_the_dra_125_screen(pygame_headless: None) -> None:
    # The DRA-126 parameters default to the DRA-125 screen: the message GAME OVER, no picker,
    # RETRY and MENU active.
    for choice in GameOverChoice:
        old = _surface()
        draw_game_over(old)
        draw_final_score(old, 1234)
        draw_game_over_choices(old, choice)
        new = _surface()
        draw_game_over(new, GameOverMessage.GAME_OVER, False)
        draw_final_score(new, 1234, False)
        draw_game_over_choices(new, choice, False, True)
        assert _red_channel(old) == _red_channel(new), f"{choice}: the old calls differ"
        bands = _bands(old)
        assert len(bands) == 4, f"{choice}: not the four-line screen: {bands}"
        lines = _lines(SURFACE_SIZE, picker=False)
        _check_line(old, bands[0], _ink_ref(TITLE_TEXT, TITLE_FONT_SIZE), lines.message, "title")
        _check_line(old, bands[1], _ink_ref("SCORE 1 234", BODY_FONT_SIZE), lines.score, "score")
        assert _box_of_changes(_scene(False, gray=60), 60)[2:] == (
            BOX_LEFT + BOX_SIZE[0] - 1,
            BOX_TOP + BOX_SIZE[1] - 1,
        )


def test_the_picker_box_is_larger_centered_and_see_through(pygame_headless: None) -> None:
    seen: dict[int, int] = {}
    for gray in (60, 130, 200):
        shaded = round(gray * (255 - BOX_ALPHA) / 255)
        for size in SIZES:
            lines = _lines(size, picker=True)
            box = lines.box
            expected = (box.left, box.top, box.right - 1, box.bottom - 1)
            assert (box.width, box.height) == PICKER_BOX_SIZE
            alone = _surface(size, gray)
            draw_game_over(alone, GameOverMessage.TOP_3, True)
            full = _scene(
                True,
                GameOverMessage.TOP_3,
                picker=_picker("ACE", 2),
                picking=True,
                size=size,
                gray=gray,
            )
            for name, surface in (("box alone", alone), ("all four calls", full)):
                tag = f"{gray=} {size=} {name}"
                assert _box_of_changes(surface, gray) == expected, f"{tag}: not the picker box"
                levels = _red_channel(surface)
                width = size[0]
                for x, y in ((box.left, box.top), (box.right - 1, box.bottom - 1)):
                    assert abs(levels[y * width + x] - shaded) <= BLEND_TOLERANCE, f"{tag}: {x, y}"
            seen[gray] = _red_channel(alone)[box.top * size[0] + box.left]
    assert len(set(seen.values())) == 3, "the picker box did not let each background through"


def _check_region(
    surface: pygame.Surface, top: int, bottom: int, ref: _Ref, line_top: int, what: str
) -> None:
    """The ink in rows [top, bottom) is ``ref``'s render exactly, its ink top is ``line_top`` plus
    the text's own offset, and the render is centered across the surface."""
    width = surface.get_width()
    ink = _ink_in(_red_channel(surface), width, 0, top, width, bottom)
    assert ink is not None, f"{what}: no ink in rows {top} to {bottom - 1}"
    _check_line(surface, ink, ref, line_top, what)


def test_the_picker_screen_stacks_six_lines_in_the_box(pygame_headless: None) -> None:
    for size in SIZES:
        lines = _lines(size, picker=True)
        for message, text in MESSAGE_TEXTS.items():
            tag = f"{size=} {message}"
            surface = _scene(True, message, picker=_picker("ACE", 3), picking=True, size=size)
            # The hint's ink starts on the row under the slot row, so those two are one band.
            bands = _bands(surface)
            assert len(bands) == 5, f"{tag}: {bands}"
            title, score, slots_and_hint, retry, menu = bands
            for above, below in pairwise(bands):
                assert above[1] < below[0], f"{tag}: lines out of order: {bands}"
            for band in bands:
                assert band[0] >= lines.box.top, f"{tag}: {band} above the box"
                assert band[1] < lines.box.bottom, f"{tag}: {band} below the box"
                assert band[2] >= lines.box.left, f"{tag}: {band} left of the box"
                assert band[3] < lines.box.right, f"{tag}: {band} right of the box"
            _check_line(surface, title, _ink_ref(text, TITLE_FONT_SIZE), lines.message, tag)
            score_ref = _ink_ref("SCORE 1 234 567", BODY_FONT_SIZE)
            _check_line(surface, score, score_ref, lines.score, tag)
            # The six lines, one under the other: the slot row from its top, the hint from the
            # row under it, in rows of their own.
            hint_ref = _ink_ref(HINT_TEXT, BODY_FONT_SIZE)
            _check_region(surface, lines.hint, lines.retry, hint_ref, lines.hint, f"{tag} hint")
            assert slots_and_hint[0] == lines.slots, f"{tag}: the slot row's top"
            assert lines.hint == lines.slots + lines.slot_line, f"{tag}: the hint is not under it"
            ink = _ink_in(_red_channel(surface), size[0], 0, lines.slots, size[0], lines.hint)
            assert ink is not None
            assert ink[1] == lines.hint - 1, f"{tag}: the slot row ends at row {ink[1]}"
            # RETRY and MENU are grey and have no marker while the picker takes the keys.
            for band, label, top in ((retry, "RETRY", lines.retry), (menu, "MENU", lines.menu)):
                ref = _ink_ref(label, BODY_FONT_SIZE, GREY)
                _check_line(surface, band, ref, top, f"{tag} {label}")
            # The block, from the message line's top to MENU's font height, sits in the box.
            body = pygame.font.Font(None, BODY_FONT_SIZE)
            block_bottom = lines.menu + body.get_height()
            assert abs((lines.message - lines.box.top) - (lines.box.bottom - block_bottom)) <= 1


def _cells(size: tuple[int, int]) -> tuple[list[tuple[int, int]], int]:
    """The ten cells as (left, width), read from the underlines of a blank picker, and the row of
    the underlines. A blank picker draws nothing else."""
    surface = _surface(size)
    draw_name_picker(surface, _picker(), False)
    width = size[0]
    levels = _red_channel(surface)
    bands = _bands(surface)
    assert len(bands) == 1, f"{size=}: not one line of ink: {bands}"
    assert bands[0][0] == bands[0][1], f"{size=}: not one row of ink: {bands}"
    row = bands[0][0]
    runs: list[tuple[int, int]] = []
    for x in range(width):
        level = levels[row * width + x]
        assert level in (0, GREY), f"{size=}: the underline is not grey: {level}"
        if level == GREY and (x == 0 or levels[row * width + x - 1] == 0):
            end = x
            while end < width and levels[row * width + end] == GREY:
                end += 1
            runs.append((x, end - x))
    return runs, row


def test_the_picker_has_ten_equal_cells_centered_each_with_an_underline(
    pygame_headless: None,
) -> None:
    font = pygame.font.Font(None, PICKER_FONT_SIZE)
    cell_width = max(font.size(character)[0] for character in CHARACTERS)
    gap = font.size(" ")[0]
    for size in SIZES:
        lines = _lines(size, picker=True)
        runs, row = _cells(size)
        assert len(runs) == SLOT_COUNT, f"{size=}: {len(runs)} underlines"
        assert row == lines.slots + lines.slot_line - 1, f"{size=}: the underline is on row {row}"
        # Equal cells, the widest character wide, one space of the picker font apart.
        assert all(width == cell_width for _, width in runs), f"{size=}: {runs}"
        steps = [b[0] - a[0] for a, b in pairwise(runs)]
        assert steps == [cell_width + gap] * (SLOT_COUNT - 1), f"{size=}: cells {steps} apart"
        # The row of cells is centered across the width.
        row_width = SLOT_COUNT * cell_width + (SLOT_COUNT - 1) * gap
        assert abs(2 * runs[0][0] + row_width - size[0]) <= TOLERANCE_PX, f"{size=}: {runs[0]}"


def _ink_in(levels: bytes, width: int, left: int, top: int, right: int, bottom: int) -> Band | None:
    """The ink's top row, bottom row, left column and right column inside the rectangle
    [left, right) x [top, bottom), or None when it holds none."""
    points = [
        (x, y) for y in range(top, bottom) for x in range(left, right) if levels[y * width + x]
    ]
    if not points:
        return None
    ys = [y for _, y in points]
    xs = [x for x, _ in points]
    return min(ys), max(ys), min(xs), max(xs)


def test_the_picker_centers_each_character_in_its_cell_and_a_blank_draws_nothing(
    pygame_headless: None,
) -> None:
    size = SURFACE_SIZE
    width = size[0]
    lines = _lines(size, picker=True)
    runs, underline = _cells(size)
    cell_width = runs[0][1]
    mixed = _picker("A C-E_0*?!")
    for character in CHARACTERS:
        pickers = [
            (NamePicker(slots=(character,) * SLOT_COUNT, cursor=0), [character] * SLOT_COUNT)
        ]
        if character == "A":
            pickers.append((mixed, list(mixed.slots)))
        for picker, expected_slots in pickers:
            surface = _surface(size)
            draw_name_picker(surface, picker, False)
            levels = _red_channel(surface)
            for (left, _), slot_character in zip(runs, expected_slots, strict=True):
                tag = f"{slot_character!r} in the cell at {left}"
                ink = _ink_in(levels, width, left, lines.slots, left + cell_width, underline)
                if slot_character == " ":
                    assert ink is None, f"{tag}: a blank drew ink {ink}"
                    continue
                assert ink is not None, f"{tag}: no ink"
                ref = _ink_ref(slot_character, PICKER_FONT_SIZE)
                crop = tuple(
                    levels[y * width + ink[2] : y * width + ink[3] + 1]
                    for y in range(ink[0], ink[1] + 1)
                )
                assert crop == ref.crop, f"{tag}: not the default font's render at 24 px"
                assert ink[0] == lines.slots + ref.ink_top, f"{tag}: not on the row's top"
                rect_left = ink[2] - ref.ink_left
                assert (
                    abs(2 * rect_left + ref.image_width - (2 * left + cell_width)) <= TOLERANCE_PX
                ), f"{tag}: not centered across its cell"
                # The underline is still the cell's bottom row, the cell's full width.
                assert all(
                    levels[underline * width + x] == GREY for x in range(left, left + cell_width)
                ), f"{tag}: the underline is broken"
    # A blank is never `_`: the picker with `_` has ink above the underline, the blank has none.
    assert _ink_ref("_", PICKER_FONT_SIZE).crop, "the underscore has no ink"


def _edges(cell: tuple[int, int], top: int, bottom: int) -> set[tuple[int, int]]:
    """The pixels of a rectangle outline 1 px wide on the cell's own edges, rows ``top`` to
    ``bottom`` inclusive."""
    left, width = cell
    right = left + width - 1
    edge = {(x, y) for x in range(left, right + 1) for y in (top, bottom)}
    edge |= {(x, y) for y in range(top, bottom + 1) for x in (left, right)}
    return edge


def test_while_picking_the_outline_is_on_the_cursor_cell_only_and_the_hint_shows(
    pygame_headless: None,
) -> None:
    for size in SIZES:
        width = size[0]
        lines = _lines(size, picker=True)
        runs, underline = _cells(size)
        for cursor in (0, 1, 4, 8, 9):
            tag = f"{size=} {cursor=}"
            picker = _picker("", cursor)
            picking = _scene(True, picker=picker, picking=True, size=size)
            saved = _scene(True, picker=picker, picking=False, size=size)
            levels_picking, levels_saved = _red_channel(picking), _red_channel(saved)
            # Blank slots, so a cell's edge has no character ink: the outline is white (255) on the
            # edges of the cursor's cell, from the row's top to the underline's row, drawn over the
            # underline, and no other cell's top row and sides have ink.
            for index, cell in enumerate(runs):
                edge = _edges(cell, lines.slots, underline)
                inside = {
                    (x, y)
                    for x in range(cell[0], cell[0] + cell[1])
                    for y in range(lines.slots, underline + 1)
                }
                for x, y in sorted(inside):
                    level = levels_picking[y * width + x]
                    if index == cursor and (x, y) in edge:
                        assert level == 255, f"{tag}: the outline pixel {(x, y)} is {level}"
                    elif index != cursor and (x, y) in edge and y != underline:
                        assert level == 0, f"{tag}: cell {index} has an outline pixel {(x, y)}"
                    elif (x, y) not in edge:
                        assert level == 0, f"{tag}: ink inside cell {index} at {(x, y)}"
            # After the save the outline is gone: the underline is the cell's bottom row, grey.
            for cell in runs:
                for x in range(cell[0], cell[0] + cell[1]):
                    assert levels_saved[underline * width + x] == GREY, f"{tag}: underline"
                    assert levels_saved[lines.slots * width + x] == 0, f"{tag}: outline after save"
            # The picture differs between picking and saved only in the cursor's edge pixels and
            # the rows of the hint, RETRY and MENU (grey against white with the marker).
            changed = {
                (i % width, i // width)
                for i, (a, b) in enumerate(zip(levels_picking, levels_saved, strict=True))
                if a != b
            }
            above_hint = {p for p in changed if p[1] < lines.hint}
            assert above_hint <= _edges(runs[cursor], lines.slots, underline), (
                f"{tag}: more than the outline differs above the hint"
            )
            assert above_hint, f"{tag}: no outline drawn"
            # The hint is shown while picking and its place stays empty after the save.
            hint_rows = range(lines.hint, lines.retry)
            hint_ref = _ink_ref(HINT_TEXT, BODY_FONT_SIZE)
            _check_region(picking, lines.hint, lines.retry, hint_ref, lines.hint, f"{tag} hint")
            for y in hint_rows:
                assert not any(levels_saved[y * width : (y + 1) * width]), f"{tag}: hint row {y}"


def test_after_the_save_the_slots_and_the_lines_stay_where_they_were(pygame_headless: None) -> None:
    for size in SIZES:
        lines = _lines(size, picker=True)
        runs, underline = _cells(size)
        picker = _picker("ACE", 2)
        message = GameOverMessage.TOP_3
        picking = _scene(True, message, picker=picker, picking=True, size=size)
        saved = _scene(True, message, picker=picker, picking=False, size=size)
        picking_bands, saved_bands = _bands(picking), _bands(saved)
        # While picking the hint touches the slot row, so those two are one band; after the save the
        # hint's place is empty.
        assert len(picking_bands) == 5, f"{size=}: {picking_bands}"
        assert len(saved_bands) == 6, f"{size=}: {saved_bands}"
        # The characters, then the underlines' row alone, then RETRY and MENU.
        top_of_ink = min(_ink_ref(character, PICKER_FONT_SIZE).ink_top for character in "ACE")
        assert saved_bands[2][0] == lines.slots + top_of_ink, f"{size=}: the characters' top"
        # Message and score: the same bands, the same pixels.
        for index in (0, 1):
            assert picking_bands[index] == saved_bands[index], f"{size=}: line {index} moved"
            assert _crop(picking, picking_bands[index]) == _crop(saved, saved_bands[index])
        # The slot row ends on the same underline row, and the characters keep their pixels.
        assert saved_bands[3][:2] == (underline, underline), f"{size=}: the underline moved"
        width = size[0]
        for (left, cell_width), character in zip(runs, picker.slots, strict=True):
            ink = _ink_in(
                _red_channel(saved), width, left, lines.slots, left + cell_width, underline
            )
            if character == " ":
                assert ink is None, f"{size=}: a blank slot shows {ink}"
                continue
            assert ink is not None
            assert ink[0] == lines.slots + _ink_ref(character, PICKER_FONT_SIZE).ink_top
        # RETRY and MENU, read in the picture where the other choice has the marker: white and
        # on the rows they had while grey.
        on_menu = _scene(True, message, picker=picker, selection=GameOverChoice.MENU, size=size)
        on_retry = _scene(True, message, picker=picker, selection=GameOverChoice.RETRY, size=size)
        retry_band, menu_band = _bands(on_menu)[-2], _bands(on_retry)[-1]
        assert retry_band[:2] == picking_bands[3][:2], f"{size=}: RETRY moved after the save"
        assert menu_band[:2] == picking_bands[4][:2], f"{size=}: MENU moved after the save"
        assert _crop(on_menu, retry_band) == _ink_ref("RETRY", BODY_FONT_SIZE).crop
        assert _crop(on_retry, menu_band) == _ink_ref("MENU", BODY_FONT_SIZE).crop
        _check_line(on_menu, retry_band, _ink_ref("RETRY", BODY_FONT_SIZE), lines.retry, "RETRY")
        _check_line(on_retry, menu_band, _ink_ref("MENU", BODY_FONT_SIZE), lines.menu, "MENU")
        # The marker is on the selected choice only, left of its label, one space away.
        space = pygame.font.Font(None, BODY_FONT_SIZE).size(" ")[0]
        levels_retry, levels_menu = _red_channel(on_retry), _red_channel(on_menu)
        differing = [
            (i % width, i // width)
            for i, (a, b) in enumerate(zip(levels_retry, levels_menu, strict=True))
            if a != b
        ]
        boundary = (retry_band[1] + menu_band[0]) / 2
        for label, markers in (
            (retry_band, [p for p in differing if p[1] < boundary]),
            (menu_band, [p for p in differing if p[1] > boundary]),
        ):
            assert markers, f"{size=}: no marker"
            right = max(x for x, _ in markers)
            assert right < label[2], f"{size=}: the marker is not left of its label"
            assert label[2] - right <= space + MARKER_GAP_SLACK_PX, f"{size=}: the marker is far"
            rows = [y for _, y in markers]
            assert min(rows) >= label[0] - MARKER_ROW_SLACK_PX
            assert max(rows) <= label[1] + MARKER_ROW_SLACK_PX


def test_while_picking_retry_and_menu_are_grey_with_no_marker_whatever_the_selection(
    pygame_headless: None,
) -> None:
    for size in SIZES:
        lines = _lines(size, picker=True)
        pictures = {
            choice: _scene(True, picker=_picker("ACE"), picking=True, selection=choice, size=size)
            for choice in GameOverChoice
        }
        assert _red_channel(pictures[GameOverChoice.RETRY]) == _red_channel(
            pictures[GameOverChoice.MENU]
        ), f"{size=}: the selection changed the picture while picking"
        # Every ink pixel of the two labels' rows is at most the grey level: no white text, no
        # white marker.
        width = size[0]
        levels = _red_channel(pictures[GameOverChoice.RETRY])
        body = pygame.font.Font(None, BODY_FONT_SIZE)
        rows = range(lines.retry, lines.menu + body.get_height())
        brightest = max(max(levels[y * width : (y + 1) * width]) for y in rows)
        assert brightest == GREY, f"{size=}: the brightest label pixel is {brightest}"
        # Drawn alone, the labels are the grey render, whichever the picker layout.
        alone = _surface(size)
        draw_game_over_choices(alone, GameOverChoice.MENU, True, active=False)
        bands = _bands(alone)
        assert len(bands) == 2
        _check_line(alone, bands[0], _ink_ref("RETRY", BODY_FONT_SIZE, GREY), lines.retry, "RETRY")
        _check_line(alone, bands[1], _ink_ref("MENU", BODY_FONT_SIZE, GREY), lines.menu, "MENU")


def test_the_game_over_views_draw_the_same_pixels_twice_and_change_nothing_but_the_surface(
    pygame_headless: None, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(0)
    texts_before = (
        dict(view.MESSAGE_TEXTS),
        view.PICKER_HINT_TEXT,
        view.RETRY_TEXT,
        view.MENU_TEXT,
    )
    pickers = [_picker("ACE", 3)]
    pickers += [
        NamePicker(slots=tuple(CHARACTERS[i : i + SLOT_COUNT].ljust(SLOT_COUNT)), cursor=9)
        for i in range(0, len(CHARACTERS), SLOT_COUNT)
    ]
    copies = [dataclasses.replace(picker) for picker in pickers]

    def scenes() -> list[bytes]:
        """Every screen: each message without the picker, and with the picker while picking and
        after the save, over every picker."""
        pictures = [
            _red_channel(_scene(False, message, selection=choice))
            for message in GameOverMessage
            for choice in GameOverChoice
        ]
        for picker in pickers:
            for picking in (True, False):
                for message in GameOverMessage:
                    picture = _scene(True, message, picker=picker, picking=picking)
                    pictures.append(_red_channel(picture))
        return pictures

    first = scenes()
    second = scenes()
    assert first == second, "two draws, two pictures"
    # Nothing fills the background: outside the box the gray is still gray, and the surface keeps
    # its size.
    for picker_shown in (False, True):
        gray = _scene(picker_shown, picker=_picker("ACE") if picker_shown else None, gray=GREY // 2)
        box = _lines(SURFACE_SIZE, picker_shown).box
        levels = _red_channel(gray)
        for y in range(SURFACE_SIZE[1]):
            for x in (0, box.left - 1, box.right, SURFACE_SIZE[0] - 1):
                assert levels[y * SURFACE_SIZE[0] + x] == GREY // 2, f"{(x, y)} outside the box"
        assert gray.get_size() == SURFACE_SIZE
    assert pickers == copies, "a draw changed a picker"
    assert texts_before == (
        dict(view.MESSAGE_TEXTS),
        view.PICKER_HINT_TEXT,
        view.RETRY_TEXT,
        view.MENU_TEXT,
    )
    assert caplog.records == [], "the view logged"
    # Every fixed text, message and character is rendered once, on the first draw; the first draws
    # above warmed the caches. After that no render per frame, and a new score renders one line.
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

    for module in (view, look_view):
        monkeypatch.setattr(module, "screen_font", counting, raising=False)
    for _ in range(3):
        assert scenes() == first
    assert renders == [], f"rendered again on later frames: {renders}"
    _scene(True, picker=_picker("ACE", 3), picking=True, score=7777777)
    assert renders == ["SCORE 7 777 777"], f"a new score did not render exactly its line: {renders}"
    _scene(True, picker=_picker("ACE", 3), picking=True, score=7777777)
    assert renders == ["SCORE 7 777 777"], f"the same score rendered again: {renders}"
