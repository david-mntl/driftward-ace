"""The game flow: the screens around a run, the fresh presses, the pause and the game-over choices.

Contract: docs/contracts/systems/game-flow.md, Diagram (the state diagram, the tick flowchart, the
two tables), Interface (`core/game_flow.py`), Rules (Presses, Start, MENU, INSTRUCTIONS and
LEADERBOARD, PLAYING, PAUSED, GAME_OVER, `run_stepped`, `add_flow_drifters`, Pure, Logging).
Task: docs/contracts/DRA-125/tasks/DRA-125-10-qa-engineer.md. One test per behavior it lists.
The run is built with `start_run`; the last life is reached with a ship that falls past the floor on
its next step, at one life, with a short `LastLifeRules` delay. No expected number is imported from
the code under test; the physics values below come from the GDD.
"""

import copy
import logging
from collections.abc import Sequence
from dataclasses import replace
from itertools import product

import pytest

from core.collision import Circle
from core.drifters.base import DrifterType
from core.drifters.spawner import Placement
from core.drifters.tuning import (
    DrifterTuning,
    DrifterTypeTuning,
    PlaytestSwitches,
    VariantTuning,
)
from core.game_flow import (
    GAME_OVER_START_SELECTION,
    MENU_START_SELECTION,
    GameFlow,
    GameOverChoice,
    MenuItem,
    Screen,
    TickInput,
    add_flow_drifters,
    start_flow,
    step_flow,
)
from core.last_life import LastLifeRules
from core.run import Run, add_drifters, next_run, start_run, step_run
from core.ship import Ship, Thrust, spawn
from core.waves import (
    LevelPlaylist,
    Wave,
    WaveBook,
    WaveKind,
    WaveRun,
    start_waves,
)

SCREEN_H: int = 480
"""px. Source: 03-world-and-camera.md, Values, screen_h (guess)."""

SHIP_H: int = 32
"""px. Source: 04-ship.md, Values, ship_h (guess)."""

FALL_CAP: float = 5.5
"""px/tick. Source: 04-ship.md, Values, fall_cap (guess)."""

AT_FLOOR_Y: float = SCREEN_H + SHIP_H / 2 - FALL_CAP
"""A ship at fall_cap here moves exactly FALL_CAP next tick and its top edge lands on the floor."""

FALLING_SHIP: Ship = Ship(x=200.0, y=AT_FLOOR_Y, vx=0.0, vy=FALL_CAP)

LEVEL_COUNT: int = 8
"""Source: 08-difficulty.md, rule 1."""

SEED: int = 20261019
"""A first seed for the runs with waves."""

LAST_LIFE_DELAY: int = 3
"""A short delay so a test reaches game over quickly. The code takes any value from 1 up."""

FLOW_LOGGER: str = "core.game_flow"
RUN_LOGGER: str = "core.run"
WAVES_LOGGER: str = "core.waves"
"""Source: systems/game-flow.md, Logging; systems/run.md, Logging; systems/waves.md, Logging."""

NO_KEY = Thrust()
UP = Thrust(up=True)
DOWN = Thrust(down=True)
LEFT = Thrust(left=True)
RIGHT = Thrust(right=True)
ALL_KEYS: tuple[Thrust, ...] = tuple(
    Thrust(up=u, down=d, left=lf, right=r) for u, d, lf, r in product((False, True), repeat=4)
)
"""Every combination of the four arrows."""

IDLE = TickInput()
CONFIRM = TickInput(confirm=True)
FOCUS_LOST = TickInput(focus_lost=True)

MENU_ORDER: tuple[MenuItem, ...] = (MenuItem.PLAY, MenuItem.INSTRUCTIONS, MenuItem.LEADERBOARD)
"""Source: 02-game-flow.md, menu_items (locked): Play, Instructions, Leaderboard, top first."""

CHOICE_ORDER: tuple[GameOverChoice, ...] = (GameOverChoice.RETRY, GameOverChoice.MENU)
"""Source: 02-game-flow.md, game_over_choices (locked): RETRY first."""


def make_tuning() -> DrifterTuning:
    """The medium meteorite, from the GDD values (drifters/01-meteorite.md, 07-drifters.md)."""
    return DrifterTuning(
        drifters={
            DrifterType.METEORITE: DrifterTypeTuning(
                variants={
                    "medium": VariantTuning(
                        width=28.0, height=28.0, hitbox=(Circle(0.0, 0.0, 14.0),)
                    )
                },
                default_variant="medium",
                speed_ratio=0.375,
                entry_warning_ticks=60,
            ),
        },
        switches=PlaytestSwitches(),
    )


TUNING: DrifterTuning = make_tuning()
PLACEMENTS: tuple[Placement, ...] = (Placement(DrifterType.METEORITE, x=100.0, y=-20.0),)


def wave(wave_id: str, length: float) -> Wave:
    """A fixed wave with no placements."""
    return Wave(
        wave_id=wave_id,
        length_px=length,
        kind=WaveKind.FIXED,
        min_level=None,
        placements=(),
    )


def book() -> WaveBook:
    """Wave 0, then `a` at Level 1 and `long` at Levels 2 to 8."""
    waves: list[Wave] = [wave("w0", 11.0), wave("a", 11.0), wave("long", 10_000.0)]
    playlists: tuple[LevelPlaylist, ...] = (
        LevelPlaylist(fixed=("a",)),
        *(LevelPlaylist(fixed=("long",)) for _ in range(2, LEVEL_COUNT + 1)),
    )
    return WaveBook(
        waves={item.wave_id: item for item in waves}, wave_zero_id="w0", playlists=playlists
    )


