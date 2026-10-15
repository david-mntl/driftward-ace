"""Object list guards. Contract: docs/contracts/systems/objects.md, Rules, Tuning files.

Every ObjectType has exactly one tuning file, one registered class and one registered view.
A half-added object (a class with no view, a tuning file with no class) must fail here, not
in the browser. Source: scope report DRA-29 (the guard test).
"""

import json
from pathlib import Path

from core.objects.base import ObjectType
from core.objects.registry import available_objects
from ui.objects.registry import registered_views

TUNING_DIR: Path = Path(__file__).resolve().parents[2] / "tuning"
"""game/tuning, found from this file's place: tests/ui/ -> tests/ -> game/."""

SWITCHES: set[str] = {"hazard_speed_scaling", "timer_scaling"}
"""Source: docs/contracts/schemas/playtest-switches.schema.json; 08-difficulty.md, rule 5."""


def test_object_lists_match_everywhere() -> None:
    types: set[str] = {t.value for t in ObjectType}
    files: set[str] = {p.stem for p in (TUNING_DIR / "objects").glob("*.json")}
    classes: set[str] = {t.value for t in available_objects()}
    views: set[str] = {t.value for t in registered_views()}

    assert types, "ObjectType has no members"
    assert files == types, f"tuning files {sorted(files)} vs ObjectType {sorted(types)}"
    assert classes == types, f"registered classes {sorted(classes)} vs ObjectType {sorted(types)}"
    assert views == types, f"registered views {sorted(views)} vs ObjectType {sorted(types)}"


def test_playtest_file_holds_exactly_the_two_switches() -> None:
    path: Path = TUNING_DIR / "playtest.json"
    assert path.is_file(), f"{path} is missing"

    data: object = json.loads(path.read_text(encoding="utf-8"))

    assert isinstance(data, dict)
    assert set(data) == SWITCHES
    for name in SWITCHES:
        assert isinstance(data[name], bool), f"{name} is not a boolean"
