# App, frame loop
Part of: app
Read when: you change the frame loop: ticks, keys, draw order, the catch-up cap.

## Interface

### game/app/loop.py (Integration Engineer)
```python
async def run() -> None:
    ...
    # Startup order, then guarded(functools.partial(start, choice.mode), choice.mode).


async def start(mode: RunMode) -> None:
    ...
    # The guarded body. Imports app.frame here, inside the guard, then awaits frame_loop(mode).
```
Module level: stdlib, `app.mode`, `app.log` and `app.guard` only. No pygame, no `core`, no `ui`, no `app.frame`.

### game/app/frame.py (Integration Engineer)
```python
ARROW_NAMES: dict[
    int, str
]  # pygame.K_UP -> "up", K_DOWN -> "down", K_LEFT -> "left", K_RIGHT -> "right"


async def frame_loop(mode: RunMode) -> None:
    ...
    # pygame init, window, frames until pygame.QUIT.
    # Owns: run (core.run.Run), thrust (core.ship.Thrust), overlay_visible (bool).
```
Imports pygame, `app.settings`, `app.mode`, `app.tuning` and `app.debug_spawns` (DRA-29), `core.world`, `core.ship` (for `Thrust`), `core.run`, `ui.look`, `ui.starfield`, `ui.drifters.registry` (DRA-29, for `render_drifter`), `ui.ship_view`, `ui.debug_overlay`, `ui.game_over` and `ui.hud`. From DRA-23 it no longer imports `core.scroll`, `spawn` or `step`. From DRA-76 it also imports `random` (stdlib), `app.waves`, `core.waves` (for `start_waves`) and `draw_debug_wave_lines` from `ui.debug_overlay`. Only `start()` imports this module, inside the guard.

App-owned state in `frame_loop` (DRA-23, DRA-29, DRA-39):
```python
tuning: DrifterTuning  # DRA-29. app.tuning.load_tuning() once, before start_run(). Never reloaded
spawn_list: (
    DebugSpawnList | None
)  # DRA-39. Debug mode: app.debug_spawns.load_debug_spawns(tuning) once,
# right after load_tuning(). Normal mode: None, the file is never read
book: WaveBook  # DRA-76. app.waves.load_wave_book(tuning) once, in both modes, right after
# load_tuning() and before the spawn list. Never reloaded
plays_list: bool  # DRA-76. True only when spawn_list is not None and spawn_list.play == PLAY_LIST.
# Fixed for the page
run: Run  # core.run.start_run(waves=...) before the first frame (waves: start_waves(book,
# random.getrandbits(64)), or None when plays_list); replaced by step_run() every tick,
# and by add_drifters() after every tick
thrust: Thrust  # rebuilt once per frame from the held arrow keys
overlay_visible: (
    bool  # True from the first frame in debug mode, always False in normal mode.
)
# F3 flips it, debug mode only.
```
The ship, the scroll and the drifters are `run.ship`, `run.scroll` and `run.drifters`. The app never keeps its own copy.

## Rules

