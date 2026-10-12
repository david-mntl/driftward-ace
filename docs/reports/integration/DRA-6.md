Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-6 (ship movement, debug overlay, F3, catch-up cap) into the app. Requested in Integrate mode, with the app changes from the Impact table in `docs/contracts/DRA-5/DRA-5-app.md`.
2. **Delivered:**
   - `game/app/settings.py`: `SCREEN_SIZE` removed, `MAX_TICKS_PER_FRAME = 5` added.
   - `game/app/guard.py`: no module-level settings import. The error step imports `core.world` and opens the window at `(SCREEN_W, SCREEN_H)`.
   - `game/app/loop.py`: `start(mode)`. `run()` passes `functools.partial(start, choice.mode)` to `guarded`.
   - `game/app/frame.py`: `frame_loop(mode)`. Adds the ship, the held-key thrust, the tick with `step`, the 5-tick cap and its log, the draw (background, ship, overlay), key lines with x/y, and F3.
   - `docs/reports/integration/DRA-6.md`: this report.
   - No change: `game/main.py`, `game/app/mode.py`, `game/app/log.py`, `game/scripts/start-driftward-ace.sh`, `pygbag.ini` (as the Impact table says).
3. **Checks:**
   - QA line 1 is `Verdict: pass` for all four tasks, DRA-6-01 to DRA-6-04.
   - `game/tests/check.sh` ends with `QA: pass` (env, lint, format, core, ui).
   - Headless import is clean. `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy DRIFTWARD_DEBUG=1 timeout -s INT 3 python -c "import main"`, run from `game/`, logged `INFO app.loop: start mode=debug`, then `respawn from x=320.00 y=500.20` once a second.
   - Blocked `app.frame` (headless): start line, then ERROR `unexpected error, showing the error screen` with the `ModuleNotFoundError` traceback. The process idled until the timeout stopped it (exit 124).
   - Blocked `pygame` (headless): start line, the ERROR with its traceback, then ERROR `error screen failed` with its own traceback. The process ended by itself (exit 0).
   - Build: `pygbag --archive game` (exit 0) wrote `game/build/web.zip`, 43042 bytes, git-ignored. Package contents are below.
   - Every required browser check and every extra check passed. See Browser run.
4. **Assumptions:**
   - Arrow holds were sent as `keydown` and, later, `keyup` `KeyboardEvent`s on `#canvas` through `browser_evaluate`. My Playwright tools can't hold a key (`browser_press_key` is press-and-release). pygame read them as real arrow events, and the logs show it.
   - The catch-up cap was shown with a 5 s main-thread stall, because headless Chromium wouldn't hide the tab. GDD rule 2 names "a hidden tab or a stall". See Observations.
5. **Documentation differences:** None.
6. **Next:**
   - Architect started for close-out of DRA-6 (prompt: "Close-out run for DRA-6. Integration report: docs/reports/integration/DRA-6.md"). `DRA-5-app.md` is still `Status: draft` with its Impact table, for the Architect to freeze.
   - Director: run `game/scripts/start-driftward-ace.sh --debug` and open `http://localhost:6060/?debug=1`. Click the canvas and hold ArrowUp. The build check is `pygbag --archive game`, which writes `game/build/web.zip`.
7. **Status:** done.

## Browser run
- **Build check:** `pygbag --archive game`, run from the repo root, built `game/build/web.zip` (exit 0, not committed). `game.apk` holds exactly these files: `assets/main.py`, `assets/app/{frame,guard,log,loop,mode,settings}.py`, `assets/core/{ship,world}.py`, `assets/ui/{debug_overlay,error_screen,look,ship_view}.py`. There are no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml` or `__pycache__` files. `core/world.py`, `core/ship.py`, `ui/ship_view.py` and `ui/debug_overlay.py` are all in it. **Passed.**
- **Served with** `game/scripts/start-driftward-ace.sh --debug` in the background, with its pid (209384) in the scratchpad. The log printed `Serving Driftward Ace at http://localhost:6060/?debug=1`. `curl` got 200 after 2 s.
- **Stopped** with `kill <script pid>`. The trap logged `Stopping server (pid 209393)` and `Server stopped`. Port 6060 was free afterwards.
- Each URL was opened in a fresh tab, closed between runs.

