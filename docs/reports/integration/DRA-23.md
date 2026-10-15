Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-23 (lives, falls, respawn wait, game over and retry) into the app. Requested in Integrate mode. All five DRA-23 QA reports have `Verdict: pass` on line 1.
2. **Delivered:** `game/app/frame.py`, `docs/reports/integration/DRA-23.md`. No change to `game/main.py`, the other `game/app/` modules, `game/scripts/start-driftward-ace.sh` or `pygbag.ini`, as the Impact table in `docs/contracts/systems/app.md` says.
3. **Checks:**
   - Headless import (`SDL_VIDEODRIVER=dummy`, from `game/`): `import app.loop, app.frame, app.guard` is clean. A 5 s timed run of `main` with `DRIFTWARD_DEBUG=1` logged `start mode=debug`, `scroll start tick=31`, `life lost lives=2`, `respawn from x=320.00 y=500.20 wait=True`, `invulnerable end`, and nothing per tick.
   - `game/tests/check.sh`: env, lint, format, core and ui all PASS, `QA: pass`.
   - Desktop guard checks (headless): with `app.frame` blocked, the start line, then ERROR `unexpected error, showing the error screen` with the `ImportError`, then it idles until stopped. With `pygame` blocked, the same ERROR, then ERROR `error screen failed`, and the process exits by itself (exit 0). With the null-character stand-in (`ValueError("bad\x00value")`, debug), the start line, then the ERROR with the `ValueError` traceback, no `error screen failed`, then it idles until stopped.
   - Build: `pygbag --archive game` from the repo root built `game/build/web.zip` (exit 0, git-ignored, not committed). Package contents are clean. See Browser run.
   - Browser: every required check and every DRA-23 check in `systems/app.md` passed, and so did the reworded DRA-5, DRA-6, DRA-13 and DRA-19 checks. See Browser run.
   - Logging is by event. The app logs only quit, arrow keys with `run.ship` x/y, F3 and the cap. Nothing is logged per tick.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** I started the Architect for the DRA-23 close-out (prompt: "Close-out run for DRA-23. Integration report: docs/reports/integration/DRA-23.md"). Director: run `game/scripts/start-driftward-ace.sh` (or `--debug`) and open `http://localhost:6060` (or `/?debug=1`). Build check: `pygbag --archive game` from the repo root gives `game/build/web.zip`. The frame loop changed in this feature, so the contract asks you to check pygbag's click screen by hand in a desktop browser (see Observations).
7. **Status:** done.

## Browser run
- **Build check:** `pygbag --archive game` (pygbag 0.9.3), run from the repo root, gave `game/build/web.zip` (51849 bytes). `web.zip` holds `index.html`, `favicon.png` and `game.apk`. `game.apk` holds exactly: `assets/main.py`, `assets/app/{frame,guard,log,loop,mode,settings}.py`, `assets/core/{run,scroll,ship,world}.py` and `assets/ui/{debug_overlay,error_screen,game_over,hud,look,ship_view,starfield}.py`. There is no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml` or `__pycache__`. `core/run.py` and `ui/game_over.py` are in it, and the packed `app/frame.py` calls `step_run(run, thrust)`. Listed with Python's `zipfile`. **Passed.**
- **Served** with `game/scripts/start-driftward-ace.sh --debug` in the background (script pid 53446, log and pid file in the scratchpad). Port 6060 was free first. `curl` got 200 after 2 s. Six pages were opened against the one server: four `?debug=1`, one `/`, one `?debug=yes`.
- **Stopped** with `kill 53446`. The trap logged `Stopping server (pid 53456)` and `Server stopped`. Port 6060 was free afterwards.
- **How inputs and reads were done.** Arrow and F3 keys were sent as `keydown`/`keyup` `KeyboardEvent`s on `#canvas` through `browser_evaluate`, as in DRA-6 to DRA-19. Times are page ms. Canvas pixels were read with `getImageData`. Text (overlay, readout, the Game Over box) was compared with references drawn in the same page with the game's font through `window.python.PyRun_SimpleString`, onto offscreen surfaces. The box reference comes from the game's own `ui.game_over.draw_game_over`. A score of 0 means no differing pixel (star pixels under black reference pixels are skipped). Timed windows were captured as raw frames first and checked afterwards, so the check's own stall never fell inside a timed window.

