"""Load and check the drifter tuning files, the playtest switches, the shared hazard values and the
graze values.

Reads `tuning/playtest.json`, `tuning/hazards.json` and one
`tuning/drifters/<drifter_type value>.json` per DrifterType, once, at startup (`load_tuning`), and
`tuning/scoring.json` once, at startup (`load_graze_rules`). Checks every rule of
their schemas by hand (pygbag has no schema library) and builds the core records. Core trusts what
this returns. Any bad file raises ValueError naming the file and the field; a missing file raises
FileNotFoundError as it is. Never falls back to a default for a missing file. A hazards field left
out keeps its default from core.drifters.base, and a scoring field left out keeps its default from
core.graze.
A drifter whose file has a schema of its own has a tuning module in `app.drifters`
(`<drifter>_tuning.py`) that registers its loader by type: this module names no drifter. A drifter
with none follows drifter-tuning.schema.json (`app.drifters.checks.load_generic`). The shared
field checks are in `app.drifters.checks`.
Not a startup module: it imports core.drifters, so only app.frame imports it, inside the guard.

Source: docs/contracts/systems/app.md, Interface and Rules, Tuning loader;
docs/contracts/schemas/drifter-tuning.schema.json, playtest-switches.schema.json and
hazards.schema.json, and each drifter's own schema named in its tuning module;
docs/contracts/systems/app/tuning-loader.md (DRA-117) and scoring.schema.json.
"""

import json
import logging
from pathlib import Path

from app.drifters.checks import (
    check_boolean,
    check_fields,
    check_integer,
    check_positive,
    is_number,
    load_generic,
)
from app.drifters.registry import TuningLoader, tuning_loader
from core.drifters.base import (
    DEFAULT_REHIT_COOLDOWN_TICKS,
    DEFAULT_REHIT_DIM,
    DEFAULT_TELEGRAPH_MIN_TICKS,
    GRAZE_MARGIN,
    DrifterType,
)
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
)
from core.graze import (
    DEFAULT_GRAZE_POINTS,
    DEFAULT_GRAZE_POPUP_RISE_PER_TICK,
    DEFAULT_GRAZE_POPUP_TICKS,
    DEFAULT_GRAZE_RING_END_DIAMETER,
    DEFAULT_GRAZE_RING_START_DIAMETER,
    DEFAULT_GRAZE_RING_TICKS,
    DEFAULT_GRAZE_RING_WIDTH,
    GrazeRules,
)

log = logging.getLogger(__name__)

TUNING_DIR: Path = Path(__file__).resolve().parent.parent / "tuning"
"""The game's tuning folder. Read at call time, so a check can point it elsewhere."""

PLAYTEST_FILE: str = "playtest.json"
"""The playtest switches file, in TUNING_DIR."""

HAZARDS_FILE: str = "hazards.json"
"""The shared hazard values file, in TUNING_DIR. Every field optional; the file must exist."""

DRIFTERS_DIR: str = "drifters"
"""The drifter tuning folder, in TUNING_DIR. One `<drifter_type value>.json` per DrifterType."""

SCORING_FILE: str = "scoring.json"
"""The graze values file, in TUNING_DIR. Every field optional; the file must exist. DRA-117."""


_SWITCH_FIELDS: frozenset[str] = frozenset({"hazard_speed_scaling", "timer_scaling"})
_HAZARD_FIELDS: frozenset[str] = frozenset(
    {"rehit_cooldown", "rehit_dim", "telegraph_min", "graze_margin"}
)
_SCORING_FIELDS: frozenset[str] = frozenset(
    {
        "graze_points",
        "graze_popup_ticks",
        "graze_popup_rise_per_tick",
        "graze_ring_ticks",
        "graze_ring_start_diameter",
        "graze_ring_end_diameter",
        "graze_ring_width",
    }
)


def load_tuning() -> DrifterTuning:
    """Read and check the playtest switches, the hazard values and every drifter's file."""
    switches: PlaytestSwitches = _load_switches(Path(PLAYTEST_FILE))
    hazards: HazardRules = _load_hazards(Path(HAZARDS_FILE))
    drifters: dict[DrifterType, DrifterTypeTuning] = {
        drifter_type: _load_drifter(Path(DRIFTERS_DIR) / f"{drifter_type.value}.json", drifter_type)
        for drifter_type in DrifterType
    }
    log.info(
        "tuning loaded drifters=%s hazard_speed_scaling=%s timer_scaling=%s "
        "rehit_cooldown=%d rehit_dim=%.2f telegraph_min=%d graze_margin=%g",
        ",".join(drifter_type.value for drifter_type in drifters),
        switches.hazard_speed_scaling,
        switches.timer_scaling,
        hazards.rehit_cooldown_ticks,
        hazards.rehit_dim,
        hazards.telegraph_min_ticks,
        hazards.graze_margin,
    )
    return DrifterTuning(drifters=drifters, switches=switches, hazards=hazards)


