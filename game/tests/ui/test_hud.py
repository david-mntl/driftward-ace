"""HUD panel tests. Contract: docs/contracts/systems/hud.md, Presentation and Rules.

The panel is read from drawn pixels: a tile's top bar and digit, a heart's center, a climb bar's
column. Every position and color comes from tuning/hud.json, never from a number in a test.
"""

import dataclasses

import pygame
import pytest

from app.assets import load_hud_art
from app.hud_tuning import load_hud_rules
from core.world import SCREEN_H, SCREEN_W
from ui.hud import (
    HudArt,
    HudView,
    beat_scale_at,
    break_state_at,
    bump_scale_at,
    clamp_score,
    lamp_level_at,
    lit_segments,
    tier_color_key,
)
from ui.hud_rules import RGB, HudRules

SENTINEL: RGB = (255, 0, 255)
"""Fills the window before a draw, so any pixel the HUD didn't write shows."""


@dataclasses.dataclass(frozen=True)
class FakeRun:
    """The four numbers the HUD reads."""

    score: int = 0
    lives: int = 3
    grazes: int = 0
    level: int = 1


@pytest.fixture(scope="module")
def rules() -> HudRules:
    """The shipped HUD rules."""
    return load_hud_rules()


@pytest.fixture(scope="module")
def window(pygame_headless: None, rules: HudRules) -> pygame.Surface:
    """A window surface the size the rules say, with a display set for convert()."""
    return pygame.display.set_mode((rules.window.width, rules.window.height))


@pytest.fixture(scope="module")
def art(window: pygame.Surface, rules: HudRules) -> HudArt:
    """The shipped pictures and fonts."""
    return load_hud_art(rules)


@pytest.fixture
def view(rules: HudRules, art: HudArt) -> HudView:
    """A fresh view: no motion has started."""
    return HudView(rules, art)


def _draw(
    view: HudView, window: pygame.Surface, run: FakeRun, best: int | None = None, tick: int = 0
) -> None:
    window.fill(SENTINEL)
    view.draw(window, run, best, tick)


def _panel(rules: HudRules, x: int, y: int) -> tuple[int, int]:
    """Window position of panel-space point (x, y)."""
    return rules.panel.x + x, rules.panel.content_y + y


def _near(
    color: tuple[int, int, int, int] | pygame.Color, target: RGB, tolerance: int = 30
) -> bool:
    return all(abs(color[i] - target[i]) <= tolerance for i in range(3))


def _tile_bright_pixels(window: pygame.Surface, rules: HudRules, index: int) -> int:
    """Pixels in tile `index` below its top bar that are bright, like a lit digit's."""
    spec = rules.score
    x, y = _panel(rules, spec.tile_x + index * spec.tile_pitch, spec.tile_y + spec.tile_top)
    count = 0
    for px in range(x, x + spec.tile_w):
        for py in range(y, y + spec.tile_h - spec.tile_top):
            if sum(window.get_at((px, py))[:3]) > 600:
                count += 1
    return count


def _tile_top(window: pygame.Surface, rules: HudRules, index: int) -> pygame.Color:
    spec = rules.score
    x, y = _panel(rules, spec.tile_x + index * spec.tile_pitch + 1, spec.tile_y)
    return window.get_at((x, y))


def _heart_pixel(window: pygame.Surface, rules: HudRules, slot: int) -> pygame.Color:
    x, y = _panel(rules, *rules.hearts.slots[slot])
    return window.get_at((x, y))


# ----- pure helpers -----


def test_clamp_score_stops_at_the_last_number_the_tiles_can_show() -> None:
    assert clamp_score(48210, 7) == 48210
    assert clamp_score(9_999_999, 7) == 9_999_999
    assert clamp_score(12_000_000, 7) == 9_999_999
    assert clamp_score(0, 7) == 0
    assert clamp_score(-5, 7) == 0


@pytest.mark.parametrize(
    ("score", "best", "expected"),
    [
        (0, 112_430, 0),
        (0, None, 0),
        (1, 100, 1),
        (50, 100, 7),
        (100, 100, 14),
        (250, 100, 14),
        (5_000, None, 7),
        (9_999, None, 14),
        (10_000, None, 7),
        (20_000, None, 10),
        (9_999, 0, 14),
    ],
)
def test_the_score_bar_fills_toward_the_best_or_the_next_ten_thousand(
    score: int, best: int | None, expected: int
) -> None:
    assert lit_segments(score, best, 14, 10_000) == expected