BOOK: WaveBook = book()

RUN: Run = start_run()


def advanced(run: Run, ticks: int, thrust: Thrust = NO_KEY) -> Run:
    """The run after `ticks` steps, so the ship has a speed."""
    for _ in range(ticks):
        run = step_run(run, thrust)
    return run


MOVING: Run = advanced(RUN, 10)
"""A run that has flown 10 ticks: the ship falls, so a frozen run is easy to tell."""


def flow_on(
    screen: Screen,
    run: Run | None = None,
    *,
    menu: MenuItem = MENU_START_SELECTION,
    choice: GameOverChoice = GAME_OVER_START_SELECTION,
    confirm_held: bool = False,
    arrows: Thrust = NO_KEY,
) -> GameFlow:
    """A flow on `screen` with no key held, unless told."""
    base: GameFlow = start_flow(RUN if run is None else run)
    return replace(
        base,
        screen=screen,
        menu_selection=menu,
        game_over_selection=choice,
        confirm_held=confirm_held,
        arrows_held=arrows,
    )


def last_life_run(*, waves: WaveRun | None = None) -> Run:
    """A one-life run whose ship falls past the floor next step: that tick starts the last life."""
    rules: LastLifeRules = LastLifeRules(delay_ticks=LAST_LIFE_DELAY)
    return replace(
        start_run(waves, last_life_rules=rules),
        ship=FALLING_SHIP,
        lives=1,
    )


def to_game_over(flow: GameFlow, keys: TickInput = IDLE) -> GameFlow:
    """Step `flow` with `keys` until the screen is GAME_OVER, and return that flow."""
    for _ in range(LAST_LIFE_DELAY + 5):
        assert flow.screen is Screen.PLAYING
        flow = step_flow(flow, keys)
        if flow.screen is Screen.GAME_OVER:
            return flow
    raise AssertionError("the run never reached game over")


def over_flow(
    *,
    waves: WaveRun | None = None,
    choice: GameOverChoice = GAME_OVER_START_SELECTION,
    menu: MenuItem = MENU_START_SELECTION,
) -> GameFlow:
    """The flow on the game-over screen after a real last life, no key held."""
    start: GameFlow = flow_on(Screen.PLAYING, last_life_run(waves=waves), menu=menu, choice=choice)
    return to_game_over(start)


def after(flow: GameFlow, *ticks: TickInput) -> GameFlow:
    """The flow after each of `ticks`, in order."""
    for keys in ticks:
        flow = step_flow(flow, keys)
    return flow


def move(selection: MenuItem | GameOverChoice, by: int) -> MenuItem | GameOverChoice:
    """The member `by` places down the selection's order, wrapping around."""
    order: Sequence[MenuItem | GameOverChoice] = (
        MENU_ORDER if isinstance(selection, MenuItem) else CHOICE_ORDER
    )
    return order[(order.index(selection) + by) % len(order)]


def lines_after(
    caplog: pytest.LogCaptureFixture, flow: GameFlow, keys: TickInput
) -> tuple[GameFlow, list[tuple[str, str]]]:
    """Step once and return the flow and the (logger, message) lines that step wrote, in order."""
    caplog.clear()
    out: GameFlow = step_flow(flow, keys)
    return out, [(r.name, r.getMessage()) for r in caplog.records]


def flow_lines(lines: list[tuple[str, str]]) -> list[str]:
    """The messages the flow's own logger wrote."""
    return [message for name, message in lines if name == FLOW_LOGGER]


def test_start_flow_shows_the_menu_and_ignores_keys_held_from_the_start() -> None:
    flow: GameFlow = start_flow(RUN)

    assert flow.screen is Screen.MENU
    assert flow.menu_selection is MenuItem.PLAY
    assert flow.game_over_selection is GameOverChoice.RETRY
    assert flow.run == RUN
    assert flow.confirm_held
    assert flow.arrows_held == Thrust(up=True, down=True, left=True, right=True)
    assert not flow.run_stepped

    # Every key down at the start does nothing, however long it stays down.
    held_all: TickInput = TickInput(
        thrust=Thrust(up=True, down=True, left=True, right=True), confirm=True
    )
    for _ in range(5):
        flow = step_flow(flow, held_all)
        assert flow.screen is Screen.MENU
        assert flow.menu_selection is MenuItem.PLAY

    # Released, then pressed again: it acts.
    released: GameFlow = step_flow(start_flow(RUN), IDLE)
    assert step_flow(released, CONFIRM).screen is Screen.PLAYING
    assert step_flow(released, TickInput(thrust=DOWN)).menu_selection is MenuItem.INSTRUCTIONS
    assert step_flow(released, TickInput(thrust=UP)).menu_selection is MenuItem.LEADERBOARD

    # Each key on its own: a confirm alone, an arrow alone, held through the click.
    confirm_only: GameFlow = start_flow(RUN)
    assert step_flow(confirm_only, CONFIRM).screen is Screen.MENU
    for thrust in (UP, DOWN):
        arrow_only: GameFlow = step_flow(start_flow(RUN), TickInput(thrust=thrust))
        assert arrow_only.menu_selection is MenuItem.PLAY
        # The arrow is released and pressed again: it moves.
        again: GameFlow = after(arrow_only, IDLE, TickInput(thrust=thrust))
        assert again.menu_selection is not MenuItem.PLAY