**Required checks (`?debug=1`, page 1):**
- **Build is served and loads: passed.** `#canvas` is 640x480. pygbag logged `orig_argv [debug=1]` and `config.debug = false`, so `?debug=1` reached Python and didn't switch pygbag into a mode of its own.
- **Start line: passed.** `18:10:40 INFO app.loop: start mode=debug`, 4566 ms after navigation. I clicked the canvas once afterwards.
- **No console errors: passed.** Every page had only `Failed to load resource: 404 //cdn/0.9.3//browserfs.min.js` and `PyMain: BrowserFS not found`, which are known and normal. One more line came from my test, not the game: see Observations.
- **Arrow-key input with x/y: passed.** The ship was waiting at the respawn point. I held ArrowUp for 2 s:
  - `key down key=up x=320.00 y=240.00`
  - `respawn wait end`
  - `top line stop x=320.00 y=184.00`
  - `key up key=up x=320.00 y=184.00`
  - Before: x=320.00, y=240.00. After: x=320.00, y=184.00. The y went down, so the ship rose and stopped at the top line.

**DRA-23 checks (extra):**
- **A fall costs a life (`?debug=1`, no key): passed.** On page 2, `life lost lives=2`, then `respawn from x=320.00 y=500.20 wait=True`, 1.13 s after the start line. White heart pixels per box (x 544, 576, 608, rows 8 to 31) went from [364, 364, 364] to [0, 364, 364]. The heart area (x 536 to 639, rows 0 to 39) went from 1092 white pixels to 728, so nothing else is white there.
- **Three hearts at the start (`/`): passed.** The first frame the game drew came 98 ms after the start line, with all three boxes at 364 white pixels and 1092 in the whole area. That held on every frame until the fall.
- **Blink (`/` and `?debug=1`, no key): passed.** Pixel (320, 240) on every frame:
  - `/`: the fall at 1135 ms after the start line, then white 1135 to 1235, not white 1235 to 1335, white 1335 to 1435, not white 1435 to 1535, then white from 1535 on. That is three white spans and two not-white spans of about 0.1 s.
  - `?debug=1`: the same pattern, 4390 / 4489 / 4588 / 4688 / 4788 ms. `invulnerable end` came 498 ms after `respawn from`.
- **The wait (`?debug=1`, no key): passed.** Six frames over 5 s all read exactly (score 0) `x 320.00`, `y 240.00`, `vx 0.00`, `vy 0.00`. No line was logged in those 5 s (the one `invulnerable end` came earlier, 0.5 s after the respawn). The readout went from `279 m` to `312 m` in 5.035 s, that is +33 m. The stars moved 67 px in 1015 ms (131 of 131 star pixels matched).
- **A press ends the wait and thrusts (`?debug=1`): passed.** ArrowUp tapped for 0.2 s:
  - `key down key=up x=320.00 y=240.00`
  - `respawn wait end`
  - `key up key=up x=320.00 y=219.72`
  - Then `life lost lives=1` and `respawn from x=320.00 y=497.82 wait=True`, 1.5 s later: the ship fell after the release.
- **A held key doesn't end the wait (`?debug=1`, page 4): passed.** ArrowDown went down after the start line (`key down key=down x=320.00 y=245.76`). The ship dove: `life lost lives=2`, then `respawn from x=320.00 y=496.46 wait=True`. I kept Down held for 3.0 s after the respawn: no `respawn wait end`. The overlay read exactly `x 320.00 y 240.00 vx 0.00 vy 0.00` at 216, 1161 and 2077 ms after the respawn. Then the release (`key up key=down x=320.00 y=240.00`), then an ArrowLeft tap: `respawn wait end`, and `key up key=left x=295.07 y=252.48`, so the ship moved left. An earlier try on page 3 is void: Down went down before the game started, so the game never saw it.
- **Game over (`?debug=1`): passed.** On page 2, the second fall's wait ended with an ArrowUp tap, and the third fall was a dive:
  - `life lost lives=0`, then `INFO core.run: game over meters=435`, and no `respawn from` after it.
  - Hearts read [0, 0, 0].
  - The box text matched the reference exactly: 0 differing pixels out of 1563 ink pixels. Page 1's game over gave the same result.
  - Stars inside x 160 to 479, rows 180 to 299 are (58, 64, 90): 13 to 15 pixels, and no (90, 100, 140) pixel inside. Outside, the stars are (90, 100, 140).
  - Page 1: no white pixel outside the box and the readout, so no ship.
