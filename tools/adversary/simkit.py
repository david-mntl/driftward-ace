"""Shared kit for the adversarial test harness: build real runs and flows headless.

Loads the shipped tuning, wave book, graze, last-life and level-up rules exactly as
game/app/frame.py does, with no window and no sound. Nothing here ships; game/ is never edited.
"""

import os
from dataclasses import dataclass, replace

import paths  # noqa: F401  (puts game/ on sys.path)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from app.hud_tuning import load_hud_rules
from app.level_up_tuning import load_level_up
from app.tuning import load_graze_rules, load_last_life_rules, load_tuning
from app.waves import load_wave_book
from core.drifters.base import DrifterType
from core.drifters.tuning import DrifterTuning
from core.game_flow import GameFlow, start_flow
from core.run import LIVES_START, Run, start_run
from core.waves import WaveBook, start_waves


@dataclass(frozen=True)
class Kit:
    """Everything a run needs, loaded once."""

    tuning: DrifterTuning
    book: WaveBook
    graze_rules: object
    last_life_rules: object
    level_up_rules: object

    def new_run(self, seed: int) -> Run:
        """A fresh run at Wave 0, Level 1, with the waves seeded by `seed`."""
        return start_run(
            waves=start_waves(self.book, seed, self.level_up_rules),
            graze_rules=self.graze_rules,
            last_life_rules=self.last_life_rules,
        )

    def new_flow(self, seed: int) -> GameFlow:
        """A fresh flow on the start screen, no saves."""
        return start_flow(self.new_run(seed), None)


def drifter_type(name: str) -> DrifterType:
    """The drifter type called `name`, as the wave files spell it ("floating_island", "coin").

    A script that has to spawn one particular drifter asks by name. The game's rule is that only a
    drifter's own modules write `DrifterType.<MEMBER>` (test_drifter_registration enforces it), and
    the harness is not one of them. To find a drifter by what it does, ask the instance instead:
    `d.effect_on_touch()` says hit, collect or block.
    """
    return DrifterType(name)


def refill_lives(run: Run) -> Run:
    """Immortal mode: top the lives up to the full count while the run is still alive.

    A run at 0 lives is in its last-life burst, which the harness lets play out.
    """
    return replace(run, lives=LIVES_START) if 0 < run.lives < LIVES_START else run


_KIT: Kit | None = None


def load_kit() -> Kit:
    """Load the kit once per process."""
    global _KIT
    if _KIT is None:
        pygame.init()
        tuning = load_tuning()
        level_up_rules, _look = load_level_up(load_hud_rules())
        _KIT = Kit(
            tuning=tuning,
            book=load_wave_book(tuning),
            graze_rules=load_graze_rules(),
            last_life_rules=load_last_life_rules(),
            level_up_rules=level_up_rules,
        )
    return _KIT