@pytest.mark.parametrize("start", MENU_ORDER)
def test_up_and_down_move_the_menu_selection_one_item_per_fresh_press_and_wrap(
    start: MenuItem,
) -> None:
    flow: GameFlow = flow_on(Screen.MENU, menu=start)

    down: GameFlow = step_flow(flow, TickInput(thrust=DOWN))
    up: GameFlow = step_flow(flow, TickInput(thrust=UP))
    assert down.menu_selection is move(start, 1)
    assert up.menu_selection is move(start, -1)
    assert down.screen is up.screen is Screen.MENU

    # Holding moves once, whatever the length.
    held: GameFlow = flow
    for _ in range(20):
        held = step_flow(held, TickInput(thrust=DOWN))
    assert held.menu_selection is move(start, 1)

    # Release and press again: one more item. Three presses go the whole way round.
    round_the_menu: GameFlow = flow
    seen: list[MenuItem] = []
    for _ in range(len(MENU_ORDER)):
        round_the_menu = after(round_the_menu, TickInput(thrust=DOWN), IDLE)
        assert isinstance(round_the_menu.menu_selection, MenuItem)
        seen.append(round_the_menu.menu_selection)
    assert seen == [move(start, 1), move(start, 2), start]
    backwards: GameFlow = flow
    for _ in range(len(MENU_ORDER)):
        backwards = after(backwards, TickInput(thrust=UP), IDLE)
    assert backwards.menu_selection is start

    # Up and down on one tick cancel out.
    cancel: GameFlow = step_flow(flow, TickInput(thrust=Thrust(up=True, down=True)))
    assert cancel.menu_selection is start
    assert cancel.screen is Screen.MENU

    # Left and right do nothing, pressed or held.
    for thrust in (LEFT, RIGHT, Thrust(left=True, right=True)):
        sideways: GameFlow = after(flow, *[TickInput(thrust=thrust)] * 3)
        assert sideways.menu_selection is start
        assert sideways.screen is Screen.MENU

    # Down held, then up pressed on top of it: the fresh up alone moves.
    down_held: GameFlow = step_flow(flow, TickInput(thrust=DOWN))
    both: GameFlow = step_flow(down_held, TickInput(thrust=Thrust(up=True, down=True)))
    assert both.menu_selection is move(move(start, 1), -1)

    # A confirm press picks the selection as it was going into the tick: a down on the same tick
    # does not move it first.
    picked: GameFlow = step_flow(flow, TickInput(confirm=True, thrust=DOWN))
    expected: dict[MenuItem, Screen] = {
        MenuItem.PLAY: Screen.PLAYING,
        MenuItem.INSTRUCTIONS: Screen.INSTRUCTIONS,
        MenuItem.LEADERBOARD: Screen.LEADERBOARD,
    }
    assert picked.screen is expected[start]
    assert picked.menu_selection is start


@pytest.mark.parametrize("page", [MenuItem.INSTRUCTIONS, MenuItem.LEADERBOARD])
def test_a_confirm_opens_a_page_and_a_confirm_there_goes_back_to_the_menu_with_play_selected(
    page: MenuItem,
) -> None:
    screens: dict[MenuItem, Screen] = {
        MenuItem.INSTRUCTIONS: Screen.INSTRUCTIONS,
        MenuItem.LEADERBOARD: Screen.LEADERBOARD,
    }
    menu: GameFlow = flow_on(Screen.MENU, RUN, menu=page)

    opened: GameFlow = step_flow(menu, CONFIRM)
    assert opened.screen is screens[page]
    assert opened.run == RUN
    assert not opened.run_stepped

    # Nothing else acts on a page: any arrow, a focus loss, a held confirm.
    quiet: GameFlow = replace(opened, confirm_held=False)
    for thrust in ALL_KEYS:
        for focus in (False, True):
            out: GameFlow = step_flow(quiet, TickInput(thrust=thrust, focus_lost=focus))
            assert out.screen is screens[page]
            assert out.menu_selection is page
            assert out.run == RUN
    held: GameFlow = quiet
    for _ in range(10):
        held = step_flow(held, TickInput(confirm=True, thrust=DOWN))
        if held.screen is not screens[page]:
            break
    # The confirm was fresh on the first of these ticks: it went back once, and no further.
    assert held.screen is Screen.MENU

    # A fresh confirm goes back to the menu with Play selected, whatever was selected before.
    for before in MENU_ORDER:
        on_page: GameFlow = flow_on(screens[page], RUN, menu=before)
        back: GameFlow = step_flow(on_page, CONFIRM)
        assert back.screen is Screen.MENU
        assert back.menu_selection is MenuItem.PLAY
        assert back.run == RUN
        assert not back.run_stepped

    # A page opened and closed leaves the menu on Play, and the next confirm picks Play.
    closed: GameFlow = after(menu, CONFIRM, IDLE, CONFIRM)
    assert closed.screen is Screen.MENU
    assert closed.menu_selection is MenuItem.PLAY


def held_confirm_does_nothing(after_pick: GameFlow, stays: Screen, then: Screen) -> None:
    """A confirm held on from the pick never acts on `stays`; pressed afresh it goes `then`."""
    assert after_pick.confirm_held
    assert after_pick.screen is stays
    flow: GameFlow = after_pick
    for _ in range(25):
        flow = step_flow(flow, CONFIRM)
        assert flow.screen is stays
        if stays is Screen.MENU:
            assert flow.menu_selection is MenuItem.PLAY
    flow = step_flow(flow, IDLE)
    assert flow.screen is stays
    assert step_flow(flow, CONFIRM).screen is then


