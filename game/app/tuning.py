"""Load and check the drifter tuning files, the playtest switches and the shared hazard values.

Reads `tuning/playtest.json`, `tuning/hazards.json` and one
`tuning/drifters/<drifter_type value>.json` per DrifterType, once, at startup. Checks every rule of
their schemas by hand (pygbag has no schema library) and builds the core records. Core trusts what
this returns. Any bad file raises ValueError naming the file and the field; a missing file raises
FileNotFoundError as it is. Never falls back to a default for a missing file. A hazards field left
out keeps its default from core.drifters.base.
A drifter whose file has a schema of its own has a tuning module in `app.drifters`
(`<drifter>_tuning.py`) that registers its loader by type: this module names no drifter. A drifter
with none follows drifter-tuning.schema.json (`app.drifters.checks.load_generic`). The shared
field checks are in `app.drifters.checks`.
Not a startup module: it imports core.drifters, so only app.frame imports it, inside the guard.

Source: docs/contracts/systems/app.md, Interface and Rules, Tuning loader;
docs/contracts/schemas/drifter-tuning.schema.json, playtest-switches.schema.json and
hazards.schema.json, and each drifter's own schema named in its tuning module.
"""

import json
import logging
from pathlib import Path

from app.drifters.checks import check_boolean, check_fields, check_integer, is_number, load_generic
from app.drifters.registry import TuningLoader, tuning_loader
from core.drifters.base import (
    DEFAULT_REHIT_COOLDOWN_TICKS,
    DEFAULT_REHIT_DIM,
    DEFAULT_TELEGRAPH_MIN_TICKS,
    DrifterType,
)
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    HazardRules,
    PlaytestSwitches,
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


_SWITCH_FIELDS: frozenset[str] = frozenset({"hazard_speed_scaling", "timer_scaling"})
_HAZARD_FIELDS: frozenset[str] = frozenset({"rehit_cooldown", "rehit_dim", "telegraph_min"})


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
        "rehit_cooldown=%d rehit_dim=%.2f telegraph_min=%d",
        ",".join(drifter_type.value for drifter_type in drifters),
        switches.hazard_speed_scaling,
        switches.timer_scaling,
        hazards.rehit_cooldown_ticks,
        hazards.rehit_dim,
        hazards.telegraph_min_ticks,
    )
    return DrifterTuning(drifters=drifters, switches=switches, hazards=hazards)


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
    return HazardRules(
        rehit_cooldown_ticks=cooldown, rehit_dim=dim, telegraph_min_ticks=telegraph_min
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
