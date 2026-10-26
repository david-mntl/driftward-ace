"""Game-over screen tests: the box, the title, the score line, and RETRY above MENU.

Contract: docs/contracts/systems/game-flow.md, Interface (ui/game_over.py) and Presentation,
Game-over screen and the shared items (Text, Lines and blank lines, Selection marker, Box, Cache,
Only draws). The box's size, the texts, the font sizes, the marker and the fill's alpha are
stand-ins from scope report DRA-125, Values needed (Game-over screen; the DRA-23 box fill and the
DRA-61 score line); the GDD does not hold them until UI-04.

Positions are read from the drawn pixels (`pygame.image.tobytes`), never from a font size or a
line height. On a black 640 x 480 surface the box (black at alpha 90) adds no ink, so the ink is
the text alone. The score line's text is written here from the contract's examples (groups of
three split by a space), never taken from `score_text`.
"""

import pygame

from core.game_flow import GameOverChoice
from ui.game_over import draw_final_score, draw_game_over, draw_game_over_choices

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
