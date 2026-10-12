Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-19 (review follow-ups) into the app. Requested in Integrate mode. The only app change is the guard row in the Impact table of `docs/contracts/DRA-5/DRA-5-app.md`.
2. **Delivered:**
   - `game/app/guard.py`: `_detail` now also removes every `\x00` from the debug-mode detail line, after the newline handling. Normal mode still returns `None`. The docstring says why and gives the source.
   - `docs/reports/integration/DRA-19.md`: this report.
   - No change: `game/main.py`, `game/app/loop.py`, `frame.py`, `mode.py`, `log.py`, `settings.py`, `game/scripts/start-driftward-ace.sh`, `pygbag.ini` (as the Impact table says).
3. **Checks:**
   - QA line 1 is `Verdict: pass` for all three tasks, DRA-19-01 to DRA-19-03.
   - `game/tests/check.sh` ends with `QA: pass` (env, lint, format, core, ui). `ruff check` and `ruff format --check` on `app/` and `main.py` are clean.
   - Headless import is clean. `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy DRIFTWARD_DEBUG=1 timeout -s INT 2 python -c "import main"`, run from `game/`, logged `INFO app.loop: start mode=debug`, `DEBUG core.scroll: scroll start tick=31`, `DEBUG core.ship: respawn from x=320.00 y=500.20`. The only traceback was the SIGINT from `timeout` (exit 124).
   - **Null character in debug mode (contract check, headless): passed.** From `game/`, with `SDL_VIDEODRIVER=dummy`, `DRIFTWARD_DEBUG=1`, `app.loop.start` replaced before `run()` by an async function that raises `ValueError("bad\x00value")`. Log: `INFO app.loop: start mode=debug`, then `ERROR app.guard: unexpected error, showing the error screen` with the `ValueError: bad^@value` traceback. No `error screen failed` line. The process idled in `_idle()` until `timeout` sent SIGINT (exit 124).
   - Cross-check, headless: `_detail(ValueError("bad\x00value"), DEBUG)` returns `'ValueError: badvalue'`, and `draw_error_screen` draws it. The old shape, `'ValueError: bad\x00value'`, makes `draw_error_screen` raise `ValueError: A null character was found in the text`. Normal mode returns `None`.
   - Build: `pygbag --archive game` (exit 0) wrote `game/build/web.zip`, 47073 bytes, git-ignored. Contents are under Browser run.
   - Every required browser check passed, and the DRA-19 overlay check and the DRA-5, DRA-6 and DRA-13 checks still pass. See Browser run.
4. **Assumptions:**
   - Arrow, F3 and hold inputs were sent as `keydown`/`keyup` `KeyboardEvent`s on `#canvas` through `browser_evaluate`, as in DRA-6 and DRA-13. My tools can't hold a key.
   - The contract asks for a screenshot of the overlay's vx line. I have no screenshot tool and must not compare screenshots. So I read the canvas pixels. I compared them with reference text rendered in the same page with the game's font, `pygame.font.Font(None, 16)`, through pygbag's `window.python.PyRun_SimpleString`. The references went onto an offscreen surface, never the display. I did the same for the HUD readout, as in DRA-13. This reads no game state and changes nothing in the game.
5. **Documentation differences:** None.
6. **Next:**
   - Architect started for close-out of DRA-19 (prompt: "Close-out run for DRA-19. Integration report: docs/reports/integration/DRA-19.md"). `DRA-5-app.md`, `DRA-6-debug-overlay.md` and the other DRA-19 contracts are `Status: draft`. Every row of the DRA-5 Impact table is now done in code.
   - Director: run `game/scripts/start-driftward-ace.sh` and open `http://localhost:6060`, or use `--debug` for `/?debug=1`. In debug mode, hold Up, tap Left, let go, and the overlay's third line settles on `vx 0.00`. The build check is `pygbag --archive game`, run from the repo root, which writes `game/build/web.zip`.
7. **Status:** done.

## Browser run
- **Build check:** `pygbag --archive game`, run from the repo root, built `game/build/web.zip` (exit 0, not committed). `web.zip` holds `index.html`, `favicon.png` and `game.apk`. `game.apk` holds exactly: `assets/main.py`, `assets/app/{frame,guard,log,loop,mode,settings}.py`, `assets/core/{scroll,ship,world}.py`, `assets/ui/{debug_overlay,error_screen,hud,look,ship_view,starfield}.py`. It has no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml` or `__pycache__`. The packed `app/guard.py` has the null removal, and `ui/debug_overlay.py` has `z.2f`. I listed it with Python's `zipfile`, because `unzip` isn't installed. **Passed.**
- **Port check first:** a bash `/dev/tcp` check found 6060, 6061 and 6062 all free. No other server was running, so I used 6060.
- **Served with** `game/scripts/start-driftward-ace.sh --debug` in the background, script pid 1109995, with the pid file and log in the scratchpad. The log printed `Serving Driftward Ace at http://localhost:6060/?debug=1`. `curl` got 200 after 2 s.
- **Stopped** with `kill 1109995`. The trap logged `Stopping server (pid 1110007)` and `Server stopped`. Port 6060 was free afterwards (bash `/dev/tcp` check).

