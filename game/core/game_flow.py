"""The screens around a run and the keys that move between them: one state, one step per tick.

`GameFlow` holds the screen that shows, the run, the saves, the two selections, the game-over
screen's message and letter picker, and the keys of the last tick. `step_flow` reads one
`TickInput`, acts on the current screen and steps the run only while it plays. Stdlib and core
only, no frame time, no randomness. Same input, same output, apart from logging on
`core.game_flow`.

Source: docs/contracts/systems/game-flow.md; 02-game-flow.md, rules 1 to 12.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Final

from core.drifters.spawner import Placement
from core.drifters.tuning import DrifterTuning
from core.run import Run, add_drifters, hold_arrows, next_run, step_run
from core.saves import (
    GameOverMessage,
    NamePicker,
    Saves,
    ScoreEntry,
    add_entry,
    message_for,
    move_cursor,
    picked_name,
    place_of,
    start_picker,
    turn_character,
)
from core.ship import Thrust

log = logging.getLogger(__name__)


class Screen(Enum):
    """The screen that shows."""

    MENU = "menu"
    INSTRUCTIONS = "instructions"
    LEADERBOARD = "leaderboard"
    PLAYING = "playing"
    """The run is stepped, its last life too (`run.last_life`)."""
    PAUSED = "paused"
    GAME_OVER = "game_over"


class MenuItem(Enum):
    """The menu's items, in menu order, top first."""

    PLAY = "play"
    INSTRUCTIONS = "instructions"
    LEADERBOARD = "leaderboard"


class GameOverChoice(Enum):
    """The game-over screen's choices, in screen order, top first."""

    RETRY = "retry"
    MENU = "menu"


MENU_START_SELECTION: Final[MenuItem] = MenuItem.PLAY
"""The item selected whenever the menu opens. Source: 02-game-flow.md, menu_start_selection
(guess)."""

GAME_OVER_START_SELECTION: Final[GameOverChoice] = GameOverChoice.RETRY
"""The choice selected whenever the game-over screen opens. Source: 02-game-flow.md,
game_over_choices (locked)."""

