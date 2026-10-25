# App, release
Part of: app
Read when: you change the launch script, the release package or `pygbag.ini`.

## Interface

### pygbag.ini (repo root, Integration Engineer)
```ini
[DEPENDENCIES]
ignoreDirs = [...]    # folders under game/ left out of the package
ignoreFiles = [...]   # files under game/ left out of the package
```
pygbag 0.9.3 reads it from its working directory. The start script and the build check both run pygbag from the repo root. Source: Director decision (DRA-5 close-out, round 1 observations). docs/crew/roster.md, row 12.

The DRA-6 and DRA-13 call blocks below are kept as history. From DRA-23 the ship and scroll calls in them are replaced: the current order is the DRA-23 block after them.

DRA-6 calls, all made by `frame_loop`. Their signatures are set in the DRA-6 contracts:
```python
# before the first frame:
ship = spawn()  # systems/ship.md
# per frame, after the events:
thrust = Thrust(up=..., down=..., left=..., right=...)
# per tick, inside the accumulator loop:
ship = step(ship, thrust)  # systems/ship.md
# per frame, draw:
surface.fill(BACKGROUND)
draw_ship(surface, ship)  # systems/ship.md
if overlay_visible:
    draw_debug_overlay(surface, ship)  # systems/debug-overlay.md
```

DRA-13 calls, all made by `frame_loop`. Their signatures are set in the DRA-13 contracts. The full order, with the DRA-6 calls in place:
```python
# before the first frame:
ship = spawn()
scroll = start_scroll()  # systems/scroll.md, right after spawn(): play starts
# per tick, inside the accumulator loop:
ship = step(ship, thrust)
scroll = step_scroll(scroll)  # systems/scroll.md
# per frame, draw:
surface.fill(BACKGROUND)
draw_starfield(surface, scroll)  # systems/scroll.md, behind everything
draw_ship(surface, ship)
if overlay_visible:
    draw_debug_overlay(surface, ship)
draw_hud(
    surface, scroll, below_overlay=debug
)  # systems/hud.md, last; debug = mode is RunMode.DEBUG
```

DRA-23 calls, all made by `frame_loop`. Their signatures are set in `systems/run.md` and `systems/hud.md`. They replace the DRA-6 and DRA-13 ship and scroll calls above. The full order:
```python
# before the first frame:
run = start_run()  # systems/run.md: spawn() and start_scroll(), play starts
# per frame, after the events:
thrust = Thrust(up=..., down=..., left=..., right=...)
# per tick, inside the accumulator loop:
run = step_run(run, thrust)  # systems/run.md: the only call per tick
# per frame, draw:
surface.fill(BACKGROUND)
draw_starfield(surface, run.scroll)
if run.ship_visible:
    draw_ship(surface, run.ship)  # the blink
if overlay_visible:
    draw_debug_overlay(surface, run.ship)
if run.game_over:
    draw_game_over(surface)  # systems/run.md, Presentation
draw_hud(surface, run, below_overlay=debug)  # systems/hud.md, last
```

DRA-29 calls, all made by `frame_loop`. Their signatures are set in `systems/drifters.md`, `systems/run.md` and `systems/debug-overlay.md`. They add to the DRA-23 block above. The full order:
```python
# before the first frame:
tuning = load_tuning()  # app.tuning, both modes. A bad file raises here
run = start_run()
# per frame, after the events:
thrust = Thrust(up=..., down=..., left=..., right=...)
# per tick, inside the accumulator loop:
run = step_run(run, thrust)
if debug:
    run = add_drifters(
        run, debug_spawns_due(run.scroll.ticks), tuning
    )  # systems/run.md
# per frame, draw:
surface.fill(BACKGROUND)
draw_starfield(surface, run.scroll)
for obj in run.drifters:
    render_drifter(surface, obj)  # systems/drifters.md: warnings and drifters
if run.ship_visible:
    draw_ship(surface, run.ship)  # the inverted T (systems/ship.md)
if overlay_visible:
    draw_debug_hitboxes(
        surface, run
    )  # systems/debug-overlay.md: outlines and labels first
    draw_debug_overlay(surface, run.ship)
if run.game_over:
    draw_game_over(surface)
draw_hud(surface, run, below_overlay=debug)
```

DRA-39 calls, all made by `frame_loop`. They change the DRA-29 block above only before the first frame and in the tick. The draw order is unchanged: `render_drifter(surface, obj)` keeps its signature (the brightness and the tilt come from the drifter itself).
```python
# before the first frame:
tuning = (
    load_tuning()
)  # app.tuning, both modes: drifter files, playtest.json, hazards.json
spawn_list = (
    load_debug_spawns(tuning) if debug else None
)  # app.debug_spawns, debug mode only
run = start_run()
# per tick, inside the accumulator loop:
run = step_run(run, thrust)
if debug:
    run = add_drifters(run, debug_spawns_due(spawn_list, run.scroll.ticks), tuning)
```

