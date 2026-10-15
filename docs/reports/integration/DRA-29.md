Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-29 (object base, spawner and the meteorite) into the app. Requested in Integrate mode. All nine DRA-29 QA reports have `Verdict: pass` on line 1.
2. **Delivered:** `game/app/tuning.py` (new, the tuning loader), `game/app/debug_spawns.py` (new, the debug test spawn list), `game/app/frame.py` (tuning load, `add_objects` after each tick in debug mode, the DRA-29 draw order), `docs/reports/integration/DRA-29.md`. No change to `game/main.py`, the other `game/app/` modules, `game/scripts/start-driftward-ace.sh` or `pygbag.ini`, as the Impact table in `docs/contracts/systems/app.md` says.
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck, core and ui all PASS, `QA: pass`.
   - Headless import (`SDL_VIDEODRIVER=dummy`, from `game/`): `import app.loop, app.frame, app.guard, app.tuning, app.debug_spawns` is clean.
   - Desktop runs, headless: a 4 s run of `main.py` with `DRIFTWARD_DEBUG=1` logged `start mode=debug`, `tuning loaded objects=meteorite hazard_speed_scaling=True timer_scaling=True`, then the same object timeline as the browser. A 3 s normal run logged only the start line, `tuning loaded` and `quit`.
   - Tuning loader, 20 bad-file cases run against scratch copies of `game/tuning/`. Each raised `ValueError` naming the file from `tuning/` down and the field, for example `tuning/objects/meteorite.json: variants.small.hitbox[0].r must be a number > 0`. The cases: a bool width, r 0, a circle bigger than its variant, an unknown default variant, an extra field, a missing field, `entry_warning_ticks` 30.0 and 0, a negative `speed_ratio`, a bad variant name, no variants, an empty hitbox, an unknown shape, a box outside its variant, invalid JSON, a string switch and an extra switch. A box that fits was accepted. A missing `playtest.json` raised `FileNotFoundError` with its path.
   - Desktop guard checks, headless, all still pass:
     - **DRA-29 bad tuning file:** `"speed_ratio": "fast"` in a scratch copy, with `app.tuning.TUNING_DIR` pointed at it. The log shows `start mode=debug`, then ERROR `unexpected error, showing the error screen` with `ValueError: tuning/objects/meteorite.json: speed_ratio must be a number`. There is no `error screen failed` line, and the process idled until `timeout` stopped it (exit 124).
     - **DRA-5, `app.frame` blocked:** the start line, then the ERROR with the `ModuleNotFoundError`, then it idled (exit 124).
     - **DRA-5, `pygame` blocked:** the ERROR, then ERROR `error screen failed`, then it exited by itself (exit 0).
     - **DRA-19, null character:** the ERROR with `ValueError: bad\x00value`, no `error screen failed`, then it idled (exit 124).
   - Build: `pygbag --archive game` from the repo root built `game/build/web.zip` (git-ignored, not committed). The package contents are clean. See Browser run.
   - Browser: every required check and every DRA-29 check in `systems/app.md` passed, and so did the earlier DRA-5 to DRA-23 checks as reworded for DRA-29. See Browser run.
   - Logging is by event. The app adds one DRA-29 line, INFO `tuning loaded ...` at startup. Nothing is logged per tick or per frame.
4. **Assumptions:** none beyond the loader choices under Decisions.
5. **Documentation differences:** None.
6. **Next:** I started the Architect for the DRA-29 close-out (prompt: "Close-out run for DRA-29. Integration report: docs/reports/integration/DRA-29.md"). Director: run `game/scripts/start-driftward-ace.sh --debug` and open `http://localhost:6060/?debug=1` to see the test meteorites, or run it with no argument for normal mode. Build check: `pygbag --archive game` from the repo root gives `game/build/web.zip`. The frame loop changed, so the contract asks you to check pygbag's click screen by hand in a desktop browser (see Observations).
7. **Status:** done.