@pytest.mark.parametrize(
    ("level", "expected"),
    [(1, "level"), (3, "level"), (4, "mid"), (6, "mid"), (7, "last_life"), (8, "last_life")],
)
def test_the_level_number_warms_up_at_the_tier_levels(level: int, expected: str) -> None:
    assert tier_color_key(level, 4, 7) == expected


def test_the_last_heart_beats_up_to_the_scale_and_back_every_beat(rules: HudRules) -> None:
    motion = rules.motion
    assert beat_scale_at(0, motion) == 1.0
    peak = round(motion.beat_ticks * motion.beat_peak_at)
    assert beat_scale_at(peak, motion) == pytest.approx(motion.beat_scale, abs=0.02)
    assert beat_scale_at(motion.beat_ticks - 1, motion) == 1.0
    assert beat_scale_at(motion.beat_ticks, motion) == 1.0


def test_the_graze_count_swells_once_then_rests(rules: HudRules) -> None:
    motion = rules.motion
    assert bump_scale_at(0, motion) == 1.0
    peak = round(motion.bump_ticks * motion.bump_peak_at)
    assert bump_scale_at(peak, motion) == pytest.approx(motion.bump_scale, abs=0.03)
    assert bump_scale_at(motion.bump_ticks, motion) == 1.0
    assert bump_scale_at(-1, motion) == 1.0


