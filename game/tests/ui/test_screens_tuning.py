"""Screens tuning tests: the shipped file loads, the palette is the Director's, every bad value
names the file and the field, and the screens' font loads at every role's size.

Source: docs/contracts/schemas/screens.schema.json; docs/contracts/systems/screens.md, Interface;
12-art-and-audio.md, Screen colors.
"""

import copy
import json
from pathlib import Path

import pygame
import pytest

import app.screens_tuning as tuning
from app.assets import load_screen_fonts
from app.screens_tuning import SCREENS_FILE, load_screen_rules
from ui.screen_rules import FONT_ROLES, PALETTE_KEYS


def _shipped() -> dict[str, object]:
    path = Path(tuning.__file__).resolve().parent.parent / "tuning" / SCREENS_FILE
    data: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data: object) -> None:
    (tmp_path / SCREENS_FILE).write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(tuning, "TUNING_DIR", tmp_path)


def _with(path: str, value: object) -> dict[str, object]:
    """The shipped file with the field at the dotted `path` set to `value`."""
    data = copy.deepcopy(_shipped())
    node: dict[str, object] = data
    *parents, last = path.split(".")
    for key in parents:
        child = node[key]
        assert isinstance(child, dict)
        node = child
    node[last] = value
    return data


def _without(path: str) -> dict[str, object]:
    data = copy.deepcopy(_shipped())
    node: dict[str, object] = data
    *parents, last = path.split(".")
    for key in parents:
        child = node[key]
        assert isinstance(child, dict)
        node = child
    del node[last]
    return data


def test_the_shipped_file_loads() -> None:
    rules = load_screen_rules()
    assert set(rules.palette) == set(PALETTE_KEYS)
    assert {role.name for role in rules.fonts.roles} == set(FONT_ROLES)
    assert (rules.pause.w, rules.pause.h) == (320, 120)
    assert (rules.game_over.w, rules.game_over.h) == (320, 160)
    assert (rules.game_over.picker_w, rules.game_over.picker_h) == (400, 280)


def test_the_palette_is_the_one_the_director_approved() -> None:
    palette = load_screen_rules().palette
    assert palette["ship_lines"] == (0x9D, 0x6B, 0xFF)
    assert palette["ship_lines_light"] == (0xC9, 0xB5, 0xFF)
    assert palette["frame_lights"] == (0x8B, 0xE9, 0xFF)
    assert palette["panel_body"] == (0x0C, 0x0B, 0x24)
    assert palette["score"] == (0xD8, 0xC8, 0xFF)
    assert palette["level"] == (0xFF, 0xD1, 0x66)
    assert palette["hearts"] == (0xE6, 0xA8, 0xFF)
    assert palette["graze"] == (0xE6, 0xA8, 0xFF)
    assert palette["last_life"] == (0xFF, 0x9E, 0x5E)
    assert palette["plating"] == (0xF4, 0xF1, 0xFF)
    assert palette["rank_1"] == (0xFF, 0xD1, 0x66)
    assert palette["rank_2"] == (0xCF, 0xD2, 0xFF)
    assert palette["rank_3"] == (0xF0, 0xA0, 0x7A)


def test_the_screens_never_share_the_hud_palette_file() -> None:
    hud = json.loads(
        (Path(tuning.__file__).resolve().parent.parent / "tuning" / "hud.json").read_text()
    )
    assert hud["palette"]["ship_lines"] != _shipped()["palette"]["ship_lines"]  # type: ignore[index]


def test_a_missing_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tuning, "TUNING_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        load_screen_rules()