## Browser run
- **Build check:** `pygbag --archive game` (pygbag 0.9.3), run from the repo root, gave `game/build/web.zip` (73350 bytes). It holds `index.html`, `favicon.png` and `game.apk`. Listed with Python's `zipfile`, `game.apk` holds exactly:
  - `assets/main.py`
  - `assets/app/{debug_spawns,frame,guard,log,loop,mode,settings,tuning}.py`
  - `assets/core/{collision,levels,run,scroll,ship,world}.py`
  - `assets/core/objects/{__init__,base,meteorite,registry,spawner,tuning}.py`
  - `assets/tuning/objects/meteorite.json` and `assets/tuning/playtest.json`
  - `assets/ui/{debug_overlay,error_screen,game_over,hud,look,shapes,ship_view,starfield}.py`
  - `assets/ui/objects/{__init__,entry_warning,meteorite_view,registry}.py`

  There is no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml`, `__pycache__` or tool cache. The packed `app/frame.py` calls `add_objects`. **Passed.**
- **Served** with `game/scripts/start-driftward-ace.sh --debug` in the background (script pid 396176, log and pid file in the scratchpad). Port 6060 was free first, and `curl` got 200 after 2 s. I opened 15 pages against that one server, closing each tab before the next. They break down as eleven `?debug=1`, three `/` and one `?debug=yes`.
- **Stopped** with `kill 396176`. The trap logged `Stopping server (pid 396186)` and `Server stopped`. Port 6060 was free afterwards.
- **How inputs and reads were done:**
  - Keys were sent as `keydown`/`keyup` `KeyboardEvent`s on `#canvas` through `browser_evaluate`, as in DRA-6 to DRA-23.
  - Console lines were timestamped in page ms by a `console.log` hook. The hook and each test were kept in the page origin's `localStorage`, so the call right after navigation was short and the hook was in place before the start line. Times below are ms after play start (the `object spawn id=1` line in debug mode, the `tuning loaded` line in normal mode).
  - Canvas pixels were read with `getImageData`.
  - Text was compared with reference text rendered in the same page with the game's own default font (`pygame.font.Font(None, size)`, through `window.python.PyRun_SimpleString`). The comparison checks every fully inked pixel, then counts extra ink-colored pixels in the text box. "Exact" below means 0 missing and 0 extra.

**Required checks:**
- **Build is served and loads: passed.** `#canvas` is 640x480. pygbag logged `orig_argv [debug=1]` and `config.debug = false`, so `?debug=1` reached Python and didn't switch pygbag into a mode of its own.
- **Start line: passed.** On the first page, `01:10:51 INFO app.loop: start mode=debug` came 4.4 s after navigation. I clicked the canvas once after it.
- **No console errors: passed.** Every one of the 15 pages had exactly two errors: `Failed to load resource: 404 //cdn/0.9.3//browserfs.min.js` and `PyMain: BrowserFS not found`. Both are known and normal. Nothing else was logged at error level (counted over all 15 saved console logs).
- **Arrow-key input with x/y (`?debug=1`): passed.** I held ArrowUp from play start for about 10 s:
  - `key down key=up x=320.00 y=240.96` and `top line stop x=320.00 y=184.00`
  - `key up key=up x=320.00 y=184.00`
  - The y went from 240.96 down to 184.00, so the ship rose to the top line.

  A short tap on another page (test G) gave `key down key=up x=320.00 y=240.00`, `respawn wait end`, then `key up key=up x=320.00 y=219.72`.

**DRA-29 checks (extra):**
- **Tuning loaded (`/` and `?debug=1`): passed.** On every page there is one INFO `tuning loaded objects=meteorite hazard_speed_scaling=True timer_scaling=True`. It comes about 100 ms after the start line and before `scroll start`.
- **The ship is an inverted T (`/`): passed.** On the frame 48 ms after play start, (320, 230) is white, (308, 230) and (331, 230) are not white, and (308, 250) and (331, 250) are white.
- **Normal mode spawns nothing (`/`): passed, with a note.** For 5 s there is no (255, 220, 120) pixel and no meteorite. Four (140, 140, 140) pixels did show up: x 7 to 15 on row 31, the anti-aliased edge of the white meters readout. They are not a rock. See Observations. In normal mode no `object` line can show, because it logs at INFO.
- **The test spawn list (`?debug=1`, no key): passed.** Times from page A:
  - 0: `object spawn id=1 type=meteorite variant=small x=160.00 y=-10.00 speed=4.93 level=1`
  - 485: `object active id=1 type=meteorite x=160.00 y=-10.00`
  - 985: `object spawn id=2 ... variant=medium x=320.00 y=-14.00`
  - 1985: `object spawn id=3 ... variant=big x=480.00 y=-20.00`
  - 2185: `object gone id=1 type=meteorite x=160.00 y=493.37`
  - 2985: `object spawn id=4 ... variant=small`

  Ids 1 to 9 each have exactly one `spawn` and one `active`. The ones that left have exactly one `gone`: y 493.37 for small, 494.31 for medium and 503.11 for big.
