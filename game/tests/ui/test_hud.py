"""HUD layout tests. Contract: docs/contracts/systems/hud.md, Rules and Presentation.

From DRA-117 line 2 holds the GRAZE line (`GRAZE 0` for a fresh run), so the tests that said
line 2 was empty and compared the whole surface with the SCORE line alone now expect the GRAZE
line beside it.

Positions are read from the drawn pixels, never from a font size or a line height. The HUD
and the debug overlay must never overlap (Director, scope report DRA-13, Decision log). The
hearts show the lives left (scope report DRA-23, Values needed).
"""

from collections.abc import Callable

import pygame
import pytest

import ui.hud as hud_module
from core.graze import GrazeRules
from core.run import Run, start_run
from core.scroll import Scroll
from core.ship import spawn
from ui.debug_overlay import draw_debug_overlay, overlay_text_bottom
from ui.hud import (
    HEART_COLOR,
    HEART_GAP,
    HEART_MARGIN,
    HEART_SIZE,
    HUD_COLOR,
    HUD_FONT_SIZE,
    HUD_LINE_SPACING,
    HUD_MARGIN,
    HUD_OVERLAY_GAP,
    HUD_TOP,
    draw_hud,
)
from ui.score_text import graze_text, score_text

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
assert HUD_FONT_SIZE == 16

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
    flat = list(zip(data[0::3], data[1::3], data[2::3], strict=True))
    return [flat[y * width : (y + 1) * width] for y in range(height)]


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


def test_hud_normal_layout_starts_inside_the_margin_and_top(pygame_headless: None) -> None:
    rows = _hud(below_overlay=False)
    ink = _ink(rows)
    assert _white(rows), "no white readout pixel drawn"
    top = min(y for _, y in ink)
    left = min(x for x, _ in ink)
    assert top >= HUD_TOP, f"ink above the HUD top: row {top}"
    assert left >= HUD_MARGIN, f"ink left of the margin: column {left}"


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
    first = min(y for _, y in hud)
    assert first >= bottom + HUD_OVERLAY_GAP, f"HUD ink at row {first}, overlay bottom {bottom}"


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


# SCORE line tests, from DRA-61. Contract: systems/hud.md, Presentation (SCORE line) and Rules.
# Scope report DRA-61, Limits: SCORE on line 1 at the left margin, in the DRA-13 HUD look (default
# font, 16 px, white, antialiased); the meters readout is gone and line 2 stays empty.

SCORES: tuple[int, ...] = (0, 5, 999, 1234, 1234567, 10**11)
"""Scores drawn: 0, one digit, a full group, two groups, three groups, twelve digits. Source:
systems/hud.md, Presentation, score_text (the scope report's examples)."""

ZERO_SCROLL = Scroll(ticks=0, scrolled_ticks=0)
"""No meters flown, so the run's score is its coin points alone. Source: systems/run.md, score."""


def _score_run(score: int, lives: int = 0) -> Run:
    return Run(ship=spawn(), scroll=ZERO_SCROLL, lives=lives, coin_points=score)


def _score_hud(score: int, below_overlay: bool, lives: int = 0) -> Pixels:
    surface = _blank()
    draw_hud(surface, _score_run(score, lives), below_overlay)
    return _pixels(surface)


def _hud_top(below_overlay: bool) -> int:
    return overlay_text_bottom() + HUD_OVERLAY_GAP if below_overlay else HUD_TOP


def _reference_text(score: int) -> pygame.Surface:
    """The SCORE text as the contract sets its look: default font, 16 px, antialiased, white."""
    return pygame.font.Font(None, HUD_FONT_SIZE).render(score_text(score), True, HUD_COLOR)


def _reference_graze(grazes: int) -> pygame.Surface:
    """The GRAZE text as the contract sets its look: the SCORE line's, from `graze_text`."""
    return pygame.font.Font(None, HUD_FONT_SIZE).render(graze_text(grazes), True, HUD_COLOR)


def _expected_score_line(score: int, below_overlay: bool) -> Pixels:
    """A black surface with the SCORE text blitted at (HUD_MARGIN, hud_top)."""
    surface = _blank()
    surface.blit(_reference_text(score), (HUD_MARGIN, _hud_top(below_overlay)))
    return _pixels(surface)


