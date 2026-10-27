"""The game flow: the screens around a run, the fresh presses, the pause and the game-over choices.

Contract: docs/contracts/systems/game-flow.md, Diagram (the state diagram, the tick flowchart, the
two tables), Interface (`core/game_flow.py`), Rules (Presses, Start, MENU, INSTRUCTIONS and
LEADERBOARD, PLAYING, PAUSED, GAME_OVER, `run_stepped`, `add_flow_drifters`, Pure, Logging).
Task: docs/contracts/DRA-125/tasks/DRA-125-10-qa-engineer.md. One test per behavior it lists.
From DRA-126 (docs/contracts/DRA-126/tasks/DRA-126-07-qa-engineer.md): the saves, the game-over
message and letter picker, `saves_changed`, `stop_saves`, `best` and `leaderboard`, and their log
lines (Diagram's game-over table; Rules: Presses, Start, Opening GAME_OVER, GAME_OVER,
`saves_changed`, `stop_saves`, `best` and `leaderboard`, Pure, Logging).
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
    stop_saves,
)
from core.last_life import LastLifeRules
from core.run import Run, add_drifters, next_run, start_run, step_run
from core.saves import GameOverMessage, NamePicker, Saves, ScoreEntry
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
    # that ends in game over writes the run's lines, then the flow's two lines: the message and
    # place (DRA-126, no saves: `game_over`, `none`) right before `screen game_over`. No select
    # line.
    flow: GameFlow = flow_on(Screen.PLAYING, last_life_run())
    for _ in range(LAST_LIFE_DELAY + 5):
        flow, lines = step(flow, IDLE)
        if flow.screen is Screen.GAME_OVER:
            break
        assert flow_lines(lines) == []
    assert flow.screen is Screen.GAME_OVER
    names: list[str] = [name for name, _ in lines]
    assert names.count(FLOW_LOGGER) == 2
    assert flow_lines(lines) == ["game over message=game_over place=none", "screen game_over"]
    assert names[-2:] == [FLOW_LOGGER, FLOW_LOGGER]
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


# ---------------------------------------------------------------------------------------------
# DRA-126: saves, the game-over message, the letter picker, `saves_changed`, `stop_saves`
# ---------------------------------------------------------------------------------------------

TOP_N: int = 10
"""Entries on the list. Source: 11-save-data.md, top_n (locked)."""

PICKER_SLOTS: int = 10
"""Slots of the picker. Source: 11-save-data.md, nickname_length and nickname_input (locked)."""

CHARACTERS: str = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_!?*"
"""The picker's characters in turn order: blank, A to Z, 0 to 9, then `. - _ ! ? *`. Source:
11-save-data.md, nickname_chars (locked), nickname_char_order (guess: up moves forward)."""

RUN_SCORE: int = 500
"""The score the test game overs are given (the run's frozen `final_score`)."""

FAR_SCORE: int = 1_000_000
"""A score far above any test run: an entry with it always ranks above the run."""

BOTH_ARROWS = Thrust(up=True, down=True, left=True, right=True)


def entry(nickname: str, score: int, level: int) -> ScoreEntry:
    """One saved entry."""
    return ScoreEntry(nickname=nickname, score=score, level_reached=level)


def saves_of(*rows: tuple[str, int, int], last: str | None = None) -> Saves:
    """A list in the order given, #1 first: (nickname, score, level) rows."""
    return Saves(entries=tuple(entry(*row) for row in rows), last_nickname=last)


def beating(count: int, *, last: str | None = None) -> Saves:
    """`count` entries that all rank above a run of RUN_SCORE: that run takes place `count + 1`.

    With ten entries no run of RUN_SCORE has a place.
    """
    return saves_of(*((f"N{i + 1}", FAR_SCORE - 100 * i, 1) for i in range(count)), last=last)


def picker_of(name: str, cursor: int = 0) -> NamePicker:
    """A picker holding `name` from slot 0, blanks after."""
    return NamePicker(slots=tuple(name.ljust(PICKER_SLOTS)), cursor=cursor)


def message_of(place: int | None) -> GameOverMessage:
    """#1 NEW BEST SCORE, #2 to 3 TOP 3, #4 to 10 TOP 10, off the list GAME OVER. Source:
    10-ui.md, game_over_message (locked)."""
    if place is None:
        return GameOverMessage.GAME_OVER
    if place == 1:
        return GameOverMessage.NEW_BEST_SCORE
    if place <= 3:
        return GameOverMessage.TOP_3
    return GameOverMessage.TOP_10


def game_over_from(base: GameFlow, *, score: int = RUN_SCORE, level: int = 1) -> GameFlow:
    """`base` played through a real last life to GAME_OVER, the run's score and level as given.

    The run is a one-life run that falls on the first tick. Its `final_score` and `final_level` are
    set on the state after the death tick (the last life keeps them), so the flow opens GAME_OVER
    on its own tick, from the saves and every other field `base` holds. No key is held after.
    """
    start: GameFlow = replace(
        base, screen=Screen.PLAYING, run=last_life_run(), confirm_held=False, arrows_held=NO_KEY
    )
    death: GameFlow = step_flow(start, IDLE)
    assert death.run.last_life
    assert death.screen is Screen.PLAYING
    frozen: Run = replace(death.run, final_score=score, final_level=level)
    return to_game_over(replace(death, run=frozen))


def game_over_with(saves: Saves | None, *, score: int = RUN_SCORE, level: int = 1) -> GameFlow:
    """The flow on GAME_OVER after a run of `score` and `level` with `saves` held."""
    return game_over_from(replace(flow_on(Screen.PLAYING), saves=saves), score=score, level=level)


def picked(picker: NamePicker, thrust: Thrust) -> NamePicker:
    """The picker after one tick of fresh presses of `thrust`: the cursor's slot turns (up one
    forward, down one back), then the cursor moves (right one on, left one back). Up with down and
    left with right cancel out. Source: systems/game-flow.md, Rules, Presses and GAME_OVER."""
    turn: int = int(thrust.up) - int(thrust.down)
    shift: int = int(thrust.right) - int(thrust.left)
    slots: list[str] = list(picker.slots)
    slots[picker.cursor] = CHARACTERS[
        (CHARACTERS.index(slots[picker.cursor]) + turn) % len(CHARACTERS)
    ]
    return NamePicker(slots=tuple(slots), cursor=(picker.cursor + shift) % PICKER_SLOTS)


def test_start_flow_holds_no_saves_or_the_saves_it_is_given_and_every_other_new_field_default() -> (
    None
):
    plain: GameFlow = start_flow(RUN)
    assert plain.saves is None
    assert plain.game_over_message is GameOverMessage.GAME_OVER
    assert plain.picker is None
    assert not plain.picking
    assert not plain.saves_changed
    assert plain.best is None
    assert plain.leaderboard == ()
    assert start_flow(RUN, None) == plain

    for saves in (
        Saves(),
        saves_of(("ACE", 900, 2), ("BOB", 400, 1), last="ACE"),
        beating(TOP_N, last="N1"),
    ):
        before: Saves = copy.deepcopy(saves)
        given: GameFlow = start_flow(RUN, saves)
        assert given.saves is saves
        assert saves == before
        # The rest is what `start_flow(run)` builds: the menu, every key held, nothing opened.
        assert given == replace(plain, saves=saves)
        assert given.screen is Screen.MENU
        assert given.menu_selection is MENU_START_SELECTION
        assert given.game_over_selection is GAME_OVER_START_SELECTION
        assert given.run == RUN
        assert given.confirm_held
        assert given.arrows_held == BOTH_ARROWS
        assert not given.run_stepped
        assert given.game_over_message is GameOverMessage.GAME_OVER
        assert given.picker is None
        assert not given.picking
        assert not given.saves_changed


@pytest.mark.parametrize("last", [None, "ACE"])
@pytest.mark.parametrize("beaten_by", range(TOP_N + 1))
def test_game_over_opens_with_the_message_and_picker_of_the_runs_place(
    beaten_by: int, last: str | None
) -> None:
    saves: Saves = beating(beaten_by, last=last)
    place: int | None = beaten_by + 1 if beaten_by < TOP_N else None

    over: GameFlow = game_over_with(saves)

    assert over.screen is Screen.GAME_OVER
    assert over.run.score == RUN_SCORE
    assert over.run.level_reached == 1
    assert over.game_over_message is message_of(place)
    assert over.game_over_selection is GameOverChoice.RETRY
    assert over.saves is saves
    assert not over.saves_changed
    if place is None:
        assert over.picker is None
        assert not over.picking
        # RETRY and MENU take keys from the first frame.
        assert step_flow(over, TickInput(thrust=DOWN)).game_over_selection is GameOverChoice.MENU
        assert step_flow(over, CONFIRM).screen is Screen.PLAYING
        menu: GameFlow = step_flow(replace(over, game_over_selection=GameOverChoice.MENU), CONFIRM)
        assert menu.screen is Screen.MENU
    else:
        assert over.picker == picker_of(last or "")
        assert over.picker is not None
        assert over.picker.cursor == 0
        assert over.picking
        # The picker has the keys: a confirm saves (it never picks RETRY), down turns a character.
        assert step_flow(over, CONFIRM).screen is Screen.GAME_OVER
        down: GameFlow = step_flow(over, TickInput(thrust=DOWN))
        assert down.game_over_selection is GameOverChoice.RETRY
        assert down.picker != over.picker


def test_a_flow_with_no_saves_opens_game_over_with_no_picker_and_retry_and_menu_at_once() -> None:
    over: GameFlow = game_over_with(None)

    assert over.saves is None
    assert over.game_over_message is GameOverMessage.GAME_OVER
    assert over.picker is None
    assert not over.picking
    assert over.game_over_selection is GameOverChoice.RETRY
    assert step_flow(over, TickInput(thrust=UP)).game_over_selection is GameOverChoice.MENU
    assert step_flow(over, CONFIRM).screen is Screen.PLAYING
    # The same flow built through the plain helper (no saves at all).
    plain: GameFlow = over_flow()
    assert plain.game_over_message is GameOverMessage.GAME_OVER
    assert plain.picker is None
    assert not plain.picking
    assert plain.best is None
    assert plain.leaderboard == ()


@pytest.mark.parametrize(
    ("count", "entry_score", "entry_level", "score", "level", "place"),
    [
        # one entry, 500 on level 2: a tie on score is decided by the level
        (1, 500, 2, 500, 1, 2),
        (1, 500, 2, 500, 2, 2),
        (1, 500, 2, 500, 3, 1),
        (1, 500, 2, 501, 1, 1),
        (1, 500, 2, 499, 8, 2),
        # a full list of 500 on level 2: only a higher level, or a higher score, gets in
        (TOP_N, 500, 2, 500, 1, None),
        (TOP_N, 500, 2, 500, 2, None),
        (TOP_N, 500, 2, 499, 8, None),
        (TOP_N, 500, 2, 500, 3, 1),
        (TOP_N, 500, 2, 501, 1, 1),
    ],
)
def test_the_message_follows_the_score_and_the_level_the_run_reached(
    count: int,
    entry_score: int,
    entry_level: int,
    score: int,
    level: int,
    place: int | None,
) -> None:
    saves: Saves = saves_of(*((f"N{i}", entry_score, entry_level) for i in range(count)))

    over: GameFlow = game_over_with(saves, score=score, level=level)

    assert over.run.score == score
    assert over.run.level_reached == level
    assert over.game_over_message is message_of(place)
    assert (over.picker is not None) == (place is not None)
    assert over.picking == (place is not None)


def test_a_run_beating_only_the_tenth_takes_place_ten() -> None:
    nine_above: tuple[tuple[str, int, int], ...] = tuple(
        (f"N{i}", FAR_SCORE - i, 1) for i in range(TOP_N - 1)
    )
    saves: Saves = saves_of(*nine_above, ("LAST", RUN_SCORE - 1, 1))

    over: GameFlow = game_over_with(saves)

    assert over.game_over_message is GameOverMessage.TOP_10
    assert over.picking
    saved: GameFlow = step_flow(replace(over, picker=picker_of("ME")), CONFIRM)
    assert saved.saves is not None
    assert len(saved.saves.entries) == TOP_N
    assert saved.saves.entries[-1] == entry("ME", RUN_SCORE, 1)
    assert all(e.nickname != "LAST" for e in saved.saves.entries)


def test_each_opening_sets_the_message_picker_and_picking_again_and_keeps_nothing_before() -> None:
    # A natural story: an empty list, a picker, a name saved, RETRY, a second game over.
    first: GameFlow = game_over_with(Saves())
    assert first.game_over_message is GameOverMessage.NEW_BEST_SCORE
    named: GameFlow = step_flow(after(first, TickInput(thrust=UP), IDLE), CONFIRM)
    assert named.saves is not None
    assert named.saves.entries == (entry("A", RUN_SCORE, 1),)
    retried: GameFlow = after(named, IDLE, CONFIRM)
    assert retried.screen is Screen.PLAYING
    second: GameFlow = game_over_from(retried, score=300)
    assert second.game_over_message is GameOverMessage.TOP_3, "place 2"
    assert second.picker == picker_of("A"), "filled from last_nickname, the cursor back on slot 0"
    assert second.picking
    assert second.game_over_selection is GameOverChoice.RETRY

    # Stale fields from an earlier game over, one case each, set again by the opening.
    half_edited: NamePicker = picker_of("ZZ", cursor=7)
    cases: list[tuple[str, dict[str, object], Saves | None, GameOverMessage, NamePicker | None]] = [
        (
            "picking, half-edited, then off the list",
            {
                "picker": half_edited,
                "picking": True,
                "game_over_message": GameOverMessage.TOP_10,
                "game_over_selection": GameOverChoice.MENU,
            },
            beating(TOP_N),
            GameOverMessage.GAME_OVER,
            None,
        ),
        (
            "after a save, then saves that don't work",
            {
                "picker": half_edited,
                "picking": False,
                "game_over_message": GameOverMessage.NEW_BEST_SCORE,
                "game_over_selection": GameOverChoice.MENU,
            },
            None,
            GameOverMessage.GAME_OVER,
            None,
        ),
        (
            "off the list, then place 4",
            {
                "picker": None,
                "picking": False,
                "game_over_message": GameOverMessage.GAME_OVER,
                "game_over_selection": GameOverChoice.MENU,
            },
            beating(3, last="BOB"),
            GameOverMessage.TOP_10,
            picker_of("BOB"),
        ),
        (
            "a half-edited picker, then place 1 with no last name",
            {
                "picker": half_edited,
                "picking": True,
                "game_over_message": GameOverMessage.TOP_10,
                "game_over_selection": GameOverChoice.MENU,
            },
            Saves(),
            GameOverMessage.NEW_BEST_SCORE,
            picker_of(""),
        ),
    ]
    for label, stale, saves, message, picker in cases:
        base: GameFlow = replace(flow_on(Screen.PLAYING), saves=saves, **stale)  # type: ignore[arg-type]
        over: GameFlow = game_over_from(base)
        assert over.game_over_message is message, label
        assert over.picker == picker, label
        assert over.picking == (picker is not None), label
        assert over.game_over_selection is GameOverChoice.RETRY, label


@pytest.mark.parametrize("beaten_by", [0, 1, 2, 3, 9, 10])
def test_the_message_never_changes_while_game_over_shows_the_save_included(
    beaten_by: int,
) -> None:
    saves: Saves = beating(beaten_by)
    over: GameFlow = game_over_with(saves)
    message: GameOverMessage = over.game_over_message
    script: list[TickInput] = [
        TickInput(thrust=UP),
        IDLE,
        TickInput(thrust=RIGHT),
        IDLE,
        FOCUS_LOST,
        IDLE,
        # Saves a name when a picker shows (slot 0 was turned to A). Off the list a confirm would
        # pick RETRY and leave the screen, so there is none.
        CONFIRM if over.picking else IDLE,
        IDLE,
        TickInput(thrust=DOWN),
        IDLE,
        TickInput(thrust=UP),
        IDLE,
        TickInput(thrust=BOTH_ARROWS),
        IDLE,
    ]
    flow: GameFlow = over
    saved_somewhere: bool = False
    for keys in script:
        flow = step_flow(flow, keys)
        assert flow.screen is Screen.GAME_OVER
        assert flow.game_over_message is message
        saved_somewhere = saved_somewhere or flow.saves != saves

    # With a picker the confirm saved the run, and the message still says what it said before.
    assert saved_somewhere == (beaten_by < TOP_N)
    # Saves that stop working on the screen change nothing shown.
    assert stop_saves(flow).game_over_message is message
    assert stop_saves(over).game_over_message is message
    # The next confirm picks RETRY or MENU; the screen was GAME_OVER until then.
    assert step_flow(flow, CONFIRM).screen in (Screen.PLAYING, Screen.MENU)


def test_while_picking_up_and_down_turn_the_character_and_left_and_right_move_the_cursor() -> None:
    over: GameFlow = game_over_with(beating(0))
    assert over.picker == picker_of("")

    # Up goes forward through the characters, down goes back, one per fresh press, wrapping.
    assert step_flow(over, TickInput(thrust=UP)).picker == picker_of("A")
    assert step_flow(over, TickInput(thrust=DOWN)).picker == picker_of("*")
    forward: GameFlow = over
    backward: GameFlow = over
    for i in range(len(CHARACTERS)):
        forward = after(forward, TickInput(thrust=UP), IDLE)
        backward = after(backward, TickInput(thrust=DOWN), IDLE)
        assert forward.picker == picker_of(CHARACTERS[(i + 1) % len(CHARACTERS)])
        assert backward.picker == picker_of(CHARACTERS[-(i + 1) % len(CHARACTERS)])
    assert forward.picker == picker_of("")
    assert backward.picker == picker_of("")

    # Left and right move the cursor, wrapping, and change no character.
    assert step_flow(over, TickInput(thrust=RIGHT)).picker == picker_of("", cursor=1)
    assert step_flow(over, TickInput(thrust=LEFT)).picker == picker_of("", cursor=PICKER_SLOTS - 1)
    lap: GameFlow = over
    for i in range(PICKER_SLOTS):
        lap = after(lap, TickInput(thrust=RIGHT), IDLE)
        assert lap.picker == picker_of("", cursor=(i + 1) % PICKER_SLOTS)

    # A held arrow never repeats, whatever the length of the hold.
    for thrust, expected in (
        (UP, picker_of("A")),
        (DOWN, picker_of("*")),
        (RIGHT, picker_of("", cursor=1)),
        (LEFT, picker_of("", cursor=PICKER_SLOTS - 1)),
    ):
        held: GameFlow = over
        for _ in range(30):
            held = step_flow(held, TickInput(thrust=thrust))
        assert held.picker == expected

    # Up with down and left with right cancel out; so do both pairs together.
    for thrust in (Thrust(up=True, down=True), Thrust(left=True, right=True), BOTH_ARROWS):
        assert step_flow(over, TickInput(thrust=thrust)).picker == over.picker

    # A turn and a move on one tick both act: the turn lands in the slot the cursor was on.
    both: GameFlow = step_flow(over, TickInput(thrust=Thrust(up=True, right=True)))
    assert both.picker == NamePicker(slots=("A",) + (" ",) * 9, cursor=1)
    both_back: GameFlow = step_flow(over, TickInput(thrust=Thrust(down=True, left=True)))
    assert both_back.picker == NamePicker(slots=("*",) + (" ",) * 9, cursor=PICKER_SLOTS - 1)
    # Only the fresh arrow acts: up held, then right pressed on top of it moves the cursor alone.
    up_held: GameFlow = step_flow(over, TickInput(thrust=UP))
    right_on_top: GameFlow = step_flow(up_held, TickInput(thrust=Thrust(up=True, right=True)))
    assert right_on_top.picker == NamePicker(slots=("A",) + (" ",) * 9, cursor=1)


@pytest.mark.parametrize("cursor", [0, 3, PICKER_SLOTS - 1])
def test_while_picking_every_arrow_combination_acts_by_the_rules_and_retry_and_menu_never_move(
    cursor: int,
) -> None:
    over: GameFlow = game_over_with(beating(2, last="AB C"))
    assert over.picker is not None
    start: NamePicker = replace(over.picker, cursor=cursor)
    flow: GameFlow = replace(over, picker=start)

    for thrust in ALL_KEYS:
        for focus in (False, True):
            out: GameFlow = step_flow(flow, TickInput(thrust=thrust, focus_lost=focus))
            assert out.picker == picked(start, thrust), (thrust, focus)
            assert out.picking
            assert out.screen is Screen.GAME_OVER
            assert out.game_over_selection is GameOverChoice.RETRY, "RETRY and MENU never move"
            assert out.game_over_message is over.game_over_message
            assert out.run == over.run
            assert not out.run_stepped
            assert not out.saves_changed
            assert out.saves is over.saves
            assert out.arrows_held == thrust

    # An arrow held through the last life and into game over is a hold: it does nothing there.
    through: GameFlow = replace(
        flow_on(Screen.PLAYING, last_life_run(), arrows=UP), saves=beating(0)
    )
    held_over: GameFlow = to_game_over(through, TickInput(thrust=UP))
    assert held_over.picker == picker_of("")
    for _ in range(5):
        held_over = step_flow(held_over, TickInput(thrust=UP))
        assert held_over.picker == picker_of("")
    assert after(held_over, IDLE, TickInput(thrust=UP)).picker == picker_of("A")


def test_a_fresh_confirm_while_picking_saves_the_entry_with_the_runs_score_and_level() -> None:
    first, second = entry("AAA", 900, 2), entry("BBB", 300, 1)
    saves: Saves = saves_of(("AAA", 900, 2), ("BBB", 300, 1), last="OLD")
    over: GameFlow = game_over_with(saves, score=500, level=3)
    assert over.picker == picker_of("OLD")
    typed: GameFlow = replace(over, picker=picker_of("ACE", cursor=4))

    saved: GameFlow = step_flow(typed, CONFIRM)

    new: ScoreEntry = entry("ACE", 500, 3)
    assert saved.saves == Saves(entries=(first, new, second), last_nickname="ACE")
    assert saved.saves_changed
    assert not saved.picking
    assert saved.picker == typed.picker, "the picker stays, holding the slots as picked"
    assert saved.screen is Screen.GAME_OVER
    assert saved.game_over_selection is GameOverChoice.RETRY
    assert saved.game_over_message is over.game_over_message
    assert saved.run == over.run
    assert not saved.run_stepped
    assert saved.best == 900
    assert saved.leaderboard == (first, new, second)

    # `saves_changed` is True for that tick only, whatever comes next.
    for keys in (IDLE, CONFIRM, TickInput(thrust=UP), FOCUS_LOST):
        after_save: GameFlow = step_flow(saved, keys)
        assert not after_save.saves_changed
        assert after_save.saves == saved.saves

    # Arrows pressed on the confirm tick change nothing: not the picker, not the choice.
    for thrust in ALL_KEYS:
        out: GameFlow = step_flow(typed, TickInput(confirm=True, thrust=thrust))
        assert out.saves == saved.saves
        assert out.picker == typed.picker
        assert out.game_over_selection is GameOverChoice.RETRY
        assert out.saves_changed
        assert not out.picking

    # A confirm with arrows held but no fresh confirm is no save: the held confirm does nothing.
    held: GameFlow = replace(typed, confirm_held=True)
    nothing: GameFlow = step_flow(held, CONFIRM)
    assert nothing.picking
    assert nothing.saves is typed.saves
    assert not nothing.saves_changed


@pytest.mark.parametrize(
    "name",
    ["A", "AB", " A", "A B", "A  B", "ABCDEFGHIJ", "-.*_!?09Z", "  X"],
)
def test_a_saved_name_has_its_trailing_blanks_dropped_and_nothing_else_changed(name: str) -> None:
    over: GameFlow = game_over_with(Saves(), score=RUN_SCORE, level=2)
    typed: GameFlow = replace(over, picker=picker_of(name))

    saved: GameFlow = step_flow(typed, CONFIRM)

    assert saved.saves is not None
    assert saved.saves.entries == (entry(name.rstrip(" "), RUN_SCORE, 2),)
    assert saved.saves.last_nickname == name.rstrip(" ")
    assert saved.saves_changed
    assert saved.best == RUN_SCORE


def test_a_name_saved_on_a_full_list_pushes_the_tenth_out() -> None:
    full: Saves = saves_of(
        *((f"N{i + 1}", 1000 - 100 * i, 3) for i in range(TOP_N)), last="N10"
    )  # 1000 down to 100
    over: GameFlow = game_over_with(full, score=450, level=3)
    assert over.game_over_message is GameOverMessage.TOP_10, "place 7"
    saved: GameFlow = step_flow(replace(over, picker=picker_of("ME")), CONFIRM)

    assert saved.saves is not None
    names: list[str] = [e.nickname for e in saved.saves.entries]
    assert names == ["N1", "N2", "N3", "N4", "N5", "N6", "ME", "N7", "N8", "N9"], "N10 is out"
    assert saved.saves_changed
    assert saved.saves.last_nickname == "ME"

    top: GameFlow = step_flow(
        replace(game_over_with(full, score=5000, level=1), picker=picker_of("TOP")), CONFIRM
    )
    assert top.saves is not None
    assert [e.nickname for e in top.saves.entries][:2] == ["TOP", "N1"]
    assert len(top.saves.entries) == TOP_N


@pytest.mark.parametrize("last", [None, "OLD"])
def test_confirming_an_all_blank_name_saves_nothing_and_leaves_the_last_nickname(
    last: str | None,
) -> None:
    saves: Saves = saves_of(("AAA", 900, 2), last=last)
    over: GameFlow = game_over_with(saves)
    blank: GameFlow = replace(over, picker=picker_of(""))

    empty: GameFlow = step_flow(blank, CONFIRM)

    assert empty.saves is saves
    assert empty.saves is not None
    assert empty.saves.last_nickname == last
    assert not empty.saves_changed
    assert not empty.picking
    assert empty.picker == blank.picker
    assert empty.game_over_selection is GameOverChoice.RETRY
    assert empty.screen is Screen.GAME_OVER
    # Arrows on the confirm tick change nothing either.
    for thrust in ALL_KEYS:
        out: GameFlow = step_flow(blank, TickInput(confirm=True, thrust=thrust))
        assert out.saves is saves
        assert out.picker == blank.picker
        assert not out.saves_changed
        assert not out.picking
    # RETRY and MENU take over: a move, then a pick.
    moved: GameFlow = after(empty, IDLE, TickInput(thrust=DOWN))
    assert moved.game_over_selection is GameOverChoice.MENU
    assert after(moved, IDLE, CONFIRM).screen is Screen.MENU


@pytest.mark.parametrize("blank", [False, True])
def test_the_confirm_that_saves_never_picks_retry_held_and_a_fresh_press_does(blank: bool) -> None:
    # The Diagram's game-over table: Enter down on tick S, held to S + 30, up on S + 31, down
    # again on S + 32. An all-blank name takes the same path (nothing saved, the same keys).
    over: GameFlow = game_over_with(beating(0, last=None if blank else "ACE"))
    assert over.picking
    expected_picker: NamePicker = picker_of("" if blank else "ACE")
    assert over.picker == expected_picker

    flow: GameFlow = step_flow(over, CONFIRM)  # tick S
    assert flow.screen is Screen.GAME_OVER
    assert not flow.picking
    assert flow.saves_changed is (not blank)
    assert flow.confirm_held
    for _ in range(30):  # ticks S + 1 to S + 30
        flow = step_flow(flow, CONFIRM)
        assert flow.screen is Screen.GAME_OVER
        assert not flow.picking
        assert not flow.saves_changed
        assert flow.game_over_selection is GameOverChoice.RETRY
        assert flow.run == over.run
    flow = step_flow(flow, IDLE)  # tick S + 31: the key is up
    assert flow.screen is Screen.GAME_OVER
    retried: GameFlow = step_flow(flow, CONFIRM)  # tick S + 32: a fresh press
    assert retried.screen is Screen.PLAYING
    assert retried.run == next_run(over.run)


def test_saves_are_kept_through_retry_menu_and_later_runs() -> None:
    saves: Saves = saves_of(("AAA", 900, 2), last="AAA")
    over: GameFlow = game_over_with(saves, score=500)
    saved: GameFlow = step_flow(over, CONFIRM)
    assert saved.saves is not None
    kept: Saves = saved.saves
    assert kept.entries == (entry("AAA", 900, 2), entry("AAA", 500, 1))

    # RETRY: the saves go on, the flag is gone, and a run plays on with them.
    retry: GameFlow = after(saved, IDLE, CONFIRM)
    assert retry.screen is Screen.PLAYING
    assert retry.saves is kept
    assert not retry.saves_changed
    playing: GameFlow = after(retry, *[IDLE] * 5)
    assert playing.saves is kept
    assert playing.best == 900
    paused: GameFlow = after(playing, CONFIRM)
    assert paused.screen is Screen.PAUSED
    assert paused.saves is kept

    # A later game over is placed against the saves as they are now: 500 on level 1 ties the
    # saved 500 on level 1, goes under it, and is place 3.
    second: GameFlow = game_over_from(retry, score=500)
    assert second.saves is kept
    assert second.game_over_message is GameOverMessage.TOP_3
    assert second.picker == picker_of("AAA")
    # A game over off the list keeps the saves as they are.
    off: GameFlow = game_over_from(replace(retry, saves=beating(TOP_N)))
    assert off.saves == beating(TOP_N)
    assert not off.saves_changed

    # MENU: the saves go on, to Play and to the leaderboard page.
    to_menu: GameFlow = after(saved, IDLE, TickInput(thrust=DOWN), IDLE, CONFIRM, IDLE)
    assert to_menu.screen is Screen.MENU
    assert to_menu.saves is kept
    assert step_flow(to_menu, CONFIRM).saves is kept
    board: GameFlow = after(to_menu, TickInput(thrust=UP), IDLE, CONFIRM)
    assert board.screen is Screen.LEADERBOARD
    assert board.saves is kept
    assert board.leaderboard == kept.entries


def test_stop_saves_clears_the_saves_and_the_flag_and_changes_nothing_else() -> None:
    saves: Saves = saves_of(("AAA", 900, 2), ("BBB", 300, 1), last="BBB")
    over: GameFlow = game_over_with(saves)
    saved: GameFlow = step_flow(replace(over, picker=picker_of("ACE")), CONFIRM)
    assert saved.saves_changed
    flows: list[GameFlow] = [
        start_flow(RUN, saves),
        start_flow(RUN),
        flow_on(Screen.PLAYING, MOVING),
        replace(flow_on(Screen.PAUSED, MOVING), saves=saves),
        replace(flow_on(Screen.LEADERBOARD), saves=saves),
        over,
        saved,
        over_flow(),
    ]
    for flow in flows:
        before: GameFlow = copy.deepcopy(flow)
        stopped: GameFlow = stop_saves(flow)
        assert flow == before, "the input is not mutated"
        assert stopped == replace(flow, saves=None, saves_changed=False)
        assert stopped.saves is None
        assert not stopped.saves_changed
        assert stopped.best is None
        assert stopped.leaderboard == ()
        assert stop_saves(stopped) == stopped
        assert stop_saves(flow) == stopped, "the same input gives the same flow"

    # The screen the player is on stays as it is: the message, the picker, both selections.
    stopped_over: GameFlow = stop_saves(over)
    assert stopped_over.screen is Screen.GAME_OVER
    assert stopped_over.game_over_message is over.game_over_message
    assert stopped_over.picker == over.picker
    assert stopped_over.picking == over.picking
    assert stopped_over.game_over_selection is over.game_over_selection
    assert stop_saves(saved).screen is Screen.GAME_OVER

    # From then on there is no picker and no best: the next game over is GAME OVER.
    playing: GameFlow = stop_saves(replace(flow_on(Screen.PLAYING), saves=beating(0, last="ACE")))
    later: GameFlow = game_over_from(playing)
    assert later.saves is None
    assert later.game_over_message is GameOverMessage.GAME_OVER
    assert later.picker is None
    assert not later.picking
    assert later.best is None
    assert later.leaderboard == ()


def test_stop_saves_writes_no_log_line(flow_log: pytest.LogCaptureFixture) -> None:
    over: GameFlow = game_over_with(beating(1))
    flow_log.clear()

    stop_saves(over)
    stop_saves(start_flow(RUN))

    assert flow_log.records == []


def test_best_and_leaderboard_read_the_saves_and_best_changes_only_on_a_save() -> None:
    # None and empty without saves, and with an empty list.
    for none_flow in (start_flow(RUN), start_flow(RUN, Saves()), over_flow()):
        assert none_flow.best is None
        assert none_flow.leaderboard == ()

    saves: Saves = saves_of(("AAA", 1000, 2), ("BBB", 400, 1), last="BBB")
    menu: GameFlow = start_flow(RUN, saves)
    assert menu.best == 1000
    assert menu.leaderboard == saves.entries
    assert isinstance(menu.leaderboard, tuple)

    # During a run: a score above the best does not change it.
    rich: Run = replace(RUN, coin_points=5000)
    playing: GameFlow = replace(flow_on(Screen.PLAYING, rich), saves=saves)
    for _ in range(10):
        playing = step_flow(playing, IDLE)
        assert playing.run.score >= 5000
        assert playing.best == 1000

    # At game over with a new top score, while picking: still the best saved before.
    over: GameFlow = game_over_with(saves, score=5000, level=2)
    assert over.run.score == 5000
    assert over.game_over_message is GameOverMessage.NEW_BEST_SCORE
    assert over.best == 1000
    keys: list[TickInput] = [
        TickInput(thrust=UP),
        IDLE,
        TickInput(thrust=RIGHT),
        IDLE,
        FOCUS_LOST,
        TickInput(thrust=BOTH_ARROWS),
    ]
    flow: GameFlow = over
    for tick in keys:
        flow = step_flow(flow, tick)
        assert flow.best == 1000
        assert flow.leaderboard == saves.entries

    # Only the save changes it, on the save tick, and for good.
    saved: GameFlow = step_flow(flow, CONFIRM)
    assert saved.saves_changed
    assert saved.best == 5000
    assert saved.leaderboard[0] == entry("CBB", 5000, 2), "BBB with slot 0 turned up to C"
    assert saved.leaderboard[1:] == saves.entries
    assert after(saved, IDLE, TickInput(thrust=DOWN)).best == 5000

    # An all-blank confirm, or a game over off the list, leaves it where it was.
    blank: GameFlow = step_flow(replace(over, picker=picker_of("")), CONFIRM)
    assert blank.best == 1000
    assert blank.leaderboard == saves.entries
    off: GameFlow = game_over_with(beating(TOP_N), score=5000, level=1)
    assert off.best == FAR_SCORE
    assert after(off, TickInput(thrust=DOWN), IDLE, CONFIRM).best == FAR_SCORE


def saves_flows() -> list[GameFlow]:
    """Flows that hold saves, on every screen, with the picker in several states."""
    saves: Saves = beating(2, last="ACE")
    over: GameFlow = game_over_with(saves)
    assert over.picker is not None
    moved: GameFlow = replace(over, picker=replace(over.picker, cursor=2))
    blank: GameFlow = replace(over, picker=picker_of(""))
    saved: GameFlow = step_flow(over, CONFIRM)
    assert saved.saves_changed

    # One tick before the game over that opens a picker.
    before_open: GameFlow = replace(flow_on(Screen.PLAYING, last_life_run()), saves=saves)
    before_open = step_flow(before_open, IDLE)
    for _ in range(LAST_LIFE_DELAY - 1):
        before_open = step_flow(before_open, IDLE)
    assert before_open.screen is Screen.PLAYING
    assert step_flow(before_open, IDLE).screen is Screen.GAME_OVER

    return [
        start_flow(RUN, saves),
        replace(flow_on(Screen.MENU, MOVING), saves=saves),
        replace(flow_on(Screen.LEADERBOARD, MOVING), saves=saves),
        replace(flow_on(Screen.PLAYING, MOVING), saves=saves),
        replace(flow_on(Screen.PAUSED, MOVING), saves=saves),
        before_open,
        over,
        moved,
        blank,
        saved,
        game_over_with(beating(TOP_N)),
        game_over_with(None),
    ]


@pytest.mark.determinism
def test_step_flow_with_saves_never_mutates_its_input_and_gives_the_same_flow_twice() -> None:
    inputs: list[TickInput] = [
        TickInput(thrust=thrust, confirm=confirm, focus_lost=focus)
        for thrust in ALL_KEYS
        for confirm in (False, True)
        for focus in (False, True)
    ]
    for flow in saves_flows():
        for keys in inputs:
            before: GameFlow = copy.deepcopy(flow)
            first: GameFlow = step_flow(flow, keys)
            second: GameFlow = step_flow(flow, keys)
            assert flow == before, (flow.screen, flow.picking, keys)
            assert first == second, (flow.screen, flow.picking, keys)
            assert first is not flow
            assert first.saves is None or first.saves == flow.saves or first.saves_changed

    saves: Saves = beating(3, last="ACE")
    saves_before: Saves = copy.deepcopy(saves)
    assert start_flow(RUN, saves) == start_flow(RUN, saves)
    assert saves == saves_before
    over: GameFlow = game_over_with(saves)
    assert stop_saves(over) == stop_saves(over)
    assert over.saves == saves_before


def test_the_new_log_lines_come_in_the_contracts_order_and_wording(
    flow_log: pytest.LogCaptureFixture,
) -> None:
    flow_log.set_level(logging.DEBUG, logger="core.saves")

    def step(flow: GameFlow, keys: TickInput) -> tuple[GameFlow, list[tuple[str, str]]]:
        return lines_after(flow_log, flow, keys)

    def flow_line(*messages: str) -> list[tuple[str, str]]:
        return [(FLOW_LOGGER, message) for message in messages]

    # The opening: the run's own lines, then the message and place, then `screen game_over`.
    cases: list[tuple[int, str]] = [
        (0, "game over message=new_best_score place=1"),
        (1, "game over message=top_3 place=2"),
        (2, "game over message=top_3 place=3"),
        (3, "game over message=top_10 place=4"),
        (9, "game over message=top_10 place=10"),
        (TOP_N, "game over message=game_over place=none"),
    ]
    for beaten_by, text in cases:
        flow: GameFlow = replace(flow_on(Screen.PLAYING, last_life_run()), saves=beating(beaten_by))
        lines: list[tuple[str, str]] = []
        for _ in range(LAST_LIFE_DELAY + 5):
            flow, lines = step(flow, IDLE)
            if flow.screen is Screen.GAME_OVER:
                break
        assert flow.screen is Screen.GAME_OVER
        assert flow_lines(lines) == [text, "screen game_over"]
        names: list[str] = [name for name, _ in lines]
        assert names[-2:] == [FLOW_LOGGER, FLOW_LOGGER]
        run_at: int = next(
            i
            for i, (name, message) in enumerate(lines)
            if name == RUN_LOGGER and message.startswith("game over")
        )
        assert run_at < names.index(FLOW_LOGGER), "the run's lines come first"
        assert "core.saves" not in names

    # The picker's lines, once per press: the slot and its new character, the new cursor.
    over: GameFlow = game_over_with(beating(1), score=500, level=3)
    at_slot_three: GameFlow = replace(over, picker=replace(over.picker, cursor=3))  # type: ignore[type-var]
    _, lines = step(over, TickInput(thrust=UP))
    assert lines == flow_line("picker slot=0 char='A'")
    _, lines = step(over, TickInput(thrust=DOWN))
    assert lines == flow_line("picker slot=0 char='*'")
    _, lines = step(over, TickInput(thrust=RIGHT))
    assert lines == flow_line("picker cursor=1")
    _, lines = step(over, TickInput(thrust=LEFT))
    assert lines == flow_line("picker cursor=9")
    _, lines = step(at_slot_three, TickInput(thrust=UP))
    assert lines == flow_line("picker slot=3 char='A'")
    # A turn and a move on one tick: the turn's line, then the move's.
    _, lines = step(over, TickInput(thrust=Thrust(up=True, right=True)))
    assert lines == flow_line("picker slot=0 char='A'", "picker cursor=1")
    _, lines = step(over, TickInput(thrust=Thrust(down=True, left=True)))
    assert lines == flow_line("picker slot=0 char='*'", "picker cursor=9")
    # Cancels, a focus loss and an idle tick log nothing, and a held arrow logs nothing more.
    for keys in (
        TickInput(thrust=Thrust(up=True, down=True)),
        TickInput(thrust=Thrust(left=True, right=True)),
        TickInput(thrust=BOTH_ARROWS),
        FOCUS_LOST,
        IDLE,
    ):
        _, lines = step(over, keys)
        assert lines == [], keys
    turned: GameFlow
    turned, lines = step(over, TickInput(thrust=UP))
    assert len(lines) == 1
    for _ in range(5):
        turned, lines = step(turned, TickInput(thrust=UP))
        assert lines == []

    # A save: one line with the name, its place, the score and the level reached.
    named: GameFlow = replace(over, picker=picker_of("ACE"))
    saved: GameFlow
    saved, lines = step(named, CONFIRM)
    assert lines == flow_line("name saved nickname='ACE' place=2 score=500 level=3")
    # An all-blank name: one line, and nothing else.
    _, lines = step(replace(over, picker=picker_of("")), CONFIRM)
    assert lines == flow_line("name empty, nothing saved")
    # After the save the choices take the arrows: the select line, never a picker line.
    _, lines = step(saved, TickInput(thrust=DOWN))
    assert lines == flow_line("game over select menu")
    _, lines = step(saved, TickInput(thrust=UP))
    assert lines == flow_line("game over select menu")
    # While picking, down turns a character and logs no select line.
    _, lines = step(over, TickInput(thrust=DOWN))
    assert lines == flow_line("picker slot=0 char='*'")
    # The held confirm after the save logs nothing; a fresh press picks RETRY.
    held: GameFlow
    held, lines = step(saved, CONFIRM)
    assert lines == []
    _, lines = step(replace(held, confirm_held=False), CONFIRM)
    assert lines == [(RUN_LOGGER, "new run"), (FLOW_LOGGER, "screen playing")]