def test_the_lamp_pulses_down_to_its_low_halfway(rules: HudRules) -> None:
    motion = rules.motion
    assert lamp_level_at(0, motion) == 1.0
    assert lamp_level_at(motion.lamp_ticks // 2, motion) == pytest.approx(motion.lamp_low)
    assert lamp_level_at(motion.lamp_ticks, motion) == 1.0


def test_a_heart_break_runs_through_its_keys_then_ends(rules: HudRules) -> None:
    motion = rules.motion
    start = break_state_at(0, motion)
    assert start is not None
    assert start == (motion.break_keys[0][1], motion.break_keys[0][2])
    flicker = break_state_at(round(motion.break_ticks * 0.12), motion)
    assert flicker is not None
    assert flicker[0] < 0.3
    assert break_state_at(motion.break_ticks, motion) is None
    assert break_state_at(-1, motion) is None


# ----- score tiles and bar -----


def test_seven_tiles_show_a_seven_digit_score_with_no_dim_zero(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    _draw(view, window, FakeRun(score=1_204_880))
    for index in range(rules.score.tile_count):
        assert _tile_bright_pixels(window, rules, index) > 20
        assert _near(_tile_top(window, rules, index), rules.palette["score"], 0)


def test_leading_zeros_are_dim_and_the_digits_are_lit(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    _draw(view, window, FakeRun(score=48_210))
    for index in (0, 1):
        assert _tile_bright_pixels(window, rules, index) == 0
        assert _tile_top(window, rules, index) == pygame.Color(*rules.palette["dim"])
    for index in range(2, 7):
        assert _tile_bright_pixels(window, rules, index) > 20
        assert _tile_top(window, rules, index) == pygame.Color(*rules.palette["score"])


def test_a_score_of_zero_keeps_the_last_tile_lit(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    _draw(view, window, FakeRun(score=0))
    last = rules.score.tile_count - 1
    assert _tile_bright_pixels(window, rules, last) > 20
    assert _tile_bright_pixels(window, rules, 0) == 0


def test_a_score_past_the_tiles_shows_the_last_number_they_can(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    spec = rules.score
    _draw(view, window, FakeRun(score=9_999_999))
    x, y = _panel(rules, spec.tile_x, spec.tile_y)
    area = pygame.Rect(x, y, spec.tile_pitch * spec.tile_count, spec.tile_h)
    expected = window.subsurface(area).copy()
    _draw(view, window, FakeRun(score=12_345_678))
    assert pygame.image.tobytes(window.subsurface(area), "RGB") == pygame.image.tobytes(
        expected, "RGB"
    )


def test_the_score_bar_lights_the_segments_the_score_earns(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    spec = rules.score
    _draw(view, window, FakeRun(score=5_000))
    lit = lit_segments(5_000, None, spec.bar_segments, spec.bar_step)
    seg_w = (spec.bar_w - (spec.bar_segments - 1) * spec.bar_gap) / spec.bar_segments
    colors = []
    for index in range(spec.bar_segments):
        x, y = _panel(rules, spec.bar_x + round(index * (seg_w + spec.bar_gap)) + 1, spec.bar_y + 1)
        colors.append(window.get_at((x, y)))
    dim = pygame.Color(*rules.palette["dim"])
    assert all(color != dim for color in colors[:lit])
    assert all(color == dim for color in colors[lit:])


def test_best_shows_with_commas_and_is_hidden_without_a_best_score(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    spec = rules.score
    area = pygame.Rect(
        *_panel(rules, spec.best_label_x, spec.best_y - 8), spec.best_right - spec.best_label_x, 16
    )
    _draw(view, window, FakeRun(), best=None)
    hidden = pygame.image.tobytes(window.subsurface(area), "RGB")
    _draw(view, window, FakeRun(), best=112_430)
    shown = pygame.image.tobytes(window.subsurface(area), "RGB")
    assert hidden != shown
    _draw(view, window, FakeRun(), best=None)
    assert pygame.image.tobytes(window.subsurface(area), "RGB") == hidden


# ----- hearts -----


@pytest.mark.parametrize("lives", [3, 2])
def test_hearts_are_lit_for_each_life_left_and_dim_for_each_lost(
    view: HudView, window: pygame.Surface, rules: HudRules, lives: int
) -> None:
    _draw(view, window, FakeRun(lives=lives))
    for slot in range(3):
        pixel = _heart_pixel(window, rules, slot)
        if slot < lives:
            assert _near(pixel, rules.palette["hearts"]), (slot, pixel)
        else:
            assert not _near(pixel, rules.palette["hearts"], 60), (slot, pixel)


def test_the_last_life_is_one_orange_heart_and_two_dim_ones(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    _draw(view, window, FakeRun(lives=1))
    assert _near(_heart_pixel(window, rules, 0), rules.palette["last_life"])
    for slot in (1, 2):
        assert not _near(_heart_pixel(window, rules, slot), rules.palette["hearts"], 60)
        assert not _near(_heart_pixel(window, rules, slot), rules.palette["last_life"], 60)


def test_no_life_left_shows_three_dim_hearts(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    _draw(view, window, FakeRun(lives=0))
    for slot in range(3):
        pixel = _heart_pixel(window, rules, slot)
        assert not _near(pixel, rules.palette["hearts"], 60)
        assert not _near(pixel, rules.palette["last_life"], 60)


def test_the_pillar_lamp_lights_only_on_the_last_life(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    lamp = rules.frame.last_lamp
    _draw(view, window, FakeRun(lives=2))
    assert not _near(window.get_at(lamp), rules.palette["last_life"], 60)
    _draw(view, window, FakeRun(lives=1), tick=0)
    assert _near(window.get_at(lamp), rules.palette["last_life"], 30)
    _draw(view, window, FakeRun(lives=1), tick=rules.motion.lamp_ticks // 2)
    assert not _near(window.get_at(lamp), rules.palette["last_life"], 30)


# ----- level -----


@pytest.mark.parametrize("level", range(1, 9))
def test_climb_bars_are_lit_up_to_the_level_and_dim_above_it(
    view: HudView, window: pygame.Surface, rules: HudRules, level: int
) -> None:
    spec = rules.level
    _draw(view, window, FakeRun(level=level))
    span = (spec.bars - 1) * spec.bar_pitch + spec.bar_w
    dim = pygame.Color(*rules.palette["dim"])
    for index in range(spec.bars):
        x, y = _panel(
            rules, spec.bars_right - span + index * spec.bar_pitch + 1, spec.bars_bottom - 2
        )
        if index < level:
            assert window.get_at((x, y)) != dim, (level, index)
        else:
            assert window.get_at((x, y)) == dim, (level, index)


def test_the_climb_has_one_bar_per_level(rules: HudRules) -> None:
    assert rules.level.bars == 8


def test_bars_get_taller_one_by_one(view: HudView, window: pygame.Surface, rules: HudRules) -> None:
    spec = rules.level
    _draw(view, window, FakeRun(level=spec.bars))
    span = (spec.bars - 1) * spec.bar_pitch + spec.bar_w
    heights = []
    for index in range(spec.bars):
        x, _ = _panel(rules, spec.bars_right - span + index * spec.bar_pitch + 1, 0)
        top = 0
        for row in range(spec.bars_bottom - 1, 0, -1):
            if window.get_at((x, rules.panel.content_y + row)) == pygame.Color(*SENTINEL):
                break
            if window.get_at((x, rules.panel.content_y + row)) != pygame.Color(
                *rules.palette["dim"]
            ) and (
                _near(window.get_at((x, rules.panel.content_y + row)), rules.palette["level"], 120)
                or _near(
                    window.get_at((x, rules.panel.content_y + row)), rules.palette["last_life"], 60
                )
            ):
                top = spec.bars_bottom - row
        heights.append(top)
    assert heights == sorted(heights)
    assert heights[-1] > heights[0]


# ----- graze -----


def test_the_graze_count_shows_in_the_dial_and_changes_with_the_count(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    cx, cy = _panel(rules, *rules.graze.center)
    area = pygame.Rect(cx - 20, cy - 12, 40, 24)
    _draw(view, window, FakeRun(grazes=5))
    five = pygame.image.tobytes(window.subsurface(area), "RGB")
    view2 = HudView(rules, load_hud_art(rules))
    _draw(view2, window, FakeRun(grazes=12))
    assert pygame.image.tobytes(window.subsurface(area), "RGB") != five


def test_a_huge_graze_count_still_fits_the_dial(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    _draw(view, window, FakeRun(grazes=123_456_789))
    cx, cy = _panel(rules, *rules.graze.center)
    limit = rules.graze.count_limit
    outside = pygame.Rect(cx - limit // 2 - 6, cy - 14, 4, 28)
    for px in range(outside.left, outside.right):
        for py in range(outside.top, outside.bottom):
            assert not _near(window.get_at((px, py)), rules.palette["graze"], 20)


def test_the_radar_wedge_turns(view: HudView, window: pygame.Surface, rules: HudRules) -> None:
    cx, cy = _panel(rules, *rules.graze.center)
    radius = rules.graze.wedge_radius
    area = pygame.Rect(cx - radius, cy - radius, 2 * radius, 2 * radius)
    _draw(view, window, FakeRun())
    first = pygame.image.tobytes(window.subsurface(area), "RGB")
    _draw(view, window, FakeRun(), tick=rules.motion.sweep_ticks // 4)
    assert pygame.image.tobytes(window.subsurface(area), "RGB") != first
    _draw(view, window, FakeRun(), tick=rules.motion.sweep_ticks)
    assert pygame.image.tobytes(window.subsurface(area), "RGB") == first


def test_the_scan_line_moves_through_the_wireframe(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    m = rules.motion
    x, y_top = _panel(rules, m.scan_x + m.scan_w // 2, m.scan_from)
    _draw(view, window, FakeRun())
    start = window.get_at((x, y_top))
    _draw(view, window, FakeRun(), tick=m.scan_ticks // 2)
    assert window.get_at((x, y_top)) != start


# ----- motion that reacts to the run -----


def _area_around(rules: HudRules, point: tuple[int, int], half: int) -> pygame.Rect:
    x, y = _panel(rules, *point)
    return pygame.Rect(x - half, y - half, 2 * half, 2 * half)


def test_losing_a_life_breaks_that_heart_then_leaves_it_dim(
    rules: HudRules, art: HudArt, window: pygame.Surface
) -> None:
    broken = HudView(rules, art)
    _draw(broken, window, FakeRun(lives=3), tick=10)
    area = _area_around(rules, rules.hearts.slots[2], 14)
    _draw(broken, window, FakeRun(lives=2), tick=11)
    during = pygame.image.tobytes(window.subsurface(area), "RGB")
    steady = HudView(rules, art)
    _draw(steady, window, FakeRun(lives=2), tick=11)
    resting = pygame.image.tobytes(window.subsurface(area), "RGB")
    assert during != resting
    _draw(broken, window, FakeRun(lives=2), tick=11 + rules.motion.break_ticks)
    after = pygame.image.tobytes(window.subsurface(area), "RGB")
    _draw(steady, window, FakeRun(lives=2), tick=11 + rules.motion.break_ticks)
    assert after == pygame.image.tobytes(window.subsurface(area), "RGB")


def test_a_graze_swells_the_count_and_grows_a_ring_that_then_ends(
    rules: HudRules, art: HudArt, window: pygame.Surface
) -> None:
    cx, cy = _panel(rules, *rules.graze.center)
    radius = rules.graze.wedge_radius
    area = pygame.Rect(cx - radius, cy - radius, 2 * radius, 2 * radius)
    view = HudView(rules, art)
    _draw(view, window, FakeRun(grazes=4), tick=0)
    _draw(view, window, FakeRun(grazes=5), tick=1)
    during = pygame.image.tobytes(window.subsurface(area), "RGB")
    quiet = HudView(rules, art)
    _draw(quiet, window, FakeRun(grazes=5), tick=1)
    assert during != pygame.image.tobytes(window.subsurface(area), "RGB")
    late = 1 + max(rules.motion.ring_ticks, rules.motion.bump_ticks)
    _draw(view, window, FakeRun(grazes=5), tick=late)
    after = pygame.image.tobytes(window.subsurface(area), "RGB")
    _draw(quiet, window, FakeRun(grazes=5), tick=late)
    assert after == pygame.image.tobytes(window.subsurface(area), "RGB")


def test_a_new_run_starts_no_motion(rules: HudRules, art: HudArt, window: pygame.Surface) -> None:
    area = _area_around(rules, rules.hearts.slots[2], 14)
    view = HudView(rules, art)
    _draw(view, window, FakeRun(lives=0, grazes=9), tick=50)
    _draw(view, window, FakeRun(lives=3, grazes=0), tick=51)
    fresh = pygame.image.tobytes(window.subsurface(area), "RGB")
    quiet = HudView(rules, art)
    _draw(quiet, window, FakeRun(lives=3, grazes=0), tick=51)
    assert fresh == pygame.image.tobytes(window.subsurface(area), "RGB")


# ----- the frame and the play area -----


def _no_sheen(rules: HudRules) -> HudRules:
    return dataclasses.replace(rules, frame=dataclasses.replace(rules.frame, sheen=False))


def test_the_hud_never_draws_on_the_play_area_without_the_sheen(
    rules: HudRules, art: HudArt, window: pygame.Surface
) -> None:
    view = HudView(_no_sheen(rules), art)
    _draw(view, window, FakeRun(score=48_210, lives=1, grazes=5, level=5), best=112_430, tick=40)
    field = pygame.Rect(rules.window.field_x, rules.window.field_y, SCREEN_W, SCREEN_H)
    for px in (field.left, field.right - 1, field.centerx):
        for py in (field.top, field.bottom - 1, field.centery):
            assert window.get_at((px, py))[:3] == SENTINEL
    assert pygame.image.tobytes(window.subsurface(field), "RGB") == (
        pygame.image.tobytes(pygame.Surface(field.size), "RGB").replace(
            b"\x00\x00\x00", b"\xff\x00\xff"
        )
    )


def test_the_sheen_is_the_only_thing_over_the_play_area_and_it_is_faint(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    _draw(view, window, FakeRun())
    field = pygame.Rect(rules.window.field_x, rules.window.field_y, SCREEN_W, SCREEN_H)
    for px in range(field.left, field.right, 7):
        for py in range(field.top, field.bottom, 7):
            pixel = window.get_at((px, py))
            assert pixel[1] <= 120, (px, py, pixel)


def test_the_frame_covers_the_ring_round_the_glass_and_the_panel_covers_its_side(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    _draw(view, window, FakeRun())
    probes = [
        (2, 2),
        (rules.window.field_x - 2, rules.window.height // 2),
        (rules.window.width // 3, rules.window.height - 3),
        (rules.window.field_x + SCREEN_W + 4, rules.window.height // 2),
        (rules.panel.x + 5, 300),
        (rules.window.width - 3, rules.window.height - 3),
        (rules.window.width - 3, 3),
    ]
    for probe in probes:
        assert window.get_at(probe)[:3] != SENTINEL, probe


def test_dim_darkens_the_whole_window_by_the_alpha_in_the_rules(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    window.fill((200, 200, 200))
    view.dim(window)
    expected = round(200 * (255 - rules.window.dim_alpha) / 255)
    for probe in ((0, 0), (rules.window.width - 1, rules.window.height - 1), (400, 250)):
        assert abs(window.get_at(probe)[0] - expected) <= 1


def test_every_pixel_of_the_window_is_drawn_by_the_play_area_plus_the_hud(
    view: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    window.fill(SENTINEL)
    field = window.subsurface(
        pygame.Rect(rules.window.field_x, rules.window.field_y, SCREEN_W, SCREEN_H)
    )
    field.fill((0, 0, 0))
    view.draw(window, FakeRun(score=1, lives=3, level=2), 5, 0)
    raw = pygame.image.tobytes(window, "RGB")
    assert SENTINEL_BYTES not in [raw[i : i + 3] for i in range(0, len(raw), 3 * 997)]


SENTINEL_BYTES: bytes = bytes(SENTINEL)


def test_drawing_never_changes_the_loaded_pictures(
    rules: HudRules, art: HudArt, window: pygame.Surface
) -> None:
    before = [pygame.image.tobytes(heart, "RGBA") for heart in art.hearts]
    alphas = [heart.get_alpha() for heart in art.hearts] + [art.lamp.get_alpha()]
    view = HudView(rules, art)
    _draw(view, window, FakeRun(lives=3), tick=0)
    _draw(view, window, FakeRun(lives=1), tick=1)
    _draw(view, window, FakeRun(lives=0), tick=2)
    assert [pygame.image.tobytes(heart, "RGBA") for heart in art.hearts] == before
    assert [heart.get_alpha() for heart in art.hearts] + [art.lamp.get_alpha()] == alphas
