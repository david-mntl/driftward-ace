"""The async frame loop on the fixed 60 Hz tick. Imported only by app.loop.start, inside the guard.

Before the first frame it loads and checks the drifter tuning, then the drifter looks and builds
their sprites, the graze values, the last-life
values, the saves from the browser's localStorage and the wave files (both modes) and, in debug
mode only, the debug test spawn list, then builds the first run and wraps it with the saves in the
game flow, which opens on the menu. The run plays the
waves, except in debug mode when the spawn list plays (its `play` is "list", the default). Each
frame: read events (arrows, Enter and Space, F3, the page losing focus), build the thrust from the
held arrows and the confirm flag from Enter or Space, run up to MAX_TICKS_PER_FRAME ticks (one
core.game_flow.step_flow each, then the due drifters, the waves' or the spawn list's, through
core.game_flow.add_flow_drifters, then the saves written after a tick that saved an entry), draw
by screen, flip, then yield to the browser. The app holds
one GameFlow; core does the screens, the pause, the ship, the scroll, the drifters, the lives, the
respawn wait, the last life, game over, the place, the name picker, retry and grazes.
Source: docs/contracts/systems/app/frame-loop.md, Rules, Frame loop. 15-tech-constraints.md,
rules 1 and 2. systems/app/save-storage.md.
"""

import asyncio
import logging
import random
import time
from collections.abc import Sequence

import pygame

from app.assets import load_background, load_hud_art, load_screen_fonts
from app.background_tuning import load_background_rules
from app.debug_spawns import PLAY_LIST, DebugSpawnList, debug_spawns_due, load_debug_spawns
from app.drifter_looks_tuning import install_drifter_looks
from app.hud_tuning import load_hud_rules
from app.mode import RunMode
from app.saves import load_saves, write_saves
from app.screens_tuning import load_screen_rules
from app.settings import MAX_TICKS_PER_FRAME, TICK_RATE
from app.ship_tuning import load_ship_look
from app.tuning import load_graze_rules, load_last_life_rules, load_tuning
from app.waves import load_wave_book
from core.drifters.spawner import Placement
from core.drifters.tuning import DrifterTuning
from core.game_flow import (
    GameFlow,
    Screen,
    TickInput,
    add_flow_drifters,
    start_flow,
    step_flow,
    stop_saves,
)
from core.graze import GrazeRules
from core.last_life import LastLifeRules
from core.run import Run, start_run
from core.saves import Saves
from core.ship import Thrust
from core.waves import WaveBook, start_waves
from core.world import SCREEN_H, SCREEN_W
from ui.background_view import BackgroundArt, draw_background
from ui.burst_view import draw_burst
from ui.debug_overlay import draw_debug_hitboxes, draw_debug_overlay, draw_debug_wave_lines
from ui.drifters.registry import render_drifter
from ui.game_over import (
    draw_final_score,
    draw_game_over,
    draw_game_over_choices,
    draw_name_picker,
)
from ui.graze_view import draw_graze_ring
from ui.hud import HudView
from ui.hud_rules import HudRules
from ui.instructions import draw_instructions
from ui.leaderboard import draw_leaderboard
from ui.menu import draw_menu
from ui.pause_box import draw_pause_box
from ui.popup_view import draw_points_popup
from ui.screen_look import ScreenLook
from ui.screen_rules import ScreenRules
from ui.ship_view import ShipLook, draw_ship
from ui.starfield import draw_starfield
from ui.window_view import WindowBackdrop

log = logging.getLogger(__name__)

TICK_SECONDS: float = 1 / TICK_RATE

ARROW_NAMES: dict[int, str] = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
}
"""The only keys that move the ship. Source: 01-vision.md, locked decision 1."""

CONFIRM_NAMES: dict[int, str] = {
    pygame.K_RETURN: "enter",
    pygame.K_KP_ENTER: "enter",
    pygame.K_SPACE: "space",
}
"""The confirm keys, all the same everywhere. Source: 02-game-flow.md, confirm_keys (locked)."""

