"""Background asset tests: the planets and the wrecks load and take turns in the middle layer.

Source: 12-art-and-audio.md, Background, middle layer. These read the shipped pictures.
"""

import dataclasses
from collections.abc import Iterator

import pygame
import pytest

from app.assets import ASSETS_DIR, ITEM_FILES, PLANET_FILES, load_background
from app.background_tuning import load_background_rules
from ui.background_view import BackgroundArt


@pytest.fixture(scope="module")
def display() -> Iterator[None]:
    """A small display, so the pictures can be converted. pygame is shut down after."""
    pygame.init()
    pygame.display.set_mode((16, 16))
    yield
    pygame.quit()


def _art() -> BackgroundArt:
    """The shipped background at planet_scale 1, so sprite sizes are the files' own."""
    rules = dataclasses.replace(load_background_rules(), planet_scale=1.0)
    return load_background(rules)


def _size(file: str) -> tuple[int, int]:
    return pygame.image.load(ASSETS_DIR / file).get_size()


@pytest.mark.usefixtures("display")
def test_every_planet_and_every_wreck_is_in_the_middle_layer() -> None:
    art = _art()
    assert len(art.planets) == len(PLANET_FILES) + len(ITEM_FILES)


@pytest.mark.usefixtures("display")
def test_planets_and_wrecks_take_turns() -> None:
    art = _art()
    planets = [_size(file) for file in PLANET_FILES]
    wrecks = [_size(file) for file in ITEM_FILES]
    scaled = [sprite.get_size() for sprite in art.planets]
    assert scaled[0::2] == planets
    assert scaled[1::2] == wrecks