@pytest.mark.parametrize(
    "case",
    ["play", "open_page", "close_page", "retry", "game_over_menu", "resume", "through_last_life"],
)
def test_a_confirm_held_across_a_screen_change_never_acts_on_the_new_screen(case: str) -> None:
    if case == "play":
        picked: GameFlow = step_flow(flow_on(Screen.MENU, RUN), CONFIRM)
        held_confirm_does_nothing(picked, Screen.PLAYING, Screen.PAUSED)
    elif case == "open_page":
        picked = step_flow(flow_on(Screen.MENU, RUN, menu=MenuItem.LEADERBOARD), CONFIRM)
        held_confirm_does_nothing(picked, Screen.LEADERBOARD, Screen.MENU)
    elif case == "close_page":
        picked = step_flow(flow_on(Screen.INSTRUCTIONS, RUN), CONFIRM)
        held_confirm_does_nothing(picked, Screen.MENU, Screen.PLAYING)
    elif case == "retry":
        picked = step_flow(over_flow(), CONFIRM)
        held_confirm_does_nothing(picked, Screen.PLAYING, Screen.PAUSED)
    elif case == "game_over_menu":
        picked = step_flow(replace(over_flow(), game_over_selection=GameOverChoice.MENU), CONFIRM)
        held_confirm_does_nothing(picked, Screen.MENU, Screen.PLAYING)
    elif case == "resume":
        picked = step_flow(flow_on(Screen.PAUSED, MOVING), CONFIRM)
        held_confirm_does_nothing(picked, Screen.PLAYING, Screen.PAUSED)
    else:
        # A confirm held on the whole way through the last life never pauses it, and when game
        # over shows it never picks RETRY.
        flow: GameFlow = flow_on(Screen.PLAYING, last_life_run(), confirm_held=True)
        for _ in range(LAST_LIFE_DELAY + 5):
            assert flow.screen is Screen.PLAYING
            flow = step_flow(flow, CONFIRM)
            if flow.screen is Screen.GAME_OVER:
                break
        held_confirm_does_nothing(flow, Screen.GAME_OVER, Screen.PLAYING)


@pytest.mark.parametrize("with_waves", [False, True])
def test_play_starts_the_apps_run_untouched_and_after_a_game_over_it_starts_next_run(
    with_waves: bool,
) -> None:
    waves: WaveRun | None = start_waves(BOOK, SEED) if with_waves else None
    first: Run = start_run(waves)
    menu: GameFlow = step_flow(start_flow(first), IDLE)

    pick: GameFlow = step_flow(menu, CONFIRM)
    assert pick.screen is Screen.PLAYING
    assert pick.run == first, "the app's first run is not replaced"
    assert not pick.run_stepped

    stepped: GameFlow = step_flow(pick, TickInput(thrust=UP))
    assert stepped.run == step_run(first, UP), "the run is first stepped on the next tick"
    assert stepped.run_stepped

    # After a game over and MENU, Play starts next_run.
    over: GameFlow = over_flow(waves=waves)
    on_menu_choice: GameFlow = after(over, TickInput(thrust=DOWN), IDLE)
    assert on_menu_choice.game_over_selection is GameOverChoice.MENU
    at_menu: GameFlow = after(on_menu_choice, CONFIRM, IDLE)
    assert at_menu.screen is Screen.MENU
    assert at_menu.run == over.run, "the menu keeps the finished run until Play"
    assert at_menu.run.game_over

    play: GameFlow = step_flow(at_menu, CONFIRM)
    assert play.screen is Screen.PLAYING
    assert play.run == next_run(over.run)
    assert not play.run.game_over
    assert play.run.lives == 3
    assert not play.run_stepped
    assert step_flow(play, IDLE).run == step_run(next_run(over.run), NO_KEY)


def test_a_confirm_or_a_focus_loss_pauses_and_only_a_fresh_confirm_resumes() -> None:
    playing: GameFlow = flow_on(Screen.PLAYING, MOVING)

    # A fresh confirm, a focus loss, or both: paused, and the run was not stepped on that tick.
    for keys in (
        CONFIRM,
        FOCUS_LOST,
        TickInput(confirm=True, focus_lost=True),
        TickInput(confirm=True, thrust=UP),
        TickInput(focus_lost=True, thrust=DOWN),
    ):
        paused: GameFlow = step_flow(playing, keys)
        assert paused.screen is Screen.PAUSED
        assert paused.run == MOVING
        assert not paused.run_stepped

    # A held confirm is no press: the run plays on.
    held_over: GameFlow = flow_on(Screen.PLAYING, MOVING, confirm_held=True)
    assert step_flow(held_over, CONFIRM).screen is Screen.PLAYING
    assert step_flow(held_over, CONFIRM).run == step_run(MOVING, NO_KEY)

    # While paused the run never changes but `held`. A focus loss does nothing, and so does
    # getting the focus back; arrows do nothing.
    flow: GameFlow = step_flow(playing, CONFIRM)
    frozen: Run = MOVING
    sequence: list[TickInput] = [CONFIRM]
    for i, thrust in enumerate(ALL_KEYS):
        sequence.append(TickInput(thrust=thrust, focus_lost=i % 2 == 0))
    for keys in sequence:
        flow = step_flow(flow, keys)
        assert flow.screen is Screen.PAUSED
        assert flow.run == replace(frozen, held=keys.thrust)
        assert not flow.run_stepped

    # Only a fresh confirm resumes, and the run is not stepped on that tick.
    flow = step_flow(flow, IDLE)
    resumed: GameFlow = step_flow(flow, TickInput(confirm=True, thrust=LEFT))
    assert resumed.screen is Screen.PLAYING
    assert resumed.run == replace(frozen, held=LEFT)
    assert not resumed.run_stepped

    # It plays from the next tick on.
    played: GameFlow = step_flow(resumed, TickInput(thrust=LEFT))
    assert played.run == step_run(resumed.run, LEFT)
    assert played.run_stepped