Frame loop (`app/frame.py`, `frame_loop(mode)`):
- Inside the guard: `pygame.init()`, then `pygame.display.set_mode((SCREEN_W, SCREEN_H))` from `core.world`. Source: 03-world-and-camera.md, screen_w, screen_h (guess). systems/world.md.
- Before the first frame (DRA-29): `tuning = load_tuning()`, in both modes, before `start_run()`. A bad or missing tuning file raises inside the guard, so the page shows the error screen and the log holds the file and field. Source: game/CONTEXT.md, Error handling (validate at the edge); 15-tech-constraints.md, rule 8; scope report DRA-29, Limits ("The app loads and validates them once at startup").
- Before the first frame, debug mode only (DRA-39): `spawn_list = load_debug_spawns(tuning)`, right after `load_tuning()`. A bad or missing list raises inside the guard the same way. Normal mode never reads the file, so a broken list can't break normal play. Source: 15-tech-constraints.md, rule 7 (debug only adds the test spawn list); scope report DRA-39, Limits.
- Before the first frame, both modes (DRA-76): `book = load_wave_book(tuning)`, right after `load_tuning()` and before the spawn list. A bad or missing wave file raises inside the guard, so the page shows the error screen and the log names the file and the problem, in both modes, whatever debug mode plays. Source: scope report DRA-76, Limits ("Loading the wave and playlist files once at startup, in both modes"); 15-tech-constraints.md, rule 8.
- Before the first frame (DRA-76): `plays_list` is True only in debug mode with the spawn list's `play` equal to `PLAY_LIST` (its default). The run is `start_run(waves=None)` when `plays_list`, else `start_run(waves=start_waves(book, random.getrandbits(64)))`: one seed from Python's `random` module, which the interpreter seeds from the OS at start, drawn once per page load. Core makes every later run's seed from it (`systems/waves.md`, Seeds). The app never draws another seed and never restarts the waves. Source: 10-ui.md, rule 7; 09-waves.md, rule 4 (picks new every run); scope report DRA-76, Not in GDD (picks not seeded, new every run).
- Before the first frame: `overlay_visible = mode is RunMode.DEBUG`. Play starts at `start_run`: the ship first appears at screen center on the first frame drawn after this. Source: 03-world-and-camera.md, ship_start; 10-ui.md, debug_overlay_toggle (shown from the first frame); scope report DRA-13, Values needed (play start); systems/run.md (DRA-23).
- The app never calls `spawn`, `step`, `start_scroll` or `step_scroll` itself, and never calls `start_run()` again. A respawn, the wait, game over and a retry all happen inside `step_run`. Source: systems/run.md (DRA-23).
- **Game over.** While `run.game_over` is True the frame loop carries on as always: it reads events, builds `thrust`, runs ticks (`step_run` keeps the run frozen and watches for the retry) and draws. Nothing in the app changes. Source: 02-game-flow.md, rules 5 and 6; systems/run.md.
- Each frame, in order: read all events, build `thrust` from the held keys, add the frame time to the accumulator, run one tick per whole 1/60 s in the accumulator, draw, `pygame.display.flip()`, `await asyncio.sleep(0)`. Source: 15-tech-constraints.md, rules 1 and 2.
- Frame time comes from a monotonic clock (`time.perf_counter`). Ticks never use frame time. Source: 15-tech-constraints.md, rule 2.
- **Held keys.** After the events, read `pygame.key.get_pressed()` once and build `Thrust(up=pressed[K_UP], down=pressed[K_DOWN], left=pressed[K_LEFT], right=pressed[K_RIGHT])`. Every tick in that frame uses the same `thrust`. Only the four arrow keys move the ship. Source: 01-vision.md, locked decision 1; 04-ship.md, rule 2.1.
- **Tick.** `run = step_run(run, thrust)`. One `step_run` call per tick. Right after it, every tick: `run = add_drifters(run, due, tuning)`, where `due` is `debug_spawns_due(spawn_list, run.scroll.ticks)` when `plays_list`, else `run.wave_spawns_due` (DRA-76). Never both. The app never builds a drifter itself, never changes `run.drifters` and never reads a wave. Source: 04-ship.md, rule 1; 15-tech-constraints.md, rules 2 and 7; systems/run.md; scope report DRA-76, Limits ("Debug mode: ... the normal waves or the test spawn list").
- **Draw.** In this order: fill with `ui.look.BACKGROUND`; `draw_starfield(surface, run.scroll)`; `render_drifter(surface, obj)` for each `obj` in `run.drifters`, in order (DRA-29); `draw_points_popup(surface, popup)` for each `popup` in `run.popups`, in order (DRA-62); `draw_ship(surface, run.ship)` only if `run.ship_visible`; only if `overlay_visible`, `draw_debug_hitboxes(surface, run)` (DRA-29), then `draw_debug_overlay(surface, run.ship)`, then `draw_debug_wave_lines(surface, run)` (DRA-76); only if `run.game_over`, `draw_game_over(surface)` then `draw_final_score(surface, run.score)` (DRA-61: the final score); `draw_hud(surface, run, below_overlay=debug)` last, on top of everything. Source: systems/ship.md, systems/drifters.md, systems/debug-overlay.md, systems/scroll.md, systems/run.md and systems/hud.md, Presentation; 10-ui.md, rules 1 (the HUD on top) and 3 (the blink); 12-art-and-audio.md, rule 2 (the background stays behind).
- **Drifters behind the ship (DRA-29).** Warnings and meteorites are drawn after the starfield and before the ship, so the player's ship stays on top where they cross.
- **Popups over the drifters (DRA-62).** The points popups are drawn after every drifter, so they show over the other drifters, by Director decision, and before the ship, which stays on top as it does over every drifter. Source: scope report DRA-62, Limits and Decision log (Q5, Director override of Objection 1); systems/run.md, Presentation.
- **`below_overlay`** is `mode is RunMode.DEBUG`, fixed for the run. Never `overlay_visible`: in debug mode the HUD stays below the overlay's place while F3 hides it, so the readout never jumps. Source: scope report DRA-13, HUD layout.
- `pygame.QUIT`: log INFO `quit` and leave the loop. That only happens on desktop.
- **Arrow keys** (Up, Down, Left, Right): on `KEYDOWN` log DEBUG `key down key=%s x=%.2f y=%.2f`, on `KEYUP` log DEBUG `key up key=%s x=%.2f y=%.2f`, with names `up`, `down`, `left`, `right` and the ship's `x` and `y` (`run.ship.x`, `run.ship.y` from DRA-23) at the moment the event is read (before this frame's ticks). Example: `key down key=up x=320.00 y=240.00`. No other arrow event is logged. Source: game/CONTEXT.md, Logging (a key pressed or released is an event). 01-vision.md, locked decision 1. Director decision (DRA-6: the integration check compares y between key-down and key-up).
- **F3.** In debug mode, on `KEYDOWN` of `pygame.K_F3`: flip `overlay_visible` and log DEBUG `overlay visible=%s`. `KEYUP` of F3 does nothing. In normal mode F3 does nothing and logs nothing. F3 never retries: only `thrust`, built from the four arrows, reaches `step_run` (02-game-flow.md, retry_key, locked). Source: 10-ui.md, debug_overlay_toggle (guess) and rule 7.
- **Log by event.** The frame loop logs only on the events in these rules: quit, arrow keys, F3 and the cap. Never a line per tick or per frame. Ship events (wall hit, top-line stop) are logged by `core.ship`, the scroll start by `core.scroll`, and the run's events (life lost, respawn, wait end, invulnerable end, game over, new run, and from DRA-29 drifter spawn, active, touch and gone) by `core.run`, not by the app. The app's only drifter lines are the one `tuning loaded` line at startup and, in debug mode, the one `debug spawns loaded` line after it (DRA-39). From DRA-76 it also logs the one `waves loaded` line at startup; the wave events (`wave start`, `wave end`, `level up`, `rest start`) are `core.waves`' own. Source for the run's lines: systems/run.md, Logging (DRA-23). Source: 15-tech-constraints.md, rule 9; systems/ship.md, Rules, Logging.
- **Catch-up cap.** One frame runs at most `MAX_TICKS_PER_FRAME` (5) ticks. If, after the 5th tick, the accumulator still holds one tick or more, set it to 0.0: the owed time is dropped, never run later. The game carries on from where it was. Source: 15-tech-constraints.md, max_ticks_per_frame (guess) and rule 2; 91-decision-log.md, row 21.
- **Cap log, by event.** Log DEBUG `tick cap hit, dropped %.3f s` (the seconds dropped) on a frame where the cap drops time and the frame before didn't. While frames keep hitting the cap, log nothing more. The next capped frame after an uncapped one logs again. Source: 15-tech-constraints.md, rule 9.
- No `time.sleep`, no thread, no blocking call. Source: 15-tech-constraints.md, rule 1.
