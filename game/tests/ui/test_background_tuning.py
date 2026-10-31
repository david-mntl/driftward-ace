"""Background tuning tests: the shipped file loads, and bad values name the file and the field.

Source: docs/contracts/schemas/background.schema.json. These tests live under ui/ because the
record they build is the view's BackgroundRules.
"""

import json
from pathlib import Path

import pytest

import app.background_tuning as tuning
from app.background_tuning import DEFAULTS, load_background_rules


def _write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    (tmp_path / tuning.BACKGROUND_FILE).write_text(text, encoding="utf-8")
    monkeypatch.setattr(tuning, "TUNING_DIR", tmp_path)


def test_the_shipped_file_loads_and_matches_the_defaults() -> None:
    rules = load_background_rules()
    assert rules.planet_count == DEFAULTS["planet_count"]
    assert rules.glow_strength == DEFAULTS["glow_strength"]


def test_an_empty_object_keeps_every_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, "{}")
    assert load_background_rules().river_light_count == DEFAULTS["river_light_count"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("planet_count", -1),
        ("planet_count", 1.5),
        ("planet_speed", -0.1),
        ("planet_scale", 0),
        ("sway_loop_ticks", 0),
        ("river_light_loop_ticks", 0),
        ("river_light_strength", 1.5),
        ("glow_strength", True),
        ("glow_height", "40"),
    ],
)
def test_a_bad_value_raises_naming_the_file_and_the_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    _write(tmp_path, monkeypatch, json.dumps({field: value}))
    with pytest.raises(ValueError, match=rf"background\.json: {field}"):
        load_background_rules()


def test_an_unknown_field_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, '{"dust_count": 3}')
    with pytest.raises(ValueError, match="dust_count is not a known field"):
        load_background_rules()


def test_broken_json_raises_naming_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, "{")
    with pytest.raises(ValueError, match=r"background\.json: not valid JSON"):
        load_background_rules()
