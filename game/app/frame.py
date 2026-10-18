"""The async frame loop on the fixed 60 Hz tick. Imported only by app.loop.start, inside the guard.

Before the first frame it loads and checks the drifter tuning (both modes) and, in debug mode
only, the debug test spawn list. Each frame: read events, build the thrust from the held arrow
keys, run up to MAX_TICKS_PER_FRAME ticks (one core.run.step_run each, then in debug mode the
debug test spawn list's due drifters through core.run.add_drifters), draw the starfield, the
drifters, the points popups, the ship while the run shows it, the debug outlines and overlay if
visible, the Game Over box with the final score at game over and the HUD, flip, then yield to
the browser.
The app holds one Run; core does the ship, the scroll, the drifters, the lives, the respawn
wait, game over and retry.
Source: docs/contracts/systems/app.md, Rules, Frame loop. 15-tech-constraints.md, rules 1 and 2.
"""

import asyncio
import logging
import time

import pygame

from app.debug_spawns import DebugSpawnList, debug_spawns_due, load_debug_spawns
from app.mode import RunMode
from app.settings import MAX_TICKS_PER_FRAME, TICK_RATE
from app.tuning import load_tuning
from core.drifters.tuning import DrifterTuning
from core.run import Run, add_drifters, start_run, step_run
from core.ship import Thrust
from core.world import SCREEN_H, SCREEN_W
from ui.debug_overlay import draw_debug_hitboxes, draw_debug_overlay
from ui.drifters.registry import render_drifter
from ui.game_over import draw_final_score, draw_game_over
from ui.hud import draw_hud
from ui.look import BACKGROUND
from ui.popup_view import draw_points_popup
from ui.ship_view import draw_ship
from ui.starfield import draw_starfield

log = logging.getLogger(__name__)

TICK_SECONDS: float = 1 / TICK_RATE

ARROW_NAMES: dict[int, str] = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
}
"""The only keys that move the ship. Source: 01-vision.md, locked decision 1."""


async def frame_loop(mode: RunMode) -> None:
    """Open the window and run frames until pygame.QUIT (desktop only)."""
    pygame.init()
    surface: pygame.Surface = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    debug: bool = mode is RunMode.DEBUG
    tuning: DrifterTuning = load_tuning()
    spawn_list: DebugSpawnList | None = load_debug_spawns(tuning) if debug else None
    run: Run = start_run()
    overlay_visible: bool = debug
    accumulator: float = 0.0
    was_capped: bool = False
    previous: float = time.perf_counter()
    while True:
        keep_running, overlay_visible = _read_events(run, debug, overlay_visible)
        if not keep_running:
            break
        thrust: Thrust = _held_thrust()
        now: float = time.perf_counter()
        accumulator += now - previous
        previous = now
        run, accumulator = _run_ticks(run, thrust, accumulator, spawn_list, tuning)
        was_capped = _apply_cap(accumulator, was_capped)
        if was_capped:
            accumulator = 0.0
        _draw(surface, run, overlay_visible, debug)
        pygame.display.flip()
        await asyncio.sleep(0)
    log.info("quit")


def _read_events(run: Run, debug: bool, overlay_visible: bool) -> tuple[bool, bool]:
    """Drain the event queue. Log arrow keys with the ship's x/y, and toggle the overlay on F3.

    F3 works in debug mode only and never reaches core. Returns (keep_running,
    overlay_visible); keep_running is False on pygame.QUIT.
    """
    keep_running: bool = True
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            keep_running = False
        elif event.type in (pygame.KEYDOWN, pygame.KEYUP) and event.key in ARROW_NAMES:
            direction: str = "down" if event.type == pygame.KEYDOWN else "up"
            log.debug(
                "key %s key=%s x=%.2f y=%.2f",
                direction,
                ARROW_NAMES[event.key],
                run.ship.x,
                run.ship.y,
            )
        elif debug and event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            overlay_visible = not overlay_visible
            log.debug("overlay visible=%s", overlay_visible)
    return keep_running, overlay_visible


def _held_thrust() -> Thrust:
    """Build the thrust from the arrow keys held now. Read once per frame, used by every tick."""
    pressed = pygame.key.get_pressed()
    return Thrust(
        up=pressed[pygame.K_UP],
        down=pressed[pygame.K_DOWN],
        left=pressed[pygame.K_LEFT],
        right=pressed[pygame.K_RIGHT],
    )


def _run_ticks(
    run: Run,
    thrust: Thrust,
    accumulator: float,
    spawn_list: DebugSpawnList | None,
    tuning: DrifterTuning,
) -> tuple[Run, float]:
    """Run one tick per whole TICK_SECONDS in the accumulator, at most MAX_TICKS_PER_FRAME.

    Each tick is one step_run call. In debug mode only (spawn_list is not None), right after
    it, the spawn list's due placements go in through add_drifters. Returns (run, accumulator
    left). Source: 15-tech-constraints.md, rules 2 and 7; systems/app.md, Rules, Tick.
    """
    ticks: int = 0
    while accumulator >= TICK_SECONDS and ticks < MAX_TICKS_PER_FRAME:
        run = step_run(run, thrust)
        if spawn_list is not None:
            run = add_drifters(run, debug_spawns_due(spawn_list, run.scroll.ticks), tuning)
        accumulator -= TICK_SECONDS
        ticks += 1
    return run, accumulator


def _apply_cap(accumulator: float, was_capped: bool) -> bool:
    """Return True if the cap drops time this frame. Log only when capping starts.

    The caller sets the accumulator to 0.0 when this returns True.
    Source: systems/app.md, Rules, Catch-up cap and Cap log; 91-decision-log.md, row 21.
    """
    capped: bool = accumulator >= TICK_SECONDS
    if capped and not was_capped:
        log.debug("tick cap hit, dropped %.3f s", accumulator)
    return capped


def _draw(surface: pygame.Surface, run: Run, overlay_visible: bool, debug: bool) -> None:
    """Fill the background, then draw the starfield, the drifters, the points popups, the ship
    while shown, the debug outlines and overlay if visible, the Game Over box and its final
    score line at game over, and the HUD last.

    Drifters sit behind the ship, and the popups over the drifters and behind the ship. The HUD
    sits below the overlay's place for the whole run in debug mode, even while F3 hides the
    overlay. Source: systems/app.md, Rules, Draw, Drifters behind the ship and below_overlay.
    """
    surface.fill(BACKGROUND)
    draw_starfield(surface, run.scroll)
    for drifter in run.drifters:
        render_drifter(surface, drifter)
    for popup in run.popups:
        draw_points_popup(surface, popup)
    if run.ship_visible:
        draw_ship(surface, run.ship)
    if overlay_visible:
        draw_debug_hitboxes(surface, run)
        draw_debug_overlay(surface, run.ship)
    if run.game_over:
        draw_game_over(surface)
        draw_final_score(surface, run.score)
    draw_hud(surface, run, below_overlay=debug)