FOCUS_LOST_EVENTS: frozenset[int] = frozenset(
    {pygame.WINDOWFOCUSLOST, pygame.WINDOWHIDDEN, pygame.WINDOWMINIMIZED}
)
"""Events that mean the page lost focus. Source: 02-game-flow.md, pause_on_focus_loss (locked)."""

_LOGGED_KEYS: dict[int, str] = {**ARROW_NAMES, **CONFIRM_NAMES}
"""Keys whose down and up events are logged with the ship's x/y."""

BACKGROUND_MAX_STEP: float = 0.1
"""Longest stretch of real time the background moves for in one frame, s. A tab that was away
doesn't make it jump. Look only, no design meaning."""

_RUN_SCREENS: frozenset[Screen] = frozenset({Screen.PLAYING, Screen.PAUSED, Screen.GAME_OVER})
"""Screens that show the run's world in the play area and the HUD round it."""


async def frame_loop(mode: RunMode) -> None:
    """Open the window and run frames until pygame.QUIT (desktop only)."""
    pygame.init()
    hud_rules: HudRules = load_hud_rules()
    window: pygame.Surface = pygame.display.set_mode(
        (hud_rules.window.width, hud_rules.window.height)
    )
    field: pygame.Surface = window.subsurface(
        pygame.Rect(hud_rules.window.field_x, hud_rules.window.field_y, SCREEN_W, SCREEN_H)
    )
    hud: HudView = HudView(hud_rules, load_hud_art(hud_rules))
    screen_rules: ScreenRules = load_screen_rules()
    look: ScreenLook = ScreenLook(screen_rules, load_screen_fonts(screen_rules))
    backdrop: WindowBackdrop = WindowBackdrop(window.get_size())
    background: BackgroundArt = load_background(load_background_rules())
    ship_look: ShipLook = load_ship_look()
    debug: bool = mode is RunMode.DEBUG
    tuning: DrifterTuning = load_tuning()
    install_drifter_looks(tuning)
    graze_rules: GrazeRules = load_graze_rules()
    last_life_rules: LastLifeRules = load_last_life_rules()
    saves: Saves | None = load_saves()
    book: WaveBook = load_wave_book(tuning)
    spawn_list: DebugSpawnList | None = load_debug_spawns(tuning) if debug else None
    list_plays: bool = spawn_list is not None and spawn_list.play == PLAY_LIST
    run: Run = start_run(
        waves=None if list_plays else start_waves(book, random.getrandbits(64)),
        graze_rules=graze_rules,
        last_life_rules=last_life_rules,
    )
    flow: GameFlow = start_flow(run, saves)
    overlay_visible: bool = debug
    focus_lost_pending: bool = False
    accumulator: float = 0.0
    was_capped: bool = False
    background_ticks: float = 0.0
    previous: float = time.perf_counter()
    while True:
        keep_running, overlay_visible, focus_lost = _read_events(flow.run, debug, overlay_visible)
        if not keep_running:
            break
        focus_lost_pending = focus_lost_pending or focus_lost
        thrust, confirm = _held_keys()
        now: float = time.perf_counter()
        accumulator += now - previous
        if flow.screen is not Screen.PAUSED:
            background_ticks += min(now - previous, BACKGROUND_MAX_STEP) * TICK_RATE
        previous = now
        flow, accumulator, focus_lost_pending = _run_ticks(
            flow,
            thrust,
            confirm,
            focus_lost_pending,
            accumulator,
            spawn_list,
            list_plays,
            tuning,
        )
        was_capped = _apply_cap(accumulator, was_capped)
        if was_capped:
            accumulator = 0.0
        _draw(
            window,
            field,
            backdrop,
            hud,
            look,
            background,
            background_ticks,
            ship_look,
            flow,
            overlay_visible,
        )
        pygame.display.flip()
        await asyncio.sleep(0)
    log.info("quit")


