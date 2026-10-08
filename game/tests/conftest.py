"""Shared fixtures. Every test runs headless: no window, no sound device."""

import os
import random
from collections.abc import Iterator

import pytest

# Set before any test module imports pygame. conftest.py always loads first.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

SEED = 1234


@pytest.fixture
def rng() -> random.Random:
    """A fresh random.Random with a fixed seed. Pass it to code that needs randomness."""
    return random.Random(SEED)


@pytest.fixture(scope="session")
def pygame_headless() -> Iterator[None]:
    """Initialise pygame once for the session, for tests that need fonts or surfaces."""
    import pygame

    pygame.init()
    yield
    pygame.quit()
