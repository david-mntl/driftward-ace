"""Demo flight values file tests: the loader, and the shipped script played through.

Spec: docs/contracts/schemas/demo.schema.json; docs/contracts/systems/demo.md. The file is
copied to a `tmp_path` folder (`app.demo_tuning.TUNING_DIR` patched) and edited one field at a
time; every field of the shipped file is required.
"""

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import app.demo_tuning as demo_tuning
from app.screens_tuning import load_screen_rules
from app.tuning import TUNING_DIR, load_tuning
from core.demo import DemoRules, start_demo, step_demo
from core.drifters.tuning import DrifterTuning
from core.ship import SHIP_H, SHIP_W
from core.world import SCREEN_H, SCREEN_W, TOP_LINE_Y
from ui.demo_view import DemoLook
from ui.screen_rules import ScreenRules

TUNING: DrifterTuning = load_tuning()
SCREENS: ScreenRules = load_screen_rules()
SHIPPED: dict[str, Any] = json.loads((TUNING_DIR / "demo.json").read_text(encoding="utf-8"))


def _load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data: object
) -> tuple[DemoRules | None, DemoLook]:
    (tmp_path / "demo.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(demo_tuning, "TUNING_DIR", tmp_path)
    return demo_tuning.load_demo(TUNING, SCREENS)


def _paths(data: dict[str, Any], prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    """Every field path of the shipped file, objects walked, the steps by their first entry."""
    found: list[tuple[str, ...]] = []
    for key, value in data.items():
        found.append((*prefix, key))
        if isinstance(value, dict):
            found += _paths(value, (*prefix, key))
    return found


def test_the_shipped_file_loads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rules, look = _load(tmp_path, monkeypatch, SHIPPED)
    assert rules is not None
    assert len(rules.steps) == len(SHIPPED["steps"])
    assert look.skip_word == SHIPPED["look"]["skip_word"]


def test_enabled_false_gives_no_script(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = copy.deepcopy(SHIPPED)
    data["enabled"] = False
    rules, _ = _load(tmp_path, monkeypatch, data)
    assert rules is None


@pytest.mark.parametrize("path", _paths(SHIPPED), ids=".".join)
def test_every_field_is_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, path: tuple[str, ...]
) -> None:
    data = copy.deepcopy(SHIPPED)
    holder: dict[str, Any] = data
    for key in path[:-1]:
        holder = holder[key]
    del holder[path[-1]]
    with pytest.raises(ValueError, match=f"tuning/demo.json: .*{path[-1]} is missing"):
        _load(tmp_path, monkeypatch, data)


@pytest.mark.parametrize("field", ["keys", "ticks", "caption", "stand", "pilot_to"])
def test_every_step_field_is_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    data = copy.deepcopy(SHIPPED)
    del data["steps"][0][field]
    with pytest.raises(ValueError, match=f"steps\\[0\\].{field} is missing"):
        _load(tmp_path, monkeypatch, data)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda d: d.update(steps=[]), "steps must be a non-empty list"),
        (lambda d: d["steps"][1].update(keys=["jump"]), "keys must list"),
        (lambda d: d["steps"][1].update(keys=["up", "up"]), "keys must list"),
        (lambda d: d["steps"][1].update(ticks=0), "ticks must be"),
        (lambda d: d["steps"][1].update(caption=""), "caption must be text or null"),
        (lambda d: d["steps"][0].update(keys=["up"]), "stands, so it can hold no keys"),
        (lambda d: d.update(coin_step=99), "coin_step 99"),
        (lambda d: d.update(coin_type="dragon"), "coin_type must be one of"),
        (lambda d: d.update(coin_variant="gold"), "coin_variant must be one of"),
        (lambda d: d["look"].update(lit_fill_alpha=256), "lit_fill_alpha must be 0 to 255"),
        (lambda d: d["look"].update(key_size=0), "key_size must be"),
        (lambda d: d["look"].update(caption_role="huge"), "caption_role must be one of"),
        (lambda d: d["look"].update(skip_word=" "), "skip_word must be text"),
        (lambda d: d.update(extra=1), "extra is not a known field"),
        (lambda d: d["steps"][3].update(pilot_to=[700, 100]), "pilot_to must be null or"),
        (lambda d: d["steps"][3].update(pilot_to=[100]), "pilot_to must be null or"),
        (lambda d: d["steps"][3].update(keys=["up"]), "holds keys and flies"),
        (lambda d: d["pilot"].update(gain=0), "pilot.gain must be a number > 0"),
        (lambda d: d["pilot"].update(near_px=-1), "pilot.near_px must be a number >= 0"),
        (lambda d: d["look"].update(start_scale=0.5), "start_scale must be a number >= 1"),
        (lambda d: d["look"].update(start_role="huge"), "start_role must be one of"),
        (lambda d: d["look"].update(start_text=""), "start_text must be text"),
        (lambda d: d["look"].update(key_fade_ticks=0), "key_fade_ticks must be"),
    ],
)
def test_a_bad_value_is_refused_naming_the_file_and_the_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: Callable[[dict[str, Any]], None],
    message: str,
) -> None:
    data = copy.deepcopy(SHIPPED)
    change(data)
    with pytest.raises(ValueError, match=f"tuning/demo.json: .*{message}"):
        _load(tmp_path, monkeypatch, data)


def test_the_shipped_script_collects_its_coin_and_keeps_the_ship_in_the_play_area(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rules, _ = _load(tmp_path, monkeypatch, SHIPPED)
    assert rules is not None
    demo = start_demo(rules, TUNING)
    collected: int = 0
    while not demo.done:
        demo = step_demo(demo)
        collected += len(demo.sound_cues)
        ship = demo.ship
        assert SHIP_W / 2 <= ship.x <= SCREEN_W - SHIP_W / 2
        assert TOP_LINE_Y + SHIP_H / 2 < ship.y < SCREEN_H - SHIP_H / 2
        assert not ship.at_top_line
        assert ship.wall is None
    assert collected == 1
