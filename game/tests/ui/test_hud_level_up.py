"""HUD level pop tests. Contract: docs/contracts/systems/level-up/view.md, Interface (`HudView`,
`LevelSlot`) and Presentation (the HUD pop, Cost); docs/contracts/systems/level-up/core.md, Rules
(the shown level); docs/contracts/systems/hud.md, Rules (the level pop and the level bars).

Like test_hud.py, the HUD is built from the game's hud.json and art. The level-up look is written
below, to the shape of docs/contracts/schemas/level-up.schema.json: no level_up.json is read. The
HUD is read from drawn pixels: the number is found by its exact color, a climb bar by a pixel of
its column, the box outline by a pixel of its top edge. Every position comes from hud.json.
"""

import dataclasses
from collections.abc import Callable

import pygame
import pytest

from app.assets import load_hud_art
from app.hud_tuning import load_hud_rules
from core.level_up import LevelUpBanner
from core.levels import LEVEL_COUNT
from ui.hud import HudArt, HudView
from ui.hud_rules import RGB, HudRules
from ui.level_up_rules import (
    BandLook,
    BumpLook,
    FlyLook,
    GlintLook,
    HoldLook,
    LabelLook,
    LevelUpLook,
    NumberLook,
    PipsLook,
    PopLook,
    RingLook,
    StreakLook,
)

SENTINEL: RGB = (255, 0, 255)
"""Fills the window before a draw, so any pixel the HUD didn't write shows."""

FLASH: RGB = (255, 255, 255)
BOX_FLASH: RGB = (0, 255, 128)
"""The pop's white and the box outline's flash color. Test-local, like every value of `LOOK`."""

ARRIVAL: int = 110
LIFETIME: int = 140

POP = PopLook(
    ticks=20,
    start_scale=1.4,
    undershoot_scale=0.9,
    undershoot_share=0.5,
    flash_ticks=12,
    steps=10,
    bar_flash_ticks=16,
    box_flash_ticks=18,
    box_flash_width=1,
    box_corner_cut=8,
)
"""`box_corner_cut` 8 is the cut the panel art draws (10 x panel.scale 0.8). Source: level-up
schema, pop.box_corner_cut."""

LOOK = LevelUpLook(
    colors={
        "glass": (10, 16, 41),
        "hairline": (61, 255, 252),
        "label": (247, 247, 247),
        "number_top": (255, 246, 214),
        "number_bottom": (255, 200, 0),
        "number_outline": (10, 16, 41),
        "ring": (255, 246, 214),
        "streak": (255, 246, 214),
        "glint": (255, 246, 214),
        "pip_lit": (255, 200, 0),
        "pip_unlit": (41, 52, 106),
        "flash": FLASH,
        "box_flash": BOX_FLASH,
    },
    band=BandLook(
        height=100,
        alpha=100,
        center_offset_y=0,
        open_start=3,
        open_end=13,
        close_start=90,
        close_end=120,
        close_glass_share=0.6,
        hairline_width=1,
        corner_tick_length=6,
    ),
    number=NumberLook(
        font_size=80,
        outline_width=2,
        center_offset_y=0,
        fall_start=4,
        fall_end=20,
        fall_overshoot_px=8.0,
        fall_peak_share=0.7,
        fall_stretch_x=0.9,
        fall_stretch_y=1.1,
        squash_ticks=6,
        squash_x=1.25,
        squash_y=0.8,
        pose_steps=4,
    ),
    label=LabelLook(
        font_size=14,
        offset_y=-48,
        fade_in_start=22,
        fade_in_end=36,
        spacing_wide=14,
        spacing_normal=4,
        spacing_steps=5,
    ),
    hold=HoldLook(fade_out_start=96, fade_out_end=106),
    pips=PipsLook(size=10, pitch=18, offset_y=48, start=26, end=48, pop_ticks=6, flash_ticks=10),
    ring=RingLook(start_diameter=48.0, end_diameter=170.0, width=2, ticks=18),
    streaks=StreakLook(
        count=12, ticks=14, length=20.0, width=2, start_radius=34.0, end_radius=130.0
    ),
    glint=GlintLook(start=44, end=60, frames=8, width=14, slant_degrees=20.0, strength=0.8),
    bump=BumpLook(pixels=4, ticks=12, peak_share=0.3),
    fly=FlyLook(start=90, arc_px=30.0, steps=8),
    pop=POP,
)

LIVES: int = 5
"""Lives and grazes stay the same in every draw, so no heart or graze motion starts."""


