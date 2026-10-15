"""Ship view: draws the ship as its own hitbox, the inverted T, from core state.

The look is the hitbox: the bar and the foot, filled. Source: docs/contracts/systems/ship.md,
Interface and Presentation; 04-ship.md, placeholder_look and hitbox. The view only draws. It
never fills the background, never flips the display, never logs per frame, never catches an
error and never changes the ship.
"""

import logging

import pygame

from core.ship import Ship, ship_hitbox
from ui.shapes import draw_hitbox

log = logging.getLogger(__name__)

SHIP_COLOR: tuple[int, int, int] = (255, 255, 255)
"""Ship fill, RGB. Source: 04-ship.md, placeholder_look (guess)."""


def draw_ship(surface: pygame.Surface, ship: Ship) -> None:
    """Draw the ship's hitbox, the bar and the foot, filled in SHIP_COLOR.

    Boxes are centered on the ship and drawn through `ui.shapes`. Parts outside the surface
    are clipped. Units: pixels. Source: systems/ship.md, Presentation.
    """
    draw_hitbox(surface, SHIP_COLOR, ship_hitbox(ship))
