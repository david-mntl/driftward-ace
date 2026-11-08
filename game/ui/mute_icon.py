"""Muted-music icon: one still picture in the bottom-right corner of the window.

`MuteIconView.draw` blits the picture while the music is muted and draws nothing otherwise.
The picture is baked at its on-screen size, so it is blitted, never scaled. The view holds no
state between frames, reads nothing from core and never imports `app`.

Source: docs/contracts/systems/mute-icon.md, Interface, Presentation, Rules 2, 5, 6, 8, 9, 18
and 19; 10-ui.md, mute_icon_place and mute_icon_look.
"""

import logging
from dataclasses import dataclass

import pygame

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class MuteIconLook:
    """Where the icon sits and how large it is, from tuning/mute_icon.json."""

    margin: int
    """Distance from the window's right and bottom edges, px, >= 0."""

    size: int
    """Width and height of the picture on screen, px, >= 1."""


class MuteIconView:
    """Draws the mute picture in the window's bottom-right corner while muted."""

    def __init__(self, look: MuteIconLook, image: pygame.Surface) -> None:
        """Keep the look and the picture. The picture is already `look.size` square, with alpha."""
        self._look: MuteIconLook = look
        self._image: pygame.Surface = image

    def draw(self, window: pygame.Surface, muted: bool) -> None:
        """Blit the picture once when `muted`, else draw nothing.

        The picture's bottom-right corner sits `look.margin` px from the window's right and
        bottom edges, worked out from the window's size on every call.
        """
        if not muted:
            return
        window_w, window_h = window.get_size()
        offset: int = self._look.margin + self._look.size
        window.blit(self._image, (window_w - offset, window_h - offset))
