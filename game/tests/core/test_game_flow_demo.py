"""Game flow tests for the demo flight: the first Play shows it, a confirm skips it, it ends in the
run, and it shows once per page load.

Spec: 02-game-flow.md, rule 5a; docs/contracts/systems/game-flow.md and systems/demo.md.
"""

from dataclasses import replace

from app.demo_tuning import load_demo
from app.screens_tuning import load_screen_rules
from app.tuning import load_tuning
from core.demo import Demo, DemoRules, DemoStep, start_demo
from core.drifters.base import DrifterType
from core.game_flow import GameFlow, Screen, TickInput, start_flow, step_flow
from core.run import Run, start_run
from core.ship import Thrust

_shipped: DemoRules | None = load_demo(load_tuning(), load_screen_rules())[0]
assert _shipped is not None
SHIPPED: DemoRules = _shipped
"""The shipped tuning/demo.json, for its autopilot and glow values."""

RULES: DemoRules = DemoRules(
    steps=(
        DemoStep(keys=Thrust(up=True), ticks=6, caption="HOLD"),
        DemoStep(keys=Thrust(up=True, right=True), ticks=6, caption="STEER"),
    ),
    coin_step=1,
    coin_type=DrifterType.COIN,
    coin_variant="common",
    fade_out_ticks=2,
    pilot=SHIPPED.pilot,
    key_fade_ticks=SHIPPED.key_fade_ticks,
)

NOTHING = TickInput()
CONFIRM = TickInput(confirm=True)


def _demo() -> Demo:
    return start_demo(RULES, load_tuning())


def _menu(demo: Demo | None) -> GameFlow:
    """The flow on the menu with every key released, PLAY selected."""
    return step_flow(start_flow(start_run(), None, demo), NOTHING)


def _press_play(flow: GameFlow) -> GameFlow:
    return step_flow(flow, CONFIRM)


def test_the_first_play_shows_the_demo_and_the_run_waits() -> None:
    flow = _press_play(_menu(_demo()))
    assert flow.screen is Screen.DEMO
    run: Run = flow.run
    flow = step_flow(flow, CONFIRM)
    flow = step_flow(flow, NOTHING)
    assert flow.screen is Screen.DEMO
    assert flow.demo is not None
    assert flow.demo.tick == 2
    assert flow.run is run
    assert not flow.run_stepped


def test_the_demo_ignores_the_players_arrows() -> None:
    flow = step_flow(_press_play(_menu(_demo())), NOTHING)
    held = step_flow(flow, TickInput(thrust=Thrust(left=True, down=True)))
    plain = step_flow(flow, NOTHING)
    assert held.demo == plain.demo


def test_a_fresh_confirm_skips_the_demo_into_the_run() -> None:
    flow = step_flow(_press_play(_menu(_demo())), NOTHING)
    flow = step_flow(flow, CONFIRM)
    assert flow.screen is Screen.PLAYING
    assert flow.demo is None


def test_the_demo_runs_out_into_the_run() -> None:
    flow = _press_play(_menu(_demo()))
    ticks: int = 0
    while flow.screen is Screen.DEMO:
        flow = step_flow(flow, NOTHING)
        ticks += 1
        assert ticks <= 12 + 1
    assert ticks == 12 + 1
    assert flow.screen is Screen.PLAYING
    assert flow.demo is None


def test_after_the_demo_the_next_play_starts_the_run_at_once() -> None:
    flow = step_flow(_press_play(_menu(_demo())), NOTHING)
    flow = step_flow(flow, CONFIRM)
    over: GameFlow = replace(flow, screen=Screen.MENU, run=replace(flow.run, game_over=True))
    flow = step_flow(step_flow(over, NOTHING), CONFIRM)
    assert flow.screen is Screen.PLAYING


def test_without_a_demo_play_starts_the_run_at_once() -> None:
    flow = _press_play(_menu(None))
    assert flow.screen is Screen.PLAYING