**Required checks (`?debug=1`):**
- **Build is served and loads: passed.** `#canvas` was 640x480. pygbag logged `orig_argv [debug=1]` and `PYBUILD = 3.12`.
- **Start line in the console: passed.** `22:56:06 INFO app.loop: start mode=debug`, 6.0 s after navigation. I clicked the canvas once afterwards, at about 18 s.
- **No console errors: passed.** The only errors were `Failed to load resource: 404 //cdn/0.9.3//browserfs.min.js` and `PyMain: BrowserFS not found`, which `game/CONTEXT.md` lists as known and normal. The `/` tabs and the `?debug=yes` tab had the same two errors and no others.
- **Arrow-key input with x/y: passed.** ArrowUp held 2 s:
  - `22:56:26 DEBUG app.frame: key down key=up x=320.00 y=494.70`
  - `22:56:26 DEBUG core.ship: respawn from x=320.00 y=499.94` (the ship was already past the floor and respawned on that tick)
  - `22:56:27 DEBUG core.ship: top line stop x=320.00 y=184.00`
  - `22:56:28 DEBUG app.frame: key up key=up x=320.00 y=184.00`
  - Before: x=320.00, y=494.70. After: x=320.00, y=184.00. The y went down, so the ship rose, and it stopped at the ceiling.

**DRA-19 check from the contract:**
- **No `-0.00` in the overlay (`?debug=1`): passed.** ArrowUp was held for the whole run. Left was pressed at 1501 ms and released at 1701 ms. The canvas was captured at 4718 ms, then Up was released.
  - Log: `key down key=up x=320.00 y=243.36`, `top line stop x=320.00 y=184.00`, `key down key=left x=320.00 y=184.00`, `key up key=left x=295.07 y=184.00`, `key up key=up x=241.04 y=184.00`. There was no wall hit and no respawn during the hold. So vx was still a small negative at capture (drag 0.94 per tick, with no snap to zero in `core/ship.py`), which the old format would have shown as `vx -0.00`.
  - Overlay text rows were `5-12 17-26 29-36 41-50`. The third line starts at row 28 (`4 + 2 * linesize`, linesize 12, height 11).
  - The 160x11 band of the vx line matched the reference `vx 0.00` exactly: 0 of 1760 pixels differed, and no star pixels were in the band. Against the reference `vx -0.00`, 199 pixels differed. The ink spans columns 4 to 41.
  - The packed overlay also proves that `z` formatting works on the browser's Python 3.12: the overlay drew every frame, and no error was logged.

**DRA-13 checks, still passing:**
- **Scroll start, logged once (`?debug=1`): passed.** `22:56:07 DEBUG core.scroll: scroll start tick=31`, 593 ms after the start line. That tab ran for about 2 minutes, through every hold, F3 and a 5 s stall, and logged no second `scroll start`.
- **Readout counts up (`/`, fresh tab, no click): passed.** The first frame the game drew read `0 m`, and it stayed `0 m` for 39 frames (to 634 ms). It read `1 m` at 657 ms and `6 m` at 1511 ms. All 90 frames matched a reference.
- **Readout rate and hover (`/`, second tab, no click): passed.** 902 frames were sampled over 15 s, starting at `42 m`. All 902 matched a reference exactly. The readout never went down and never stepped by more than 1.
  - No key: 42 m at 0 ms to 82 m at 6016 ms, which is 6.65 m/s.
  - ArrowUp held from 6016 ms to 11015 ms: 85 m at 6500 ms to 115 m at 11015 ms, which is 6.64 m/s. The ship's top row was 168 in every sample from 8 s to 11 s.
  - After release: 115 m to 141 m at 14915 ms, which is 6.67 m/s.