- **Warning, then the rock (`?debug=1`): passed.**
  - At 201 ms: 61 glow pixels, all within 10 px of (160, 10) in x and in y (largest offsets 10 and 10). 56 grey pixels, all within 5 px of (160, 10). No grey pixel anywhere else.
  - At 701 ms: no glow pixel near (160, 10). 256 grey pixels in columns 151 to 168, centered on y 48.5.
  - At 1201 ms: the same disc, centered on y 196.5. That is 148 px lower in 500 ms; 4.935 px a tick gives 148.08.
- **A hit costs one life, once (`?debug=1`, ArrowUp held from play start): passed.**
  - 2068: `object touch id=2 type=meteorite effect=hit`, then `life lost lives=2`. There is no `respawn from`.
  - 5068: `object touch id=5 ...`, then `life lost lives=1`.
  - 8068: `object touch id=8 ...`, `life lost lives=0`, then INFO `game over meters=50`.
  - Id 2 never logged a second touch. No small or big meteorite (ids 1, 3, 4, 6, 7, 9) logged a touch.
  - The pixel at (320, 184), read each frame, after the id 2 hit: white 0 to 87 ms, dark 103 to 188, white 205 to 288, dark 303 to 388, then white from 405 on. After the id 5 hit the pattern was the same. That is three white and two dark spans of about 0.1 s.
  - The `key up` line read `x=320.00 y=184.00`, so the hits never moved the ship.
- **Game over freezes the objects, retry clears them (`?debug=1`): passed.**
  - Two full canvas reads 2 s apart, starting 0.3 s after the game over, were identical. No line of any kind came in between.
  - I released ArrowUp, waited 0.5 s and tapped ArrowLeft. INFO `new run` came, then `object spawn id=1 ... variant=small` 16 ms later.
  - The frame read 106 ms after `new run` had 56 grey pixels, all inside the new warning near (160, 10).
- **Outlines and labels (`?debug=1`): passed.**
  - At 1751 ms, medium id 2 is active with its disc centered at (319.5, 59.5).
  - Green pixels lie on a circle of radius 14 and on one of radius 28 around it: 36 of 36 sample points each, within 1 px. A control circle of radius 21 hit only 7 of 36, where the label crosses it. The rock's center is not green.
  - The label below the rock is exactly `meteorite medium x 320.00 y 60.02 active`, at (306, 74). The y one tick before and after (55.09, 64.96) leave 11 and 66 inked pixels unmatched.
  - The ship's T outline is green: column 314, rows 224 to 255 (32 of 32), and column 304, rows 244 to 255 (12 of 12).
  - While id 2 showed its warning (at 1201 ms), its label was exactly `meteorite medium x 320.00 y -14.00 warning` at (306, 0), against the top edge.
  - F3 logged `overlay visible=False`. The canvas then had 0 green pixels: no outlines, labels, text or lines. F3 again logged `overlay visible=True`: 2835 green pixels, 640 of them on row 168.
- **Bad tuning file (desktop, headless): passed.** See Checks.
- **Package contents: passed.** See Build check.

