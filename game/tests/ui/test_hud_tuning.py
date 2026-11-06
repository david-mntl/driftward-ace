"""HUD tuning tests: the shipped file loads, every bad value names the file and the field, and the
baked pictures fit the rules.

Source: docs/contracts/schemas/hud.schema.json; docs/contracts/systems/hud.md, Interface.
"""

import copy
import dataclasses
import json
from pathlib import Path

import pygame
import pytest

import app.hud_tuning as tuning
from app.assets import load_hud_art
from app.hud_tuning import HUD_FILE, load_hud_rules
from core.run import LIVES_START
from ui.hud_rules import PALETTE_KEYS, HudRules


def _shipped() -> dict[str, object]:
    path = Path(tuning.__file__).resolve().parent.parent / "tuning" / HUD_FILE
    data: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data: object) -> None:
    (tmp_path / HUD_FILE).write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(tuning, "TUNING_DIR", tmp_path)


def _set(path: str, value: object) -> dict[str, object]:
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


def _drop(path: str) -> dict[str, object]:
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
    rules = load_hud_rules()
    assert (rules.window.width, rules.window.height) == (856, 518)
    assert (rules.window.field_x, rules.window.field_y) == (16, 10)
    assert rules.score.tile_count == 7
    assert rules.level.bars == 8
    assert len(rules.hearts.slots) == LIVES_START
    assert set(rules.palette) == set(PALETTE_KEYS)


def test_the_palette_is_the_one_the_director_approved() -> None:
    palette = load_hud_rules().palette
    assert palette["ship_lines"] == (0xFF, 0x00, 0xAE)
    assert palette["ship_lines_light"] == (0xBD, 0x7C, 0xFE)
    assert palette["plating"] == (0xF7, 0xF7, 0xF7)
    assert palette["hearts"] == (0xF7, 0x9A, 0xFE)
    assert palette["last_life"] == (0xFF, 0x8A, 0x3D)
    assert palette["score"] == (0xB4, 0x8C, 0xFF)
    assert palette["level"] == (0xFF, 0xC8, 0x00)
    assert palette["graze"] == (0xF8, 0x9F, 0xFE)
    assert palette["panel_body"] == (0x0A, 0x10, 0x29)
    assert palette["frame_lights"] == (0x3D, 0xFF, 0xFC)


def test_the_window_is_the_play_area_plus_the_frame_and_panel() -> None:
    rules = load_hud_rules()
    assert rules.window.field_x + 640 + rules.window.field_x == rules.panel.x
    assert rules.panel.x + rules.panel.width == rules.window.width
    assert rules.window.field_y + 480 + 28 == rules.window.height


def test_a_missing_file_raises_file_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tuning, "TUNING_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        load_hud_rules()


def test_invalid_json_names_the_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / HUD_FILE).write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(tuning, "TUNING_DIR", tmp_path)
    with pytest.raises(ValueError, match=r"tuning/hud\.json: not valid JSON"):
        load_hud_rules()


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("window.width", 0),
        ("window.width", -5),
        ("window.width", 856.5),
        ("window.width", True),
        ("window.dim_alpha", 256),
        ("panel.content_y", -1),
        ("frame.sheen", "yes"),
        ("frame.spill", 1.5),
        ("frame.light_radius", 0),
        ("panel.scale", 0),
        ("score.tile_count", 0),
        ("score.bar_segments", 0),
        ("score.best_separator", 5),
        ("score.box", [1, 2, 3]),
        ("hearts.slots", [[1, 2], [3, 4]]),
        ("level.bars", 0),
        ("level.tier_mid", 9),
        ("graze.count_limit", 0),
        ("motion.sweep_ticks", 0),
        ("motion.beat_scale", 0.5),
        ("motion.beat_peak_at", 0),
        ("motion.beat_peak_at", 0.9),
        ("motion.scan_from", 999),
        ("motion.break_keys", [[0, 1, "white"]]),
        ("motion.break_keys", [[0.1, 1, "white"], [1, 0.2, "plain"]]),
        ("motion.break_keys", [[0, 1, "glow"], [1, 0.2, "plain"]]),
        ("motion.break_keys", [[0, 2, "white"], [1, 0.2, "plain"]]),
        ("level.tier_mid_mix", 2),
        ("fonts.label_mix", 2),
        ("fonts.ui_file", 7),
        ("palette.hearts", "pink"),
        ("palette.hearts", "#12345"),
    ],
)
def test_a_bad_value_names_the_file_and_the_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: str, value: object
) -> None:
    _write(tmp_path, monkeypatch, _set(path, value))
    field = path.split(".")[-1]
    with pytest.raises(ValueError, match=rf"tuning/hud\.json: .*{field}"):
        load_hud_rules()