- **Starfield moves (`/`): passed.** 131 (90, 100, 140) pixels. From the frame at 1015 ms to the frame at 2015 ms, the best vertical shift was 66 px, with 126 of 127 pixels matched (wrap at row 480 included).
- **No overlap in debug mode (`?debug=1`): passed.** Rows with pixels in the top-left 200x168 area:
  - Overlay shown: green rows `5-12 17-26 29-36 41-50`, white readout rows `77-84`, 0 shared rows. Row 168 had 640 green pixels.
  - After F3 (`overlay visible=False`): no green pixels, row 168 had 0 green, and the readout was still on rows `77-84`.
  - After F3 again (`overlay visible=True`): the same rows as before, 0 shared.
- **Top line is still a ceiling: passed.** The required check ended at `y=184.00` with one `top line stop` line.
- **Package contents: passed.** See Build check.

**DRA-6 checks, still passing (`?debug=1` unless noted):**
- **Log by event:** ArrowUp and ArrowLeft were held together for 3 s. Both key-down lines read (320.00, 248.80). Then exactly one `top line stop x=215.13 y=184.00` and exactly one `wall hit side=left x=16.00 y=184.00`. Both key-up lines read (16.00, 184.00). Before: (320.00, 248.80). After: (16.00, 184.00). The ship stopped at the left wall with no bounce. Nothing else was logged during the hold.
- **Respawn:** `respawn from x=16.00 y=499.20` came 1.2 s after the release. With no key held, `respawn from x=320.00 y=500.20` came every 1.066 to 1.067 s, with no line per tick.
- **Overlay and F3:** see No overlap above. The lines were `overlay visible=False` and `overlay visible=True`.
- **Ship visible, no overlay in normal mode (`/`):** 0 (0, 255, 0) pixels in every sampled frame (one in six, over 15 s).
- **Catch-up cap:** a 5000 ms main-thread stall gave one line, `22:58:06 DEBUG app.frame: tick cap hit, dropped 4.941 s`, not repeated. Respawns went on every 1.066 s afterwards.

**DRA-5 checks, still passing:**
- `/`: `INFO app.loop: start mode=normal`, twice (two tabs).
- `?debug=1`: `start mode=debug`.
- `?debug=yes`: `WARNING app.loop: debug switch value 'yes' is not 1, using normal mode`, then `INFO app.loop: start mode=normal`.
- Error guard, headless: see Checks (the null-character run).

## Observations
- **The browser shows one deprecation warning:** `The ScriptProcessorNode is deprecated. Use AudioWorkletNode instead.` It appears once, about when the game starts. It is a warning from pygbag's audio setup, not an error, and the game has no audio code. The DRA-13 report didn't list it.
- **Leaving the debug tab opened a `beforeunload` dialog.** My tools can't answer it, so I closed the page and opened a new one for each later URL. Each check ran in a fresh page.
- **The game starts before any click, as in DRA-5, DRA-6 and DRA-13.** In the three `/` and `?debug=yes` tabs I never clicked, and the start line came about 3.6 s after navigation. No "MEDIA USER ACTION REQUIRED" appeared. A desktop browser may still show pygbag's click screen. That is worth one manual look.
- **The DRA-19 overlay check reads pixels, not a screenshot.** See Assumptions. The match was exact: 0 differing pixels against `vx 0.00`.
- **In the required check, the key-down y was 494.70.** The ship was falling past the floor when Up went down, and it respawned on the same tick. The change in y still shows the ship rising: 494.70 at key down, 184.00 at key up. The DRA-19 run gives a cleaner pair: 243.36 at key down, 184.00 at the stop.
- **The hidden-tab path wasn't tested.** As in DRA-6 and DRA-13, a main-thread stall stood in for it to show the cap.
- **No other server was running.** Port 6060 was free at the start, so the DRA-13 note about a foreign server on 6060 didn't apply this time. I deleted nothing outside my paths, and `.playwright-mcp/` is untouched apart from this run's own output.

## Decisions
- **Remove `\x00` after joining the lines, in `_detail`.** `" ".join(text.splitlines()).replace("\x00", "")` keeps the existing newline rule and then drops every null. The guard is the one place that turns an exception into display text, and the view draws whatever it gets. Source: DRA-5-app.md, Rules, Error guard, step 2; Impact (`game/app/guard.py` row); Rationale (the guard removes null characters, the view doesn't).
- **Remove the character, don't replace it.** The contract says "removed". The full message, null included, stays in the logged traceback. Source: DRA-5-app.md, Rules, Error guard, step 2; 10-ui.md, error_debug_line.
- **No other app change.** The loop, frame, mode, log, settings, `main.py`, the start script and `pygbag.ini` stay as they are. Source: DRA-5-app.md, Impact.
- **No new logging.** The guard's ERROR line and traceback are unchanged. Source: game/CONTEXT.md, Logging.
