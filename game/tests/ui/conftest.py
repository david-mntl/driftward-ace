"""Fixtures for the screens' tests: the real screens values and the look built from them."""

from collections.abc import Iterator

import pygame
import pytest

from app.assets import load_screen_fonts
from app.screens_tuning import load_screen_rules
from ui.screen_look import ScreenLook
from ui.screen_rules import ScreenRules


@pytest.fixture(scope="session")
def screen_rules() -> ScreenRules:
    """The values of tuning/screens.json, as the game loads them."""
    return load_screen_rules()


@pytest.fixture(scope="session")
def look(screen_rules: ScreenRules) -> Iterator[ScreenLook]:
    """The shared look, with the real font at every role's size. pygame is initialized for it."""
    pygame.init()
    yield ScreenLook(screen_rules, load_screen_fonts(screen_rules))
    pygame.quit()
