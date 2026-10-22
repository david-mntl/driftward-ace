"""Tests for the bot check. Synthetic waves, so a change to the real waves never breaks them."""

import json
from pathlib import Path
from typing import Any

import pytest
import store
import wave_check
from app.tuning import load_tuning
from bot import check_bot
from checks import Context, Result, ships_at_spots
from core.wave_files import _build_wave
from settings import BotConfig, Config, load_config
from tracks import build_tracks

QUICK = BotConfig()
"""The tool's default search."""


def wave(*placements: dict[str, Any]) -> dict[str, Any]:
    return {"length_px": 1000, "kind": "fixed", "placements": list(placements)}


def big_rocks(*xs: int) -> dict[str, Any]:
    return wave(
        *({"at_px": 300, "type": "meteorite", "x": x, "variant": "big"} for x in xs)
    )


WALL: list[int] = list(range(15, 640, 30))
"""Big meteorites (40 px across) every 30 px: a row with no way through."""


def bot_result(document: dict[str, Any], bot: BotConfig = QUICK) -> Result:
    config = Config(bot=bot)
    tuning = load_tuning()
    built = _build_wave("t", document, tuning)
    tracks = build_tracks(built, 8, tuning, ships_at_spots(config)["center"], 2400)
    return check_bot(Context(built, 8, tuning, config, tracks, ships_at_spots(config)))


def test_a_wave_with_no_hazard_passes() -> None:
    assert (
        bot_result(wave({"at_px": 300, "type": "coin", "x": 300, "y": 200})).status
        == "PASS"
    )


def test_a_wall_with_no_way_through_fails_from_every_start_spot() -> None:
    result = bot_result(big_rocks(*WALL))
    assert result.status == "FAIL"
    assert len(result.findings) == 3
    for spot, finding in zip(("left", "center", "right"), result.findings, strict=True):
        assert f"start spot '{spot}'" in finding.message
        assert finding.tick is not None and finding.px is not None
        assert any("meteorite big" in name for name in finding.drifters)


@pytest.mark.parametrize(
    ("low", "high", "spot"),
    [(60, 160, "right"), (280, 380, "center"), (480, 580, "left")],
)
def test_a_wall_with_a_gap_the_ship_fits_through_passes(
    low: int, high: int, spot: str
) -> None:
    # An 80 px gap. The far ones need a full-speed dash from the opposite start spot.
    gap = [x for x in WALL if not low < x < high]
    assert bot_result(big_rocks(*gap), BotConfig(start_spots=(spot,))).status == "PASS"


def test_a_gap_narrower_than_the_ship_fails() -> None:
    assert bot_result(big_rocks(*(x for x in WALL if x != 525))).status == "FAIL"


def test_the_bot_flies_only_the_start_spots_it_is_given() -> None:
    result = bot_result(big_rocks(*WALL), BotConfig(start_spots=("left",)))
    assert [f.message.split("'")[1] for f in result.findings] == ["left"]
    assert "from left to tick" in result.note


def test_a_margin_grows_the_hitboxes_for_the_bot() -> None:
    gap = [x for x in WALL if not 480 < x < 580]
    tight = BotConfig(start_spots=("right",), margin_px=30)
    assert bot_result(big_rocks(*gap), tight).status == "FAIL"


# ---- config, passes, command line ---------------------------------------------------------


def test_the_shipped_config_loads_the_bot_values() -> None:
    bot = load_config().bot
    assert bot.decision_ticks >= 1 and bot.beam_width >= 1


@pytest.mark.parametrize(
    "bad",
    [
        {"start_spots": ["middle"]},
        {"decision_ticks": 0},
        {"beam_width": 2.5},
        {"cell_px": 0},
        {"spread_speed": -3},
        {"margin_px": -1},
    ],
)
def test_config_rejects_a_bad_bot_value(tmp_path: Path, bad: dict[str, Any]) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"bot": bad}))
    with pytest.raises(ValueError, match="bot"):
        load_config(path)


def test_bot_passes_are_kept_apart_from_part_one(tmp_path: Path) -> None:
    config = Config()
    document = big_rocks(300)
    part_one = store.fingerprint(document, config)
    bot = store.fingerprint(document, config, store.BOT_SUITE)
    assert part_one != bot
    passes: dict[str, str] = {}
    store.remember(passes, "a", 8, bot, ok=True, suite=store.BOT_SUITE)
    assert list(passes) == ["a@8/bot"]
    assert not store.is_fresh(passes, "a", 8, bot)
    assert store.is_fresh(passes, "a", 8, bot, store.BOT_SUITE)


def test_command_line_bot_runs_the_bot_check_alone(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"bot": {"start_spots": ["center"]}}))
    good = tmp_path / "good.json"
    good.write_text(json.dumps(big_rocks(300)))
    wall = tmp_path / "wall.json"
    wall.write_text(json.dumps(big_rocks(*WALL)))
    common = ["--bot", "--no-record", "--config", str(config)]
    assert wave_check.main(["--wave", str(good), *common]) == 0
    out = capsys.readouterr().out
    assert "PASS the bot finds a zero-hit path" in out
    assert "seam" not in out and "coin" not in out
    assert wave_check.main(["--wave", str(wall), *common]) == 1
    assert "every path is hit" in capsys.readouterr().out
    assert (
        wave_check.main(["--wave", str(good), "--no-record", "--config", str(config)])
        == 0
    )
    assert "runs on its own: wave_check.py --bot" in capsys.readouterr().out
