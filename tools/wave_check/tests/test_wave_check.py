"""Tests for wave_check part 1. Synthetic waves, so a change to the real waves never breaks them."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import store
import wave_check
from app import tuning as tuning_module
from app.tuning import load_tuning
from checks import Context, run_checks, ships_at_spots
from core.wave_files import _build_wave
from settings import Config, load_config
from tracks import build_tracks

GAME_TUNING = Path(__file__).resolve().parents[3] / "game" / "tuning"


def wave(length: float, *placements: dict[str, Any]) -> dict[str, Any]:
    return {"length_px": length, "kind": "fixed", "placements": list(placements)}


def run(
    document: dict[str, Any], level: int = 8, config: Config | None = None
) -> dict[str, str]:
    """Status of every check of a synthetic wave."""
    config = config or Config()
    tuning = load_tuning()
    built = _build_wave("t", document, tuning)
    tracks = build_tracks(built, level, tuning, ships_at_spots(config)["center"], 2400)
    ctx = Context(built, level, tuning, config, tracks, ships_at_spots(config))
    return {r.name: r.status for r in run_checks(ctx)}


def findings(document: dict[str, Any], name: str, level: int = 8) -> list[str]:
    config = Config()
    tuning = load_tuning()
    built = _build_wave("t", document, tuning)
    tracks = build_tracks(built, level, tuning, ships_at_spots(config)["center"], 2400)
    ctx = Context(built, level, tuning, config, tracks, ships_at_spots(config))
    return [f.message for r in run_checks(ctx) if r.name == name for f in r.findings]


GOOD = wave(
    1400,
    {"at_px": 300, "type": "meteorite", "x": 300, "variant": "medium"},
    {"at_px": 300, "type": "coin", "x": 360, "y": 150},
)


def test_a_fair_wave_passes_part_one() -> None:
    status = run(GOOD)
    assert [
        status[k] for k in ("placement", "telegraph", "coin_near", "coin_in_island", "seam")
    ] == ["PASS"] * 5
    assert status["bot"] == status["gap"] == "SKIP"


def test_seam_does_not_check_the_end_of_a_wave() -> None:
    # Still on screen at the end of a 450 px wave: fine, the wave's extra rest covers it.
    late = wave(450, {"at_px": 300, "type": "meteorite", "x": 300})
    assert run(late)["seam"] == "PASS"


def test_seam_counts_the_entry_warning() -> None:
    # Triggers at 120 px (loader allows it) but the hazard is on screen from then on: fine at
    # the start. A trigger one tick short of the end fails at the end, not the start.
    ok = wave(1400, {"at_px": 120, "type": "meteorite", "x": 300})
    assert run(ok)["seam"] == "PASS"


def test_coin_with_no_hazard_near_fails() -> None:
    lonely = wave(1400, {"at_px": 300, "type": "coin", "x": 300, "y": 200})
    messages = findings(lonely, "coin_near")
    assert len(messages) == 1
    assert "no hazard is on screen" in messages[0]


def test_coin_far_from_the_hazard_fails_and_names_the_nearest() -> None:
    far = wave(
        1400,
        {"at_px": 300, "type": "meteorite", "x": 40},
        {"at_px": 300, "type": "coin", "x": 600, "y": 200},
    )
    messages = findings(far, "coin_near")
    assert len(messages) == 1
    assert "meteorite" in messages[0]


def island(at_px: float, x: float, y: float, variant: str = "rectangle") -> dict[str, Any]:
    return {"at_px": at_px, "type": "floating_island", "x": x, "y": y, "variant": variant}


def coin(at_px: float, x: float, y: float) -> dict[str, Any]:
    return {"at_px": at_px, "type": "coin", "x": x, "y": y}


def test_coin_inside_an_island_fails() -> None:
    # Rectangle 320 x 120 at (320, 150) spans y 90 to 210. Both parked, so they stay overlapped.
    inside = wave(1400, island(300, 320, 150), coin(300, 320, 150))
    assert findings(inside, "coin_in_island") == ["#2 coin sits inside #1 floating_island rectangle"]


def test_coin_touching_an_island_edge_passes() -> None:
    # The coin's 12 x 10 box ends at y 210, the island's bottom edge: touching is not inside.
    touching = wave(1400, island(300, 320, 150), coin(300, 320, 215))
    status = run(touching)
    assert status["coin_in_island"] == "PASS"


def test_coin_inside_the_triangle_uses_its_slope() -> None:
    # Triangle 320 x 120 at (320, 150): slope from (160, 90) down to (480, 210).
    above_slope = wave(1400, island(300, 320, 150, "triangle"), coin(300, 400, 120))
    below_slope = wave(1400, island(300, 320, 150, "triangle"), coin(300, 200, 190))
    assert run(above_slope)["coin_in_island"] == "PASS"
    assert len(findings(below_slope, "coin_in_island")) == 1


def test_an_island_counts_as_a_hazard_for_the_seam_and_coin_near() -> None:
    # 09-waves.md, rule 7: for wave_check an island counts as a hazard.
    early = wave(1400, island(0, 320, 150))
    assert run(early)["seam"] == "FAIL"
    near = wave(1400, island(300, 320, 150), coin(300, 320, 240))
    assert run(near)["coin_near"] == "PASS"


def test_a_hazard_that_never_enters_the_screen_fails() -> None:
    gone = wave(1400, {"at_px": 300, "type": "meteorite", "x": 2000})
    assert run(gone)["placement"] == "FAIL"


def test_telegraph_fails_when_the_scaled_charge_is_under_the_minimum(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "tuning"
    shutil.copytree(GAME_TUNING, folder)
    path = folder / "drifters" / "chain_lightning.json"
    values = json.loads(path.read_text())
    values["charge_ticks"] = 50  # x 0.70 at level 8 = 35, under 45
    path.write_text(json.dumps(values))
    original = tuning_module.TUNING_DIR
    tuning_module.TUNING_DIR = folder
    try:
        chain = wave(
            1400,
            {"at_px": 300, "type": "chain_lightning", "x": 300, "variant": "pair_flat"},
        )
        messages = findings(chain, "telegraph")
        assert len(messages) == 1
        assert "35 ticks" in messages[0]
        assert findings(chain, "telegraph", level=1) == []
    finally:
        tuning_module.TUNING_DIR = original


def test_the_real_chain_lightning_charge_passes_at_level_8() -> None:
    chain = wave(1400, {"at_px": 300, "type": "chain_lightning", "x": 300})
    assert run(chain)["telegraph"] == "PASS"


# ---- config, passes, command line ---------------------------------------------------------


def test_config_rejects_a_bad_level(tmp_path: Path) -> None:
    bad = tmp_path / "config.json"
    bad.write_text(json.dumps({"levels": [9]}))
    with pytest.raises(ValueError, match="levels"):
        load_config(bad)


def test_the_shipped_config_loads_and_tests_level_8() -> None:
    assert load_config().levels == (8,)


def test_fingerprint_changes_with_the_wave_and_with_the_tuning(tmp_path: Path) -> None:
    config = Config()
    base = store.fingerprint(GOOD, config)
    assert store.fingerprint(json.loads(json.dumps(GOOD)), config) == base
    other = json.loads(json.dumps(GOOD))
    other["placements"][0]["x"] = 301
    assert store.fingerprint(other, config) != base
    folder = tmp_path / "tuning"
    shutil.copytree(GAME_TUNING, folder)
    path = folder / "drifters" / "meteorite.json"
    values = json.loads(path.read_text())
    values["speed_ratio"] += 0.01
    path.write_text(json.dumps(values))
    original = tuning_module.TUNING_DIR
    tuning_module.TUNING_DIR = folder
    try:
        assert store.fingerprint(GOOD, config) != base
    finally:
        tuning_module.TUNING_DIR = original


def test_passes_are_remembered_dropped_and_ignored_across_suites(
    tmp_path: Path,
) -> None:
    file = tmp_path / "passes.json"
    passes: dict[str, str] = {}
    store.remember(passes, "a", 8, "abc", ok=True)
    store.write(passes, file)
    assert store.is_fresh(store.read(file), "a", 8, "abc")
    assert not store.is_fresh(store.read(file), "a", 8, "changed")
    store.remember(passes, "a", 8, "abc", ok=False)
    assert "a@8" not in passes
    file.write_text(json.dumps({"suite": "other", "passes": {"a@8": "abc"}}))
    assert store.read(file) == {}


def test_command_line_exit_codes_and_pass_skipping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(store, "STORE_FILE", tmp_path / "passes.json")
    good = tmp_path / "good_wave.json"
    good.write_text(json.dumps(GOOD))
    bad = tmp_path / "bad_wave.json"
    bad.write_text(
        json.dumps(wave(450, {"at_px": 300, "type": "coin", "x": 300, "y": 200}))
    )
    assert wave_check.main(["--wave", str(good)]) == 0
    assert wave_check.main(["--wave", str(bad)]) == 1
    out = capsys.readouterr().out
    assert "FAIL every coin near a hazard" in out
    assert "no hazard is on screen" in out
    assert wave_check.main(["--wave", str(tmp_path / "nope.json")]) == 2
    data = json.loads((tmp_path / "passes.json").read_text())
    assert list(data["passes"]) == ["good_wave@8"]


def test_the_loader_refusing_a_wave_is_a_failure(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps({"length_px": 100}))
    assert wave_check.main(["--wave", str(broken), "--no-record"]) == 1


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def waves_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway git repo with game/waves/{a,b}.json committed, standing in for the real one."""
    folder = tmp_path / "game" / "waves"
    folder.mkdir(parents=True)
    for name in ("a", "b"):
        (folder / f"{name}.json").write_text(json.dumps(GOOD))
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "start")
    monkeypatch.setattr(wave_check, "ROOT", tmp_path.resolve())
    monkeypatch.setattr(wave_check, "WAVES_DIR", folder)
    monkeypatch.setattr(store, "STORE_FILE", tmp_path / "passes.json")
    return tmp_path


