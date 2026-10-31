"""The full-window background for the screens that fill the whole window.

Source: docs/contracts/systems/hud.md, Interface (`WindowBackdrop`); 10-ui.md, `window_screens`. The
view only draws. The painted background is made for the play area (SCREEN_W x SCREEN_H), so the
menu, the instructions page and the leaderboard page get it drawn at that size, then scaled up to
cover the window and cut to it, keeping the bottom left where the black hole is.
"""

import logging
import math

import pygame

from core.world import SCREEN_H, SCREEN_W
from ui.background_view import BackgroundArt, draw_background

log = logging.getLogger(__name__)


class WindowBackdrop:
    """Draws the background across a window larger than the play area. Needs a display set."""

    def __init__(self, window_size: tuple[int, int]) -> None:
        width, height = window_size
        scale: float = max(width / SCREEN_W, height / SCREEN_H)
        self._scaled_size: tuple[int, int] = (
            math.ceil(SCREEN_W * scale),
            math.ceil(SCREEN_H * scale),
        )
        self._field: pygame.Surface = pygame.Surface((SCREEN_W, SCREEN_H))
        self._scaled: pygame.Surface = pygame.Surface(self._scaled_size)
        self._crop: pygame.Rect = pygame.Rect(0, self._scaled_size[1] - height, width, height)

    def draw(self, window: pygame.Surface, art: BackgroundArt, ticks: float) -> None:
        """Draw the background at ``ticks`` over the whole ``window``: play-area size, scaled to

        cover, cut to fit.
        """
        draw_background(self._field, art, ticks)
        pygame.transform.scale(self._field, self._scaled_size, self._scaled)
        window.blit(self._scaled, (0, 0), self._crop)