**Earlier checks, reworded for DRA-29 where the contract says so (all passed):**
- **DRA-23, a fall costs a life (`?debug=1`):** `life lost lives=2`, then `respawn from x=320.00 y=500.20 wait=True` at 1033 ms. 200 ms later the hearts read [0, 364, 364] white pixels per box.
- **DRA-23, three hearts at the start (`/`):** 150 ms after play start the boxes read [364, 364, 364] and the area x 536 to 639, rows 0 to 39 had 1092 white pixels, so nothing else is white there.
- **DRA-23, blink (`/`):** pixel (320, 240) on every frame from the fall:
  - dark until 149 ms (the respawn)
  - white 167 to 250, dark 266 to 350, white 367 to 450, dark 467 to 550
  - white from 567 on

  In debug mode, `invulnerable end` came 499 ms after `respawn from`.
- **DRA-23, the wait (`?debug=1`, 4 s), and DRA-6, log by event, waiting part:**
  - Overlay reads at 0.3, 1.5, 2.5 and 3.95 s after the respawn all matched exactly: `x 320.00`, `y 240.00`, `vx 0.00`, `vy 0.00`, at rows 4, 16, 28 and 40.
  - Besides `object` lines, the only new lines came in this order:
    - `invulnerable end`, 499 ms after the respawn
    - `object touch id=2 type=meteorite effect=hit` and `life lost lives=1`, 2248 ms after play start
    - `invulnerable end`, 500 ms after that
  - The readout went from 5 m to 29 m in 3.65 s, which is the 6.6 m/s rate (about 26 m in 4 s).
- **DRA-23, a press ends the wait and thrusts (`?debug=1`):** `key down key=up x=320.00 y=240.00`, `respawn wait end`, then `key up key=up x=320.00 y=219.72`. After the release the ship fell: `life lost lives=0` at 3371 ms, after one hit by id 2.
- **DRA-23, a held key doesn't end the wait (`?debug=1`):**
  - ArrowDown was held from play start. `respawn from x=320.00 y=498.60 wait=True` came at 879 ms.
  - I kept Down held for 2 s after the respawn. No `respawn wait end` came. The overlay read exactly `x 320.00 y 240.00 vx 0.00 vy 0.00` at 0.2, 1.0 and 1.95 s.
  - Medium id 2 hit the waiting ship in that window (`life lost lives=1`). It stayed waiting and didn't move, as `systems/run.md` says for a hit during the wait.
  - Then the release (`key up key=down x=320.00 y=240.00`) and an ArrowLeft tap: `respawn wait end`, and `key up key=left x=304.80`.
- **DRA-23, game over by a fall and retry needs a fresh press (`?debug=1`, three dives with Down):**
  - The first attempt is void, because id 2 caught the third dive first. The contract says to repeat in that case.
  - Second attempt: `life lost lives=0`, then `game over meters=14`, at 2737 ms, with no `object touch` before it.
  - The hearts read [0, 0, 0]. "Game Over" (32 px) and "Press any arrow to retry" (16 px) matched exactly. 14 star pixels inside the box read (58, 64, 90).
  - No white pixel outside the box text below row 100, so no ship.
  - Down stayed held for 2.3 s after the box appeared: no `new run`. F3 twice gave only `overlay visible=False` and `overlay visible=True`.
  - Then the release (`key up key=down x=320.00 y=497.10`, so the frozen y is at least 496), 0.5 s with no new line, and an ArrowLeft tap: INFO `new run`, 503 ms after the release.
- **DRA-23, everything freezes (`?debug=1`):** on the box, two full reads 2 s apart were identical on every game-over page: three by a hit and one by a fall.
- **DRA-23, a new run plays like the first (`?debug=1`):**
  - 250 ms after `new run` the readout matched `0 m` exactly at (4, 76), and the hearts read [364, 364, 364].
  - The box is gone: no (58, 64, 90) pixel, and "Game Over" no longer matches.
  - The ship had white pixels on every frame until it left the bottom, so there was no wait and no blink.
  - `scroll start tick=31` came 517 ms after `new run`, and `life lost lives=2` 1066 ms after.
  - Page A gave the same numbers: 517 ms and 1066 ms.