**Required checks (`?debug=1`):**
- **Build is served and loads: passed.** The `#canvas` was 640x480. pygbag fetched `pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl`.
- **Start line in the console: passed.** `[LOG] 15:44:45 INFO app.loop: start mode=debug`.
- **No console errors: passed.** There were exactly two errors: `Failed to load resource: 404 //cdn/0.9.3//browserfs.min.js` and `PyMain: BrowserFS not found`. Both are known-normal per `game/CONTEXT.md`, INTEGRATION > Browser. The same two, and no others, appeared in the `/` and `?debug=yes` runs. Every warning came from pygbag or the Chrome loader.
- **Arrow-key input with x/y: passed.** ArrowUp held 2 s (keydown 15:45:37, keyup 15:45:39):
  - `15:45:37 DEBUG app.frame: key down key=up x=320.00 y=324.48`
  - `15:45:38 DEBUG core.ship: top line stop x=320.00 y=184.00`
  - `15:45:39 DEBUG app.frame: key up key=up x=320.00 y=184.00`
  - Before: x=320.00, y=324.48. After: x=320.00, y=184.00. The key-up y is smaller, and it is `184.00` (top edge on line 168), as the contract says.

**DRA-6 checks from the contract (`?debug=1` unless noted):**
- **Log by event, not by tick: passed.** ArrowUp and ArrowLeft held together for 3 s (15:45:48 to 15:45:51):
  - Key down: `key=up` and `key=left`, both at x=320.00, y=390.20.
  - `wall hit side=left x=16.00 y=223.42`, exactly once.
  - `top line stop x=16.00 y=184.00`, exactly once.
  - Key up: `key=left` and `key=up`, both at x=16.00, y=184.00.
  - Before: (320.00, 390.20). After: (16.00, 184.00). The left edge is on the wall, with no bounce.
  - With no key held for 5 s or more, the only lines were `respawn from x=320.00 y=500.20`, 1.066 s apart (64 ticks of free fall). No line per tick.
- **Respawn: passed.** After each release, a `respawn from` line came 1.2 s later: `respawn from x=320.00 y=499.20` after the Up hold, and `respawn from x=16.00 y=499.20` after the Up+Left hold. Both y values are at least 496.00.
- **Overlay and F3: passed.**
  - From the first frame, row 168 had 640 (0, 255, 0) pixels, and so did row 479. Pixel (600, 168), away from the ship, was (0, 255, 0).
  - F3 logged `15:45:17 DEBUG app.frame: overlay visible=False`. The canvas then had 0 green pixels, and (600, 168) was (0, 0, 0).
  - F3 again logged `15:45:23 DEBUG app.frame: overlay visible=True`. Row 168 had 640 green pixels again.
- **Ship visible (`/`): passed.** `start mode=normal`. The canvas had 1024 (255, 255, 255) pixels (one 32x32 ship) and 0 (0, 255, 0) pixels. After F3: still 0 green and 1024 white, and no new console line.
- **Catch-up cap: passed, shown with a stall** (see Observations).
  - A 5000 ms busy loop on the page's main thread (15:46:21 to 15:46:26) gave one line: `15:46:26 DEBUG app.frame: tick cap hit, dropped 4.923 s`. That is the 5 s gap minus the 5 ticks that ran.
  - It wasn't repeated. Respawns went on at 15:46:27, 28, 29 and so on, 1.066 s apart.
  - Game time across the stall: from the respawn before the stall to the one after was 6.000 s of wall time. Taking off the 4.923 s dropped leaves 1.077 s, which is one normal fall. The ship didn't jump ahead.
- **Click to start, follow-up (fresh tab, `?debug=1`, nothing done before reading the console):**
  - The page showed "Loading, please wait ..." while loading. Then no pygbag click screen showed: the only visible DOM text was pygbag's font-measure span.
  - No "MEDIA USER ACTION REQUIRED" line appeared.
  - The start line was at 15:44:45, 3.2 s after navigation and before any click. `respawn` lines followed from 15:44:46, once a second, all before the click. The ship was already falling.
  - `navigator.userActivation.hasBeenActive` was `true` at 15:45:04, read before my first click (15:45:08). See Observations for why this reading can't be trusted.
  - After the click the game kept running, and all the checks above ran after it.
