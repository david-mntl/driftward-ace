"""Demo flight tests: the script, the autopilot, the coin placed on the ship's path, the pickup,
the keys' glow and the fade.

Spec: docs/contracts/systems/demo.md; 02-game-flow.md, rule 5a. The ship's path is the real
`core.ship.step`, flown here to say where the ship must be. The coin and its points are the real
coin tuning (`app.tuning.load_tuning`). The autopilot values are the shipped tuning/demo.json's.
"""

from dataclasses import replace

import pytest

from app.tuning import load_tuning
from core.demo import (
    Demo,
    DemoRules,
    DemoStep,
    PilotRules,
    autopilot,
    check_demo_rules,
    start_demo,
    step_demo,
)
from core.drifters.base import DrifterType
from core.drifters.tuning import DrifterTuning
from core.ship import Ship, Thrust, spawn, step
from core.sound_cue import SoundCue

TUNING: DrifterTuning = load_tuning()

UP = Thrust(up=True)
UP_RIGHT = Thrust(up=True, right=True)

PILOT: PilotRules = PilotRules(gain=0.06, max_speed=3.0, band=0.35, near_px=6, near_speed=0.8)
"""The shipped autopilot values, tuning/demo.json `pilot`."""

KEY_FADE: int = 5
"""Ticks a key's glow takes to fill: tuning/demo.json `look.key_fade_ticks`."""

CENTER: tuple[float, float] = (320.0, 240.0)

RULES: DemoRules = DemoRules(
    steps=(
        DemoStep(keys=Thrust(), ticks=10, caption="HOLD", stand=True),
        DemoStep(keys=UP, ticks=12, caption=None),
        DemoStep(keys=Thrust(), ticks=40, caption="LET GO"),
        DemoStep(keys=UP_RIGHT, ticks=30, caption="STEER"),
        DemoStep(keys=Thrust(), ticks=20, caption="POINTS"),
    ),
    coin_step=3,
    coin_type=DrifterType.COIN,
    coin_variant="common",
    fade_out_ticks=8,
    pilot=PILOT,
    key_fade_ticks=KEY_FADE,
)
TOTAL: int = 112


def _fly(rules: DemoRules, ticks: int) -> Ship:
    """The ship after `ticks` demo ticks, flown here with the real step."""
    ship: Ship = spawn()
    played: int = 0
    for demo_step in rules.steps:
        for _ in range(demo_step.ticks):
            if played == ticks:
                return ship
            if not demo_step.stand:
                ship = step(ship, demo_step.keys)
            played += 1
    return ship


def _play(demo: Demo, ticks: int) -> Demo:
    for _ in range(ticks):
        demo = step_demo(demo)
    return demo


def test_the_demo_starts_at_spawn_with_the_coin_where_the_ship_ends_the_coin_step() -> None:
    demo = start_demo(RULES, TUNING)
    assert demo.ship == spawn()
    assert demo.tick == 0
    assert demo.coin is not None
    end_of_coin_step: Ship = _fly(RULES, 10 + 12 + 40 + 30)
    assert (demo.coin.x, demo.coin.y) == pytest.approx((end_of_coin_step.x, end_of_coin_step.y))


def test_the_ship_follows_the_script_and_stands_through_a_standing_step() -> None:
    demo = start_demo(RULES, TUNING)
    for tick in range(TOTAL):
        demo = step_demo(demo)
        if demo.coin is not None:
            assert demo.ship == _fly(RULES, tick + 1)
    standing = _play(start_demo(RULES, TUNING), 10)
    assert standing.ship == spawn()


def test_held_keys_and_captions_follow_the_steps_and_a_null_caption_keeps_the_last() -> None:
    demo = start_demo(RULES, TUNING)
    assert (demo.held, demo.stood, demo.caption) == (Thrust(), True, "HOLD")
    demo = _play(demo, 11)
    assert (demo.held, demo.stood, demo.caption) == (UP, False, "HOLD")
    demo = _play(demo, 12)
    assert (demo.held, demo.caption) == (Thrust(), "LET GO")
    demo = _play(demo, 40)
    assert (demo.held, demo.caption) == (UP_RIGHT, "STEER")
    demo = _play(demo, 30)
    assert (demo.held, demo.caption) == (Thrust(), "POINTS")


def test_a_keys_glow_fills_over_the_fade_ticks_and_drains_the_same_way() -> None:
    demo = _play(start_demo(RULES, TUNING), 10)
    assert demo.glow == (0.0, 0.0, 0.0, 0.0)
    for tick in range(1, KEY_FADE + 2):
        demo = step_demo(demo)
        assert demo.glow[0] == pytest.approx(min(tick / KEY_FADE, 1.0))
        assert demo.glow[1:] == (0.0, 0.0, 0.0)
    demo = _play(demo, 12 - KEY_FADE - 1)
    for tick in range(1, KEY_FADE + 1):
        demo = step_demo(demo)
        assert demo.glow[0] == pytest.approx(max(1.0 - tick / KEY_FADE, 0.0))


def _pilot_rules(start_keys: Thrust, start_ticks: int, hover_ticks: int) -> DemoRules:
    return replace(
        RULES,
        steps=(
            DemoStep(keys=start_keys, ticks=start_ticks, caption="GO"),
            DemoStep(keys=Thrust(), ticks=hover_ticks, caption="HOVER", pilot_to=CENTER),
        ),
        coin_step=0,
    )