def test_an_arrow_pressed_in_a_pause_and_held_after_the_resume_does_not_end_the_respawn_wait() -> (
    None
):
    waiting: Run = replace(RUN, waiting=True, lives=2, ship=spawn())
    assert not step_run(waiting, UP).waiting, "an arrow press ends the wait when nothing pauses"

    flow: GameFlow = flow_on(Screen.PLAYING, waiting)
    flow = step_flow(flow, CONFIRM)
    assert flow.screen is Screen.PAUSED
    for _ in range(4):
        flow = step_flow(flow, TickInput(thrust=UP))
        assert flow.run.waiting
        assert flow.run.held == UP
    flow = step_flow(flow, TickInput(confirm=True, thrust=UP))
    assert flow.screen is Screen.PLAYING
    assert flow.run.waiting
    assert flow.run.held == UP
    standing: Ship = flow.run.ship

    # The arrow is still held after the resume: no press, the wait goes on, the ship stands.
    for _ in range(3):
        flow = step_flow(flow, TickInput(thrust=UP))
        assert flow.run.waiting, "a key pressed in the pause and held is not a press"
        assert flow.run.ship == standing
        assert flow.run_stepped

    flow = step_flow(flow, IDLE)
    assert flow.run.waiting
    flow = step_flow(flow, TickInput(thrust=UP))
    assert not flow.run.waiting, "a fresh press ends the wait"

    # An arrow pressed and released in the pause leaves nothing held: the first press after ends it.
    flow = step_flow(flow_on(Screen.PLAYING, waiting), CONFIRM)
    flow = after(flow, TickInput(thrust=UP), IDLE)
    flow = step_flow(flow, CONFIRM)
    assert flow.screen is Screen.PLAYING
    assert flow.run.waiting
    flow = step_flow(flow, IDLE)
    assert flow.run.waiting
    assert not step_flow(flow, TickInput(thrust=UP)).run.waiting


def test_during_the_last_life_the_run_is_stepped_on_every_tick_and_nothing_pauses() -> None:
    flow: GameFlow = flow_on(Screen.PLAYING, last_life_run())
    flow = step_flow(flow, IDLE)
    assert flow.run.last_life, "the death tick starts the last life"
    assert flow.screen is Screen.PLAYING
    assert flow.run_stepped

    expected: Run = flow.run
    ticks: int = 0
    while flow.screen is Screen.PLAYING:
        # A fresh confirm on every other tick, a focus loss on every tick.
        keys: TickInput = TickInput(
            confirm=ticks % 2 == 0,
            focus_lost=True,
            thrust=ALL_KEYS[ticks % len(ALL_KEYS)],
        )
        flow = step_flow(flow, keys)
        expected = step_run(expected, keys.thrust)
        assert flow.run == expected
        assert flow.run_stepped
        ticks += 1
        assert ticks <= LAST_LIFE_DELAY + 1
    assert flow.screen is Screen.GAME_OVER
    assert flow.run.game_over
    assert ticks == LAST_LIFE_DELAY


def test_a_step_that_ends_in_game_over_shows_the_game_over_screen_with_retry_selected() -> None:
    # The choice was MENU when the run ended: the screen opens on RETRY.
    over: GameFlow = over_flow(choice=GameOverChoice.MENU)
    assert over.screen is Screen.GAME_OVER
    assert over.run.game_over
    assert over.game_over_selection is GameOverChoice.RETRY

    # Up and down wrap between RETRY and MENU, one move per fresh press.
    to_menu: GameFlow = step_flow(over, TickInput(thrust=DOWN))
    assert to_menu.game_over_selection is GameOverChoice.MENU
    assert after(to_menu, IDLE, TickInput(thrust=DOWN)).game_over_selection is GameOverChoice.RETRY
    assert step_flow(over, TickInput(thrust=UP)).game_over_selection is GameOverChoice.MENU
    assert after(to_menu, IDLE, TickInput(thrust=UP)).game_over_selection is GameOverChoice.RETRY
    held: GameFlow = over
    for _ in range(20):
        held = step_flow(held, TickInput(thrust=DOWN))
    assert held.game_over_selection is GameOverChoice.MENU
    cancel: GameFlow = step_flow(over, TickInput(thrust=Thrust(up=True, down=True)))
    assert cancel.game_over_selection is GameOverChoice.RETRY

    # The run is never stepped, the arrows never retry, a focus loss does nothing, left and right
    # do nothing: from any arrows, with or without a focus loss, the screen stays and the run is
    # exactly as it was.
    for thrust in ALL_KEYS:
        for focus in (False, True):
            out: GameFlow = step_flow(over, TickInput(thrust=thrust, focus_lost=focus))
            assert out.screen is Screen.GAME_OVER
            assert out.run == over.run
            assert not out.run_stepped
            pressed: int = int(thrust.up) - int(thrust.down)
            assert out.game_over_selection is move(GameOverChoice.RETRY, -pressed)
    for _ in range(10):
        held = step_flow(held, TickInput(thrust=Thrust(up=True, down=True, left=True, right=True)))
        assert held.run == over.run
        assert held.screen is Screen.GAME_OVER

    # An arrow held through the last life and into game over does not move the choice.
    through: GameFlow = flow_on(Screen.PLAYING, last_life_run(), arrows=DOWN)
    through = to_game_over(through, TickInput(thrust=DOWN))
    for _ in range(10):
        through = step_flow(through, TickInput(thrust=DOWN))
        assert through.game_over_selection is GameOverChoice.RETRY
        assert through.screen is Screen.GAME_OVER
    through = step_flow(through, IDLE)
    assert step_flow(through, TickInput(thrust=DOWN)).game_over_selection is GameOverChoice.MENU


