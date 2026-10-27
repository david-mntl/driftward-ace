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
    # Owns: flow (core.game_flow.GameFlow, from DRA-125; it holds the run), thrust (core.ship.Thrust),
    # confirm and focus_lost_pending (bool, DRA-125), overlay_visible (bool).
```
Imports pygame, `app.settings`, `app.mode`, `app.tuning` and `app.debug_spawns` (DRA-29), `core.world`, `core.ship` (for `Thrust`), `core.run`, `ui.look`, `ui.starfield`, `ui.drifters.registry` (DRA-29, for `render_drifter`), `ui.ship_view`, `ui.debug_overlay`, `ui.game_over` and `ui.hud`. From DRA-23 it no longer imports `core.scroll`, `spawn` or `step`. From DRA-76 it also imports `random` (stdlib), `app.waves`, `core.waves` (for `start_waves`) and `draw_debug_wave_lines` from `ui.debug_overlay`. From DRA-117 it also imports `load_graze_rules` from `app.tuning` and `draw_graze_ring` from `ui.graze_view`. From DRA-125 it also imports `load_last_life_rules` from `app.tuning`, `core.game_flow` (`GameFlow`, `Screen`, `TickInput`, `start_flow`, `step_flow`, `add_flow_drifters`), `draw_burst` from `ui.burst_view`, `draw_menu` from `ui.menu`, `draw_instructions` from `ui.instructions`, `draw_leaderboard` from `ui.leaderboard`, `draw_pause_box` from `ui.pause_box` and `draw_game_over_choices` from `ui.game_over`; it no longer calls `step_run` or `add_drifters` itself. From DRA-126 it also imports `load_saves` and `write_saves` from `app.saves`, `stop_saves` from `core.game_flow` and `draw_name_picker` from `ui.game_over`. Only `start()` imports this module, inside the guard.

DRA-125 adds, module level:
```python
CONFIRM_NAMES: dict[int, str]  # pygame.K_RETURN -> "enter", K_KP_ENTER -> "enter", K_SPACE -> "space"
FOCUS_LOST_EVENTS: frozenset[int]  # pygame.WINDOWFOCUSLOST, WINDOWHIDDEN, WINDOWMINIMIZED
```

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
graze_rules: GrazeRules  # DRA-117. app.tuning.load_graze_rules() once, in both modes, right after
# load_tuning(). Never reloaded
last_life_rules: LastLifeRules  # DRA-125. app.tuning.load_last_life_rules() once, in both modes, right
# after load_graze_rules(). Never reloaded
flow: GameFlow  # DRA-125. start_flow(start_run(waves=..., graze_rules=graze_rules,
# last_life_rules=last_life_rules), saves) before the first frame (waves: start_waves(book,
# random.getrandbits(64)), or None when plays_list; saves from DRA-126); replaced by step_flow()
# every tick, by add_flow_drifters() after every tick, and by stop_saves() after a failed write
# (DRA-126). Replaces the bare `run` of DRA-23 to DRA-117
thrust: Thrust  # rebuilt once per frame from the held arrow keys
confirm: bool  # DRA-125. Rebuilt once per frame: Enter or Space held now
focus_lost_pending: bool  # DRA-125. Set when a focus-lost event is read; given to the next tick, then cleared
overlay_visible: (
    bool  # True from the first frame in debug mode, always False in normal mode.
)
# F3 flips it, debug mode only.
```
The run is `flow.run`; the ship, the scroll and the drifters are `flow.run.ship`, `flow.run.scroll` and `flow.run.drifters`. The app never keeps its own copy of any of them, nor of the screen or a selection.

## Rules