@dataclasses.dataclass(frozen=True)
class FakeRun:
    """The four numbers the HUD reads."""

    score: int = 1_250
    lives: int = LIVES
    grazes: int = 3
    level: int = 1


def banner(level: int, previous: int, age: int) -> LevelUpBanner:
    """A banner of the rise from `previous` to `level`, `age` ticks old."""
    return LevelUpBanner(
        level=level,
        previous_level=previous,
        arrival_ticks=ARRIVAL,
        lifetime_ticks=LIFETIME,
        age_ticks=age,
    )


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


@pytest.fixture(scope="module")
def plain(rules: HudRules, art: HudArt) -> HudView:
    """The HUD built the old way: no look."""
    return HudView(rules, art)


@pytest.fixture(scope="module")
def popping(rules: HudRules, art: HudArt) -> HudView:
    """The HUD built with the level-up look."""
    return HudView(rules, art, LOOK)


def draw(
    view: HudView,
    window: pygame.Surface,
    run: FakeRun,
    level_up: LevelUpBanner | None = None,
    tick: int = 0,
) -> bytes:
    """Draw the HUD on a sentinel window and return every pixel."""
    window.fill(SENTINEL)
    view.draw(window, run, 5_000, tick, level_up)
    return pygame.image.tobytes(window, "RGB")


def panel_point(rules: HudRules, x: int, y: int) -> tuple[int, int]:
    """Window position of panel-space point (x, y)."""
    return rules.panel.x + x, rules.panel.content_y + y


def bar_point(rules: HudRules, index: int) -> tuple[int, int]:
    """A pixel of climb bar `index` (0 from the left), inside its body."""
    spec = rules.level
    span = (spec.bars - 1) * spec.bar_pitch + spec.bar_w
    return panel_point(rules, spec.bars_right - span + index * spec.bar_pitch, spec.bars_bottom - 2)


def box_edge_point(rules: HudRules) -> tuple[int, int]:
    """A pixel on the level box's top edge, halfway along it, away from the cut corners."""
    left, top, width, _ = rules.level.box
    return panel_point(rules, left + width // 2, top)


def lit_bars(window: pygame.Surface, rules: HudRules) -> int:
    """How many climb bars are not `dim`."""
    dim = pygame.Color(*rules.palette["dim"])
    return sum(window.get_at(bar_point(rules, index)) != dim for index in range(rules.level.bars))


def ink_rect(window: pygame.Surface, rules: HudRules, color: RGB) -> pygame.Rect | None:
    """The box of the pixels that are exactly `color`, in the level box to the left of the climb
    bars. None when there are none.
    """
    left, top, width, height = rules.level.box
    spec = rules.level
    span = (spec.bars - 1) * spec.bar_pitch + spec.bar_w
    right = min(left + width, spec.bars_right - span)
    xs: list[int] = []
    ys: list[int] = []
    for panel_x in range(left, right):
        for panel_y in range(top, top + height):
            x, y = panel_point(rules, panel_x, panel_y)
            if window.get_at((x, y))[:3] == color:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)


RISES = [(1, 2), (3, 4), (6, 7), (7, 8), (1, 4), (2, 8)]
"""(previous level, level): a plain rise, the one that turns the number warm, the one that turns it
red, the last one, and two skipped levels."""


# ----- the shown level -----