@pytest.mark.parametrize("with_waves", [False, True])
def test_retry_gives_next_run_and_playing_at_once_and_menu_gives_the_menu_with_play_selected(
    with_waves: bool,
) -> None:
    waves: WaveRun | None = start_waves(BOOK, SEED) if with_waves else None
    over: GameFlow = over_flow(waves=waves, menu=MenuItem.LEADERBOARD)

    retry: GameFlow = step_flow(over, CONFIRM)
    assert retry.screen is Screen.PLAYING
    assert retry.run == next_run(over.run)
    assert not retry.run_stepped
    assert retry.run.lives == 3
    assert not retry.run.game_over
    # The next tick is the run's first.
    assert step_flow(retry, TickInput(thrust=UP)).run == step_run(retry.run, UP)

    # A down on the same tick as the confirm does not move the choice first.
    both: GameFlow = step_flow(over, TickInput(confirm=True, thrust=DOWN))
    assert both.screen is Screen.PLAYING
    assert both.run == next_run(over.run)

    chosen: GameFlow = replace(over, game_over_selection=GameOverChoice.MENU)
    menu: GameFlow = step_flow(chosen, CONFIRM)
    assert menu.screen is Screen.MENU
    assert menu.menu_selection is MenuItem.PLAY, "the menu opens on Play, not where it was"
    assert menu.run == over.run
    assert not menu.run_stepped
    both_menu: GameFlow = step_flow(chosen, TickInput(confirm=True, thrust=UP))
    assert both_menu.screen is Screen.MENU
    assert both_menu.run == over.run


@pytest.mark.parametrize(
    "screen",
    [Screen.MENU, Screen.INSTRUCTIONS, Screen.LEADERBOARD, Screen.PAUSED, Screen.GAME_OVER],
)
def test_a_focus_loss_changes_nothing_on_the_menu_a_page_the_pause_and_game_over(
    screen: Screen,
) -> None:
    flow: GameFlow = (
        replace(over_flow(), run_stepped=False)
        if screen is Screen.GAME_OVER
        else flow_on(screen, MOVING)
    )

    with_loss: GameFlow = step_flow(flow, FOCUS_LOST)

    assert with_loss == flow
    assert with_loss == step_flow(flow, IDLE)
    # A flow with a key held is read the same way.
    held: GameFlow = replace(flow, confirm_held=True, arrows_held=DOWN)
    assert step_flow(held, TickInput(focus_lost=True, confirm=True, thrust=DOWN)) == step_flow(
        held, TickInput(confirm=True, thrust=DOWN)
    )
    # Getting the focus back is a tick with no loss: it resumes nothing.
    assert step_flow(with_loss, IDLE).screen is screen


