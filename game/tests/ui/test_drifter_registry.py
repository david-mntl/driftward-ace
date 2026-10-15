"""Drifter list guards. Contract: docs/contracts/systems/drifters.md, Rules, Tuning files.

Every DrifterType has exactly one tuning file, one registered class and one registered view.
A half-added drifter (a class with no view, a tuning file with no class) must fail here, not
in the browser. Source: scope report DRA-29 (the guard test).
"""

import json
from pathlib import Path

from core.drifters.base import DrifterType
from core.drifters.registry import available_drifters
from ui.drifters.registry import registered_views

TUNING_DIR: Path = Path(__file__).resolve().parents[2] / "tuning"
"""game/tuning, found from this file's place: tests/ui/ -> tests/ -> game/."""

SWITCHES: set[str] = {"hazard_speed_scaling", "timer_scaling"}
"""Source: docs/contracts/schemas/playtest-switches.schema.json; 08-difficulty.md, rule 5."""


def test_drifter_lists_match_everywhere() -> None:
    types: set[str] = {t.value for t in DrifterType}
    files: set[str] = {p.stem for p in (TUNING_DIR / "drifters").glob("*.json")}
    classes: set[str] = {t.value for t in available_drifters()}
    views: set[str] = {t.value for t in registered_views()}

    assert types, "DrifterType has no members"
    assert files == types, f"tuning files {sorted(files)} vs DrifterType {sorted(types)}"
    assert classes == types, f"registered classes {sorted(classes)} vs DrifterType {sorted(types)}"
    assert views == types, f"registered views {sorted(views)} vs DrifterType {sorted(types)}"


def test_playtest_file_holds_exactly_the_two_switches() -> None:
    path: Path = TUNING_DIR / "playtest.json"
    assert path.is_file(), f"{path} is missing"

    data: object = json.loads(path.read_text(encoding="utf-8"))

    assert isinstance(data, dict)
    assert set(data) == SWITCHES
    for name in SWITCHES:
        assert isinstance(data[name], bool), f"{name} is not a boolean"