Frame loop (`app/frame.py`, `frame_loop(mode)`):
- Inside the guard: `pygame.init()`, then `pygame.display.set_mode((SCREEN_W, SCREEN_H))` from `core.world`. Source: 03-world-and-camera.md, screen_w, screen_h (guess). systems/world.md.
- Before the first frame (DRA-29): `tuning = load_tuning()`, in both modes, before `start_run()`. A bad or missing tuning file raises inside the guard, so the page shows the error screen and the log holds the file and field. Source: game/CONTEXT.md, Error handling (validate at the edge); 15-tech-constraints.md, rule 8; scope report DRA-29, Limits ("The app loads and validates them once at startup").
- Before the first frame, debug mode only (DRA-39): `spawn_list = load_debug_spawns(tuning)`, right after `load_tuning()`. A bad or missing list raises inside the guard the same way. Normal mode never reads the file, so a broken list can't break normal play. Source: 15-tech-constraints.md, rule 7 (debug only adds the test spawn list); scope report DRA-39, Limits.
- Before the first frame, both modes (DRA-76): `book = load_wave_book(tuning)`, right after `load_tuning()` and before the spawn list. A bad or missing wave file raises inside the guard, so the page shows the error screen and the log names the file and the problem, in both modes, whatever debug mode plays. Source: scope report DRA-76, Limits ("Loading the wave and playlist files once at startup, in both modes"); 15-tech-constraints.md, rule 8.
- Before the first frame, both modes (DRA-117): `graze_rules = load_graze_rules()`, right after `load_tuning()`. A bad or missing `scoring.json` raises inside the guard, so the page shows the error screen and the log names the file and the field. The run is started with it: `start_run(waves=..., graze_rules=graze_rules)`, below. A retry keeps it inside core (`systems/run.md`, a game-over tick). Source: scope report DRA-117, Limits ("Every value in tuning"); 15-tech-constraints.md, rule 8.
- Before the first frame (DRA-76): `plays_list` is True only in debug mode with the spawn list's `play` equal to `PLAY_LIST` (its default). The run is `start_run(waves=None, graze_rules=graze_rules)` when `plays_list`, else `start_run(waves=start_waves(book, random.getrandbits(64)), graze_rules=graze_rules)` (`graze_rules` from DRA-117): one seed from Python's `random` module, which the interpreter seeds from the OS at start, drawn once per page load. Core makes every later run's seed from it (`systems/waves.md`, Seeds). The app never draws another seed and never restarts the waves. Source: 10-ui.md, rule 7; 09-waves.md, rule 4 (picks new every run); scope report DRA-76, Not in GDD (picks not seeded, new every run).
- Before the first frame, both modes (DRA-125): `last_life_rules = load_last_life_rules()`, right after `load_graze_rules()`. A bad or missing `last_life.json` raises inside the guard, so the page shows the error screen and the log names the file and the field. The first run is started with it, `start_run(waves=..., graze_rules=graze_rules, last_life_rules=last_life_rules)`, and wrapped once: `flow = start_flow(run)`. The first frame shows the menu. Source: scope report DRA-125, Limits ("Every value in tuning, never hard-coded: `last_life_delay` ..."); 02-game-flow.md, rules 1 and 2; 15-tech-constraints.md, rule 8.
- Before the first frame, both modes (DRA-126): `saves = load_saves()`, right after `load_last_life_rules()`, then `flow = start_flow(run, saves)`. `load_saves` never raises for a storage or data problem: saves that don't work give None and the game starts as usual (`save-storage.md`). The saves are never read again. Source: 11-save-data.md, rule 5; 91-decision-log.md, row 93 (debug saves the same).
- Before the first frame: `overlay_visible = mode is RunMode.DEBUG`. From DRA-125 play starts when Play is picked on the menu: the ship first appears at screen center on the first frame drawn after that tick. Source: 03-world-and-camera.md, ship_start; 10-ui.md, debug_overlay_toggle (shown from the first frame); scope report DRA-13, Values needed (play start); systems/game-flow.md, Rules, MENU.
- The app never calls `spawn`, `step`, `start_scroll`, `step_scroll`, `start_run` (after the first), `step_run`, `next_run` or `add_drifters` itself. A respawn, the wait, the last life, game over, the pause, the screens and a new run all happen inside `step_flow`. Source: systems/run.md; systems/game-flow.md.
- **Screens.** On every screen the frame loop carries on as always: it reads events, builds `thrust` and `confirm`, runs ticks (`step_flow` decides what they do) and draws. Nothing in the app depends on the screen but the draw. Source: systems/game-flow.md, Rules.
- Each frame, in order: read all events, build `thrust` and `confirm` from the held keys, add the frame time to the accumulator, run one tick per whole 1/60 s in the accumulator, draw, `pygame.display.flip()`, `await asyncio.sleep(0)`. Source: 15-tech-constraints.md, rules 1 and 2.
- Frame time comes from a monotonic clock (`time.perf_counter`). Ticks never use frame time. Source: 15-tech-constraints.md, rule 2.
- **Held keys.** After the events, read `pygame.key.get_pressed()` once and build `Thrust(up=pressed[K_UP], down=pressed[K_DOWN], left=pressed[K_LEFT], right=pressed[K_RIGHT])`. Every tick in that frame uses the same `thrust`. Only the four arrow keys move the ship. Source: 01-vision.md, locked decision 1; 04-ship.md, rule 2.1.
- **Confirm keys** (DRA-125). From the same `get_pressed()`: `confirm` is True when any key in `CONFIRM_NAMES` is held (Enter, keypad Enter or Space). Every tick in that frame uses the same `confirm`. The app never works out a fresh press: `step_flow` does, from the held state tick by tick. Source: 02-game-flow.md, confirm_keys (locked), fresh_press; 01-vision.md, locked decision 1.
- **Focus** (DRA-125). An event in `FOCUS_LOST_EVENTS` (the window or the browser tab losing focus, being hidden or minimized) sets `focus_lost_pending = True`. The next tick gets `TickInput(focus_lost=True)`, then the flag is cleared, so each loss reaches exactly one tick even when its frame runs none. Getting the focus back sets nothing. The browser check must show which of these events pygbag delivers for a tab switch and a click outside the page; if none arrives for either, stop and report it: that is a contract change, not a fix. Source: 02-game-flow.md, pause_on_focus_loss (locked), rule 7; 91-decision-log.md, row 81.
- **Tick.** `flow = step_flow(flow, TickInput(thrust=thrust, confirm=confirm, focus_lost=focus_lost_pending))`, then `focus_lost_pending = False`. One `step_flow` call per tick. Right after it, every tick: `flow = add_flow_drifters(flow, due, tuning)`, where `due` is `debug_spawns_due(spawn_list, flow.run.scroll.ticks)` when `plays_list`, else `flow.run.wave_spawns_due` (DRA-76). Never both. `add_flow_drifters` adds them only after a tick the run was stepped, so a paused run, a page and the game-over screen get nothing (DRA-125). Then, every tick (DRA-126): if `flow.saves_changed` and `flow.saves` is not None, `write_saves(flow.saves)`; when it returns False, `flow = stop_saves(flow)`. So each saved entry is written right after its tick, even when one frame runs several ticks, and never twice. The app never builds a drifter itself, never changes `flow.run.drifters` and never reads a wave. It never builds, changes or orders a save entry: core does (`systems/saves.md`). Source: 04-ship.md, rule 1; systems/game-flow.md, `add_flow_drifters`; 15-tech-constraints.md, rules 2 and 7; systems/run.md; scope report DRA-76, Limits ("Debug mode: ... the normal waves or the test spawn list").
- **Draw** (from DRA-125 by `flow.screen`; `run` is `flow.run`). First fill with `ui.look.BACKGROUND`. On MENU: `draw_menu(surface, flow.menu_selection)`; on INSTRUCTIONS: `draw_instructions(surface)`; on LEADERBOARD: `draw_leaderboard(surface, flow.leaderboard)` (DRA-126); nothing else on those three: no world, no overlay, no HUD. On PLAYING, PAUSED and GAME_OVER, the list below, with three DRA-125 additions: `draw_burst(surface, run.burst)` only if `run.last_life`, right after the ship's place; on PAUSED, `draw_pause_box(surface)` in the game-over box's place; on GAME_OVER (not on `run.game_over`), the game-over calls of `systems/game-flow.md`, Presentation (`flow.screen` GAME_OVER row, DRA-126): `draw_game_over(surface, flow.game_over_message, picker_shown)`, `draw_final_score(surface, run.score, picker_shown)`, `draw_name_picker(surface, flow.picker, flow.picking)` only when `flow.picker` is not None, then `draw_game_over_choices(surface, flow.game_over_selection, picker_shown, active=not flow.picking)`, with `picker_shown = flow.picker is not None`. The HUD gets `best=flow.best` (DRA-126). The list: `draw_starfield(surface, run.scroll)`; `render_drifter(surface, obj)` for each `obj` in `run.drifters`, in order (DRA-29); `draw_points_popup(surface, popup)` for each `popup` in `run.popups`, in order (DRA-62); `draw_ship(surface, run.ship)` only if `run.ship_visible`; `draw_graze_ring(surface, ring, run.ship)` for each `ring` in `run.graze_rings`, in order, on every frame whatever `run.ship_visible` is (DRA-117); only if `overlay_visible`, `draw_debug_hitboxes(surface, run)` (DRA-29), then `draw_debug_overlay(surface, run.ship)`, then `draw_debug_wave_lines(surface, run)` (DRA-76); only if `run.game_over`, `draw_game_over(surface)` then `draw_final_score(surface, run.score)` (DRA-61: the final score); `draw_hud(surface, run, below_overlay=debug, best=flow.best)` last, on top of everything (`best` from DRA-126). Source: systems/ship.md, systems/drifters.md, systems/debug-overlay.md, systems/scroll.md, systems/run.md and systems/hud.md, Presentation; 10-ui.md, rules 1 (the HUD on top) and 3 (the blink); 12-art-and-audio.md, rule 2 (the background stays behind).
- **Drifters behind the ship (DRA-29).** Warnings and meteorites are drawn after the starfield and before the ship, so the player's ship stays on top where they cross.
- **Popups over the drifters (DRA-62).** The points popups are drawn after every drifter, so they show over the other drifters, by Director decision, and before the ship, which stays on top as it does over every drifter. Source: scope report DRA-62, Limits and Decision log (Q5, Director override of Objection 1); systems/run.md, Presentation.
- **Graze rings over the ship (DRA-117).** The rings are drawn right after the ship's place, so they show over the ship they grow from, and under the debug overlay, the Game Over box and the HUD. They don't follow the blink: a ring is not the ship. Graze popups are in `run.popups` and drawn with the coins' popups, in their DRA-62 place. Source: systems/run.md, Presentation (Graze ring); 06-scoring.md, graze_ring.
- **`below_overlay`** is `mode is RunMode.DEBUG`, fixed for the run. Never `overlay_visible`: in debug mode the HUD stays below the overlay's place while F3 hides it, so the readout never jumps. Source: scope report DRA-13, HUD layout.
- `pygame.QUIT`: log INFO `quit` and leave the loop. That only happens on desktop.
- **Arrow keys** (Up, Down, Left, Right): on `KEYDOWN` log DEBUG `key down key=%s x=%.2f y=%.2f`, on `KEYUP` log DEBUG `key up key=%s x=%.2f y=%.2f`, with names `up`, `down`, `left`, `right` and the ship's `x` and `y` (`run.ship.x`, `run.ship.y` from DRA-23) at the moment the event is read (before this frame's ticks). Example: `key down key=up x=320.00 y=240.00`. No other arrow event is logged. From DRA-125 x and y are `flow.run.ship.x` and `.y`, on every screen. Source: game/CONTEXT.md, Logging (a key pressed or released is an event). 01-vision.md, locked decision 1. Director decision (DRA-6: the integration check compares y between key-down and key-up).
- **Confirm keys log** (DRA-125): on `KEYDOWN` and `KEYUP` of a key in `CONFIRM_NAMES`, the same line as an arrow's with its name, `enter` or `space`: `key down key=space x=320.00 y=240.00`. Source: game/CONTEXT.md, Logging.
- **Focus log** (DRA-125): DEBUG `focus lost event=%s` on each event in `FOCUS_LOST_EVENTS`, with the event's name (`pygame.event.event_name`), e.g. `focus lost event=WindowFocusLost`. Nothing when the focus comes back. Source: game/CONTEXT.md, Logging.
- **F3.** In debug mode, on `KEYDOWN` of `pygame.K_F3`: flip `overlay_visible` and log DEBUG `overlay visible=%s`. `KEYUP` of F3 does nothing. In normal mode F3 does nothing and logs nothing. F3 never reaches core: only `thrust`, `confirm` and the focus reach `step_flow` (02-game-flow.md, retry_key, locked). Source: 10-ui.md, debug_overlay_toggle (guess) and rule 7.
- **Log by event.** The frame loop logs only on the events in these rules: quit, arrow keys, confirm keys and focus losses (DRA-125), F3 and the cap. The saves' load and write lines are `app.saves`' own (`save-storage.md`, DRA-126). Screen changes are logged by `core.game_flow`, the last life and game over by `core.run`. Never a line per tick or per frame. Ship events (wall hit, top-line stop) are logged by `core.ship`, the scroll start by `core.scroll`, and the run's events (life lost, respawn, wait end, invulnerable end, game over, new run, and from DRA-29 drifter spawn, active, touch and gone) by `core.run`, not by the app. The app's only drifter lines are the one `tuning loaded` line at startup and, in debug mode, the one `debug spawns loaded` line after it (DRA-39). From DRA-76 it also logs the one `waves loaded` line at startup; the wave events (`wave start`, `wave end`, `level up`, `rest start`) are `core.waves`' own. Source for the run's lines: systems/run.md, Logging (DRA-23). Source: 15-tech-constraints.md, rule 9; systems/ship.md, Rules, Logging.
- **Catch-up cap.** One frame runs at most `MAX_TICKS_PER_FRAME` (5) ticks. If, after the 5th tick, the accumulator still holds one tick or more, set it to 0.0: the owed time is dropped, never run later. The game carries on from where it was. Source: 15-tech-constraints.md, max_ticks_per_frame (guess) and rule 2; 91-decision-log.md, row 21.
- **Cap log, by event.** Log DEBUG `tick cap hit, dropped %.3f s` (the seconds dropped) on a frame where the cap drops time and the frame before didn't. While frames keep hitting the cap, log nothing more. The next capped frame after an uncapped one logs again. Source: 15-tech-constraints.md, rule 9.
- No `time.sleep`, no thread, no blocking call. Source: 15-tech-constraints.md, rule 1.