def test_bad_json_names_the_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / SCREENS_FILE).write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(tuning, "TUNING_DIR", tmp_path)
    with pytest.raises(ValueError, match=r"tuning/screens\.json: not valid JSON"):
        load_screen_rules()


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        ("pause.w", 0, "pause.w"),
        ("pause.w", -5, "pause.w"),
        ("pause.w", 3.5, "pause.w"),
        ("pause.w", True, "pause.w"),
        ("pause.blur", 1, "pause.blur must be a boolean"),
        ("glass.fill_alpha", 256, "glass.fill_alpha must be an integer from 0 to 255"),
        ("glass.blur_down", 0, "glass.blur_down"),
        ("glow.box_strength", 1.5, "glow.box_strength must be a number from 0 to 1"),
        ("glow.text_strength", -0.1, "glow.text_strength"),
        ("palette.score", "red", "palette.score must be a color like #rrggbb"),
        ("palette.score", "#12345", "palette.score must be a color like #rrggbb"),
        ("fonts.text_file", 7, "fonts.text_file must be a string"),
        ("fonts.roles", [], "fonts.roles must be a non-empty array"),
        ("instructions.foot_group_gap", -1, "instructions.foot_group_gap"),
        ("version.margin_left", -1, "version.margin_left"),
        ("version.margin_bottom", 2.5, "version.margin_bottom"),
        ("version.text_alpha", 256, "version.text_alpha must be an integer from 0 to 255"),
    ],
)
def test_a_bad_value_names_the_file_and_the_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    value: object,
    message: str,
) -> None:
    _write(tmp_path, monkeypatch, _with(path, value))
    with pytest.raises(ValueError, match=rf"tuning/screens\.json: .*{message}"):
        load_screen_rules()


def test_a_missing_field_names_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, _without("pause.gap"))
    with pytest.raises(ValueError, match=r"tuning/screens\.json: .*pause\.gap"):
        load_screen_rules()


def test_a_missing_version_section_names_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, _without("version"))
    with pytest.raises(ValueError, match=r"tuning/screens\.json: .*version"):
        load_screen_rules()


def test_an_unknown_field_names_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = _with("pause.extra", 1)
    _write(tmp_path, monkeypatch, data)
    with pytest.raises(ValueError, match=r"tuning/screens\.json: .*extra"):
        load_screen_rules()


def test_a_missing_palette_key_is_named(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, _without("palette.rank_2"))
    with pytest.raises(ValueError, match=r"palette\.rank_2 is missing"):
        load_screen_rules()


def test_an_unknown_palette_key_is_named(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, _with("palette.mauve", "#aa66ff"))
    with pytest.raises(ValueError, match=r"palette\.mauve is not a known field"):
        load_screen_rules()


def test_a_font_role_must_be_named_once_and_known(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    roles = copy.deepcopy(_shipped()["fonts"])["roles"]  # type: ignore[index]
    _write(tmp_path, monkeypatch, _with("fonts.roles", roles[1:]))
    with pytest.raises(ValueError, match=r"fonts\.roles has no title"):
        load_screen_rules()
    _write(tmp_path, monkeypatch, _with("fonts.roles", [*roles, roles[0]]))
    with pytest.raises(ValueError, match=r"fonts\.roles names title more than once"):
        load_screen_rules()
    bad = [{"name": "banner", "size": 9, "spacing": 0.0}, *roles[1:]]
    _write(tmp_path, monkeypatch, _with("fonts.roles", bad))
    with pytest.raises(ValueError, match=r"fonts\.roles\[0\]\.name must be one of"):
        load_screen_rules()


def test_the_picker_box_cannot_be_smaller_than_the_plain_box(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, _with("game_over.picker_w", 100))
    with pytest.raises(ValueError, match=r"game_over\.picker_w and picker_h"):
        load_screen_rules()


def test_the_screen_font_loads_at_every_role_size() -> None:
    pygame.init()
    rules = load_screen_rules()
    fonts = load_screen_fonts(rules)
    assert set(fonts) == set(FONT_ROLES)
    sizes = {role.name: role.size for role in rules.fonts.roles}
    assert fonts["title"].get_height() > fonts["key"].get_height()
    assert sizes["title"] > sizes["key"]
