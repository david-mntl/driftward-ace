"""Load and check the audio levels file.

Reads `tuning/audio.json` once, at startup (`load_audio_levels`), in both run modes. Checks every
rule of audio.schema.json by hand (pygbag has no schema library) and builds `AudioLevels`. Every
field is required and no default lives in code. A missing file raises FileNotFoundError; a bad one
raises ValueError naming the file and the field. Imports no pygame, but only app.frame imports it,
inside the guard.

Source: docs/contracts/schemas/audio.schema.json; docs/contracts/systems/audio.md, Interface and
Rules 13 and 14.
"""

import json
import logging
from dataclasses import dataclass

from app.drifters.checks import check_fields, check_integer, is_number
from app.tuning import TUNING_DIR

log = logging.getLogger(__name__)

AUDIO_FILE: str = "audio.json"
"""The audio levels file, in TUNING_DIR."""

_FILE_NAME: str = f"tuning/{AUDIO_FILE}"

_PERCENT_FIELDS: tuple[str, ...] = (
    "music_master",
    "effects_master",
    "loop_level",
    "hit_level",
    "graze_level",
    "coin_level",
    "game_over_level",
    "level_up_level",
)
"""The fields that are a percent, 0 to 100, an int or a float."""

_FIELDS: frozenset[str] = frozenset((*_PERCENT_FIELDS, "effect_channels"))


@dataclass(frozen=True, slots=True)
class AudioLevels:
    """The loudness of every sound and the effect channel count."""

    music_master: float
    """The music's master level, percent, 0..100."""
    effects_master: float
    """The effects' master level, percent, 0..100."""
    loop_level: float
    """The loop's own level, percent, 0..100."""
    hit_level: float
    """The hit's own level, percent, 0..100."""
    graze_level: float
    """The graze's own level, percent, 0..100."""
    coin_level: float
    """The coin's own level, percent, 0..100."""
    game_over_level: float
    """The game-over sound's own level, percent, 0..100."""
    level_up_level: float
    """The level-up sound's own level, percent, 0..100."""
    effect_channels: int
    """How many effects can sound at once, >= 1."""


def load_audio_levels() -> AudioLevels:
    """Read and check tuning/audio.json and build its record. Logs one INFO line."""
    text: str = (TUNING_DIR / AUDIO_FILE).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{_FILE_NAME}: not valid JSON: {err}") from err
    fields: dict[str, object] = check_fields(_FILE_NAME, "", data, _FIELDS)
    percents: dict[str, float] = {name: _percent(name, fields[name]) for name in _PERCENT_FIELDS}
    levels: AudioLevels = AudioLevels(
        effect_channels=check_integer(_FILE_NAME, "effect_channels", fields["effect_channels"], 1),
        **percents,
    )
    log.info(
        "audio loaded music_master=%g effects_master=%g loop_level=%g hit_level=%g "
        "graze_level=%g coin_level=%g game_over_level=%g level_up_level=%g effect_channels=%d",
        levels.music_master,
        levels.effects_master,
        levels.loop_level,
        levels.hit_level,
        levels.graze_level,
        levels.coin_level,
        levels.game_over_level,
        levels.level_up_level,
        levels.effect_channels,
    )
    return levels


def _percent(field: str, value: object) -> float:
    """Return value as a float if it is an int or float from 0 to 100 (never a bool)."""
    if not is_number(value) or not 0 <= value <= 100:
        raise ValueError(f"{_FILE_NAME}: {field} must be a number from 0 to 100")
    return float(value)
