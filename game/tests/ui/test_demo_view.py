"""Demo flight view tests: lit keys, the caption, the skip hint and the fades.

Spec: docs/contracts/systems/demo.md, Rules, Draw; 10-ui.md, demo_look. The look values are the
shipped tuning/demo.json; colors are the screens' palette (the `look` fixture). Drawn on a black
surface the size of the play area, so any lit pixel is ink.
"""

from dataclasses import replace

import pygame
import pytest

from app.demo_tuning import load_demo
from app.drifter_looks_tuning import install_drifter_looks
from app.screens_tuning import load_screen_rules
from app.tuning import load_tuning
from core.demo import Demo, DemoRules, DemoStep, start_demo, step_demo
from core.drifters.base import DrifterType
from core.ship import Thrust
from core.world import SCREEN_H, SCREEN_W
from ui.demo_view import draw_demo, draw_fade_in, key_light, starting
from ui.screen_look import ScreenLook
from ui.ship_view import DEFAULT_SHIP_LOOK

TUNING = load_tuning()
_shipped_rules, LOOK = load_demo(TUNING, load_screen_rules())
assert _shipped_rules is not None
SHIPPED: DemoRules = _shipped_rules

TOTAL: int = 80

RULES: DemoRules = DemoRules(
    steps=(
        DemoStep(keys=Thrust(), ticks=10, caption=None, stand=True),
        DemoStep(keys=Thrust(up=True), ticks=10, caption="HOLD UP"),
        DemoStep(keys=Thrust(), ticks=60, caption=None, pilot_to=(320.0, 240.0)),
    ),
    coin_step=1,
    coin_type=DrifterType.COIN,
    coin_variant="common",
    fade_out_ticks=4,
    pilot=SHIPPED.pilot,
    key_fade_ticks=SHIPPED.key_fade_ticks,
)


@pytest.fixture(autouse=True, scope="module")
def _real_sprites(look: ScreenLook) -> None:
    """Install the game's drifter sprites, as the app does before the first frame."""
    pygame.display.set_mode((1, 1))
    install_drifter_looks(TUNING)


def _demo_at(tick: int) -> Demo:
    demo = start_demo(RULES, TUNING)
    for _ in range(tick):
        demo = step_demo(demo)
    return demo


def _draw(look: ScreenLook, demo: Demo) -> pygame.Surface:
    surface = pygame.Surface((SCREEN_W, SCREEN_H))
    draw_demo(surface, demo, LOOK, look, DEFAULT_SHIP_LOOK, 0)
    return surface


def _up_cap() -> pygame.Rect:
    """Where the UP key cap sits at rest, from the look values: the top of the inverted T."""
    size, gap = LOOK.key_size, LOOK.key_gap
    top = SCREEN_H - LOOK.key_bottom - 2 * size - gap
    return pygame.Rect(SCREEN_W // 2 - size // 2, top, size, size)


def _brightness(surface: pygame.Surface, area: pygame.Rect) -> int:
    """Summed channels of every pixel in ``area``."""
    total: int = 0
    for x in range(area.left, area.right):
        for y in range(area.top, area.bottom):
            total += sum(surface.get_at((x, y))[:3])
    return total


def _ink(surface: pygame.Surface, area: pygame.Rect) -> int:
    count: int = 0
    for x in range(area.left, area.right):
        for y in range(area.top, area.bottom):
            count += surface.get_at((x, y))[:3] != (0, 0, 0)
    return count


def test_a_held_key_lights_up_and_a_free_one_stays_dark(look: ScreenLook) -> None:
    cap = _up_cap().inflate(4, 4 + 2 * LOOK.press_depth)
    idle = _brightness(_draw(look, _demo_at(5)), cap)
    lit = _brightness(_draw(look, _demo_at(18)), cap)
    assert lit > 3 * idle


def test_a_key_lights_while_held_and_goes_dark_after() -> None:
    fade: int = SHIPPED.key_fade_ticks
    assert key_light(_demo_at(10), "UP") == 0.0
    assert 0.0 < key_light(_demo_at(11), "UP") < 1.0
    assert key_light(_demo_at(10 + fade), "UP") == 1.0
    assert key_light(_demo_at(20), "UP") == 1.0
    assert key_light(_demo_at(5), "RIGHT") == 0.0


def test_the_start_word_takes_the_captions_place_in_the_last_start_ticks(look: ScreenLook) -> None:
    assert LOOK.start_ticks > 0
    assert not starting(_demo_at(TOTAL - LOOK.start_ticks - 1), LOOK)
    shown = _demo_at(TOTAL - LOOK.start_ticks + LOOK.start_pop_ticks + 1)
    assert starting(shown, LOOK)
    band = pygame.Rect(0, LOOK.start_y - 25, SCREEN_W // 2 - 40, 50)
    caption_band = pygame.Rect(0, _up_cap().top - LOOK.caption_gap - 40, SCREEN_W // 2 - 40, 40)
    before = _draw(look, _demo_at(TOTAL - LOOK.start_ticks - 1))
    after = _draw(look, shown)
    assert _ink(before, band) == 0
    assert _ink(after, band) > 0
    assert _ink(before, caption_band) > 0
    assert _ink(after, caption_band) == 0


def test_the_caption_shows_above_the_keys_once_set(look: ScreenLook) -> None:
    band = pygame.Rect(0, _up_cap().top - LOOK.caption_gap - 40, SCREEN_W, 40)
    before = _draw(look, _demo_at(5))
    after = _draw(look, _demo_at(10 + LOOK.caption_fade_ticks + 1))
    ship_free = band.clip(pygame.Rect(0, band.top, SCREEN_W // 2 - 40, band.height))
    assert _ink(before, ship_free) == 0
    assert _ink(after, ship_free) > 0


def test_the_skip_hint_sits_in_the_top_right_corner(look: ScreenLook) -> None:
    surface = _draw(look, _demo_at(0))
    corner = pygame.Rect(SCREEN_W // 2, 0, SCREEN_W // 2, LOOK.skip_margin + 30)
    assert _ink(surface, corner) > 0


def test_the_play_area_is_black_when_the_demo_ends(look: ScreenLook) -> None:
    surface = _draw(look, _demo_at(TOTAL))
    assert _ink(surface, surface.get_rect()) == 0


def test_the_run_after_the_demo_fades_in_from_black() -> None:
    fading = replace(LOOK, fade_in_ticks=18)
    surface = pygame.Surface((SCREEN_W, SCREEN_H))
    surface.fill((200, 200, 200))
    draw_fade_in(surface, 0, fading)
    assert surface.get_at((10, 10))[:3] == (0, 0, 0)
    surface.fill((200, 200, 200))
    draw_fade_in(surface, fading.fade_in_ticks // 2, fading)
    assert 0 < surface.get_at((10, 10))[0] < 200
    surface.fill((200, 200, 200))
    draw_fade_in(surface, fading.fade_in_ticks, fading)
    assert surface.get_at((10, 10))[:3] == (200, 200, 200)


def test_no_fade_in_when_its_ticks_are_zero() -> None:
    surface = pygame.Surface((SCREEN_W, SCREEN_H))
    surface.fill((200, 200, 200))
    draw_fade_in(surface, 0, replace(LOOK, fade_in_ticks=0))
    assert surface.get_at((10, 10))[:3] == (200, 200, 200)