def test_run_stepped_is_true_only_after_a_step_and_flow_drifters_follow_it() -> None:
    ticks: list[tuple[str, GameFlow, bool]] = []

    def record(label: str, flow: GameFlow, stepped: bool) -> GameFlow:
        ticks.append((label, flow, stepped))
        assert flow.run_stepped is stepped, label
        return flow

    flow: GameFlow = record("start", start_flow(RUN), False)
    flow = record("menu", step_flow(flow, IDLE), False)
    flow = record("menu arrow", step_flow(flow, TickInput(thrust=DOWN)), False)
    flow = record(
        "open page", step_flow(replace(flow, menu_selection=MenuItem.INSTRUCTIONS), CONFIRM), False
    )
    flow = record("page", step_flow(flow, IDLE), False)
    flow = record("close page", step_flow(flow, CONFIRM), False)
    flow = record("menu again", step_flow(flow, IDLE), False)
    flow = record("Play", step_flow(flow, CONFIRM), False)
    flow = record("play 1", step_flow(flow, IDLE), True)
    flow = record("play 2", step_flow(flow, TickInput(thrust=UP)), True)
    flow = record("pause", step_flow(flow, CONFIRM), False)
    flow = record("paused held", step_flow(flow, CONFIRM), False)
    flow = record("paused", step_flow(flow, IDLE), False)
    flow = record("resume", step_flow(flow, CONFIRM), False)
    flow = record("play 3", step_flow(flow, IDLE), True)
    flow = record("focus pause", step_flow(flow, FOCUS_LOST), False)

    last: GameFlow = flow_on(Screen.PLAYING, last_life_run())
    last = record("death", step_flow(last, IDLE), True)
    assert last.run.last_life
    last = record("last life", step_flow(last, IDLE), True)
    over: GameFlow = to_game_over(last)
    # The tick that ends in game over stepped the run; add_drifters hands a game-over run back
    # unchanged, so what it says about this tick can't show. Its flag is not asserted here.
    ticks.append(("game over tick", over, over.run_stepped))
    over_idle: GameFlow = record("game over", step_flow(over, IDLE), False)
    over_move: GameFlow = record(
        "game over arrow", step_flow(over_idle, TickInput(thrust=DOWN)), False
    )
    retried: GameFlow = record(
        "RETRY", step_flow(replace(over, confirm_held=False), CONFIRM), False
    )
    retried = record("play after retry", step_flow(retried, IDLE), True)
    to_menu: GameFlow = step_flow(replace(over_move, confirm_held=False), CONFIRM)
    record("MENU", to_menu, False)

    for label, state, stepped in ticks:
        before: GameFlow = copy.deepcopy(state)
        out: GameFlow = add_flow_drifters(state, PLACEMENTS, TUNING)
        assert state == before, label
        if label == "game over tick":
            assert out.run == state.run, label
        elif stepped:
            assert out.run == add_drifters(state.run, PLACEMENTS, TUNING), label
            assert len(out.run.drifters) == len(state.run.drifters) + 1, label
            assert replace(out, run=state.run) == state, label
        else:
            assert out == state, label

    # A paused, page or menu run never gets the same placements twice, however many ticks.
    paused: GameFlow = step_flow(flow_on(Screen.PLAYING, MOVING), CONFIRM)
    for _ in range(5):
        paused = add_flow_drifters(step_flow(paused, IDLE), PLACEMENTS, TUNING)
    assert paused.run.drifters == ()

    # A last-life tick takes the placements: the world runs on.
    taken: GameFlow = add_flow_drifters(last, PLACEMENTS, TUNING)
    assert len(taken.run.drifters) == 1

    # It raises what add_drifters raises, and only when it adds.
    bad: tuple[Placement, ...] = (Placement(DrifterType.COIN, x=100.0, y=-20.0),)
    playing: GameFlow = step_flow(flow_on(Screen.PLAYING, RUN), IDLE)
    with pytest.raises(ValueError, match="no tuning for drifter type 'coin'"):
        add_drifters(playing.run, bad, TUNING)
    with pytest.raises(ValueError, match="no tuning for drifter type 'coin'"):
        add_flow_drifters(playing, bad, TUNING)
    assert add_flow_drifters(step_flow(playing, CONFIRM), bad, TUNING).screen is Screen.PAUSED


def pure_flows() -> list[GameFlow]:
    """One flow per screen, the playing ones with a drifter in the run, and a last-life flow."""
    with_rock: Run = add_drifters(MOVING, PLACEMENTS, TUNING)
    last: GameFlow = step_flow(flow_on(Screen.PLAYING, last_life_run()), IDLE)
    assert last.run.last_life
    return [
        start_flow(RUN),
        flow_on(Screen.MENU, MOVING, menu=MenuItem.LEADERBOARD),
        flow_on(Screen.INSTRUCTIONS, MOVING),
        flow_on(Screen.LEADERBOARD, MOVING),
        flow_on(Screen.PLAYING, with_rock),
        flow_on(Screen.PAUSED, with_rock),
        over_flow(),
        last,
    ]


@pytest.mark.determinism
def test_step_flow_never_mutates_its_input_and_gives_the_same_flow_for_the_same_input() -> None:
    inputs: list[TickInput] = [
        TickInput(thrust=thrust, confirm=confirm, focus_lost=focus)
        for thrust in ALL_KEYS
        for confirm in (False, True)
        for focus in (False, True)
    ]
    for flow in pure_flows():
        for keys in inputs:
            before: GameFlow = copy.deepcopy(flow)
            first: GameFlow = step_flow(flow, keys)
            second: GameFlow = step_flow(flow, keys)
            assert flow == before, (flow.screen, keys)
            assert first == second, (flow.screen, keys)
            assert first is not flow

    run: Run = start_run(start_waves(BOOK, SEED))
    assert start_flow(run) == start_flow(run)
    stepped: GameFlow = step_flow(flow_on(Screen.PLAYING, run, confirm_held=True), CONFIRM)
    before_add: GameFlow = copy.deepcopy(stepped)
    assert add_flow_drifters(stepped, PLACEMENTS, TUNING) == add_flow_drifters(
        stepped, PLACEMENTS, TUNING
    )
    assert stepped == before_add