@pytest.mark.parametrize(
    ("keys", "ticks"),
    [(Thrust(), 50), (UP, 20), (UP_RIGHT, 20), (Thrust(left=True), 25)],
    ids=["falling", "climbing", "up and right", "sliding left"],
)
def test_the_autopilot_flies_back_to_its_spot_and_hovers_there(keys: Thrust, ticks: int) -> None:
    demo = _play(start_demo(_pilot_rules(keys, ticks, 240), TUNING), ticks)
    for _ in range(240):
        before: Ship = demo.ship
        demo = step_demo(demo)
        assert demo.ship == step(before, demo.held), "the autopilot only presses real arrows"
        assert not demo.ship.at_top_line
        assert demo.ship.wall is None
    assert demo.ship.x == pytest.approx(CENTER[0], abs=6)
    assert demo.ship.y == pytest.approx(CENTER[1], abs=4)
    assert abs(demo.ship.vy) < 1.0
    assert abs(demo.ship.vx) < 1.0


def test_hovering_taps_up_and_never_holds_it_down() -> None:
    demo = _play(start_demo(_pilot_rules(Thrust(), 1, 300), TUNING), 160)
    ups: list[bool] = []
    sides: list[bool] = []
    for _ in range(120):
        demo = step_demo(demo)
        ups.append(demo.held.up)
        sides.append(demo.held.left or demo.held.right)
    assert any(ups)
    assert not all(ups)
    assert not any(sides)


def test_the_autopilot_waits_out_a_small_drift_sideways() -> None:
    near: Ship = Ship(x=CENTER[0] + 3, y=CENTER[1], vx=0.2, vy=0.0)
    keys = autopilot(near, CENTER, Thrust(), PILOT)
    assert not keys.left
    assert not keys.right


def test_the_ship_collects_the_coin_once_in_the_coin_step_with_its_points_popup_and_sound() -> None:
    demo = start_demo(RULES, TUNING)
    assert demo.coin is not None
    coin_points: int = demo.coin.collect_points()
    coin_at: tuple[float, float] = (demo.coin.x, demo.coin.y)
    collected: list[int] = []
    for _ in range(TOTAL):
        demo = step_demo(demo)
        if demo.sound_cues:
            assert demo.sound_cues == (SoundCue.COIN,)
            collected.append(demo.tick)
            assert demo.coin is None
            assert len(demo.popups) == 1
            assert (demo.popups[0].x, demo.popups[0].start_y) == pytest.approx(coin_at)
    assert len(collected) == 1
    assert 10 + 12 + 40 < collected[0] <= 10 + 12 + 40 + 30
    assert demo.points == coin_points == 50


def test_the_coin_stays_put_until_collected() -> None:
    demo = start_demo(RULES, TUNING)
    assert demo.coin is not None
    where = (demo.coin.x, demo.coin.y)
    demo = _play(demo, 40)
    assert demo.coin is not None
    assert (demo.coin.x, demo.coin.y) == where


def test_the_demo_is_done_after_every_step_and_then_stops() -> None:
    demo = _play(start_demo(RULES, TUNING), TOTAL - 1)
    assert not demo.done
    demo = step_demo(demo)
    assert demo.done
    assert demo.total_ticks == TOTAL
    assert step_demo(demo) is demo
    assert demo.held == Thrust()


def test_the_fade_stays_clear_until_the_last_fade_ticks_then_reaches_black() -> None:
    demo = start_demo(RULES, TUNING)
    for tick in range(TOTAL + 1):
        expected: float = max(0.0, 1.0 - (TOTAL - tick) / 8)
        assert demo.fade == pytest.approx(expected)
        demo = step_demo(demo)
    assert demo.fade == 1.0


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"steps": ()}, "no steps"),
        ({"coin_step": 5}, "coin_step 5"),
        ({"coin_step": -1}, "coin_step -1"),
        ({"fade_out_ticks": -1}, "fade_out_ticks"),
        ({"key_fade_ticks": 0}, "key_fade_ticks"),
    ],
)
def test_a_script_that_cannot_play_is_refused(change: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        check_demo_rules(replace(RULES, **change))  # type: ignore[arg-type]  # test-only values


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (DemoStep(keys=UP, ticks=5, caption=None, stand=True), "stands"),
        (DemoStep(keys=Thrust(), ticks=5, caption=None, stand=True, pilot_to=CENTER), "stands"),
        (DemoStep(keys=UP, ticks=5, caption=None, pilot_to=CENTER), "holds keys and flies"),
    ],
)
def test_a_step_that_does_two_things_at_once_is_refused(bad: DemoStep, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        check_demo_rules(replace(RULES, steps=(*RULES.steps, bad)))


def test_a_step_under_one_tick_is_refused() -> None:
    steps = (*RULES.steps[:4], replace(RULES.steps[4], ticks=0))
    with pytest.raises(ValueError, match="step 4"):
        check_demo_rules(replace(RULES, steps=steps))


def test_a_coin_type_that_is_not_a_pickup_is_refused() -> None:
    rock: str = TUNING.drifters[DrifterType.METEORITE].default_variant
    rules = replace(RULES, coin_type=DrifterType.METEORITE, coin_variant=rock)
    with pytest.raises(ValueError, match="not a pickup"):
        start_demo(rules, TUNING)
