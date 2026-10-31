"""Loads the painted art the game shows. Reads files, so it lives in app/, not ui/."""

import logging
from pathlib import Path

import pygame

from core.world import SCREEN_H, SCREEN_W
from ui.background_view import BackgroundArt, BackgroundRules, build_background

log = logging.getLogger(__name__)

ASSETS_DIR: Path = Path(__file__).resolve().parent.parent / "assets"
"""The assets folder, next to main.py. Found the same way as the tuning folder."""

SWAY_FRAMES: int = 12
"""Frames in the far painting's sway loop. Must match KEYFRAMES in tools/art/background_sway.py."""

SWAY_FILES: tuple[str, ...] = tuple(
    f"background_sway_{index:02d}.png" for index in range(SWAY_FRAMES)
)
"""The far-layer painting as a loop of frames, each SCREEN_W x SCREEN_H px. Baked from
background.png by tools/art/background_sway.py. Source: 12-art-and-audio.md, Background, far
layer."""

PLANET_FILES: tuple[str, ...] = tuple(f"bg_planet_{index}.png" for index in range(6))
"""The broken planets of the middle layer, each cut to its own bounds. Source:
12-art-and-audio.md, Background, middle layer."""


def load_background(rules: BackgroundRules) -> BackgroundArt:
    """Load the painting's sway frames and the planets, and build the background from them.

    Call it once, after the display is open. A missing file raises FileNotFoundError (from
    pygame). A frame that is not SCREEN_W x SCREEN_H raises ValueError naming the file.
    """
    sway: tuple[pygame.Surface, ...] = tuple(_load_frame(name) for name in SWAY_FILES)
    planets: tuple[pygame.Surface, ...] = tuple(_load(name, alpha=True) for name in PLANET_FILES)
    log.info("background loaded %d painting frames and %d planets", len(sway), len(planets))
    return build_background(sway, planets, rules)


def _load_frame(file: str) -> pygame.Surface:
    """Read one far-painting frame and check it is screen size."""
    frame: pygame.Surface = _load(file, alpha=False)
    if frame.get_size() != (SCREEN_W, SCREEN_H):
        raise ValueError(
            f"assets/{file}: size is {frame.get_size()}, "
            f"expected {(SCREEN_W, SCREEN_H)} (screen size)"
        )
    return frame


def _load(file: str, alpha: bool) -> pygame.Surface:
    """Read one image and convert it to the display format, keeping its alpha if `alpha`."""
    image: pygame.Surface = pygame.image.load(ASSETS_DIR / file)
    return image.convert_alpha() if alpha else image.convert()
