"""The sounds the game asks for. A cue names an event, never a file.

`Run.sound_cues` lists them for each stepped tick; the app plays them. Stdlib only.

Source: docs/contracts/systems/audio.md, Interface (game/core/sound_cue.py).
"""

from enum import Enum


class SoundCue(Enum):
    """A sound the game wants to play."""

    HIT = "hit"
    """A life was lost, by a drifter or a fall, the last life included."""

    GRAZE = "graze"
    """A graze paid."""

    COIN = "coin"
    """A pickup was collected."""

    GAME_OVER = "game_over"
    """The last life was lost: the ship bursts and the run is ending."""

    LEVEL_UP = "level_up"
    """The level rose and its banner started."""