DRA-61 calls. They add one call to the DRA-29 draw block above: the final score line, right after the Game Over box. Its signature is set in `systems/run.md`. `draw_game_over(surface)` and `draw_hud(surface, run, below_overlay=debug)` don't change; the HUD reads `run.score` itself.
```python
# per frame, draw:
if run.game_over:
    draw_game_over(surface)  # systems/run.md, Presentation: box, title, prompt
    draw_final_score(surface, run.score)  # systems/run.md, Presentation: the score line
draw_hud(surface, run, below_overlay=debug)  # systems/hud.md, last
```
`app/frame.py` imports `draw_final_score` from `ui.game_over`, next to `draw_game_over`.

DRA-62 calls. They add one loop to the DRA-29 draw block above: the points popups, right after the drifters and before the ship. Its signature is set in `systems/run.md`. Nothing else in the frame changes: coins enter through the same `add_drifters` call and are drawn by `render_drifter`.
```python
# per frame, draw:
for obj in run.drifters:
    render_drifter(surface, obj)  # systems/drifters.md: coins too
for popup in run.popups:
    draw_points_popup(surface, popup)  # systems/run.md, Presentation: over the drifters
if run.ship_visible:
    draw_ship(surface, run.ship)  # the ship stays on top of the popups
```
`app/frame.py` imports `draw_points_popup` from `ui.popup_view`.

DRA-76 calls. They change the DRA-39 block above before the first frame and in the tick, and add one call to the draw. Signatures are set in `systems/waves.md`, `systems/run.md` and `systems/debug-overlay.md`.
```python
# before the first frame:
tuning = load_tuning()  # app.tuning, both modes
book = load_wave_book(tuning)  # app.waves, both modes. A bad wave file raises here
spawn_list = load_debug_spawns(tuning) if debug else None  # app.debug_spawns, debug mode only
plays_list = spawn_list is not None and spawn_list.play == PLAY_LIST
run = start_run(waves=None if plays_list else start_waves(book, random.getrandbits(64)))
# per tick, inside the accumulator loop:
run = step_run(run, thrust)  # steps the waves too (systems/run.md, step 9a)
due = debug_spawns_due(spawn_list, run.scroll.ticks) if plays_list else run.wave_spawns_due
run = add_drifters(run, due, tuning)  # systems/run.md: the one way in, both sources
# per frame, draw:
if overlay_visible:
    draw_debug_hitboxes(surface, run)
    draw_debug_overlay(surface, run.ship)
    draw_debug_wave_lines(surface, run)  # systems/debug-overlay.md: lines 5 and 6
```
A retry needs no app call: `step_run` restarts the waves itself (`systems/run.md`, a game-over tick).

### game/scripts/start-driftward-ace.sh (Integration Engineer)
```
start-driftward-ace.sh            # serves the build, prints http://localhost:<PORT>
start-driftward-ace.sh --debug    # same build, prints http://localhost:<PORT>/?debug=1
```

## Rules

Launch script (`game/scripts/start-driftward-ace.sh`):
- `--debug`: same build and same server. The only difference is the printed URL, `http://localhost:${PORT}/?debug=1`. Source: 15-tech-constraints.md, debug_switch_launcher.
- No argument: unchanged behavior, prints `http://localhost:${PORT}`.
- Any other argument: print a usage line naming the bad argument to stderr and exit non-zero before starting anything.
- Keep the existing rules: `set -euo pipefail`, quoted variables, cleanup trap, never `--bind`. Source: game/CONTEXT.md, Good practice and INTEGRATION.
- Keep running pygbag from the repo root, so it reads `pygbag.ini`.

Release package (`pygbag.ini`):
- The package (`game.apk` inside `game/build/web.zip`, and the live build the start script serves) holds only runtime files: `main.py`, `app/`, `ui/`, `core/`, and later the asset and data files the game reads. From DRA-6, `core/*.py` must be in it. From DRA-29, `tuning/` with its JSON files must be in it, along with the subpackages `core/drifters/` and `ui/drifters/`. From DRA-76, `waves/` with its JSON files. Source: Director decision (DRA-5 close-out, round 1 observations).
- Left out, at least: `tests/` (with its `CONTEXT.md` and `conftest.py`), `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml`. Any non-runtime file added to `game/` later is left out the same way. Source: Director decision (DRA-5 close-out).
- Configured only in `pygbag.ini` at the repo root, `[DEPENDENCIES]` section, `ignoreDirs` and `ignoreFiles`. Built by the Integration Engineer. Source: Director decision (DRA-5 close-out). docs/crew/roster.md, row 12.
- No pygbag flag or template change. pygbag stays at 0.9.3. Source: 15-tech-constraints.md, web_build.
