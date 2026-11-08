"""Window tests: the full-window background and the screens drawn through the app's draw function.

Source: docs/contracts/systems/hud.md, Interface (WindowBackdrop);
docs/contracts/systems/app/frame-loop.md, Rules, Draw; 10-ui.md, `window_screens`.
"""

import dataclasses

import pygame
import pytest

import app.frame as frame
from app.assets import load_background, load_hud_art, load_screen_fonts
from app.background_tuning import load_background_rules
from app.hud_tuning import load_hud_rules
from app.screens_tuning import load_screen_rules
from app.ship_tuning import load_ship_look
from app.tuning import load_graze_rules, load_last_life_rules
from core.game_flow import GameFlow, Screen, start_flow
from core.run import start_run
from core.world import SCREEN_H, SCREEN_W
from ui.background_view import BackgroundArt
from ui.debug_overlay import draw_debug_overlay
from ui.hud import HudView
from ui.hud_rules import HudRules
from ui.screen_look import ScreenLook
from ui.ship_view import ShipLook
from ui.window_view import WindowBackdrop

SENTINEL: tuple[int, int, int] = (255, 0, 255)


class Parts:
    """The window, the play-area subsurface and everything frame._draw needs."""

    def __init__(self) -> None:
        self.rules: HudRules = load_hud_rules()
        self.window: pygame.Surface = pygame.display.set_mode(
            (self.rules.window.width, self.rules.window.height)
        )
        self.field: pygame.Surface = self.window.subsurface(
            pygame.Rect(self.rules.window.field_x, self.rules.window.field_y, SCREEN_W, SCREEN_H)
        )
        self.hud: HudView = HudView(self.rules, load_hud_art(self.rules))
        screen_rules = load_screen_rules()
        self.screens: ScreenLook = ScreenLook(screen_rules, load_screen_fonts(screen_rules))
        self.backdrop: WindowBackdrop = WindowBackdrop(self.window.get_size())
        self.background: BackgroundArt = load_background(load_background_rules())
        self.look: ShipLook = load_ship_look()
        run = start_run(
            waves=None, graze_rules=load_graze_rules(), last_life_rules=load_last_life_rules()
        )
        self.flow: GameFlow = start_flow(run, None)

    def draw(self, screen: Screen, overlay: bool = False) -> None:
        """Fill the window with the sentinel, then draw `screen` the way the app does."""
        self.window.fill(SENTINEL)
        flow = dataclasses.replace(self.flow, screen=screen)
        frame._draw(
            self.window,
            self.field,
            self.backdrop,
            self.hud,
            self.screens,
            self.background,
            120.0,
            self.look,
            flow,
            overlay,
        )

    def sentinel_left(self) -> int:
        """Pixels still the sentinel, sampled on a grid across the whole window."""
        found = 0
        for x in range(0, self.window.get_width(), 5):
            for y in range(0, self.window.get_height(), 5):
                if self.window.get_at((x, y))[:3] == SENTINEL:
                    found += 1
        return found


@pytest.fixture(scope="module")
def parts(pygame_headless: None) -> Parts:
    return Parts()


@pytest.mark.parametrize(
    "screen", [Screen.MENU, Screen.INSTRUCTIONS, Screen.LEADERBOARD, Screen.CREDITS]
)
def test_the_menu_pages_fill_the_whole_window(parts: Parts, screen: Screen) -> None:
    parts.draw(screen)
    assert parts.sentinel_left() == 0


@pytest.mark.parametrize("screen", [Screen.PLAYING, Screen.PAUSED, Screen.GAME_OVER])
def test_the_run_screens_fill_the_whole_window(parts: Parts, screen: Screen) -> None:
    parts.draw(screen)
    assert parts.sentinel_left() == 0


def _mean(parts: Parts, area: pygame.Rect) -> float:
    total = 0
    count = 0
    for x in range(area.left, area.right, 4):
        for y in range(area.top, area.bottom, 4):
            total += sum(parts.window.get_at((x, y))[:3])
            count += 3
    return total / count


def test_pause_and_game_over_dim_the_panel_too(parts: Parts) -> None:
    rules = parts.rules
    panel = pygame.Rect(rules.panel.x + 30, 300, 150, 100)
    parts.draw(Screen.PLAYING)
    playing = _mean(parts, panel)
    for screen in (Screen.PAUSED, Screen.GAME_OVER):
        parts.draw(screen)
        assert _mean(parts, panel) < playing * 0.7


def test_the_menu_pages_show_no_panel_and_no_frame(parts: Parts) -> None:
    rules = parts.rules
    parts.draw(Screen.MENU)
    cell = (rules.panel.x + 5, 300)
    parts.draw(Screen.PLAYING)
    with_panel = parts.window.get_at(cell)
    parts.draw(Screen.MENU)
    assert parts.window.get_at(cell) != with_panel


def test_the_debug_overlay_stays_inside_the_play_area(parts: Parts) -> None:
    parts.window.fill(SENTINEL)
    draw_debug_overlay(parts.field, parts.flow.run.ship)
    rules = parts.rules
    field = pygame.Rect(rules.window.field_x, rules.window.field_y, SCREEN_W, SCREEN_H)
    for x in range(0, rules.window.width, 3):
        for y in range(0, rules.window.height, 3):
            if not field.collidepoint(x, y):
                assert parts.window.get_at((x, y))[:3] == SENTINEL, (x, y)


def test_the_overlay_and_the_panel_never_share_a_pixel(parts: Parts) -> None:
    rules = parts.rules
    parts.draw(Screen.PLAYING, overlay=False)
    without = pygame.image.tobytes(parts.window, "RGB")
    parts.draw(Screen.PLAYING, overlay=True)
    with_overlay = pygame.image.tobytes(parts.window, "RGB")
    width = rules.window.width
    for y in range(0, rules.window.height, 3):
        start = (y * width + rules.panel.x) * 3
        end = (y * width + width) * 3
        assert without[start:end] == with_overlay[start:end], y


def test_the_backdrop_covers_a_window_larger_than_the_play_area(parts: Parts) -> None:
    surface = pygame.Surface(parts.window.get_size())
    surface.fill(SENTINEL)
    parts.backdrop.draw(surface, parts.background, 0.0)
    for x in range(0, surface.get_width(), 9):
        for y in range(0, surface.get_height(), 9):
            assert surface.get_at((x, y))[:3] != SENTINEL