- **DRA-23, normal mode (`/`):**
  - After three falls (two ArrowUp taps to end the waits): INFO `game over meters=90`. Hearts [0, 0, 0], the box text exact, 14 darkened stars, and no white pixel except the box text.
  - An ArrowLeft tap gave INFO `new run`. Then hearts [364, 364, 364], `0 m` exact, and no darkened star.
  - No (0, 255, 0) pixel in 139 full-canvas reads over 15 s.
- **DRA-19, no `-0.00` (`?debug=1`):** ArrowUp held the whole time, ArrowLeft tapped (`key up key=left x=295.07 y=184.00`), then I read the overlay 3 s later. `vx 0.00` matched exactly. `vx -0.00` left 34 inked pixels unmatched.
- **DRA-13, scroll start logged once:** exactly one `scroll start tick=31` per run on every debug page, about 480 ms after play start. Each retry's new run logged its own.
- **DRA-13, readout counts up (`/`):** exact matches at (4, 24): `0 m` at 150 ms and at 400 ms, `29 m` at 5 s and `62 m` at 10 s. In debug mode it sits at (4, 76), below the overlay.
- **DRA-13, hovering still earns meters (`/`):** I held ArrowUp from 10.3 s, and the ship's top row was 168. The readout went from 71 m to 97 m in 4 s, the same 6.6 m/s.
- **DRA-13, starfield moves (`/`):** between 150 ms and 400 ms the shift was 0 (119 of 119 star pixels). Between 1 s and 2 s it was 66 px (119 of 119).
- **DRA-13, no overlap in debug mode:** the four overlay lines matched exactly at rows 4 to 40 at x 4. The readout matched at (4, 76), below them. Hitbox outlines and labels lie elsewhere.
- **DRA-6, log by event (`?debug=1`):** ArrowUp and ArrowLeft were held together for 3 s from the waiting ship. Between key-down (320.00, 240.00) and key-up (16.00, 184.00) there was exactly one `top line stop x=256.79 y=184.00` and exactly one `wall hit side=left x=16.00 y=184.00`. The ship stopped at the left wall with no bounce.
- **DRA-6, respawn:** after that release, `life lost lives=1` and `respawn from x=16.00 y=499.20 wait=True` came 1.2 s later.
- **DRA-6, ship visible (`/`):** white ship pixels on every frame, and no green. F3 logged nothing and drew no green.
- **DRA-6, overlay and F3 (`?debug=1`):** row 168 had 640 green pixels on the first frames. F3 cleared it to 0, with (100, 168) at (0, 0, 0). F3 again brought back 640.
- **DRA-6, catch-up cap (`?debug=1`):**
  - A 5000 ms main-thread stall while the ship waited gave one line, `tick cap hit, dropped 4.928 s`, not repeated.
  - The readout went from 29 m to 30 m.
  - The overlay still read exactly `x 320.00 y 240.00 vx 0.00 vy 0.00`.
- **DRA-6, click to start, follow-up (`/`, fresh tab, never clicked):** `navigator.userActivation.hasBeenActive` read `true` before any click. The page text was "Loading, please wait ...". No click screen and no "MEDIA USER ACTION REQUIRED" appeared. The start line came 2.73 s after navigation, and the game ran with no click. This is the same result as DRA-6 to DRA-23.
- **DRA-5, run modes:** `/` logged `start mode=normal`. `?debug=1` logged `start mode=debug`. `?debug=yes` logged `WARNING app.loop: debug switch value 'yes' is not 1, using normal mode`, then `INFO app.loop: start mode=normal`.

