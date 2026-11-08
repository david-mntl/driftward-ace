"""Tests for the bench's replay after an edit and the at-spot search. Synthetic waves, so a change
to the real waves never breaks them."""

import functools
import logging
from collections.abc import Callable
from typing import Any

import bench as bench_module
import pytest
from bench import SNAPSHOT_TICKS, Bench
from core.drifters.base import DrifterType
from core.drifters.spawner import Placement
from core.scroll import scroll_speed
from core.ship import SPAWN_Y, Ship, Thrust
from doc import Doc
from place import ScanPool, _chunks, _closer, _path, _scan_values

logging.disable(logging.CRITICAL)

PLAYHEAD_TICKS = 150


def make_bench() -> Bench:
    """A fly-mode bench on a wave of meteorites and a fireball, played to PLAYHEAD_TICKS with
    some steering, so a replay has real inputs to repeat."""
    placements: list[dict[str, Any]] = [
        {"at_px": 130 + 20 * i, "type": "meteorite", "x": 40 + 45 * i}
        for i in range(12)
    ]
    placements.append({"at_px": 400, "type": "fireball", "x": 300})
    bench = Bench(Doc({"length_px": 900, "kind": "fixed", "placements": placements}))
    bench.ghost = False
    bench.restart()
    for tick in range(PLAYHEAD_TICKS):
        bench.step(Thrust(up=tick % 7 < 3, left=tick % 11 < 4, right=tick % 13 > 9))
    return bench


def ticks_played(bench: Bench, edit: Callable[[Doc], None]) -> int:
    """Make `edit`, return how many ticks the replay simulated."""
    played: list[int] = []
    real = bench._tick

    def counting(run: Any, thrust: Thrust) -> Any:
        played.append(1)
        return real(run, thrust)

    bench._tick = counting  # type: ignore[method-assign]
    try:
        assert bench.edit(edit)
    finally:
        del bench._tick
    return len(played)


def add_meteorite(at_px: int) -> Callable[[Doc], None]:
    def change(doc: Doc) -> None:
        assert doc.wave is not None
        doc.wave["placements"].append({"at_px": at_px, "type": "meteorite", "x": 200})
        doc.sort()

    return change


EDITS: dict[str, Callable[[Doc], None]] = {
    "add late": add_meteorite(600),
    "add at the playhead": add_meteorite(200),
    "add before the playhead": add_meteorite(135),
    "delete first": lambda doc: doc.wave["placements"].pop(0),  # type: ignore[index]
    "move one": lambda doc: doc.wave["placements"][3].update(at_px=700),  # type: ignore[index]
    "tune meteorite": lambda doc: doc.set_value("meteorite", ("speed_ratio",), 0.9),
    "tune fireball": lambda doc: doc.set_value("fireball", ("speed_ratio",), 0.9),
    "graze margin": lambda doc: doc.set_hazard("graze_margin", 20),
    "wave length": lambda doc: doc.wave.update(length_px=800),  # type: ignore[union-attr]
}


@pytest.mark.parametrize("name", EDITS)
def test_replay_after_an_edit_is_the_same_as_replaying_from_tick_0(name: str) -> None:
    bench = make_bench()
    pos = bench.pos
    assert bench.edit(EDITS[name])
    resumed, resumed_pos = bench.run, bench.pos
    bench.replay_to(pos)  # no snapshot allowed: from tick 0
    assert (resumed_pos, resumed) == (bench.pos, bench.run)


def test_an_edit_late_in_the_wave_replays_nothing_before_it() -> None:
    assert ticks_played(make_bench(), add_meteorite(600)) == 0


def test_an_edit_at_the_playhead_replays_at_most_one_snapshot_gap() -> None:
    assert ticks_played(make_bench(), add_meteorite(200)) <= SNAPSHOT_TICKS


def test_a_value_of_a_type_not_yet_spawned_replays_nothing() -> None:
    # The fireball first spawns at 400 px, after the playhead.
    assert ticks_played(make_bench(), EDITS["tune fireball"]) == 0


def test_a_value_of_a_spawned_type_replays_from_its_first_placement() -> None:
    played = ticks_played(make_bench(), EDITS["tune meteorite"])
    assert 0 < played <= PLAYHEAD_TICKS


def test_a_shared_value_replays_from_the_first_placement() -> None:
    # The graze margin reaches every drifter, so any placement may differ: from the first one.
    played = ticks_played(make_bench(), EDITS["graze margin"])
    assert 0 < played < PLAYHEAD_TICKS


def test_a_change_to_the_wave_itself_starts_over() -> None:
    assert ticks_played(make_bench(), EDITS["wave length"]) == PLAYHEAD_TICKS


def test_a_refused_edit_changes_nothing() -> None:
    bench = make_bench()
    before, pos = bench.run, bench.pos
    assert not bench.edit(
        lambda doc: doc.wave["placements"].append({"type": "nonsense"})
    )  # type: ignore[index]
    assert (bench.run, bench.pos) == (before, pos)
    assert bench.error