@pytest.mark.parametrize(("previous", "level"), RISES)
def test_the_hud_shows_the_previous_level_for_every_age_below_the_arrival(
    plain: HudView,
    popping: HudView,
    window: pygame.Surface,
    previous: int,
    level: int,
) -> None:
    old = draw(plain, window, FakeRun(level=previous))
    new = draw(plain, window, FakeRun(level=level))
    assert old != new
    run = FakeRun(level=level)
    for age in (0, 1, ARRIVAL // 2, ARRIVAL - 2, ARRIVAL - 1):
        assert draw(popping, window, run, banner(level, previous, age)) == old, age


@pytest.mark.parametrize(("previous", "level"), RISES)
def test_the_hud_shows_the_new_level_from_the_arrival_and_lights_its_bars(
    popping: HudView,
    window: pygame.Surface,
    rules: HudRules,
    previous: int,
    level: int,
) -> None:
    run = FakeRun(level=level)
    for age in range(ARRIVAL - 1, ARRIVAL + POP.ticks + 3):
        draw(popping, window, run, banner(level, previous, age))
        expected = previous if age < ARRIVAL else level
        assert lit_bars(window, rules) == expected, age
        for index in range(rules.level.bars):
            lit = window.get_at(bar_point(rules, index)) != pygame.Color(*rules.palette["dim"])
            assert lit == (index < expected), (age, index)


@pytest.mark.parametrize(("previous", "level"), RISES)
def test_the_hud_is_exactly_the_hud_of_the_new_level_once_the_pop_is_over(
    plain: HudView,
    popping: HudView,
    window: pygame.Surface,
    previous: int,
    level: int,
) -> None:
    expected = draw(plain, window, FakeRun(level=level))
    run = FakeRun(level=level)
    for age in (ARRIVAL + POP.ticks, ARRIVAL + POP.ticks + 1, LIFETIME - 1):
        assert draw(popping, window, run, banner(level, previous, age)) == expected, age


# ----- the pop -----


@pytest.mark.parametrize(("previous", "level"), RISES)
def test_the_level_number_is_larger_than_normal_on_the_arrival_and_normal_by_the_pops_end(
    plain: HudView,
    popping: HudView,
    window: pygame.Surface,
    rules: HudRules,
    previous: int,
    level: int,
) -> None:
    tier = plain.level_slot(level).color
    draw(plain, window, FakeRun(level=level))
    normal = ink_rect(window, rules, tier)
    assert normal is not None
    run = FakeRun(level=level)
    draw(popping, window, run, banner(level, previous, ARRIVAL))
    arrival = ink_rect(window, rules, FLASH)
    assert arrival is not None
    assert arrival.width > normal.width
    assert arrival.height > normal.height
    assert arrival.center == pytest.approx(normal.center, abs=2)
    draw(popping, window, run, banner(level, previous, ARRIVAL + POP.ticks))
    assert ink_rect(window, rules, tier) == normal
    assert ink_rect(window, rules, FLASH) is None


def test_the_number_is_never_larger_than_its_arrival_size_during_the_pop(
    popping: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    level = 5
    run = FakeRun(level=level)
    tier = popping.level_slot(level).color
    draw(popping, window, run, banner(level, level - 1, ARRIVAL))
    arrival = ink_rect(window, rules, FLASH)
    assert arrival is not None
    for age in range(ARRIVAL, ARRIVAL + POP.ticks + 2):
        draw(popping, window, run, banner(level, level - 1, age))
        rect = ink_rect(window, rules, tier) or ink_rect(window, rules, FLASH)
        if rect is not None:
            assert rect.width <= arrival.width, age
            assert rect.height <= arrival.height, age


@pytest.mark.parametrize(("previous", "level"), RISES)
def test_the_new_climb_bar_and_the_box_outline_flash_then_are_as_without_a_banner(
    plain: HudView,
    popping: HudView,
    window: pygame.Surface,
    rules: HudRules,
    previous: int,
    level: int,
) -> None:
    run = FakeRun(level=level)
    draw(plain, window, run)
    bar = bar_point(rules, level - 1)
    edge = box_edge_point(rules)
    normal_bar = window.get_at(bar)
    normal_edge = window.get_at(edge)
    other_bars = {
        index: window.get_at(bar_point(rules, index)) for index in range(rules.level.bars)
    }
    assert normal_edge[:3] != BOX_FLASH
    assert normal_bar[:3] != FLASH

    draw(popping, window, run, banner(level, previous, ARRIVAL))
    assert window.get_at(bar)[:3] == FLASH
    assert window.get_at(edge)[:3] == BOX_FLASH
    for index, color in other_bars.items():
        if index != level - 1:
            assert window.get_at(bar_point(rules, index)) == color, index

    draw(popping, window, run, banner(level, previous, ARRIVAL + 1))
    assert window.get_at(bar) != normal_bar
    assert window.get_at(edge) != normal_edge

    draw(popping, window, run, banner(level, previous, ARRIVAL + POP.bar_flash_ticks))
    assert window.get_at(bar) == normal_bar
    draw(popping, window, run, banner(level, previous, ARRIVAL + POP.box_flash_ticks))
    assert window.get_at(edge) == normal_edge
    for age in range(ARRIVAL + POP.ticks, ARRIVAL + POP.ticks + 3):
        draw(popping, window, run, banner(level, previous, age))
        assert window.get_at(bar) == normal_bar
        assert window.get_at(edge) == normal_edge


def test_the_box_outline_and_the_bar_fade_without_going_back(
    popping: HudView, window: pygame.Surface, rules: HudRules
) -> None:
    level = 3
    run = FakeRun(level=level)
    bar = bar_point(rules, level - 1)
    edge = box_edge_point(rules)

    def distance(color: pygame.Color, target: RGB) -> int:
        return sum(abs(color[i] - target[i]) for i in range(3))

    draw(popping, window, run, banner(level, level - 1, ARRIVAL + POP.ticks))
    lit = window.get_at(bar)
    bars = []
    edges = []
    for age in range(ARRIVAL, ARRIVAL + POP.ticks):
        draw(popping, window, run, banner(level, level - 1, age))
        bars.append(distance(window.get_at(bar), (lit[0], lit[1], lit[2])))
        edges.append(distance(window.get_at(edge), BOX_FLASH))
    assert bars == sorted(bars, reverse=True)
    assert bars[0] > bars[-1] == 0
    assert edges == sorted(edges)
    assert edges[0] == 0 < edges[-1]


# ----- the HUD without a banner -----


RUNS = [
    FakeRun(level=1),
    FakeRun(level=3, score=48_210, grazes=12),
    FakeRun(level=4, lives=3, score=900),
    FakeRun(level=7, lives=1, score=9_999_999, grazes=100),
    FakeRun(level=LEVEL_COUNT, lives=2, score=0, grazes=0),
]


def test_the_hud_with_no_banner_or_no_look_draws_what_it_always_drew(
    rules: HudRules, art: HudArt, window: pygame.Surface
) -> None:
    old = HudView(rules, art)
    looked = HudView(rules, art, LOOK)
    old_with_banner = HudView(rules, art)
    for tick, run in enumerate(RUNS * 2):
        expected = draw(old, window, run, None, tick * 7)
        assert draw(looked, window, run, None, tick * 7) == expected, (tick, run)
        for age in (0, ARRIVAL - 1, ARRIVAL, ARRIVAL + 5, ARRIVAL + POP.ticks):
            given = banner(run.level, max(1, run.level - 1), age)
            assert draw(old_with_banner, window, run, given, tick * 7) == expected, (tick, age)


# ----- the slot -----


@pytest.mark.parametrize("with_look", [False, True])
def test_the_level_slot_center_lies_inside_the_level_box_for_every_level(
    plain: HudView,
    popping: HudView,
    window: pygame.Surface,
    rules: HudRules,
    with_look: bool,
) -> None:
    view = popping if with_look else plain
    left, top, width, height = rules.level.box
    box = pygame.Rect(*panel_point(rules, left, top), width, height)
    for level in range(1, LEVEL_COUNT + 1):
        slot = view.level_slot(level)
        assert box.collidepoint(slot.center), level
        assert slot.size[0] > 0
        assert slot.size[1] > 0
        image = pygame.Rect((0, 0), slot.size)
        image.center = slot.center
        assert box.contains(image), level
        draw(view, window, FakeRun(level=level))
        ink = ink_rect(window, rules, slot.color)
        assert ink is not None, level
        assert image.contains(ink), level


# ----- cost -----


def test_no_hud_draw_during_the_pop_builds_a_surface_or_renders_text(
    rules: HudRules,
    art: HudArt,
    window: pygame.Surface,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    view = HudView(rules, art, LOOK)
    run = FakeRun(level=5)
    draw(view, window, run)
    built: list[str] = []
    original_surface = pygame.Surface

    def counting_surface(size: tuple[int, int], flags: int = 0) -> pygame.Surface:
        built.append("Surface")
        return original_surface(size, flags)

    class CountingFont:
        """Stands in for a font after the HUD is built: any render is a bug."""

        def __init__(self, font: pygame.font.Font) -> None:
            self._font = font

        def render(self, text: str, antialias: bool, color: RGB) -> pygame.Surface:
            built.append("render")
            return self._font.render(text, antialias, color)

        def __getattr__(self, name: str) -> object:
            return getattr(self._font, name)

    for key, font in list(art.fonts.items()):
        monkeypatch.setitem(art.fonts, key, CountingFont(font))
    monkeypatch.setattr(pygame, "Surface", counting_surface)
    for name in ("smoothscale", "scale", "rotate", "rotozoom", "scale_by", "flip"):
        original = getattr(pygame.transform, name)

        def counted(
            *args: object,
            _name: str = name,
            _original: Callable[..., pygame.Surface] = original,
            **kwargs: object,
        ) -> pygame.Surface:
            built.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(pygame.transform, name, counted)

    for age in range(ARRIVAL + POP.ticks + 3):
        draw(view, window, run, banner(5, 4, age), age)
    assert built == []
    pygame.Surface((1, 1))
    art.fonts["level"].render("1", True, FLASH)
    pygame.transform.scale(original_surface((2, 2)), (4, 4))
    assert built == ["Surface", "render", "scale"]
