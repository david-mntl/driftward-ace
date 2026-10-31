"""Load and check the ship look values file.

Reads `tuning/ship_look.json` once, at startup (`load_ship_look`). Checks every rule of
ship-look.schema.json by hand (pygbag has no schema library) and builds a ShipLook. A field left
out keeps its default from ui.ship_view.DEFAULT_SHIP_LOOK. A missing file raises
FileNotFoundError; a bad one raises ValueError naming the file and the field. Never falls back
for a missing file. Not a startup module: it imports ui, so only app.frame imports it, inside
the guard.

Source: docs/contracts/schemas/ship-look.schema.json; 04-ship.md, look.
"""

import json
import logging
from pathlib import Path

from app.drifters.checks import check_fields, check_integer, check_positive
from app.tuning import TUNING_DIR
from ui.ship_view import DEFAULT_SHIP_LOOK, ShipLook

log = logging.getLogger(__name__)

SHIP_LOOK_FILE: str = "ship_look.json"

_FIELDS: frozenset[str] = frozenset(
    {"lean_speed", "streak_speed", "streak_long_speed", "flame_ticks_per_frame"}
)


def load_ship_look() -> ShipLook:
    """Read and check the ship look values file and build its record. `{}` is valid."""
    name: str = f"tuning/{SHIP_LOOK_FILE}"
    text: str = (TUNING_DIR / Path(SHIP_LOOK_FILE)).read_text(encoding="utf-8")
    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as err:
        raise ValueError(f"{name}: not valid JSON: {err}") from err
    fields: dict[str, object] = check_fields(name, "", data, _FIELDS, optional=_FIELDS)
    default: ShipLook = DEFAULT_SHIP_LOOK
    lean: float = check_positive(name, "lean_speed", fields.get("lean_speed", default.lean_speed))
    short: float = check_positive(
        name, "streak_speed", fields.get("streak_speed", default.streak_speed)
    )
    long: float = check_positive(
        name, "streak_long_speed", fields.get("streak_long_speed", default.streak_long_speed)
    )
    if long <= short:
        raise ValueError(f"{name}: streak_long_speed must be greater than streak_speed")
    look: ShipLook = ShipLook(
        lean_speed=lean,
        streak_speed=short,
        streak_long_speed=long,
        flame_ticks_per_frame=check_integer(
            name,
            "flame_ticks_per_frame",
            fields.get("flame_ticks_per_frame", default.flame_ticks_per_frame),
            1,
        ),
    )
    log.info("ship look loaded %s", look)
    return look
