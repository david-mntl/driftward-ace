Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-39 (satellite, re-hit cooldown, editable test spawn list) into the app. Requested in Integrate mode. All seven DRA-39 QA reports have `Verdict: pass` on line 1.
2. **Delivered:** `game/app/tuning.py` (reads `hazards.json`, checks the satellite's own fields, builds `SatelliteVariantExtra` and `HazardRules`, longer log line), `game/app/debug_spawns.py` (rewritten: the spawn list file, two modes, editable loop length), `game/app/frame.py` (loads the list in debug mode, passes it to `debug_spawns_due`), `docs/reports/integration/DRA-39.md`. No change to `game/main.py`, the startup modules, `game/scripts/start-driftward-ace.sh` or `pygbag.ini`, as the Impact table in `docs/contracts/systems/app.md` says.
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck, core (448 tests) and ui (17 tests) all PASS, `QA: pass`.
   - Headless import (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, from `game/`): `import app.loop, app.frame, app.guard, app.tuning, app.debug_spawns` is clean.
   - Desktop runs, headless. `DRIFTWARD_DEBUG=1 python main.py` logged `start mode=debug`, then `tuning loaded drifters=meteorite,satellite hazard_speed_scaling=True timer_scaling=True rehit_cooldown=180 rehit_dim=0.75`, then `debug spawns loaded mode=meteorite rows=3 loop_ticks=180`, then the DRA-29 meteorite timeline. A normal run logged only the start line and `tuning loaded`.
   - Loader edge cases, 40 cases run against scratch copies of `game/tuning/`. Each bad file raised `ValueError` naming the file from `tuning/` down and the field. Examples:
     - `tuning/hazards.json: rehit_cooldown must be an integer >= 0` (for `true`, -1 and 5.0)
     - `tuning/drifters/satellite.json: variants.angled.angle_degrees must be a number >= 0 and < 90` (for 90 and -1)
     - `tuning/drifters/satellite.json: variants.flat.hitbox must be exactly two boxes` (for one box, three boxes, or a circle)
     - `tuning/drifters/meteorite.json: variants.small.angle_degrees is not a known field`
     - `tuning/debug_spawns.json: rows[0].x must be a number` (for `null`)
     - `tuning/debug_spawns.json: rows[0] needs x or y`
     - `tuning/debug_spawns.json: rows[0]: meteorite has no invert`
     - `tuning/debug_spawns.json: rows[3]: unknown variant 'tilted' for drifter type 'satellite'`

     `{}` in `hazards.json` gives 180 and 0.75. A missing `hazards.json` raises `FileNotFoundError` with its path. Mode and loop defaults are `all` and 180. The timing is as the contract says: mode `all` gives offsets 0, 25, 51, 77, 102, 128 and 154; mode `meteorite` places rows on ticks 1, 61, 121, 181 and on.
   - Desktop guard checks from `systems/app.md`, headless:
     - **DRA-39, shared hazard values:** with `{"rehit_cooldown": 5}`, the line ends `rehit_cooldown=5 rehit_dim=0.75`.
     - **DRA-39, bad spawn list:** with the row `{"type": "satellite", "x": 100}` added, ERROR `unexpected error, showing the error screen` with `ValueError: tuning/debug_spawns.json: rows[7]: satellite placement needs y`. There is no `error screen failed` line, and the process idled until `timeout` stopped it (exit 124).
     - **DRA-39, `"mode": "ufo"`:** the message is `tuning/debug_spawns.json: mode must be "all" or a drifter type (meteorite, satellite)`, and the process idled.
     - **DRA-39, normal mode ignores the list:** with the broken list, it logged `start mode=normal` and `tuning loaded ...`, with no `debug spawns loaded` and no ERROR, and ran until stopped.
     - **DRA-29, bad tuning file:** `ValueError: tuning/drifters/meteorite.json: speed_ratio must be a number`, and the process idled.
     - **DRA-5, `app.frame` blocked:** the ERROR with the `ModuleNotFoundError`, then idle (exit 124).
     - **DRA-5, `pygame` blocked:** the ERROR, then `error screen failed`, then it exited by itself (exit 0).
     - **DRA-19, null character:** the ERROR with `ValueError: bad^@value`, no `error screen failed`, and the process idled.
   - Build: `pygbag --archive game` from the repo root built `game/build/web.zip` (git-ignored, not committed). The package contents are clean. See Browser run.
   - Browser: every required check passed. Every DRA-39 check that can run with the committed file passed, and so did the earlier DRA-5 to DRA-29 checks as reworded. See Browser run.
   - Logging is by event. The app adds one line, INFO `debug spawns loaded ...`, at startup in debug mode, and the `tuning loaded` line is longer. Nothing is logged per tick or per frame.
4. **Assumptions:** none beyond the choices under Decisions.
5. **Documentation differences:** None.
6. **Next:** Director: run `scripts/close-out.sh DRA-39` to see open review findings and these Observations before close-out. Three checks need you, because the contract lets only you switch the spawn list's mode. They are Satellite warning, Satellite crosses and leaves, and Angled and inverted. Set `"mode": "satellite"` in `game/tuning/debug_spawns.json` (or allow me to switch it for one run and put it back), then run `game/scripts/start-driftward-ace.sh --debug` and open `http://localhost:6060/?debug=1`. I showed all three with an in-browser stand-in that changes no file; see Observations. For normal mode, run the script with no argument and open `http://localhost:6060`. Build check: `pygbag --archive game` from the repo root gives `game/build/web.zip`. The frame loop changed, so the contract asks you to check pygbag's click screen by hand in a desktop browser.
7. **Status:** done.

## Browser run
- **Build check:** `pygbag --archive game` (pygbag 0.9.3), run from the repo root, gave `game/build/web.zip` (82191 bytes). It holds `index.html`, `favicon.png` and `game.apk`. `game.apk` holds exactly:
  - `assets/main.py`
  - `assets/app/{debug_spawns,frame,guard,log,loop,mode,settings,tuning}.py`
  - `assets/core/{collision,levels,run,scroll,ship,world}.py`
  - `assets/core/drifters/{__init__,base,meteorite,registry,satellite,spawner,tuning}.py`
  - `assets/tuning/{debug_spawns,hazards,playtest}.json` and `assets/tuning/drifters/{meteorite,satellite}.json`
  - `assets/ui/{debug_overlay,error_screen,game_over,hud,look,shapes,ship_view,starfield}.py`
  - `assets/ui/drifters/{__init__,entry_warning,meteorite_view,registry,satellite_view}.py`

  There is no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml`, `__pycache__` or tool cache. The packed `app/frame.py` calls `load_debug_spawns(tuning)`. **Package contents: passed.**
- **Served** with `game/scripts/start-driftward-ace.sh --debug` in the background (script pid 1052932; log and pid file in the scratchpad). Port 6060 was free first, and `curl` got 200 after 1 s. I opened 18 pages against that one server and closed each tab before the next. One `/` page was never clicked; on every other page I clicked the canvas once.
- **Stopped** with `kill 1052932`. The trap logged `Stopping server (pid 1052938)` and `Server stopped`. Port 6060 was free afterwards.
- **How inputs and reads were done**, as in DRA-29:
  - Keys were sent as `KeyboardEvent`s on `#canvas` through `browser_evaluate`.
  - Console lines were timestamped in page ms by a `console.log` hook, loaded from `localStorage` 240 to 300 ms after navigation, before the start line. Times below are ms after play start: the first `drifter spawn` line in debug mode, the `tuning loaded` line in normal mode.
  - Canvas pixels were read with `getImageData`.
  - Text was compared with reference text rendered in the same page with the game's default font, after the timed reads. "Exact" means 0 inked pixels missing and 0 extra.

**Required checks:**
- **Build is served and loads: passed.** `#canvas` is 640x480. pygbag logged `orig_argv [debug=1]` and `config.debug = false`.
- **Start line: passed.** `11:16:45 INFO app.loop: start mode=debug` on the first page. On every debug page it came about 150 ms before play start.
- **No console errors: passed.** Every page had exactly the two known errors: `Failed to load resource: 404 //cdn/0.9.3//browserfs.min.js` and `PyMain: BrowserFS not found`. No game ERROR line on any page. (One extra browser line on an aborted navigation is under Observations.)
- **Arrow-key input with x/y (`?debug=1`): passed.** I held ArrowUp from play start for 11.5 s:
  - `key down key=up x=320.00 y=240.48`
  - `top line stop x=320.00 y=184.00` 352 ms later
  - `key up key=up x=320.00 y=184.00`

  The y went from 240.48 down to 184.00, so ArrowUp lifts the ship. A 200 ms tap on another page gave `key down key=up x=320.00 y=240.00`, `respawn wait end`, then `key up key=up x=320.00 y=219.72`.

**DRA-39 checks (extra):**
- **Tuning loaded, reworded (`/` and `?debug=1`): passed.** One INFO line on every page: `tuning loaded drifters=meteorite,satellite hazard_speed_scaling=True timer_scaling=True rehit_cooldown=180 rehit_dim=0.75`. It comes about 110 ms after the start line and before `scroll start`.
- **Spawn list loaded (`?debug=1`): passed.** One INFO line, `debug spawns loaded mode=meteorite rows=3 loop_ticks=180`, 2 ms after `tuning loaded` and about 520 ms before the first `scroll start`. On the three `/` pages and the `?debug=yes` page there was no such line.
- **Dim after a hit (`?debug=1`, ArrowUp held from play start): passed.**
  - `drifter touch id=2 type=meteorite effect=hit` came at 3138 ms.
  - At 4143 ms (1005 ms later), in columns 306 to 334 and rows 250 to 479, there were 524 pixels of (105, 105, 105) in a disc at x 307 to 332, y 291 to 316, and 0 of (140, 140, 140).
  - At the same moment, around x 160 there were 512 pixels of (140, 140, 140) and 0 of (105, 105, 105). Around x 480 there were 1116 and 0.
  - No (105, 105, 105) pixel was anywhere but on id 2.
- **A hit costs one life, reworded (`?debug=1`): passed.** id 2 never logged a second `drifter touch`. Its `drifter gone id=2 ... y=494.30` came 2283 ms after the touch, inside its 3 s cooldown.
- **Normal mode spawns nothing, reworded (`/`): passed, with a note.**
  - In 149 full-canvas reads over 5 s: 0 glow (255, 220, 120), 0 blue (60, 110, 220) and 0 green.
  - 13 grey (140, 140, 140) and 14 (240, 240, 240) pixels showed up. All of them are on the white meters readout's anti-aliased edge: a 3 s scan put the (240, 240, 240) pixels only at (20, 32) and (21, 32). None is a rock or a satellite. See Observations.
- **Shared hazard values, bad spawn list, normal mode ignores the list (desktop, headless): passed.** See Checks.
- **Package contents: passed.** See Build check.
- **Satellite warning, Satellite crosses and leaves, Angled and inverted (satellite mode): not run as written.** The committed file is `"mode": "meteorite"`, and I had no Director allowance to switch it. I showed all three with a stand-in that changes no repo file; see Observations. Results from the stand-in page (`?debug=1`, ArrowUp held, overlay hidden with F3 for clean pixel reads):
  - **Satellite warning:**
    - The log has `drifter spawn id=1 type=satellite variant=flat x=-18.00 y=120.00 speed=2.47 level=1`, then 981 ms later `drifter active id=1 type=satellite x=-18.00 y=120.00`.
    - At 216 ms there were 463 glow pixels, all within 18 px of (18, 120) in x and 17 in y.
    - There were 36 white (240, 240, 240) pixels, all within 3 px of (18, 120). That is the 6 x 6 half-size body.
    - There were 36 blue pixels in columns 9 to 26 and rows 118 to 120: the 18 x 3 bar.
  - **Satellite crosses and leaves:**
    - 154 ms after `drifter active`, 120 white body pixels sat at the left edge, columns 0 to 9 and rows 114 to 125. So the satellite was not removed while it sat outside the wall.
    - Reads at 1004 and 1505 ms showed the body at columns 124 to 135, then 198 to 209, in the same rows 114 to 125. That is 74 px in 0.5 s.
    - The blue bar was 36 px wide (columns 112 to 147).
    - `drifter gone id=1 type=satellite x=658.09 y=120.00` came 4567 ms after `drifter active` (274 ticks is 4567 ms). id 1 logged exactly one spawn, one active and one gone.
  - **Angled and inverted (row 4, y 180):**
    - `drifter spawn id=4 type=satellite variant=angled x=658.00 y=180.00`.
    - The warning glow was within 15 px in x and 17 px in y of (622, 180).
    - The blue half-size copy spans columns 613 to 629. The leftmost column's lowest blue pixel is at row 183, the rightmost column's at row 177, so it runs down to the left.
    - Reads 0.5 s apart after `drifter active` put the body at center (587.5, 204.5), then (518.5, 230.5). That is 69 px left and 26 px lower.
    - The body was a 12 x 12 square of 144 pixels in both reads, so its boxes stay upright.
  - **Player sees, satellite hit and dim (scope report):**
    - The angled satellite id 2 met the hovering ship: `drifter touch id=2 type=satellite effect=hit`, then `life lost lives=2`.
    - 504 ms later, around the ship it showed 144 body pixels of (180, 180, 180) and 144 bar pixels of (45, 83, 165) (0.75 of each color), and no full-color pixel. The other satellites on screen showed 648 full white and 648 full blue pixels.
    - 2003 ms after the hit, id 2 was still dim (144 and 144) at x 570 to 581.

**Earlier checks, reworded where the contract says so (all passed):**
- **DRA-29, the test spawn list (`?debug=1`, no key):**
  - 0: `drifter spawn id=1 type=meteorite variant=small x=160.00 y=-10.00 speed=2.47 level=1`
  - 978: `drifter active id=1 ... x=160.00 y=-10.00`
  - 980: `drifter spawn id=2 ... variant=medium x=320.00 y=-14.00`
  - 1980: `drifter spawn id=3 ... variant=big x=480.00 y=-20.00`
  - 2979: `drifter spawn id=4 ... variant=small`
  - 4361: `drifter gone id=1 ... x=160.00 y=490.90`

  Each id has one spawn, one active and at most one gone.
- **DRA-29, warning then the rock:**
  - At 213 ms: 61 glow pixels within 10 px of (160, 10), and 56 grey pixels within 5 px.
  - At 1215 ms: no glow near it, and a grey disc in columns 151 to 168, centered on y 24.5.
  - At 1717 ms: the disc centered on y 98.5, 74 px lower.
- **DRA-29, a hit costs one life (ArrowUp held):**
  - 3138: `drifter touch id=2`, `life lost lives=2`, no `respawn from`
  - 6137: id 5 hit, `life lost lives=1`
  - 9137: id 8 hit, `life lost lives=0`, then 9139: `game over meters=57`

  No small or big rock touched. Pixel (320, 184) after the hit showed visible spans 22 to 89, 208 to 273 and 407 ms on, with hidden spans 105 to 191 and 290 to 390. The visible spans had one-frame green dips; see Observations.
- **DRA-29, game over freezes, retry clears:**
  - Two full reads 2 s apart were identical, and no line came in between.
  - After the ArrowUp release and an ArrowLeft tap 500 ms later: `new run`, then `drifter spawn id=1 ... variant=small` 16 ms after it.
  - The frame 100 ms later had 56 grey pixels, all at x 155 to 164 and y 5 to 14, inside the new warning.
- **DRA-29, outlines and labels (`?debug=1`):**
  - At 2503 ms, id 2's disc was centered at (319.5, 61.5).
  - Green covered 36 of 36 sample points on the radius 14 circle and 36 of 36 on the radius 28 circle. A radius 21 control circle got 7 of 36.
  - The label at (306, 76) is exactly `meteorite medium x 320.00 y 62.49 active`. The 18 extra green pixels in its box all lie on the graze circle. The tick values before and after leave 53 and 48 inked pixels unmatched.
  - The ship's T outline is green: column 314 rows 224 to 255 (32 of 32), and column 304 rows 244 to 255 (12 of 12).
  - During the warning, the label `meteorite medium x 320.00 y -14.00 warning` matched exactly at (306, 0).
  - F3 logged `overlay visible=False` and left 0 green pixels. F3 again logged `overlay visible=True` and brought back 3103.
- **DRA-23, a fall costs a life:** `life lost lives=2` and `respawn from x=320.00 y=500.20 wait=True` at 1030 ms. The hearts then read [0, 364, 364].
- **DRA-23, three hearts (`/`):** [364, 364, 364] at 160 ms. The area x 536 to 639, rows 0 to 39 had 1092 white pixels, so nothing else is white there.
- **DRA-23, blink (`/`):** pixel (320, 240) was dark 915 to 1061 ms (the fall), white 1079 to 1161, dark 1177 to 1261, white 1278 to 1361, dark 1378 to 1461, then white from 1478 on.
- **DRA-23, the wait, and DRA-6, log by event (waiting part):**
  - The overlay read exactly `x 320.00 y 240.00 vx 0.00 vy 0.00` at 0.7, 1.5, 2.5 and 3.95 s after the respawn.
  - Leaving out `drifter spawn/active/gone`, the only new lines were:
    - `invulnerable end` at +499 ms
    - `drifter touch id=2 type=meteorite effect=hit` and `life lost lives=1` at 3495 ms after play start
    - `invulnerable end` 500 ms after that
  - The readout went from 8 m to 29 m in 3.26 s.
- **DRA-23, a press ends the wait:** see the required check (y 240.00 to 219.72). After the release the ship fell.
- **DRA-23, a held key doesn't end the wait:**
  - ArrowDown was held from play start. `respawn from x=320.00 y=500.42 wait=True` came at 864 ms.
  - For 2 s with Down held there was no `respawn wait end`, and the overlay was exact at 0.2, 1.0 and 1.95 s.
  - Then the release, and an ArrowLeft tap: `respawn wait end`, and `key up key=left x=295.07`.
- **DRA-23, game over by a fall, freeze, retry needs a fresh press, new run (three dives):**
  - `life lost lives=0` and `game over meters=14` at 2658 ms, with no `drifter touch` before them.
  - Hearts [0, 0, 0]. `Game Over` matched exactly at (260, 222) and `Press any arrow to retry` at (257, 246). 17 star pixels inside the box read (58, 64, 90). No white pixel outside the text below row 100.
  - Two reads 2 s apart were identical, with no line in between.
  - With Down still held, F3 twice gave only the two `overlay visible` lines. The release logged `key up key=down x=320.00 y=497.10`.
  - An ArrowLeft tap 500 ms later gave `new run`, 510 ms after the release.
  - 250 ms into the new run: `0 m` exact at (4, 76), hearts [364, 364, 364], no darkened star, and the box text gone.
  - The ship showed on every frame. `scroll start tick=31` came 515 ms after `new run`, and `life lost lives=2` 1066 ms after.
- **DRA-23, normal mode (`/`):**
  - Three falls (ArrowUp taps ended the waits) came at 1075, 2908 and 4748 ms.
  - Hearts [0, 0, 0]. Both texts exact at the same places as in debug mode. 15 darkened stars, and no stray white.
  - An ArrowLeft tap gave hearts [364, 364, 364], `0 m` exact at (4, 24), and no darkened star.
  - 0 green pixels in 230 reads.
- **DRA-19, no `-0.00`:** with ArrowUp held I tapped ArrowLeft (`key up key=left x=295.07 y=184.00`). 3 s later `vx 0.00` matched exactly, and `vx -0.00` left 34 inked pixels unmatched.
- **DRA-13, scroll start logged once:** exactly one `scroll start tick=31` per run on every debug page, 479 to 515 ms after play start.
- **DRA-13, readout counts up (`/`):** exact matches at (4, 24): `0 m` at 160 ms and at 411 ms, `29 m` at 5.0 s and `62 m` at 10.0 s.
- **DRA-13, hovering still earns meters (`/`):** ArrowUp held from 10.3 s, with the ship's top row at 168. The readout went from 67 m to 91 m in 3.6 s.
- **DRA-13, starfield moves (`/`):** 0 px shift between 160 and 411 ms (131 of 131 star pixels). 65 px between 1 s and 2 s (130 of 131).
- **DRA-13, no overlap and top line:** the four overlay lines were exact at x 4, rows 4 to 40, with ink down to row 48. The readout was exact at (4, 76), with ink from row 77. With F3 hiding the overlay, the readout stayed at (4, 76). The top line ceiling is `y=184.00`.
- **DRA-6, log by event (Up and Left held 3 s from the waiting ship):**
  - Between `key down` at (320.00, 240.00) and `key up` at (16.00, 184.00) there was exactly one `top line stop x=256.79 y=184.00` and exactly one `wall hit side=left x=16.00 y=184.00`.
  - Extra check, the left wall: the ship's white box stayed at x 1 to 30 for the whole last second of the hold. It stopped at the wall with no bounce.
- **DRA-6, respawn:** `life lost lives=1`, then `respawn from x=16.00 y=499.20 wait=True`, 1228 ms after the release.
- **DRA-6, ship visible and overlay with F3:** row 168 had 640 green pixels on the first frame. F3 took it to 0, and F3 again brought back 640. In `/` there was no green, and F3 logged nothing.
- **DRA-6, catch-up cap:** a 5000 ms main-thread stall while the ship waited gave one line, `tick cap hit, dropped 4.940 s`, not repeated. The readout went from 5 m to 6 m, and the overlay still read exactly `x 320.00 y 240.00 vx 0.00 vy 0.00`.
- **DRA-6, click to start, follow-up (`/`, fresh tab, never clicked):** `navigator.userActivation.hasBeenActive` read `true` before any click. The page text was "Loading, please wait ...". There was no click screen and no "MEDIA USER ACTION REQUIRED". The start line came 2.70 s after navigation, and the game ran with no click. This is the same result as DRA-6 to DRA-29.
- **DRA-5, run modes:** `/` logged `start mode=normal`, and `?debug=1` logged `start mode=debug`. `?debug=yes` logged `WARNING app.loop: debug switch value 'yes' is not 1, using normal mode`, then `INFO app.loop: start mode=normal`.

## Observations
- **The three satellite-mode checks need the Director.** The contract allows only the Director to switch `game/tuning/debug_spawns.json` to `"mode": "satellite"`, or to allow me to switch it for the run. I had neither, so the file stays `"mode": "meteorite"`.
  - On one page I showed the checks with an in-browser stand-in that changes no repo file. In-page Python copied the committed list into the browser's own temporary folder with `mode` set to `satellite`, and loaded it with the game's `load_debug_spawns`. That logged `debug spawns loaded mode=satellite rows=4 loop_ticks=180`. Then it pointed `app.frame.debug_spawns_due` at that list.
  - Core, the views, the loader and the frame loop are the real ones, and it took effect before tick 1, so the ids match the contract.
  - It is still not the check as written. Run it once with the file switched.
- **"Then can hit again" after the 3 s cooldown was not shown in the browser.** With the committed rows, every hazard that hits leaves the screen before its cooldown ends: meteorite id 2 after 2.28 s, satellite id 2 after about 2.3 s. The QA tests in `DRA-39-07` cover the re-hit headless. Showing it in a browser needs a slow or still row in the spawn list, which is the Director's file.
- **The list's `all` mode and a changed `loop_ticks` were not shown in the browser.** Both need a file edit. Both were checked on desktop against scratch copies (see Checks).
- **The "Normal mode spawns nothing" check catches the readout again.** DRA-39 adds "no (240, 240, 240) pixel anywhere". The white meters readout's anti-aliased edge lands on that grey at (20, 32) and (21, 32), as it lands on (140, 140, 140) (DRA-29 Observations). No satellite drew in normal mode: no blue pixel, and no body square. The Architect may want to leave the HUD text area out of this check.
- **With the overlay on, the blink pixel (320, 184) dips to green for one frame inside the visible spans.** The debug outlines are drawn above the ship (`systems/app.md`, Draw), so the falling rock's hitbox and graze circles cross the sampled pixel. The spans themselves are right. The hidden spans show the dimmed rock (105, 105, 105) behind the ship.
- **One browser console error came from my test, not the game.** On my first navigation away from a running page, pygbag's `beforeunload` handler logged `Blocked confirm('Are you sure you want to navigate away from this page ?') during beforeunload`. After that I closed each tab before opening the next.
- **The Director's hand check of the click screen is due.** `systems/app.md` asks for it when the frame loop changes, and DRA-39 changed the tick call. The test browser gave the known result: the game starts before any click.
- **The Playwright tool writes its console and snapshot logs to `/workspace/.playwright-mcp/`.** That folder is git-ignored. Nothing from it is committed.

## Decisions
- **Load order:**
  - Both modes: `tuning = load_tuning()`.
  - Debug mode only: `spawn_list = load_debug_spawns(tuning)`.
  - Then `start_run()`. All inside the guard, so a bad file shows the error screen.
  - Normal mode never reads the list.

  Source: `systems/app.md`, Rules, Frame loop (DRA-39) and the DRA-39 call block.
- **The debug gate in the tick is `spawn_list is not None`.** It is None exactly in normal mode. Gating on it instead of on `debug` lets mypy narrow the type without a cast. Each tick is still one `step_run`, then in debug mode only `add_drifters(run, debug_spawns_due(spawn_list, run.scroll.ticks), tuning)`. Source: `systems/app.md`, Rules, Tick.
- **A drifter's own fields come from a table in `app/tuning.py`.** `_OWN_FIELDS` maps `DrifterType.SATELLITE` to its extra variant field (`angle_degrees`) and a checker. The checker requires exactly two boxes and an angle >= 0 and < 90, and builds `SatelliteVariantExtra`. A type not in the table follows `drifter-tuning.schema.json` and gets `extra=None`. The fireball adds one entry. Source: `systems/app.md`, Rules, Tuning loader (A drifter's own fields); `satellite-tuning.schema.json`.
- **Hazard defaults come from core.** A field left out of `hazards.json` takes `DEFAULT_REHIT_COOLDOWN_TICKS` or `DEFAULT_REHIT_DIM` from `core.drifters.base`. The loader holds no copy. `rehit_cooldown` must be a Python `int` (5.0 is rejected), because the schema says integer and the contract says types exact. Source: `systems/app.md`, Rules, Tuning loader (Hazards file).
- **The optional fields in the spawn list count as absent only when the key is missing.** A JSON `null` for `x`, `y`, `variant`, `speed` or `invert` fails its type check, because the schema allows no null. Source: `debug-spawn-list.schema.json`; game/CONTEXT.md, Error handling.
- **Row checks go schema first, then the spawn.** Each row is checked against the schema: type, then x or y, then field types. Then it is spawned once with `spawn_drifter(placement, 1, tuning)`. A `ValueError` from the spawn is raised again as `tuning/debug_spawns.json: rows[i]: <message>`, `from` the original. Only `ValueError` is caught, since that is what `spawn_drifter` raises. Source: `systems/app.md`, Rules, Debug test spawn list.
- **Timing.** Row `i` of `n` in play has offset `(i * loop_ticks) // n`. `debug_spawns_due` returns the rows whose offset is `(ticks - 1) % loop_ticks`, in schedule order, and `()` below tick 1. An empty list in play gives an empty schedule and no division. Source: `systems/app.md`, Rules, Debug test spawn list (Timing).
- **`debug_spawns.py` reuses the tuning loader's private helpers** (`_read_json`, `_fields`, `_is_number`). The spawn list file is then read through `app.tuning.TUNING_DIR` at call time and named the same way, `tuning/...`. `_fields` gained an `optional` argument for the files whose fields are optional. Both modules are mine, and their public interface is as the contract gives it. Source: `systems/app.md`, Interface, `app/debug_spawns.py` (`SPAWN_LIST_FILE` in `app.tuning.TUNING_DIR`, read at call time).
- **Nothing else changed.** The loop structure (fixed 60 Hz accumulator, cap of 5 ticks, `await asyncio.sleep(0)` each frame), key and F3 handling, the draw order, `main.py`, the startup modules, the start script and `pygbag.ini` are as they were. Source: `systems/app.md`, Impact; `15-tech-constraints.md`, rules 1 and 2.