@pytest.mark.parametrize(
    "path", ["window", "window.field_x", "palette.dim", "motion.ring_to", "fonts.label_file"]
)
def test_a_missing_field_is_an_error_not_a_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    _write(tmp_path, monkeypatch, _drop(path))
    with pytest.raises(ValueError, match=r"tuning/hud\.json: .*is missing"):
        load_hud_rules()


def test_an_unknown_field_is_an_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, _set("window.glow", 3))
    with pytest.raises(ValueError, match=r"tuning/hud\.json: window\.glow is not a known field"):
        load_hud_rules()


def test_an_unknown_palette_color_is_an_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path, monkeypatch, _set("palette.teal", "#008080"))
    with pytest.raises(ValueError, match=r"tuning/hud\.json: palette\.teal is not a known field"):
        load_hud_rules()


def test_the_top_level_must_be_an_object(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path, monkeypatch, [])
    with pytest.raises(ValueError, match=r"tuning/hud\.json: the file must be an object"):
        load_hud_rules()


# ----- the pictures fit the rules -----


@pytest.fixture(scope="module")
def rules() -> HudRules:
    return load_hud_rules()


def test_every_baked_picture_and_font_loads_at_the_size_the_rules_say(
    pygame_headless: None, rules: HudRules
) -> None:
    pygame.display.set_mode((rules.window.width, rules.window.height))
    art = load_hud_art(rules)
    assert art.frame.get_size() == (rules.panel.x + rules.frame.pillar_width, rules.window.height)
    assert art.panel.get_size() == (rules.panel.width, rules.window.height)
    assert len(art.hearts) == 5
    assert len(art.radar) == rules.motion.sweep_frames
    assert len(art.ring) == rules.motion.ring_frames
    assert set(art.fonts) == {"value", "tile", "graze", "level"}


def test_a_window_taller_than_the_picture_is_caught_at_load_with_the_file_named(
    pygame_headless: None, rules: HudRules
) -> None:
    pygame.display.set_mode((rules.window.width, rules.window.height))
    taller = dataclasses.replace(
        rules, window=dataclasses.replace(rules.window, height=rules.window.height + 10)
    )
    with pytest.raises(ValueError, match=r"assets/hud_frame\.png: size is"):
        load_hud_art(taller)


def test_a_missing_font_file_is_an_error(pygame_headless: None, rules: HudRules) -> None:
    pygame.display.set_mode((rules.window.width, rules.window.height))
    odd = dataclasses.replace(
        rules, fonts=dataclasses.replace(rules.fonts, ui_file="fonts/none.ttf")
    )
    with pytest.raises(FileNotFoundError):
        load_hud_art(odd)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("window.width", 600),
        ("window.height", 400),
        ("window.field_x", 100),
        ("window.field_y", 100),
        ("panel.width", 400),
        ("frame.pillar_width", 300),
        ("score.bar_gap", 40),
    ],
)
def test_numbers_that_do_not_fit_together_are_caught_with_the_file_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: str, value: object
) -> None:
    _write(tmp_path, monkeypatch, _set(path, value))
    with pytest.raises(ValueError, match=r"tuning/hud\.json: "):
        load_hud_rules()
