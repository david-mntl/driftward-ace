"""The wave_check config: `config.json` next to this file, owned by the Director.

Part 1 reads `levels`, `skip`, `start_spots`, `limits` and `track_ticks_max`. `limits.gap_min_ship_widths`
and `bot` are for the bot (part 2) and are carried but not used yet. A key left out keeps the
default below, which are the GDD's values (09-waves.md, Values).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_FILE: Path = Path(__file__).resolve().parent / "config.json"

DEFAULT_LEVELS: tuple[int, ...] = (8,)
"""check_level, locked at 8. Source: 09-waves.md, Values."""
DEFAULT_SPOTS: dict[str, float] = {"left": 100.0, "center": 320.0, "right": 540.0}


@dataclass(frozen=True)
class Config:
    levels: tuple[int, ...] = DEFAULT_LEVELS
    skip: frozenset[str] = frozenset()
    """Wave ids that are never checked."""
    start_spots: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_SPOTS))
    """Ship x at the start of a wave, by name. The ship's y is the game's spawn y."""
    seam_clear_px: float = 120.0
    coin_near_ship_widths: float = 3.0
    """A coin must come within this many ship widths of a hazard (96 px at 32 px)."""
    gap_min_ship_widths: float = 2.5
    track_ticks_max: int = 2400
    """Longest a single drifter is followed, ticks, before it counts as never leaving."""
    bot: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    """The file as read, for the pass fingerprint."""


def load_config(path: Path = CONFIG_FILE) -> Config:
    """Read the config. Raises ValueError naming the file and the key on a bad value."""
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ValueError(f"{path.name}: not valid JSON: {err}") from err
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: must be a JSON object")  # noqa: TRY004
    levels: Any = data.get("levels", list(DEFAULT_LEVELS))
    if (
        not isinstance(levels, list)
        or not levels
        or not all(isinstance(level, int) and 1 <= level <= 8 for level in levels)
    ):
        raise ValueError(f"{path.name}: levels must be a list of integers from 1 to 8")
    skip: Any = data.get("skip", [])
    if not isinstance(skip, list) or not all(isinstance(item, str) for item in skip):
        raise ValueError(f"{path.name}: skip must be a list of wave ids")
    spots: Any = data.get("start_spots", DEFAULT_SPOTS)
    if (
        not isinstance(spots, dict)
        or not spots
        or not all(isinstance(x, int | float) for x in spots.values())
    ):
        raise ValueError(f"{path.name}: start_spots must map names to x positions")
    limits: Any = data.get("limits", {})
    if not isinstance(limits, dict):
        raise ValueError(f"{path.name}: limits must be an object")  # noqa: TRY004
    ticks: Any = data.get("track_ticks_max", 2400)
    if not isinstance(ticks, int) or ticks < 1:
        raise ValueError(f"{path.name}: track_ticks_max must be an integer >= 1")
    return Config(
        levels=tuple(levels),
        skip=frozenset(skip),
        start_spots={name: float(x) for name, x in spots.items()},
        seam_clear_px=_number(path, limits, "seam_clear_px", 120.0),
        coin_near_ship_widths=_number(path, limits, "coin_near_ship_widths", 3.0),
        gap_min_ship_widths=_number(path, limits, "gap_min_ship_widths", 2.5),
        track_ticks_max=ticks,
        bot=dict(data.get("bot", {})),
        raw=data,
    )


def _number(path: Path, limits: dict[str, Any], key: str, default: float) -> float:
    value: Any = limits.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
        raise ValueError(f"{path.name}: limits.{key} must be a number >= 0")
    return float(value)