def _read_events(run: Run, debug: bool, overlay_visible: bool) -> tuple[bool, bool, bool]:
    """Drain the event queue. Log arrow and confirm keys with the ship's x/y, note a focus loss,
    and toggle the overlay on F3.

    F3 works in debug mode only and never reaches core. Returns (keep_running, overlay_visible,
    focus_lost); keep_running is False on pygame.QUIT, focus_lost is True when any event in
    FOCUS_LOST_EVENTS was read. Source: systems/app/frame-loop.md, Rules, Arrow keys, Confirm keys
    log, Focus and Focus log.
    """
    keep_running: bool = True
    focus_lost: bool = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            keep_running = False
        elif event.type in FOCUS_LOST_EVENTS:
            focus_lost = True
            log.debug("focus lost event=%s", pygame.event.event_name(event.type))
        elif event.type in (pygame.KEYDOWN, pygame.KEYUP) and event.key in _LOGGED_KEYS:
            direction: str = "down" if event.type == pygame.KEYDOWN else "up"
            log.debug(
                "key %s key=%s x=%.2f y=%.2f",
                direction,
                _LOGGED_KEYS[event.key],
                run.ship.x,
                run.ship.y,
            )
        elif debug and event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            overlay_visible = not overlay_visible
            log.debug("overlay visible=%s", overlay_visible)
    return keep_running, overlay_visible, focus_lost


def _held_keys() -> tuple[Thrust, bool]:
    """Return (the thrust from the arrows held now, True when Enter or Space is held now).

    Read once per frame, used by every tick of that frame. The app never works out a fresh press:
    step_flow does. Source: systems/app/frame-loop.md, Rules, Held keys and Confirm keys.
    """
    pressed = pygame.key.get_pressed()
    thrust: Thrust = Thrust(
        up=pressed[pygame.K_UP],
        down=pressed[pygame.K_DOWN],
        left=pressed[pygame.K_LEFT],
        right=pressed[pygame.K_RIGHT],
    )
    confirm: bool = any(pressed[key] for key in CONFIRM_NAMES)
    return thrust, confirm


def _run_ticks(
    flow: GameFlow,
    thrust: Thrust,
    confirm: bool,
    focus_lost_pending: bool,
    accumulator: float,
    spawn_list: DebugSpawnList | None,
    list_plays: bool,
    tuning: DrifterTuning,
) -> tuple[GameFlow, float, bool]:
    """Run one tick per whole TICK_SECONDS in the accumulator, at most MAX_TICKS_PER_FRAME.

    Each tick is one step_flow call; a pending focus loss reaches the first tick only. Right after
    it the due placements go in through one add_flow_drifters call: the spawn list's when
    list_plays, else the run's waves'. Never both. Then the saves are written if that tick saved
    an entry (_write_saves). Returns (flow, accumulator left, focus loss
    still pending: True only when no tick ran). Source: 15-tech-constraints.md, rules 2 and 7;
    systems/app/frame-loop.md, Rules, Focus and Tick.
    """
    ticks: int = 0
    while accumulator >= TICK_SECONDS and ticks < MAX_TICKS_PER_FRAME:
        flow = step_flow(
            flow, TickInput(thrust=thrust, confirm=confirm, focus_lost=focus_lost_pending)
        )
        focus_lost_pending = False
        due: Sequence[Placement] = (
            debug_spawns_due(spawn_list, flow.run.scroll.ticks)
            if spawn_list is not None and list_plays
            else flow.run.wave_spawns_due
        )
        flow = add_flow_drifters(flow, due, tuning)
        flow = _write_saves(flow)
        accumulator -= TICK_SECONDS
        ticks += 1
    return flow, accumulator, focus_lost_pending


def _write_saves(flow: GameFlow) -> GameFlow:
    """Write the saves after a tick that saved an entry; turn saves off when the write fails.

    Source: systems/app/frame-loop.md, Rules, Tick; systems/app/save-storage.md, write_saves.
    """
    if not flow.saves_changed or flow.saves is None:
        return flow
    if write_saves(flow.saves):
        return flow
    return stop_saves(flow)


def _apply_cap(accumulator: float, was_capped: bool) -> bool:
    """Return True if the cap drops time this frame. Log only when capping starts.

    The caller sets the accumulator to 0.0 when this returns True.
    Source: systems/app.md, Rules, Catch-up cap and Cap log; 91-decision-log.md, row 21.
    """
    capped: bool = accumulator >= TICK_SECONDS
    if capped and not was_capped:
        log.debug("tick cap hit, dropped %.3f s", accumulator)
    return capped