def test_every_edit_changes_the_revision() -> None:
    bench = make_bench()
    revision = bench.revision
    bench.edit(add_meteorite(600))
    assert bench.revision > revision


def test_the_preview_of_a_flown_ship_is_not_redone() -> None:
    bench = make_bench()
    first = bench.preview_path(0)
    for _ in range(5):
        bench.step(Thrust(left=True))
    assert bench.preview_path(0) is first


# ---- the at-spot search ---------------------------------------------------------------------


def ufo() -> tuple[Placement, Any]:
    return (
        Placement(drifter_type=DrifterType.UFO, variant=None, seed=5),
        bench_module.load_tuning(),
    )


def test_a_path_cut_short_is_the_start_of_the_full_path() -> None:
    what, tuning = ufo()
    ship = Ship(x=320.0, y=SPAWN_Y, vx=0.0, vy=0.0)
    from dataclasses import replace

    placed = replace(what, y=200)
    full = _path(placed, 4, tuning, ship)
    assert _path(placed, 4, tuning, ship, 120) == full[:121]


def test_chunks_cover_every_value_once_in_order() -> None:
    values = range(481)
    assert [v for chunk in _chunks(values) for v in chunk] == list(values)


def test_on_a_tie_the_lower_coordinate_wins() -> None:
    assert _closer((5.0, 3, 10), (5.0, 1, 90)) == (5.0, 3, 10)
    assert _closer((5.0, 3, 10), (4.0, 1, 90)) == (4.0, 1, 90)
    assert _closer(None, (4.0, 1, 90)) == (4.0, 1, 90)
    assert _closer((5.0, 3, 10), None) == (5.0, 3, 10)


def test_the_process_pool_finds_what_the_serial_search_finds() -> None:
    what, tuning = ufo()
    ship = Ship(x=320.0, y=SPAWN_Y, vx=0.0, vy=0.0)
    scan = functools.partial(
        _scan_values, what, "y", (228.0, 300.0), 200, 4, tuning, ship
    )
    values = range(150, 190)
    serial = scan(values)
    pool = ScanPool(workers=2)
    try:
        assert pool.nearest(scan, values) == serial
        assert not pool._broken
    finally:
        pool.close()


# ---- the coin from the top ------------------------------------------------------------------


def coin_editor() -> Any:
    """An editor on an empty wave with the playhead at 4 s, a coin armed, at spot on."""
    import editor as editor_module

    bench = Bench(Doc({"length_px": 900, "kind": "fixed", "placements": []}))
    bench.level = 3
    bench.restart()
    for _ in range(240):
        bench.step()
    ed = editor_module.Editor(bench)
    ed.at_spot = True
    ed.armed = ("coin", None)
    return ed


def wait_for_search(ed: Any) -> None:
    import time

    deadline = time.time() + 20
    while ed.job is not None and time.time() < deadline:
        ed.poll_job()
        time.sleep(0.005)


def test_a_coin_from_the_top_is_placed_by_x_alone_and_is_on_the_spot_at_the_moment() -> (
    None
):
    ed = coin_editor()
    ed.toggle_coin_top()
    clicked_at = ed.bench.tick
    ed.click((100, 240))
    wait_for_search(ed)
    ed.close()
    (item,) = ed.placements()
    assert item["type"] == "coin" and item["x"] == 100 and "y" not in item
    # Far from the ghost ship at x 320, which would collect it. Play the wave again. The coin is on (100, 240) at the tick the spot was clicked at.
    bench = ed.bench
    bench.seek(clicked_at)
    coin = next(d for d in bench.run.drifters if d.drifter_type.value == "coin")
    assert abs(coin.x - 100) <= 1
    assert abs(coin.y - 240) <= scroll_speed(bench.level) / 2 + 1
    # It came in from the top: its first tick on the field is above the screen, and it only
    # ever moves down.
    ys: list[float] = []
    for tick in range(clicked_at + 1):
        bench.seek(tick)
        ys += [d.y for d in bench.run.drifters if d.drifter_type.value == "coin"]
    assert ys[0] < 0
    assert ys == sorted(ys)


def test_a_coin_without_the_mode_still_appears_where_it_is_placed() -> None:
    ed = coin_editor()
    ed.click((300, 240))
    wait_for_search(ed)
    ed.close()
    (item,) = ed.placements()
    assert item["x"] == 300 and item["y"] == 240


def test_the_coin_mode_changes_nothing_for_other_drifters() -> None:
    ed = coin_editor()
    ed.toggle_coin_top()
    assert not ed.from_top("meteorite")
    assert ed.from_top("coin")
    ed.close()


def test_a_coin_from_the_top_without_at_spot_enters_at_the_playhead_by_x_alone() -> (
    None
):
    ed = coin_editor()
    ed.at_spot = False
    ed.toggle_coin_top()
    ed.click((300, 240))
    ed.close()
    (item,) = ed.placements()
    assert "y" not in item and item["x"] == 300