def test_changed_checks_nothing_when_no_wave_changed(
    waves_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert wave_check.main(["--changed"]) == 0
    assert "no wave changed" in capsys.readouterr().out


def test_changed_checks_only_the_waves_git_sees_as_changed_or_new(
    waves_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = waves_repo / "game" / "waves"
    (folder / "a.json").write_text(
        json.dumps(wave(450, {"at_px": 300, "type": "coin", "x": 300, "y": 200}))
    )
    (folder / "c.json").write_text(json.dumps(GOOD))
    assert wave_check.main(["--changed", "--no-record"]) == 1
    out = capsys.readouterr().out
    assert "wave a  " in out and "wave c  " in out
    assert "wave b" not in out


def test_changed_with_base_reads_what_changed_since_that_ref(
    waves_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = waves_repo / "game" / "waves"
    (folder / "b.json").write_text(
        json.dumps(wave(450, {"at_px": 300, "type": "coin", "x": 300, "y": 200}))
    )
    _git(waves_repo, "commit", "-q", "-am", "change b")
    assert wave_check.main(["--changed"]) == 0  # the working tree is clean
    assert wave_check.main(["--changed", "--base", "HEAD~1", "--no-record"]) == 1
    out = capsys.readouterr().out
    assert "wave b  " in out and "wave a" not in out


def test_changed_fails_loudly_when_git_cannot_answer(waves_repo: Path) -> None:
    assert wave_check.main(["--changed", "--base", "no-such-ref"]) == 2
    assert wave_check.main(["--base", "HEAD", "--all"]) == 2
