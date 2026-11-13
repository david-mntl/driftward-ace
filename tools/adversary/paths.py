"""Where the harness reads and writes, and the one place that puts game/ on sys.path.

Every module that imports the game (core, app, ui) starts with `import paths`, so import order in a script does
not matter. Paths only: this module imports nothing from the game.
"""

import sys
from pathlib import Path

ADVERSARY_DIR = Path(__file__).resolve().parent
"""This folder: `tools/adversary/`."""

GAME_DIR = ADVERSARY_DIR.parents[1] / "game"
"""The game's source folder. The harness reads it and never edits it."""

OUT_DIR = ADVERSARY_DIR / "out"
"""Where every engine writes its results. Rebuilt by re-running the scripts."""

if str(GAME_DIR) not in sys.path:
    sys.path.insert(0, str(GAME_DIR))  # importing this module is what makes `import core` work


def out_dir(*parts: str) -> Path:
    """Return `out/<parts>`, creating the folder first, so a fresh checkout needs no setup."""
    path = OUT_DIR.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return path
