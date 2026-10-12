"""Ship view: draws the ship as its placeholder rectangle from core state.

Source: docs/contracts/DRA-6/DRA-6-ship.md, Interface and Presentation; 04-ship.md,
placeholder_look. The view only draws. It never fills the background, never flips the
display, never logs per frame, never catches an error and never changes the ship.
"""

import logging

import pygame

from core.ship import SHIP_H, SHIP_W, Ship

log = logging.getLogger(__name__)

SHIP_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Ship fill, RGB. Source: 04-ship.md, placeholder_look (guess)."""


def draw_ship(surface: pygame.Surface, ship: Ship) -> None:
    """Draw a filled SHIP_W x SHIP_H rectangle in SHIP_COLOR centered on the ship.

    The top-left corner is (round(ship.x - SHIP_W / 2), round(ship.y - SHIP_H / 2)), so the
    rectangle stays exactly SHIP_W x SHIP_H. Parts outside the surface are clipped.
    Units: pixels. Source: DRA-6-ship.md, Presentation.
    """
    left: int = round(ship.x - SHIP_W / 2)
    top: int = round(ship.y - SHIP_H / 2)
    pygame.draw.rect(surface, SHIP_COLOR, pygame.Rect(left, top, SHIP_W, SHIP_H))