def _expected_graze_line(grazes: int, below_overlay: bool) -> Pixels:
    """A black surface with the GRAZE text blitted at (HUD_MARGIN, hud_top + HUD_LINE_SPACING)."""
    surface = _blank()
    top = _hud_top(below_overlay) + HUD_LINE_SPACING
    surface.blit(_reference_graze(grazes), (HUD_MARGIN, top))
    return _pixels(surface)


def _expected_hud(run: Run, below_overlay: bool) -> Pixels:
    """SCORE on line 1 and GRAZE on line 2, as the contract sets them, for the run's own fields."""
    surface = _blank()
    top = _hud_top(below_overlay)
    surface.blit(_reference_text(run.score), (HUD_MARGIN, top))
    surface.blit(_reference_graze(run.grazes), (HUD_MARGIN, top + HUD_LINE_SPACING))
    return _pixels(surface)


def _rows(rows: Pixels, first: int, last: int) -> Pixels:
    """Rows `first` to `last - 1` of a drawn surface."""
    return rows[first:last]


def _line_one_ink(rows: Pixels, below_overlay: bool) -> list[tuple[int, int]]:
    """Ink above line 2's top: the SCORE line's rows."""
    return [(x, y) for (x, y) in _ink(rows) if y < _hud_top(below_overlay) + HUD_LINE_SPACING]


def test_hud_score_is_on_line_one_at_the_left_margin(pygame_headless: None) -> None:
    for below_overlay in (False, True):
        line_two_top = _hud_top(below_overlay) + HUD_LINE_SPACING
        for score in SCORES:
            drawn = _score_hud(score, below_overlay)
            # Line 1 is the SCORE text alone, where it always was.
            assert _rows(drawn, 0, line_two_top) == _rows(
                _expected_score_line(score, below_overlay), 0, line_two_top
            ), f"{score=}, {below_overlay=}: line 1 is not the SCORE text at ({HUD_MARGIN}, ...)"
            # The whole surface is the SCORE line with the GRAZE line beside it on line 2.
            assert drawn == _expected_hud(_score_run(score), below_overlay), (
                f"{score=}, {below_overlay=}: not SCORE on line 1 and GRAZE 0 on line 2"
            )
        ink = _line_one_ink(_score_hud(1234, below_overlay), below_overlay)
        top = _hud_top(below_overlay)
        assert min(x for x, _ in ink) >= HUD_MARGIN, f"{below_overlay=}: ink left of the margin"
        assert top <= min(y for _, y in ink), f"{below_overlay=}: ink above line 1"


def test_hud_score_pixels_follow_the_score(pygame_headless: None) -> None:
    for below_overlay in (False, True):
        seen: dict[int, Pixels] = {}
        for score in (0, 5, 1234, 0, 1234, 5):
            drawn = _score_hud(score, below_overlay)
            if score in seen:
                assert drawn == seen[score], f"{score=}, {below_overlay=}: same score, new pixels"
            seen[score] = drawn
        assert len({tuple(map(tuple, rows)) for rows in seen.values()}) == len(seen), (
            f"{below_overlay=}: two scores drew the same pixels"
        )
        widths = [
            max(x for x, _ in _line_one_ink(_score_hud(score, below_overlay), below_overlay))
            for score in SCORES
        ]
        assert widths == sorted(widths), f"{below_overlay=}: the text did not grow right: {widths}"
        assert widths[-1] > widths[0], f"{below_overlay=}: more digits did not widen the text"


def test_hud_line_two_holds_the_graze_line_only_and_the_meters_are_gone(
    pygame_headless: None,
) -> None:
    assert SCROLL.meters > 0, "the test run must have flown some meters"
    for below_overlay in (False, True):
        rows = _hud(below_overlay=below_overlay, lives=0)
        line_two_top = _hud_top(below_overlay) + HUD_LINE_SPACING
        line_three_top = line_two_top + HUD_LINE_SPACING
        # Line 2 is `GRAZE 0` and nothing else: no meters readout.
        expected = _expected_graze_line(0, below_overlay)
        assert _rows(rows, line_two_top, line_three_top) == _rows(
            expected, line_two_top, line_three_top
        ), f"{below_overlay=}: line 2 is not GRAZE 0 alone"
        assert _ink(_rows(expected, line_two_top, line_three_top)), "no GRAZE line in the reference"
        stray = [(x, y) for (x, y) in _ink(rows) if y >= line_three_top]
        assert not stray, f"{below_overlay=}: ink below line 2, first {stray[:3]}"
        assert _line_one_ink(rows, below_overlay), f"{below_overlay=}: no SCORE drawn"