def _draw(
    window: pygame.Surface,
    field: pygame.Surface,
    backdrop: WindowBackdrop,
    hud: HudView,
    look: ScreenLook,
    background: BackgroundArt,
    background_ticks: float,
    ship_look: ShipLook,
    flow: GameFlow,
    overlay_visible: bool,
) -> None:
    """Draw the screen the flow shows on the window.

    The menu, the instructions page and the leaderboard page fill the whole window: the backdrop,
    then the page alone, with no world, overlay, HUD or frame. Playing, paused and game over draw
    the background and the run's world on `field`, the play area (_draw_run), then the panel and
    frame on the window. Paused and game over then dim the whole window and draw their box centered
    on it. Source: systems/app/frame-loop.md, Rules, Draw; systems/game-flow.md, Presentation.
    """
    if flow.screen in _RUN_SCREENS:
        draw_background(field, background, background_ticks)
        _draw_run(field, flow, overlay_visible, ship_look, int(background_ticks))
        hud.draw(window, flow.run, flow.best, int(background_ticks))
        if flow.screen is Screen.PAUSED:
            hud.dim(window)
            draw_pause_box(window, look)
        elif flow.screen is Screen.GAME_OVER:
            hud.dim(window)
            _draw_game_over(window, look, flow)
        return
    backdrop.draw(window, background, background_ticks)
    if flow.screen is Screen.MENU:
        draw_menu(window, look, flow.menu_selection)
    elif flow.screen is Screen.INSTRUCTIONS:
        draw_instructions(window, look)
    elif flow.screen is Screen.LEADERBOARD:
        draw_leaderboard(window, look, flow.leaderboard)


def _draw_run(
    surface: pygame.Surface,
    flow: GameFlow,
    overlay_visible: bool,
    ship_look: ShipLook,
    ticks: int,
) -> None:
    """Draw the starfield, the drifters, the points popups, the ship while shown or the burst in the
    last life, the graze rings and the debug outlines, overlay and wave lines if visible, all on
    `surface`, the play area.

    Drifters sit behind the ship, and the popups over the drifters and behind the ship. The ship
    shows its flames only while it flies: not paused, not waiting to respawn. `ticks` steps the
    flame flicker. The burst takes the ship's place. The graze rings sit over the ship and don't
    follow its blink. The HUD is not drawn here: it lives outside the play area. Source:
    systems/app/frame-loop.md, Rules, Draw and Drifters behind the ship, Graze rings over the ship.
    """
    run: Run = flow.run
    draw_starfield(surface, run.scroll)
    for drifter in run.drifters:
        render_drifter(surface, drifter)
    for popup in run.popups:
        draw_points_popup(surface, popup)
    if run.ship_visible:
        flying: bool = flow.screen is Screen.PLAYING and not run.waiting
        draw_ship(surface, run.ship, run.held if flying else None, ticks, ship_look)
    if run.last_life and run.burst is not None:
        draw_burst(surface, run.burst)
    for ring in run.graze_rings:
        draw_graze_ring(surface, ring, run.ship)
    if overlay_visible:
        draw_debug_hitboxes(surface, run)
        draw_debug_overlay(surface, run.ship)
        draw_debug_wave_lines(surface, run)


def _draw_game_over(surface: pygame.Surface, look: ScreenLook, flow: GameFlow) -> None:
    """Draw the game-over box: the place message, the score, the letter picker when the run has
    one, then RETRY and MENU, active once the picker no longer takes keys.

    Source: systems/game-flow.md, Presentation (`flow.screen` GAME_OVER row);
    systems/app/frame-loop.md, Rules, Draw.
    """
    picker_shown: bool = flow.picker is not None
    draw_game_over(surface, look, flow.game_over_message, picker_shown)
    draw_final_score(surface, look, flow.run.score, picker_shown)
    if flow.picker is not None:
        draw_name_picker(surface, look, flow.picker, flow.picking)
    draw_game_over_choices(
        surface, look, flow.game_over_selection, picker_shown, active=not flow.picking
    )