def load_graze_rules() -> GrazeRules:
    """Read and check the graze values file and build its record. `{}` is valid.

    A field left out keeps its default from core.graze. A missing file raises FileNotFoundError;
    a bad one raises ValueError naming the file and the field. Source: scoring.schema.json;
    systems/app/tuning-loader.md, Rules, Scoring file.
    """
    name, data = _read_json(Path(SCORING_FILE))
    fields: dict[str, object] = check_fields(
        name, "", data, _SCORING_FIELDS, optional=_SCORING_FIELDS
    )
    rise: object = fields.get("graze_popup_rise_per_tick", DEFAULT_GRAZE_POPUP_RISE_PER_TICK)
    if not is_number(rise) or rise < 0:
        raise ValueError(f"{name}: graze_popup_rise_per_tick must be a number >= 0")
    rules: GrazeRules = GrazeRules(
        points=check_integer(
            name, "graze_points", fields.get("graze_points", DEFAULT_GRAZE_POINTS), 0
        ),
        popup_ticks=check_integer(
            name,
            "graze_popup_ticks",
            fields.get("graze_popup_ticks", DEFAULT_GRAZE_POPUP_TICKS),
            1,
        ),
        popup_rise_per_tick=float(rise),
        ring_ticks=check_integer(
            name, "graze_ring_ticks", fields.get("graze_ring_ticks", DEFAULT_GRAZE_RING_TICKS), 1
        ),
        ring_start_diameter=float(
            check_positive(
                name,
                "graze_ring_start_diameter",
                fields.get("graze_ring_start_diameter", DEFAULT_GRAZE_RING_START_DIAMETER),
            )
        ),
        ring_end_diameter=float(
            check_positive(
                name,
                "graze_ring_end_diameter",
                fields.get("graze_ring_end_diameter", DEFAULT_GRAZE_RING_END_DIAMETER),
            )
        ),
        ring_width=check_integer(
            name, "graze_ring_width", fields.get("graze_ring_width", DEFAULT_GRAZE_RING_WIDTH), 1
        ),
    )
    log.info(
        "scoring loaded graze_points=%d graze_popup_ticks=%d graze_popup_rise_per_tick=%g "
        "graze_ring_ticks=%d graze_ring_start_diameter=%g graze_ring_end_diameter=%g "
        "graze_ring_width=%d",
        rules.points,
        rules.popup_ticks,
        rules.popup_rise_per_tick,
        rules.ring_ticks,
        rules.ring_start_diameter,
        rules.ring_end_diameter,
        rules.ring_width,
    )
    return rules


def _read_json(relative: Path) -> tuple[str, object]:
    """Return (the file's name from the tuning folder down, its parsed JSON).

    Invalid JSON raises ValueError naming the file. A missing file raises FileNotFoundError.
    """
    name: str = f"tuning/{relative.as_posix()}"
    text: str = (TUNING_DIR / relative).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{name}: not valid JSON: {err}") from err
    return name, data


def _load_switches(relative: Path) -> PlaytestSwitches:
    """Check the playtest switches file and build its record."""
    name, data = _read_json(relative)
    fields: dict[str, object] = check_fields(name, "", data, _SWITCH_FIELDS)
    return PlaytestSwitches(
        hazard_speed_scaling=check_boolean(name, "hazard_speed_scaling", fields),
        timer_scaling=check_boolean(name, "timer_scaling", fields),
    )


def _load_hazards(relative: Path) -> HazardRules:
    """Check the shared hazard values file and build its record. `{}` is valid.

    A field left out keeps its default from core.drifters.base. Source: hazards.schema.json.
    """
    name, data = _read_json(relative)
    fields: dict[str, object] = check_fields(
        name, "", data, _HAZARD_FIELDS, optional=_HAZARD_FIELDS
    )
    cooldown: object = fields.get("rehit_cooldown", DEFAULT_REHIT_COOLDOWN_TICKS)
    if isinstance(cooldown, bool) or not isinstance(cooldown, int) or cooldown < 0:
        raise ValueError(f"{name}: rehit_cooldown must be an integer >= 0")
    dim: object = fields.get("rehit_dim", DEFAULT_REHIT_DIM)
    if not is_number(dim) or not 0 <= dim <= 1:
        raise ValueError(f"{name}: rehit_dim must be a number from 0 to 1")
    telegraph_min: int = check_integer(
        name, "telegraph_min", fields.get("telegraph_min", DEFAULT_TELEGRAPH_MIN_TICKS), 0
    )
    graze_margin: float = check_positive(
        name, "graze_margin", fields.get("graze_margin", GRAZE_MARGIN)
    )
    return HazardRules(
        rehit_cooldown_ticks=cooldown,
        rehit_dim=dim,
        telegraph_min_ticks=telegraph_min,
        graze_margin=float(graze_margin),
    )


def _load_drifter(relative: Path, drifter_type: DrifterType) -> DrifterTypeTuning:
    """Check one drifter tuning file and build its record.

    A drifter with a tuning module of its own (app/drifters/<drifter>_tuning.py) has registered its
    loader by type, and that loader checks the file. Any other follows drifter-tuning.schema.json
    (load_generic).
    """
    name, data = _read_json(relative)
    loader: TuningLoader | None = tuning_loader(drifter_type)
    return load_generic(name, data) if loader is None else loader(name, data)