- **DRA-5 run modes, still passing:**
  - No switch gave `start mode=normal`. `?debug=1` gave `start mode=debug`.
  - `?debug=yes` gave `15:47:16 WARNING app.loop: debug switch value 'yes' is not 1, using normal mode`, then `15:47:16 INFO app.loop: start mode=normal`.
  - pygbag logged `config.debug = false` and `debug_user=false` with `orig_argv [debug=1]`, so `?debug=1` reached Python unchanged and didn't switch pygbag into a mode of its own.
- **DRA-5 import errors (headless):** passed, see Checks.

## Observations
- **The game starts before the click in headless Chromium, as in DRA-5.**
  - In a fresh tab with no click and no `evaluate`, the start line came 3.2 s after load. The ship was falling and respawning before any click.
  - No click screen and no "MEDIA USER ACTION REQUIRED" appeared. pygbag logged `Auto ume unlocker safari== false` and `config.ume_block = 1`.
  - `navigator.userActivation.hasBeenActive` read `true`, but Playwright runs `page.evaluate` as a user gesture in Chromium, so reading it may have set it. I couldn't read it without a gesture using my tools.
  - The game does start and keep running after a click, so this doesn't fail DRA-6. A desktop browser opened by the Director may still show pygbag's click screen. That is worth one manual look.
- **The hidden-tab path couldn't be shown headless.**
  - With another tab opened over the game (`window.open`) for 5 s, `document.visibilityState` stayed `visible`.
  - The page was throttled while covered, though. One `tick cap hit, dropped 0.935 s` line appeared at 15:46:11, not repeated. Respawns then came 5.6 s apart instead of 1.07 s, so owed time was dropped and the ship didn't jump ahead.
  - The cap itself was shown with a 5 s main-thread stall (Browser run). A real hidden tab in a desktop browser wasn't tested.
- **Arrow holds were sent as DOM key events** through `browser_evaluate`, because the tools have no key-hold. pygame-ce handled them as real arrow events (key lines, thrust, wall and line stops), so the result is the same as a held key.
- `DRA-5-app.md` is still `Status: draft` with its Impact table. Every Impact row is now done in code. Freezing it is the Architect's call at close-out.

## Decisions
- **Frame order.** Each frame: read events (quit, arrow lines with the ship before this frame's ticks, F3), build `Thrust` from `pygame.key.get_pressed()` once, add the `time.perf_counter()` delta, run the ticks, apply the cap, draw, flip, `await asyncio.sleep(0)`. Source: DRA-5-app.md, Rules, Frame loop; 15-tech-constraints.md, rules 1 and 2.
- **Cap.** `_run_ticks` stops at `MAX_TICKS_PER_FRAME` ticks. If one whole tick or more is still owed after that, the accumulator is set to 0.0. `_apply_cap` logs `tick cap hit, dropped %.3f s` only when the previous frame wasn't capped. Source: DRA-5-app.md, Rules, Catch-up cap and Cap log; 91-decision-log.md, row 21.
- **F3 only in debug mode, on KEYDOWN.** In normal mode the event isn't handled at all, so it does nothing and logs nothing. Source: DRA-5-app.md, Rules, F3; 10-ui.md, debug_overlay_toggle.
- **`overlay_visible` starts as `mode is RunMode.DEBUG`** and is passed through `_read_events`, which returns the new value. That keeps all app state local to `frame_loop`, as the contract lists it. Source: DRA-5-app.md, Interface, App-owned state.
- **The guard imports `core.world` inside the error step**, next to pygame and `ui.error_screen`, so the import boundary holds. Source: DRA-5-app.md, Impact and Rules, Error guard step 3.1.
- **Helpers in `frame.py`** (`_read_events`, `_held_thrust`, `_run_ticks`, `_apply_cap`, `_draw`) keep each function short, per game/CONTEXT.md, Good practice. They are private, so the contract's Interface is unchanged.
