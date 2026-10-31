"""Ship look tuning tests: the shipped file loads, and bad values name the file and the field.

Source: docs/contracts/schemas/ship-look.schema.json. These tests live under ui/ because the
record they build is the view's ShipLook.
"""

import json
from pathlib import Path

import pytest

import app.ship_tuning as tuning
from app.ship_tuning import load_ship_look
from ui.ship_view import DEFAULT_SHIP_LOOK


def _write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    (tmp_path / tuning.SHIP_LOOK_FILE).write_text(text, encoding="utf-8")
    monkeypatch.setattr(tuning, "TUNING_DIR", tmp_path)


def test_the_shipped_file_loads_and_matches_the_defaults() -> None:
    assert load_ship_look() == DEFAULT_SHIP_LOOK


def test_an_empty_object_keeps_every_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, "{}")
    assert load_ship_look() == DEFAULT_SHIP_LOOK


def test_a_field_overrides_its_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, '{"lean_speed": 0.5, "flame_ticks_per_frame": 2}')
    look = load_ship_look()
    assert look.lean_speed == 0.5
    assert look.flame_ticks_per_frame == 2
    assert look.streak_long_speed == DEFAULT_SHIP_LOOK.streak_long_speed


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lean_speed", 0),
        ("lean_speed", -1),
        ("streak_speed", 0),
        ("streak_long_speed", "4"),
        ("streak_long_speed", True),
        ("flame_ticks_per_frame", 0),
        ("flame_ticks_per_frame", 1.5),
    ],
)
def test_a_bad_value_raises_naming_the_file_and_the_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    _write(tmp_path, monkeypatch, json.dumps({field: value}))
    with pytest.raises(ValueError, match=rf"ship_look\.json: {field}"):
        load_ship_look()


def test_long_streaks_must_come_after_short_streaks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, '{"streak_speed": 3, "streak_long_speed": 2}')
    with pytest.raises(ValueError, match="streak_long_speed must be greater"):
        load_ship_look()


def test_an_unknown_field_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, '{"glow": 3}')
    with pytest.raises(ValueError, match="glow is not a known field"):
        load_ship_look()
