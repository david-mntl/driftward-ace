"""The wave_check config: `config.json` next to this file, owned by the Director.

Part 1 reads `levels`, `skip`, `start_spots`, `limits` and `track_ticks_max`. The bot check
(`--bot`) also reads `bot`. `limits.gap_min_ship_widths` is for the gap check, not built yet. A key
left out keeps the default below, which are the GDD's values (09-waves.md, Values) or, for `bot`,
the tool's own starting values.
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
class BotConfig:
    """How the bot searches. Bigger beam, smaller cells: finds more paths, runs slower."""

    start_spots: tuple[str, ...] = ()
    """Start spots the bot flies from, by name. Empty means every start spot."""
    decision_ticks: int = 4
    """Ticks each arrow-key choice is held before the next."""
    beam_width: int = 60
    """Most ships kept after each choice."""
    cell_px: float = 8.0
    """Ships closer than this, px, count as one position."""
    cell_speed: float = 1.0
    """Ships with speeds closer than this, px/tick, count as one speed."""
    spread_px: float = 64.0
    """Size of the screen squares the kept ships are spread over, px."""
    spread_speed: float = 3.0
    """Sideways speed step the kept ships are spread over, px/tick."""
    safe_px: float = 96.0
    """Room to the nearest hazard past which a ship counts as safe, px."""
    margin_px: float = 6.0
    """Grows every hazard hitbox by this much, px, for the bot only. 0 is the game's hitbox."""


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
    bot: BotConfig = field(default_factory=BotConfig)
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
        bot=_bot(path, data.get("bot", {}), spots),
        raw=data,
    )


def _number(
    path: Path,
    limits: dict[str, Any],
    key: str,
    default: float,
    section: str = "limits",
) -> float:
    value: Any = limits.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
        raise ValueError(f"{path.name}: {section}.{key} must be a number >= 0")
    return float(value)


def _bot(path: Path, data: Any, spots: dict[str, Any]) -> BotConfig:
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: bot must be an object")  # noqa: TRY004
    names: Any = data.get("start_spots", [])
    if not isinstance(names, list) or not all(name in spots for name in names):
        raise ValueError(
            f"{path.name}: bot.start_spots must be a list of start_spots names"
        )
    default = BotConfig()
    for key in ("decision_ticks", "beam_width"):
        value: Any = data.get(key, getattr(default, key))
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{path.name}: bot.{key} must be an integer >= 1")
    for key in ("cell_px", "cell_speed", "spread_px", "spread_speed"):
        value = data.get(key, getattr(default, key))
        if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
            raise ValueError(f"{path.name}: bot.{key} must be a number > 0")
    return BotConfig(
        start_spots=tuple(names),
        decision_ticks=data.get("decision_ticks", default.decision_ticks),
        beam_width=data.get("beam_width", default.beam_width),
        cell_px=float(data.get("cell_px", default.cell_px)),
        cell_speed=float(data.get("cell_speed", default.cell_speed)),
        spread_px=float(data.get("spread_px", default.spread_px)),
        spread_speed=float(data.get("spread_speed", default.spread_speed)),
        safe_px=_number(path, data, "safe_px", default.safe_px, "bot"),
        margin_px=_number(path, data, "margin_px", default.margin_px, "bot"),
    )