def test_hud_score_top_is_the_overlay_bottom_plus_the_gap(pygame_headless: None) -> None:
    blit_top = overlay_text_bottom() + HUD_OVERLAY_GAP
    ink_offset = _reference_text(1234).get_bounding_rect().top
    for score in (0, 1234):
        ink = _ink(_score_hud(score, below_overlay=True))
        first = min(y for _, y in ink)
        assert first == blit_top + _reference_text(score).get_bounding_rect().top, (
            f"{score=}: first ink row {first}, expected blit top {blit_top} plus {ink_offset}"
        )
        assert _score_hud(score, True) == _expected_hud(_score_run(score), True)
    normal_first = min(y for _, y in _ink(_score_hud(1234, below_overlay=False)))
    assert normal_first == HUD_TOP + ink_offset, "normal mode: SCORE not at HUD_TOP"


def test_hud_earlier_rules_hold_with_score(pygame_headless: None) -> None:
    overlay = _ink(_overlay(), ignore_rows=(TOP_LINE_ROW, FLOOR_ROW))
    overlay_pixels = set(_ink(_overlay()))
    bottom = overlay_text_bottom()
    plain_hearts = [row[HEART_AREA_LEFT:] for row in _score_hud(0, False, lives=3)]
    for score in SCORES:
        for below_overlay in (False, True):
            tag = f"{score=}, {below_overlay=}"
            rows = _score_hud(score, below_overlay, lives=3)
            text = [(x, y) for (x, y) in _ink(rows) if x < HEART_AREA_LEFT]
            assert text, f"{tag}: no SCORE drawn"
            assert max(y for _, y in _ink(rows)) < TOP_LINE_ROW, f"{tag}: HUD reaches the top line"
            assert max(x for x, _ in text) < HEART_AREA_LEFT - 1, f"{tag}: SCORE reaches the hearts"
            assert [row[HEART_AREA_LEFT:] for row in rows] == plain_hearts, f"{tag}: hearts moved"
            if below_overlay:
                assert min(y for _, y in text) > max(y for _, y in overlay), f"{tag}: overlap"
                assert min(y for _, y in text) >= bottom + HUD_OVERLAY_GAP, f"{tag}: gap lost"
                covered = _blank()
                draw_debug_overlay(covered, spawn())
                draw_hud(covered, _score_run(score, 3), True)
                for y, row in enumerate(_pixels(covered)):
                    for x, pixel in enumerate(row):
                        if (x, y) not in overlay_pixels:
                            assert pixel == rows[y][x], f"{tag}: HUD pixel differs at {(x, y)}"


# GRAZE line tests, from DRA-117. Contract: systems/hud.md, Presentation (GRAZE line) and Rules.
# Scope report DRA-117, Limits: GRAZE on line 2 at the left margin, in SCORE's stand-in look
# (default font, 16 px, white, antialiased), digits grouped like SCORE, no digit limit.

GRAZES: tuple[int, ...] = (0, 5, 999, 1234, 1234567, 10**11)
"""Counts drawn: 0, one digit, a full group, two groups, three groups, twelve digits. Source:
systems/hud.md, Presentation, graze_text (`GRAZE 0`, `GRAZE 5`, `GRAZE 1 234`)."""

NO_GRAZE_POINTS = GrazeRules(points=0)
"""Grazes that pay nothing, so the score stays put while the count changes. Source: systems/run.md,
Interface, `GrazeRules.points` (>= 0) and `Run.score`."""


def _graze_run(
    grazes: int,
    lives: int = 0,
    coin_points: int = 1234,
    rules: GrazeRules | None = None,
) -> Run:
    return Run(
        ship=spawn(),
        scroll=ZERO_SCROLL,
        lives=lives,
        coin_points=coin_points,
        grazes=grazes,
        graze_rules=rules if rules is not None else GrazeRules(),
    )


def _graze_hud(run: Run, below_overlay: bool) -> Pixels:
    surface = _blank()
    draw_hud(surface, run, below_overlay)
    return _pixels(surface)