- **Everything freezes (`?debug=1`): passed.** Two full canvas reads 2 s apart were identical, on page 1 and page 2. No line came in those windows. The overlay values read exactly: page 1 `x 16.00`, `y 499.20`, `vx 0.00`, `vy 5.50`, readout `901 m` (the log said `game over meters=901`). On page 2 the y line is `y 497.10` in the frozen key-up log line. My pixel candidate list for that y missed 497.10, so it isn't pixel-matched there.
- **Retry needs a fresh press (`?debug=1`, page 2): passed.**
  - ArrowDown stayed held for 2.3 s after the box appeared: no `new run`.
  - F3 twice: only `overlay visible=False` and `overlay visible=True`.
  - Release (`key up key=down x=320.00 y=497.10`), 0.5 s with no new line, then an ArrowLeft tap: `key down key=left x=320.00 y=497.10`, then `INFO core.run: new run`.
- **A new run plays like the first (`?debug=1`): passed.** Page 1, from `new run`:
  - The readout read `0 m` (score 0) 250 ms later, and three hearts showed.
  - Every frame showed the ship, with no blink, until it left the bottom of the screen at about 1.06 s. No wait came first.
  - `scroll start tick=31` came after 517 ms, and `life lost lives=2` after 1067 ms.
  - The box was gone: no (58, 64, 90) pixel anywhere, and the box reference no longer matched (2060 differing pixels).
  - Page 2 gave the same lines, at 582 ms and 1132 ms. My check stalled the page right after the retry and the cap dropped 0.071 s, which explains the later times.
- **Normal mode (`/`): passed.** After three falls, `game over meters=338` (INFO). Hearts read [0, 0, 0], the box text had 0 differing pixels, and 15 darkened star pixels were in the box. An ArrowLeft tap gave `new run`: hearts [364, 364, 364], readout `0 m`, and no darkened star pixel. No (0, 255, 0) pixel in 795 frames over the first 16 s, or at any later read.
- **Package contents: passed.** See Build check.

**DRA-19 checks, still passing:**
- **No `-0.00` in the overlay (`?debug=1`): passed.** I held ArrowUp the whole time, tapped ArrowLeft for 0.2 s (`key up key=left x=295.07 y=184.00`), waited 3 s and read the frame. The third line matched `vx 0.00` exactly (score 0). Against `vx -0.00`, 199 pixels differed.
- **Null character (desktop, headless): passed.** See Checks.

**DRA-13 checks, still passing:**
- **Scroll start, logged once:** one `scroll start tick=31` per run on every page, through falls, waits, holds, F3 and a 5 s stall. Each retry's new run logged its own.
- **Readout counts up (`/`):** `0 m` at 124 ms and 400 ms after the start line, at text top y 24 (exact match). Then 2 m at 1 s, 9 m at 2 s, 29 m at 5 s and 62 m at 10 s. All were exact matches, and the number never went down.
- **Hovering still earns meters (`/`):** ArrowUp held for 5 s with the ship's top row at 168. The readout went 218 m, then 224 m (1 s), then 251 m (5 s). That is +33 m in 5 s, the same as with no key held.
- **Starfield moves (`/`):** stars at 100 ms and 400 ms after the start line had shift 0 (131 of 131). From 1000 ms to 2000 ms the shift was 66 px (128 of 129 matched).
- **No overlap in debug mode:** the readout matched exactly at its debug place (x 4, y 76) in every debug read. F3 off and on left row 168 at 0, then 640 green pixels. The readout place doesn't depend on F3 (`below_overlay=debug`, unchanged).
- **Top line is still a ceiling:** the required check ended at `y=184.00`.