_ALL_ARROWS: Final[Thrust] = Thrust(up=True, down=True, left=True, right=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class TickInput:
    """What the player did, as one tick sees it."""

    thrust: Thrust = field(default_factory=Thrust)
    """The arrows held now."""

    confirm: bool = False
    """Enter or Space held now."""

    focus_lost: bool = False
    """The page lost focus since the last tick."""


@dataclass(frozen=True, slots=True, kw_only=True)
class GameFlow:
    """The screen that shows, the run, the two selections and the keys of the last tick."""

    screen: Screen
    run: Run
    menu_selection: MenuItem
    game_over_selection: GameOverChoice
    confirm_held: bool
    """A confirm key was held on the last tick."""

    arrows_held: Thrust
    """The arrows held on the last tick."""

    run_stepped: bool
    """`step_run` ran on the last tick."""

    saves: Saves | None = None
    """The saves the app loaded. None: saves don't work."""

    game_over_message: GameOverMessage = GameOverMessage.GAME_OVER
    """Set when GAME_OVER opens, never changed while it shows."""

    picker: NamePicker | None = None
    """The letter picker shown on GAME_OVER. None: no picker."""

    picking: bool = False
    """The picker takes the keys; RETRY and MENU don't."""

    saves_changed: bool = False
    """An entry was saved on the last tick: the app writes `saves`."""

    @property
    def best(self) -> int | None:
        """The #1 score saved so far, or None without saves. Source: systems/game-flow.md, Rules."""
        if self.saves is None:
            return None
        return self.saves.best

    @property
    def leaderboard(self) -> tuple[ScoreEntry, ...]:
        """The saved entries in place order, or () without saves."""
        if self.saves is None:
            return ()
        return self.saves.entries


@dataclass(frozen=True, slots=True)
class _Presses:
    """The keys that went down on this tick, against the last tick's."""

    confirm: bool
    up: bool
    down: bool
    left: bool
    right: bool


def start_flow(run: Run, saves: Saves | None = None) -> GameFlow:
    """Return the flow at the menu with `run` as the app's first run and `saves` as given.

    Every key counts as held, so a key already down when the menu shows does nothing until it is
    released and pressed again. `saves` None: saves don't work. Source: systems/game-flow.md,
    Rules, Start; 02-game-flow.md, rules 1, 2 and 12.
    """
    return GameFlow(
        screen=Screen.MENU,
        run=run,
        menu_selection=MENU_START_SELECTION,
        game_over_selection=GAME_OVER_START_SELECTION,
        confirm_held=True,
        arrows_held=_ALL_ARROWS,
        run_stepped=False,
        saves=saves,
    )


def stop_saves(flow: GameFlow) -> GameFlow:
    """Return the flow with saves turned off: `saves` None, `saves_changed` False, the rest as is.

    The app calls it when a write fails. Source: systems/game-flow.md, Rules, stop_saves.
    """
    return replace(flow, saves=None, saves_changed=False)


def step_flow(flow: GameFlow, keys: TickInput) -> GameFlow:
    """Advance the flow one fixed 60 Hz tick and return the new flow. Never mutates the input.

    Presses are read against the last tick's keys on every screen, and the keys are stored after
    the tick whatever happened. Source: systems/game-flow.md, Rules, Presses.
    """
    presses = _Presses(
        confirm=keys.confirm and not flow.confirm_held,
        up=keys.thrust.up and not flow.arrows_held.up,
        down=keys.thrust.down and not flow.arrows_held.down,
        left=keys.thrust.left and not flow.arrows_held.left,
        right=keys.thrust.right and not flow.arrows_held.right,
    )
    idle: GameFlow = replace(flow, run_stepped=False, saves_changed=False)
    stepped: GameFlow
    match flow.screen:
        case Screen.MENU:
            stepped = _step_menu(idle, presses)
        case Screen.INSTRUCTIONS | Screen.LEADERBOARD:
            stepped = _step_page(idle, presses)
        case Screen.PLAYING:
            stepped = _step_playing(idle, keys, presses)
        case Screen.PAUSED:
            stepped = _step_paused(idle, keys, presses)
        case Screen.GAME_OVER:
            stepped = _step_game_over(idle, presses)
    return replace(stepped, confirm_held=keys.confirm, arrows_held=keys.thrust)


def add_flow_drifters(
    flow: GameFlow, placements: Sequence[Placement], tuning: DrifterTuning
) -> GameFlow:
    """Return the flow with `placements` added to its run, only when the run was just stepped.

    A paused, frozen or not yet started run never gets the same due placements twice. Raises what
    `add_drifters` raises. Source: systems/game-flow.md, Rules, add_flow_drifters.
    """
    if not flow.run_stepped:
        return flow
    return replace(flow, run=add_drifters(flow.run, placements, tuning))


def _enter(flow: GameFlow, screen: Screen) -> GameFlow:
    """Return the flow on `screen` and log INFO `screen <value>`."""
    log.info("screen %s", screen.value)
    return replace(flow, screen=screen)


def _enter_menu(flow: GameFlow) -> GameFlow:
    """Return the flow on the menu with the start item selected."""
    return _enter(replace(flow, menu_selection=MENU_START_SELECTION), Screen.MENU)


def _moved[E: Enum](selection: E, presses: _Presses) -> E:
    """Return the member one up or one down from `selection`, wrapping around.

    An up press and a down press on the same tick cancel out.
    """
    step: int = int(presses.down) - int(presses.up)
    members: list[E] = list(type(selection))
    return members[(members.index(selection) + step) % len(members)]


def _step_menu(flow: GameFlow, presses: _Presses) -> GameFlow:
    """MENU: a confirm press picks the selection, otherwise the arrows move it."""
    if not presses.confirm:
        moved: MenuItem = _moved(flow.menu_selection, presses)
        if moved is not flow.menu_selection:
            log.debug("menu select %s", moved.value)
        return replace(flow, menu_selection=moved)
    match flow.menu_selection:
        case MenuItem.PLAY:
            return _enter(_with_fresh_run(flow), Screen.PLAYING)
        case MenuItem.INSTRUCTIONS:
            return _enter(flow, Screen.INSTRUCTIONS)
        case MenuItem.LEADERBOARD:
            return _enter(flow, Screen.LEADERBOARD)


def _with_fresh_run(flow: GameFlow) -> GameFlow:
    """Return the flow with `next_run` when the run is over, else with the first run untouched."""
    if not flow.run.game_over:
        return flow
    return replace(flow, run=next_run(flow.run))


def _step_page(flow: GameFlow, presses: _Presses) -> GameFlow:
    """INSTRUCTIONS and LEADERBOARD: a confirm press goes back to the menu."""
    if presses.confirm:
        return _enter_menu(flow)
    return flow


def _step_playing(flow: GameFlow, keys: TickInput, presses: _Presses) -> GameFlow:
    """PLAYING: pause on a confirm press or a focus loss, except in the last life, else step."""
    if not flow.run.last_life and (presses.confirm or keys.focus_lost):
        log.debug("pause by=%s", "key" if presses.confirm else "focus")
        return _enter(flow, Screen.PAUSED)
    stepped: GameFlow = replace(flow, run=step_run(flow.run, keys.thrust), run_stepped=True)
    if not stepped.run.game_over:
        return stepped
    return _open_game_over(stepped)


def _open_game_over(flow: GameFlow) -> GameFlow:
    """Return the flow on GAME_OVER with the selection, message, picker and picking all set.

    The place is worked out once, from the saves as they are now. Source: systems/game-flow.md,
    Rules, Opening GAME_OVER.
    """
    saves: Saves | None = flow.saves
    place: int | None = None
    picker: NamePicker | None = None
    if saves is not None:
        place = place_of(saves, flow.run.score, flow.run.level_reached)
        if place is not None:
            picker = start_picker(saves.last_nickname)
    message: GameOverMessage = message_for(place)
    log.debug("game over message=%s place=%s", message.value, "none" if place is None else place)
    opened: GameFlow = replace(
        flow,
        game_over_selection=GAME_OVER_START_SELECTION,
        game_over_message=message,
        picker=picker,
        picking=picker is not None,
    )
    return _enter(opened, Screen.GAME_OVER)


def _step_paused(flow: GameFlow, keys: TickInput, presses: _Presses) -> GameFlow:
    """PAUSED: hold the arrows in the frozen run, and a confirm press resumes."""
    held: GameFlow = replace(flow, run=hold_arrows(flow.run, keys.thrust))
    if presses.confirm:
        return _enter(held, Screen.PLAYING)
    return held


def _step_game_over(flow: GameFlow, presses: _Presses) -> GameFlow:
    """GAME_OVER: the picker takes the keys while it picks, then RETRY and MENU do."""
    if flow.picking and flow.picker is not None:
        return _step_picker(flow, presses, flow.picker)
    return _step_choices(flow, presses)


def _step_choices(flow: GameFlow, presses: _Presses) -> GameFlow:
    """RETRY and MENU: a confirm press picks one, otherwise the arrows move the choice."""
    if not presses.confirm:
        moved: GameOverChoice = _moved(flow.game_over_selection, presses)
        if moved is not flow.game_over_selection:
            log.debug("game over select %s", moved.value)
        return replace(flow, game_over_selection=moved)
    match flow.game_over_selection:
        case GameOverChoice.RETRY:
            return _enter(replace(flow, run=next_run(flow.run)), Screen.PLAYING)
        case GameOverChoice.MENU:
            return _enter_menu(flow)


def _step_picker(flow: GameFlow, presses: _Presses, picker: NamePicker) -> GameFlow:
    """The picker: a confirm press saves the name, otherwise the arrows turn and move."""
    if presses.confirm:
        return _confirm_name(flow, picker)
    turned: NamePicker = picker
    if presses.up != presses.down:
        turned = turn_character(turned, int(presses.up) - int(presses.down))
        log.debug("picker slot=%d char=%r", turned.cursor, turned.slots[turned.cursor])
    if presses.right != presses.left:
        turned = move_cursor(turned, int(presses.right) - int(presses.left))
        log.debug("picker cursor=%d", turned.cursor)
    return replace(flow, picker=turned)


def _confirm_name(flow: GameFlow, picker: NamePicker) -> GameFlow:
    """End the picking: a name is saved and `saves_changed` set, an empty name saves nothing."""
    done: GameFlow = replace(flow, picking=False)
    name: str = picked_name(picker)
    if flow.saves is None:
        return done
    if not name:
        log.debug("name empty, nothing saved")
        return done
    run: Run = flow.run
    entry: ScoreEntry = ScoreEntry(nickname=name, score=run.score, level_reached=run.level_reached)
    place: int | None = place_of(flow.saves, entry.score, entry.level_reached)
    log.debug(
        "name saved nickname=%r place=%s score=%d level=%d",
        name,
        place,
        entry.score,
        entry.level_reached,
    )
    return replace(done, saves=add_entry(flow.saves, entry), saves_changed=True)