def test_hud_graze_is_on_line_two_at_the_left_margin(pygame_headless: None) -> None:
    for below_overlay in (False, True):
        line_two_top = _hud_top(below_overlay) + HUD_LINE_SPACING
        for grazes in GRAZES:
            run = _graze_run(grazes)
            drawn = _graze_hud(run, below_overlay)
            tag = f"{grazes=}, {below_overlay=}"
            # The whole surface: SCORE on line 1 and GRAZE on line 2, in SCORE's look.
            assert drawn == _expected_hud(run, below_overlay), f"{tag}: not the two lines"
            # Line 2 alone is the GRAZE text at (HUD_MARGIN, hud_top + HUD_LINE_SPACING).
            assert _rows(drawn, line_two_top, SURFACE_SIZE[1]) == _rows(
                _expected_graze_line(grazes, below_overlay), line_two_top, SURFACE_SIZE[1]
            ), f"{tag}: line 2 is not graze_text at ({HUD_MARGIN}, {line_two_top})"
            ink = [(x, y) for (x, y) in _ink(drawn) if y >= line_two_top]
            assert ink, f"{tag}: no GRAZE drawn"
            assert min(x for x, _ in ink) >= HUD_MARGIN, f"{tag}: ink left of the margin"
            assert max(y for _, y in ink) < line_two_top + HUD_LINE_SPACING, f"{tag}: below line 2"


def test_hud_shows_graze_zero_for_a_fresh_run_and_after_game_over(pygame_headless: None) -> None:
    fresh = start_run()
    assert fresh.grazes == 0
    for run in (fresh, _graze_run(0, lives=3, coin_points=0), _graze_run(0, lives=0)):
        for below_overlay in (False, True):
            drawn = _graze_hud(run, below_overlay)
            line_two_top = _hud_top(below_overlay) + HUD_LINE_SPACING
            # Left of the hearts' area, where line 2 is.
            band = range(line_two_top, line_two_top + HUD_LINE_SPACING)
            expected = _expected_graze_line(0, below_overlay)
            assert [drawn[y][:HEART_AREA_LEFT] for y in band] == [
                expected[y][:HEART_AREA_LEFT] for y in band
            ], f"{below_overlay=}: not GRAZE 0 on a fresh run"
    # While the Game Over box shows the HUD still shows the count: the run is frozen, not hidden.
    over = Run(ship=spawn(), scroll=ZERO_SCROLL, lives=0, game_over=True, grazes=7)
    for below_overlay in (False, True):
        assert _graze_hud(over, below_overlay) == _expected_hud(over, below_overlay)


def test_hud_score_line_stays_put_beside_the_graze_line(pygame_headless: None) -> None:
    for below_overlay in (False, True):
        line_two_top = _hud_top(below_overlay) + HUD_LINE_SPACING
        # Same score (graze points 0), counts change: line 1 is the same pixels.
        line_one = [
            _rows(_graze_hud(_graze_run(g, rules=NO_GRAZE_POINTS), below_overlay), 0, line_two_top)
            for g in GRAZES
        ]
        assert all(rows == line_one[0] for rows in line_one), f"{below_overlay=}: SCORE moved"
        assert _rows(line_one[0], 0, line_two_top) == _rows(
            _expected_score_line(1234, below_overlay), 0, line_two_top
        ), f"{below_overlay=}: SCORE is not where it was"
        # Same count, scores change: line 2 and below are the same pixels.
        line_two = [
            _rows(_graze_hud(_graze_run(5, coin_points=c), below_overlay), line_two_top, 480)
            for c in SCORES
        ]
        assert all(rows == line_two[0] for rows in line_two), f"{below_overlay=}: GRAZE moved"


def test_hud_graze_pixels_follow_the_count(pygame_headless: None) -> None:
    for below_overlay in (False, True):
        line_two_top = _hud_top(below_overlay) + HUD_LINE_SPACING
        seen: dict[int, Pixels] = {}
        for grazes in (0, 5, 1234, 0, 1234, 5):
            drawn = _rows(
                _graze_hud(_graze_run(grazes, rules=NO_GRAZE_POINTS), below_overlay),
                line_two_top,
                480,
            )
            if grazes in seen:
                assert drawn == seen[grazes], f"{grazes=}, {below_overlay=}: same count, new pixels"
            seen[grazes] = drawn
        assert len({tuple(map(tuple, rows)) for rows in seen.values()}) == len(seen), (
            f"{below_overlay=}: two counts drew the same pixels"
        )
        widths = [
            max(
                x
                for x, y in _ink(_graze_hud(_graze_run(g, rules=NO_GRAZE_POINTS), below_overlay))
                if y >= line_two_top
            )
            for g in GRAZES
        ]
        assert widths == sorted(widths), f"{below_overlay=}: the text did not grow right: {widths}"
        assert widths[-1] > widths[0], f"{below_overlay=}: more digits did not widen the text"