**DRA-6 checks, still passing (`?debug=1` unless noted):**
- **Log by event:** ArrowLeft and ArrowUp held together for 3 s from the waiting ship. Between key-down (320.00, 240.00) and key-up (16.00, 184.00) there was exactly one `top line stop x=251.90 y=184.00` and exactly one `wall hit side=left x=16.00 y=184.00`, and nothing else. The ship stopped at the left wall with no bounce. The no-key 5 s wait logged nothing (see The wait).
- **Respawn:** after the ArrowUp release at y=184.00, `life lost lives=1`, then `respawn from x=320.00 y=499.20 wait=True`, 1.2 s later.
- **Ship visible (`/`):** white pixels in every drawn frame. No (0, 255, 0) pixel. F3 logged nothing and drew no green.
- **Overlay and F3:** row 168 had 640 green pixels from the start. F3 logged `overlay visible=False`, row 168 went to 0 green and (100, 168) was (0, 0, 0). F3 again logged `overlay visible=True`, and row 168 was back to 640 green.
- **Catch-up cap:** a 5000 ms main-thread stall while the ship waited gave one line, `tick cap hit, dropped 4.962 s`, not repeated. The readout went 141 m to 142 m, and the ship stayed at exactly `x 320.00 y 240.00 vx 0.00 vy 0.00`.
- **Click to start, follow-up (`/`, fresh tab, no click):** `navigator.userActivation.hasBeenActive` read `true` at 337 ms, before any click. The page text was "Loading, please wait ...". No click screen and no "MEDIA USER ACTION REQUIRED" appeared. The start line came 3390 ms after navigation, and the ship fell and respawned with no click. On page 1, `life lost` and `respawn` lines also came before my first click. This is the same result as DRA-6, DRA-13 and DRA-19.

**DRA-5 checks, still passing:**
- `/`: `INFO app.loop: start mode=normal`.
- `?debug=1`: `start mode=debug` (four pages).
- `?debug=yes`: `WARNING app.loop: debug switch value 'yes' is not 1, using normal mode`, then `INFO app.loop: start mode=normal`.
- Import errors (desktop, headless): see Checks.

## Observations
- **The Director's hand check of the click screen is due.** `systems/app.md` says the Director checks pygbag's click screen in a desktop browser when the frame loop or start-up changes. DRA-23 changed the frame loop. The test browser gave the known result: the game starts before any click.
- **Two `tick cap hit` lines came from my test, not the game.** `dropped 0.109 s` (page 1) and `dropped 0.071 s` (page 2) were logged right after my in-page text check ran. That check blocks the page's main thread for about 0.1 s. The cap did what the contract says: one line, owed time dropped.
- **One extra console error came from my navigation.** `Blocked confirm('Are you sure you want to navigate away from this page ?') during beforeunload` appeared once, when I moved page 1 to a new URL. That is pygbag's own page handler, not the game. After that I closed each tab before opening the next, and it didn't come back.
- **The darkened star color reads (58, 64, 90).** The contract says "about (58, 65, 91)". The difference is rounding in the alpha blend, inside "about".
- **One overlay value was read from the log, not the pixels.** On page 2 the frozen overlay y (497.10, from the key-up log line) wasn't in my pixel candidate list. Page 1's frozen overlay was pixel-matched exactly (`y 499.20`).

## Decisions
- **One `Run`, one call per tick.** `frame_loop` holds `run = start_run()` from before the first frame. `_run_ticks` calls `run = step_run(run, thrust)` once per tick and nothing else. The app never calls `spawn`, `step`, `start_scroll`, `step_scroll` or `start_run` again. Source: `systems/app.md`, Rules, Frame loop (Tick, Game over) and the DRA-23 call block; `systems/run.md`, Interface.
- **Draw order:** fill `BACKGROUND`, `draw_starfield(surface, run.scroll)`, `draw_ship` only if `run.ship_visible`, the overlay only if `overlay_visible`, `draw_game_over(surface)` only if `run.game_over`, then `draw_hud(surface, run, below_overlay=debug)` last. Source: `systems/app.md`, Rules, Draw; `systems/run.md`, Presentation.
- **Key lines read `run.ship.x` and `run.ship.y` before the frame's ticks.** F3 stays app-only, so only the four-arrow `thrust` reaches `step_run`. Source: `systems/app.md`, Rules, Arrow keys and F3.
- **Imports:** `frame.py` now imports `core.run` and `ui.game_over`, keeps `Thrust` from `core.ship`, and no longer imports `core.scroll`, `spawn` or `step`. It is still imported only inside the guard. Source: `systems/app.md`, Interface, game/app/frame.py.
- **Nothing else changed.** The loop structure (fixed 60 Hz accumulator, cap of 5 ticks, `await asyncio.sleep(0)` each frame), `main.py`, the startup modules, the start script and `pygbag.ini` are as they were. Source: `systems/app.md`, Impact; CLAUDE.md / `15-tech-constraints.md`, rules 1 and 2.