@pytest.fixture
def flow_log(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture the flow's, the run's and the waves' loggers at DEBUG."""
    for name in (FLOW_LOGGER, RUN_LOGGER, WAVES_LOGGER):
        caplog.set_level(logging.DEBUG, logger=name)
    return caplog


def test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first(
    flow_log: pytest.LogCaptureFixture,
) -> None:
    def step(flow: GameFlow, keys: TickInput) -> tuple[GameFlow, list[tuple[str, str]]]:
        return lines_after(flow_log, flow, keys)

    def flow_line(*messages: str) -> list[tuple[str, str]]:
        return [(FLOW_LOGGER, message) for message in messages]

    # The menu: a move logs one line, a cancel, a sideways key and an idle tick log nothing.
    menu: GameFlow = flow_on(Screen.MENU, RUN)
    _, lines = step(menu, TickInput(thrust=DOWN))
    assert lines == flow_line("menu select instructions")
    _, lines = step(menu, TickInput(thrust=UP))
    assert lines == flow_line("menu select leaderboard")
    for keys in (
        TickInput(thrust=Thrust(up=True, down=True)),
        TickInput(thrust=LEFT),
        FOCUS_LOST,
        IDLE,
    ):
        _, lines = step(menu, keys)
        assert lines == []

    # Pages: one `screen` line to open, one to close, and nothing on the page, and the reset of the
    # selection on entering the menu is no `menu select` line.
    page: GameFlow
    page, lines = step(flow_on(Screen.MENU, RUN, menu=MenuItem.INSTRUCTIONS), CONFIRM)
    assert lines == flow_line("screen instructions")
    _, lines = step(replace(page, confirm_held=False), TickInput(thrust=DOWN, focus_lost=True))
    assert lines == []
    back: GameFlow
    back, lines = step(replace(page, confirm_held=False), CONFIRM)
    assert lines == flow_line("screen menu")
    _, lines = step(flow_on(Screen.MENU, RUN, menu=MenuItem.LEADERBOARD), CONFIRM)
    assert lines == flow_line("screen leaderboard")
    _, lines = step(flow_on(Screen.LEADERBOARD, RUN, menu=MenuItem.LEADERBOARD), CONFIRM)
    assert lines == flow_line("screen menu")
    assert back.menu_selection is MenuItem.PLAY

    # Play on the app's first run: one line. No `new run`: the run is untouched.
    playing: GameFlow
    playing, lines = step(flow_on(Screen.MENU, RUN), CONFIRM)
    assert lines == flow_line("screen playing")

    # A playing tick that changes nothing: the flow writes nothing.
    _, lines = step(playing, IDLE)
    assert flow_lines(lines) == []

    # Pause: `pause by=...` right before `screen paused`, `key` when both happen.
    ready: GameFlow = flow_on(Screen.PLAYING, MOVING)
    paused: GameFlow
    paused, lines = step(ready, CONFIRM)
    assert lines == flow_line("pause by=key", "screen paused")
    _, lines = step(ready, FOCUS_LOST)
    assert lines == flow_line("pause by=focus", "screen paused")
    _, lines = step(ready, TickInput(confirm=True, focus_lost=True))
    assert lines == flow_line("pause by=key", "screen paused")

    # Paused ticks log nothing, whatever the keys; the resume logs one line.
    for keys in (IDLE, FOCUS_LOST, TickInput(thrust=UP), CONFIRM):
        _, lines = step(paused, keys)
        assert lines == []
    _, lines = step(replace(paused, confirm_held=False), CONFIRM)
    assert lines == flow_line("screen playing")

    # The last life: the death tick and the ticks after it log nothing in the flow, and the tick
    # that ends in game over writes the run's lines, then `screen game_over` and no select line.
    flow: GameFlow = flow_on(Screen.PLAYING, last_life_run())
    for _ in range(LAST_LIFE_DELAY + 5):
        flow, lines = step(flow, IDLE)
        if flow.screen is Screen.GAME_OVER:
            break
        assert flow_lines(lines) == []
    assert flow.screen is Screen.GAME_OVER
    names: list[str] = [name for name, _ in lines]
    assert names.count(FLOW_LOGGER) == 1
    assert flow_lines(lines) == ["screen game_over"]
    assert names[-1] == FLOW_LOGGER
    assert RUN_LOGGER in names, "the run logged its own game over line"
    assert any(message.startswith("game over") for name, message in lines if name == RUN_LOGGER)

    # The game-over screen: a move logs one line each way, a reset logs none.
    over: GameFlow = flow
    _, lines = step(over, TickInput(thrust=DOWN))
    assert lines == flow_line("game over select menu")
    _, lines = step(over, TickInput(thrust=UP))
    assert lines == flow_line("game over select menu")
    to_menu: GameFlow = replace(over, game_over_selection=GameOverChoice.MENU)
    _, lines = step(to_menu, TickInput(thrust=DOWN))
    assert lines == flow_line("game over select retry")
    for keys in (
        TickInput(thrust=Thrust(up=True, down=True)),
        TickInput(thrust=RIGHT),
        FOCUS_LOST,
        IDLE,
    ):
        _, lines = step(over, keys)
        assert lines == []

    # RETRY: the run's `new run` first, then the flow's line. MENU: only the flow's.
    _, lines = step(over, CONFIRM)
    assert lines == [(RUN_LOGGER, "new run"), (FLOW_LOGGER, "screen playing")]
    _, lines = step(to_menu, CONFIRM)
    assert lines == flow_line("screen menu")

    # MENU then Play on a finished run: `new run`, then `screen playing`.
    finished: GameFlow = flow_on(Screen.MENU, over.run)
    _, lines = step(finished, CONFIRM)
    assert lines == [(RUN_LOGGER, "new run"), (FLOW_LOGGER, "screen playing")]

    # With waves, `new run` and the waves' own lines still come before the flow's.
    waves_over: GameFlow = over_flow(waves=start_waves(BOOK, SEED))
    _, lines = step(waves_over, CONFIRM)
    names = [name for name, _ in lines]
    assert names[0] == RUN_LOGGER
    assert lines[0][1] == "new run"
    assert names[-1] == FLOW_LOGGER
    assert names.count(FLOW_LOGGER) == 1
    assert flow_lines(lines) == ["screen playing"]
    assert WAVES_LOGGER in names
