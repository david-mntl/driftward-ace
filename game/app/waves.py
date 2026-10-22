"""The wave files: read once at startup, in both modes, and turned into the wave book.

Finds, reads and decodes `waves/<wave id>.json` and `waves/playlist.json`. Every check of their
contents is core's (core.wave_files.build_wave_book), so a bad file stops the game with an error
that names the file and the problem, before the first frame.
Not a startup module: it imports core, so only app.frame imports it, inside the guard.

Source: docs/contracts/systems/app.md, Interface and Rules, Wave files;
docs/contracts/systems/waves.md, Rules, The wave files.
"""

import json
import logging
from pathlib import Path

from core.drifters.tuning import DrifterTuning
from core.wave_files import WAVES_FOLDER, build_wave_book
from core.waves import WaveBook, WaveKind

log = logging.getLogger(__name__)

WAVES_DIR: Path = Path(__file__).resolve().parent.parent / WAVES_FOLDER
"""The game's wave folder, read at call time."""

PLAYLIST_FILE: str = "playlist.json"
"""The playlist file, in WAVES_DIR. Every other .json file there is a wave."""


def load_wave_book(tuning: DrifterTuning) -> WaveBook:
    """Read every wave file and the playlist, check them and return the wave book.

    A wave's id is its file name without .json. Files are read in name order, the playlist last.
    Invalid JSON raises ValueError naming the file; a missing folder or playlist raises
    FileNotFoundError as it is. Every other problem is core's ValueError.
    """
    documents: dict[str, object] = {
        path.stem: _read_json(path)
        for path in sorted(WAVES_DIR.glob("*.json"))
        if path.name != PLAYLIST_FILE
    }
    playlist: object = _read_json(WAVES_DIR / PLAYLIST_FILE)
    book: WaveBook = build_wave_book(documents, playlist, tuning)
    pool: int = sum(1 for wave in book.waves.values() if wave.kind is WaveKind.POOL)
    log.info("waves loaded waves=%d pool=%d", len(book.waves), pool)
    return book


def _read_json(path: Path) -> object:
    """Return the file's decoded JSON. Invalid JSON raises ValueError naming the file."""
    text: str = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{WAVES_FOLDER}/{path.name}: not valid JSON: {err}") from err