## Observations
- **The Director's hand check of the click screen is due.** `systems/app.md` asks for it when the frame loop changes, and DRA-29 changed it. The test browser gave the known result: the game starts before any click.
- **The "Normal mode spawns nothing" check, as written, also catches the readout.** It asks for no (140, 140, 140) pixel anywhere. The white meters readout's anti-aliased edges can land on exactly that grey: 4 pixels at x 7 to 15, row 31, at some readings. This came from DRA-13, not DRA-29. No rock, warning or glow pixel showed. The Architect may want to reword the check, for example to exclude the HUD text area or to look for a grey disc.
- **At a game over by a hit, the ship's center pixel isn't white.** At (320, 184) the ship is inside the Game Over box (rows 180 to 299), so the box's alpha darkens it to about (165, 165, 165). This is what `systems/run.md` describes: the ship shows under the box where it was hit. In test E, column 320 inside the ship read (165, 165, 165) and (205, 205, 205) values, not the background.
- **One `tick cap hit, dropped 0.183 s` line came from my test, not the game.** It was logged on one page while my in-page Python rendered 80 reference labels on the game's thread. That page's 1.7 s read caught the rock on its first active tick, so I redid it on a fresh page with all text rendering after the canvas reads. The redo is the outline and label result above.
- **Two attempts are void.** The first page A run started 11.6 s after play start because of tool-call latency, so its timed reads are void. I moved the harness into `localStorage`, and the rerun passed. The first dive attempt in test H ended by a hit, which the contract foresees and says to repeat.
- **The Playwright tool writes its console and snapshot logs to `/workspace/.playwright-mcp/`.** That folder is git-ignored. Nothing from it is committed.

## Decisions
- **Tuning load before the run, in both modes.** `frame_loop` calls `tuning = load_tuning()` right after the window opens and before `start_run()`, inside the guard, so a bad file shows the error screen. Source: `systems/app.md`, Rules, Frame loop (DRA-29) and Tuning loader; rationale "loaded in both modes".
- **One `step_run` per tick, then in debug mode only `add_objects(run, debug_spawns_due(run.scroll.ticks), tuning)`.** Both live in `_run_ticks`, which now also takes `debug` and `tuning`. Normal mode never calls `add_objects`. Source: `systems/app.md`, Rules, Tick, and the DRA-29 call block; scope report DRA-29, Limits ("Normal mode spawns nothing yet").
- **Draw order:**
  - fill
  - starfield
  - `render_object` for each object in `run.objects`, in order
  - the ship only if `run.ship_visible`
  - if `overlay_visible`: `draw_debug_hitboxes`, then `draw_debug_overlay`
  - the Game Over box at game over
  - the HUD last

  Source: `systems/app.md`, Rules, Draw and Objects behind the ship.
- **`debug_spawns_due(ticks)`:** `()` below tick 1, else every placement whose offset equals `(ticks - 1) % 180`. Offsets are 0, 60 and 120 for small x 160, medium x 320 and big x 480, each with `y=None` (its default start y). Source: `systems/app.md`, Interface and Rules, Debug test spawn list; scope report DRA-29, Test spawn list.
- **Loader: the schemas' rules, checked by hand, first problem raises.**
  - Missing fields are reported before unknown ones, so each file gives one plain message naming the file from `tuning/` down and the field path.
  - Variants keep the file's order.
  - Source: `systems/app.md`, Rules, Tuning loader; both schemas in `docs/contracts/schemas/`.
- **Loader: a number is a finite `int` or `float`, never a `bool`.** `json.loads` accepts `NaN` and `Infinity`, but neither is a JSON number, so they fail as "must be a number". `entry_warning_ticks` must be a Python `int` (30.0 is rejected) because the contract says "types exact" and "an `int` >= 1". Source: `systems/app.md`, Rules, Tuning loader; game/CONTEXT.md, Error handling (validate at the edge).
- **Module constants follow the contract's annotations.** `TUNING_DIR` is a plain `Path`, read at call time, so the bad-file check can point it at a scratch folder. `DEBUG_SPAWN_PERIOD` and `DEBUG_SPAWNS` are plain annotated constants. Source: `systems/app.md`, Interface, `app/tuning.py` and `app/debug_spawns.py`; rationale "`TUNING_DIR` from `__file__`".
- **Import boundary kept.** `app/tuning.py` and `app/debug_spawns.py` import `core.objects`, so only `app.frame` imports them, inside the guard. The startup modules are unchanged. Source: `systems/app.md`, Rules, Import boundary.
- **Nothing else changed.** The loop structure (fixed 60 Hz accumulator, cap of 5 ticks, `await asyncio.sleep(0)` each frame), the key and F3 handling, `main.py`, the startup modules, the start script and `pygbag.ini` are as they were. Source: `systems/app.md`, Impact; `15-tech-constraints.md`, rules 1 and 2.
