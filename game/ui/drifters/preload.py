"""Warm-up for the drifter views: build every image the game will draw before the first frame.

Each view module has a `warm(sprites, tuning)` that asks the sprite store for the images its
drifter needs, for every variant in the tuning. Called once, after the display opens, so no spawn
has to build an image in the middle of a run. Source: 15-tech-constraints.md, rule 5.
"""

import logging

from core.drifters.tuning import DrifterTuning
from ui.drifters import (
    chain_lightning_view,
    coin_view,
    electric_ball_view,
    fireball_view,
    floating_island_view,
    meteorite_view,
    planet_view,
    ufo_view,
)
from ui.drifters.sprites import Sprites

log = logging.getLogger(__name__)


def warm_sprites(sprites: Sprites, tuning: DrifterTuning) -> None:
    """Build the images of every drifter that has a sprite look, for every variant in `tuning`."""
    ufo_view.warm(sprites, tuning)
    meteorite_view.warm(sprites, tuning)
    planet_view.warm(sprites, tuning)
    fireball_view.warm(sprites, tuning)
    coin_view.warm(sprites, tuning)
    electric_ball_view.warm(sprites, tuning)
    chain_lightning_view.warm(sprites, tuning)
    floating_island_view.warm(sprites, tuning)