def test_hud_graze_never_overlaps_the_overlay_hearts_or_top_line(pygame_headless: None) -> None:
    overlay = _ink(_overlay(), ignore_rows=(TOP_LINE_ROW, FLOOR_ROW))
    overlay_pixels = set(_ink(_overlay()))
    bottom = overlay_text_bottom()
    plain_hearts = [row[HEART_AREA_LEFT:] for row in _graze_hud(_graze_run(0, lives=3), False)]
    for grazes in GRAZES:
        for below_overlay in (False, True):
            tag = f"{grazes=}, {below_overlay=}"
            line_two_top = _hud_top(below_overlay) + HUD_LINE_SPACING
            rows = _graze_hud(_graze_run(grazes, lives=3), below_overlay)
            text = [(x, y) for (x, y) in _ink(rows) if x < HEART_AREA_LEFT and y >= line_two_top]
            assert text, f"{tag}: no GRAZE drawn"
            assert max(y for _, y in text) < TOP_LINE_ROW, f"{tag}: GRAZE reaches the top line"
            assert max(x for x, _ in text) < HEART_AREA_LEFT - 1, f"{tag}: GRAZE reaches hearts"
            assert [row[HEART_AREA_LEFT:] for row in rows] == plain_hearts, f"{tag}: hearts moved"
            if below_overlay:
                assert min(y for _, y in text) > max(y for _, y in overlay), f"{tag}: overlap"
                assert min(y for _, y in text) >= bottom + HUD_OVERLAY_GAP + HUD_LINE_SPACING, tag
                covered = _blank()
                draw_debug_overlay(covered, spawn())
                draw_hud(covered, _graze_run(grazes, lives=3), True)
                for y, row in enumerate(_pixels(covered)):
                    for x, pixel in enumerate(row):
                        if (x, y) not in overlay_pixels:
                            assert pixel == rows[y][x], f"{tag}: HUD pixel differs at {(x, y)}"


def test_hud_graze_text_is_rendered_again_only_when_the_count_changes(
    pygame_headless: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each text is built by `graze_text` / `score_text` only when its own number is new.

    The calls are counted through the names `ui.hud` imports from `ui.score_text`; the cache is
    one slot per text (hud.md, GRAZE line and SCORE line). A count that no earlier test drew
    (41) is drawn once before counting, so the one-slot cache holds it whatever ran before.
    """
    calls: dict[str, int] = {"graze": 0, "score": 0}

    def counting(name: str, real: Callable[[int], str]) -> Callable[[int], str]:
        def wrapper(number: int) -> str:
            calls[name] += 1
            return real(number)

        return wrapper

    surface = _blank()
    draw_hud(surface, _graze_run(41, rules=NO_GRAZE_POINTS), False)
    monkeypatch.setattr(hud_module, "graze_text", counting("graze", graze_text))
    monkeypatch.setattr(hud_module, "score_text", counting("score", score_text))

    def frame(grazes: int, coin_points: int) -> None:
        draw_hud(surface, _graze_run(grazes, coin_points=coin_points, rules=NO_GRAZE_POINTS), False)

    for _ in range(5):
        frame(41, 1234)
    assert calls == {"graze": 0, "score": 0}, f"same numbers re-rendered: {calls}"
    frame(42, 1234)
    assert calls == {"graze": 1, "score": 0}, f"a new count did not render once: {calls}"
    for _ in range(5):
        frame(42, 1234)
    assert calls == {"graze": 1, "score": 0}, f"the same count re-rendered: {calls}"
    frame(42, 1235)
    assert calls == {"graze": 1, "score": 1}, f"a new score re-rendered the GRAZE text: {calls}"
    frame(41, 1235)
    assert calls == {"graze": 2, "score": 1}, f"a changed count did not render again: {calls}"
