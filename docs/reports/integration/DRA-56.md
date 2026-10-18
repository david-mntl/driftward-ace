Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-56 (fireball), Integrate mode. This is a re-run after my earlier `Verdict: blocked`, started by the main session for the Director. The main session put the contract's six fireball rows into `game/tuning/debug_spawns.json`, and allowed me to switch `mode` for the run and put it back.
2. **Delivered:**
   - `game/app/tuning.py` and `game/app/debug_spawns.py`, changed in the earlier run and not changed since.
   - `docs/reports/integration/DRA-56.md`, rewritten for this run.
   - No change to `game/main.py`, the other `game/app/` modules, `game/scripts/` or `pygbag.ini`.
   - `game/tuning/debug_spawns.json` was switched for the run and then put back. `cmp` against a copy taken before the switch shows it is byte-identical, with `"mode": "fireball"`.
3. **Checks:**
   - `game/tests/check.sh`: `QA: pass` (env, lint, format, typecheck, core, ui).
   - Headless import (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, from `game/`): `import app.loop, app.frame, app.tuning, app.debug_spawns` is clean.
   - `load_tuning()` builds fireball small 21 × 21 and big 32 × 32, with `FireballTypeExtra(angle_degrees=35, tail_ratio=0.5)`.
   - Build: `pygbag --archive game` made `game/build/web.zip`. The package is clean.
   - Every required browser check passed. Every DRA-56 contract check passed as written. I also re-ran the earlier features' main debug checks in meteorite, satellite and chain lightning mode, and the earlier desktop loader checks. All passed. Details are in Browser run.
   - One scope behaviour is still only partly visible: the top-right corner warning sits under the hearts. See Observation 1. The Director has to decide it.
   - Logging is by event. Nothing is logged per tick.
4. **Assumptions:** none new. From the earlier run: the angle error reads `angle_degrees must be a number >= 0 and < 90`, copied from the satellite's message. The contract gives no example for this error.
5. **Documentation differences:** none from my work. Observation 2 suggests a wording change to one earlier check in app.md, for the Architect if the Director wants it. Nothing depends on it.
6. **Next:**
   - Director: run `scripts/close-out.sh DRA-56`. It shows open review findings and these Observations. Decide Observation 1 (UI-01) before close-out.
   - To play the build: run `game/scripts/start-driftward-ace.sh` (or `--debug`), then open http://localhost:6060 (or `/?debug=1`).
   - Build check: `pygbag --archive game` gives `game/build/web.zip`.
7. **Status:** done.

## Browser run
- **Build check:** `pygbag --archive game` (pygbag 0.9.3), run from the repo root, made `game/build/web.zip` (97895 bytes, built 12:32, git-ignored, not committed).
  - The zip holds `index.html`, `favicon.png` and `game.apk`.
  - `game.apk` holds 46 files under `assets/`, among them `core/drifters/fireball.py`, `ui/drifters/fireball_view.py` and `tuning/drifters/fireball.json`.
  - Its `tuning/debug_spawns.json` has mode `fireball`.
  - It has no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml`, `__pycache__` or tool cache.
  - **Package contents: passed.**
- **Served** with `game/scripts/start-driftward-ace.sh` in the background, four times, once per spawn mode. Before each start the port check gave `000`, and `curl` got 200 within 2 s.
  - fireball (pid 35432), meteorite (pid 38137), satellite (pid 38495), chain_lightning (pid 38847).
  - Each was stopped with `kill <pid>`. The trap logged `Stopping server` and `Server stopped`.
  - After the last stop, `curl` got `000`, so the port is free. The logs and pid files are in the scratchpad.
- **How pages were run:**
  - One page at a time, each closed before the next. Reusing a page hits pygbag's `beforeunload` dialog.
  - Each page got a `console.log` hook that timestamps lines in page ms. Times below are ms after play start, which is the `drifter spawn id=1` line.
  - The canvas was clicked once on each page.
  - Keys were `KeyboardEvent`s on `#canvas`, sent at play start or later.
  - Canvas pixels were read with `getImageData`.
  - Two pages were thrown away and not counted. On one, the hook went in at 8.0 s, after the game had started. On the other, the key-down was sent at the start line, before the frame loop ran, so no `key down` line appeared. Each was repeated in a fresh page.

**Required checks (fireball mode, the committed file):**
- **Build is served and loads: passed.** The page title went to `pygame window` on every page.
- **Start line: passed.** `/` showed `INFO app.loop: start mode=normal`. Every `?debug=1` page showed `INFO app.loop: start mode=debug`, about 260 ms before play start. The game started before the click, which is the known headless result.
- **No console errors: passed.** Every page had only the two known lines: `404 //cdn/0.9.3//browserfs.min.js` and `PyMain: BrowserFS not found`. There was no game ERROR or WARNING line.
  - The browser warnings were pygbag's known ones.
  - One extra Canvas2D `willReadFrequently` warning came from my own pixel reads.
- **Arrow-key input with x/y (`?debug=1`): passed.** ArrowUp went down at 206 ms and up at 507 ms:
  - `DEBUG app.frame: key down key=up x=320.00 y=256.80`
  - `DEBUG app.frame: key up key=up x=320.00 y=252.66`

  The y fell by 4.14 px, so ArrowUp lifts the ship.
  - The same page also ran the DRA-6 2 s hold. Key down at 1506 ms gave `y=389.60`, then `top line stop x=320.00 y=184.00`, then key up at 3506 ms gave `y=184.00`.

**DRA-56 contract checks (extra, fireball mode, `?debug=1`):**
- **Tuning loaded: passed.** On every page: `tuning loaded drifters=meteorite,satellite,chain_lightning,fireball hazard_speed_scaling=True timer_scaling=True rehit_cooldown=180 rehit_dim=0.75 telegraph_min=45`. It comes after the start line and before `scroll start`.
- **Spawn list loaded: passed.** `debug spawns loaded mode=fireball rows=6 loop_ticks=180`.
- **Fireball warning, tilted: passed.** At 0 ms: `drifter spawn id=1 type=fireball variant=small x=125.00 y=-10.50 speed=3.09 level=1`.
  - I read all 23 frames before 465 ms. Glow sat at x 113–133, y 0–20, and no glow pixel was more than 12 px from (125, 12).
  - Within 8 px there were 76 orange and 5 dark yellow pixels.
  - Orange mean (124.9, 13.6) against yellow mean (121.0, 8.4): the orange is right of and below the yellow.
- **Every entry's warning: passed, but see Observation 1 for id 3.**
  - The spawn lines match the contract: `id=2 ... small x=0.00 y=-10.50`, `id=3 ... big x=640.00 y=-16.00`, `id=4 ... small x=-10.50 y=120.00`, `id=5 ... big x=656.00 y=200.00`, `id=6 ... small x=560.00 y=-10.50 speed=2.00`.

  | Read at | Warning | Glow box | Orange vs yellow mean |
  |---|---|---|---|
  | 1206 ms | id 2, at (12, 12) | x 3–20, y 2–20 | (11.7, 14.0) vs (8.0, 7.5) |
  | 1206 ms | id 3, at (628, 12), `invert` | x 618–636, y 1–20 | (629.5, 9.5) vs (630.2, 7.3): left and below, but from **2** orange and 6 yellow pixels. 215 white heart pixels lie within 12 px. |
  | 1706 ms | id 4, at (12, 120) | x 2–22, y 111–131 | (11.9, 121.6) vs (7.8, 115.7) |
  | 2206 ms | id 5, at (628, 200), `invert` | x 616–638, y 188–210 | (626.3, 201.0) vs (630.3, 195.2): left and below |

  No glow pixel lay more than 12 px from its warning's point.
- **It flies: passed.** At 963 ms: `drifter active id=1 type=fireball x=125.00 y=-10.50`.
  - At 1506 ms the orange head was at (179.4, 67.4). At 2006 ms it was at (232.4, 143.4). That is 53.0 px right and 76.0 px lower in 500 ms. The contract expects about 53 and 76.
  - The head reads 18 px across, because the debug outline covers the rim of the 21 px disc.
  - The dark yellow tail sits at (170.5, 54.5), up and to the left, 15.7 px from the head's center. Touching circles give 10.5 + 5.25 = 15.75. It reads 8 px across, again with the outline over its rim.
- **A touch costs a life (no key held): passed.** Three pages gave the same log.
  - After the fall: `life lost lives=2`, `respawn from x=320.00 y=500.20 wait=True`.
  - At 2598 ms: `drifter touch id=1 type=fireball effect=hit`, then `life lost lives=1`, with no `respawn from` after it.
  - At 5609 ms: `drifter touch id=7 ...`, `life lost lives=0`, then `INFO game over meters=33`.
  - No touch came from any other id.
- **It dims after the hit: passed.** Read at 3156 ms:
  - Dim orange (191, 105, 0) disc centered at (356.4, 320.4), box x 348–365, y 312–329. No (255, 140, 0) pixel within 9 px of (352, 314).
  - Dim tail (150, 120, 0) centered at (347.5, 307.5). No (200, 160, 0) pixel near (343, 301).
- **Nothing visible when it goes: passed.** Every frame from 4206 to 4490 ms, read in rows 465–479 and columns 440–500:
  - 4206 to 4240 ms: dim head and dim tail.
  - 4256, 4273 and 4290 ms: only the dim tail (rows 473–478), with no orange or dim orange pixel. The head had left and the tail still showed.
  - 4306 ms on: nothing.
  - `drifter gone id=1 type=fireball x=483.32 y=501.23` came at 4330 ms, after the last frame with tail pixels.
- **Every row leaves (ArrowUp held from play start to 9500 ms): passed.**
  - `key down key=up x=320.00 y=240.48` came at 26 ms, then `top line stop x=320.00 y=184.00`.
  - There was no `drifter touch` and no game over during the hold.
  - The gone lines match the contract exactly:

    | id | x | y | Time |
    |---|---|---|---|
    | 1 | 483.32 | 501.23 | 4335 ms |
    | 2 | 358.32 | 501.23 | 4835 ms |
    | 3 | 271.04 | 510.93 | 5436 ms |
    | 4 | 255.58 | 500.00 | 4970 ms |
    | 5 | 437.82 | 511.60 | 5020 ms |
    | 6 | 202.09 | 500.65 | 8670 ms |

  - The key up came at 9502 ms: `x=320.00 y=184.00`. The hits after the release are outside this check.
- **Outlines: passed.** At 1506 ms, around id 1:
  - Around the head's center, green (0, 255, 0) pixels peak at 9–10 px (radius 10.5) and 23–24 px (graze 24.5).
  - Around the tail's center they peak at 4–5 px (radius 5.25) and 18–19 px (graze 19.25).
  - The label sits under the head, at rows 81–91, columns 161–227.
- **Bad fireball file and a row with no position (desktop): passed.** Run with `SDL_VIDEODRIVER=dummy` and `DRIFTWARD_DEBUG=1`, using scratch copies of `game/tuning/`:
  - `"tail_ratio": 0` gives ERROR `unexpected error, showing the error screen` with `ValueError: tuning/drifters/fireball.json: tail_ratio must be a number > 0`.
  - Adding `{"type": "satellite"}` gives `ValueError: tuning/debug_spawns.json: rows[21]: satellite placement needs y`.
  - Neither case logged `error screen failed`. Both idled until the 5 s timeout (exit 124).
- **Package contents: passed.** See Build check.

**Earlier checks, re-run (extra):**
- **Normal mode (`/`), 316 frames over 5.3 s:**
  - `start mode=normal` and the `tuning loaded` line appeared. There was no `debug spawns loaded`.
  - There were 0 pixels of glow, (60, 110, 220), (0, 220, 255), (120, 200, 255), (220, 240, 255), (255, 140, 0), (200, 160, 0) or (0, 255, 0).
  - 27 pixels of (140, 140, 140) and 27 of (240, 240, 240) came from the meters readout's text edges. See Observation 2.
  - The ship is an inverted T at 70 ms: (320, 230), (308, 250) and (331, 250) are white, and (308, 230) and (331, 230) are black.
  - Three hearts showed, 364 white pixels in each box, and there was no white pixel elsewhere in x 536–639, rows 0–39.
- **Meteorite mode (`?debug=1`, ArrowUp held 10 s): passed.**
  - The spawn list loaded as `rows=3 loop_ticks=180`.
  - Spawn lines: `id=1 small x=160.00 y=-10.00 speed=2.47`, `id=2 medium x=320.00 y=-14.00`, `id=3 big x=480.00 y=-20.00`.
  - `drifter gone id=1 ... x=160.00 y=490.90` came at 4351 ms.
  - Touches came only from id 2 (3118 ms, lives=2), id 5 (6118 ms, lives=1) and id 8 (9118 ms, lives=0, then game over).
  - The key up came at 10017 ms with `y=184.00`.
  - DRA-39 dim, read at 4121 ms: in columns 306–334, rows 250–479, there were 524 pixels of (105, 105, 105) and 0 of (140, 140, 140). Near x 160 there were 512 pixels of (140, 140, 140) and 0 of (105, 105, 105).
- **Satellite mode (`?debug=1`): passed.**
  - The spawn list loaded as `rows=4`.
  - At 518 ms, id 1's warning: glow at x 0–20, y 108–128. The white body was at x 10–14, y 118–122. The blue bar was at x 5–18, y 119–120.
  - Its lines: `drifter spawn id=1 type=satellite variant=flat x=-18.00 y=120.00 speed=2.47`, then `active` at 961 ms, then `gone x=658.09 y=120.00` at 5528 ms, 4.57 s after active.
  - At 2617 ms, id 4 (angled, `invert`, y 180): glow at x 618–638, y 171–191. The blue copy's leftmost column bottoms out at y 182 and its rightmost at y 178, so it runs down to the left.
- **Chain lightning mode (`?debug=1`): passed.**
  - The spawn list loaded as `rows=8`. The spawn line: `id=1 type=chain_lightning variant=pair_flat x=320.00 y=-6.00 speed=2.00`.
  - At 176 ms: glow at x 244–264, y 0–20. Cyan pixels were near (250, 18), (256, 6) and (262, 18), and none was within 10 px of (384, 12).
  - With no key held: `drifter touch id=1` at 2975 ms (lives=1), and `drifter touch id=9` at 5975 ms (lives=0, then game over). No touch came from any other id.
  - Every variant, with ArrowUp held 10 s: there was no touch and no life lost. Ids 1–8 each logged spawn with their row's variant and x, and each was gone with y ≥ 486. id 8 went last, at 7680 ms.
- **Earlier desktop loader checks (scratch copies, headless): passed.** Each error case idled until the 5 s timeout (exit 124), and none logged `error screen failed`.
  - `speed_ratio "fast"` gives an error naming `tuning/drifters/meteorite.json` and `speed_ratio`.
  - The row `{"type": "satellite", "x": 100}` gives `rows[21]: satellite placement needs y`.
  - `"mode": "ufo"` gives an error naming `mode`.
  - `trio_l` arcs `[[0, 2]]` gives an error naming `variants.trio_l.arcs[0]`.
  - `"telegraph_min": true` gives an error naming `tuning/hazards.json` and `telegraph_min`.
  - `{"rehit_cooldown": 5}` gives `... rehit_cooldown=5 rehit_dim=0.75 telegraph_min=45`.
  - In normal mode, the broken lists are ignored: `start mode=normal` and `tuning loaded` appear, with no ERROR.

## Observations
- **1. The top-right corner warning is still mostly hidden under the hearts. The Director decides this (UI-01).**
  - A fireball with `invert` and no position puts its warning at (628, 12). The HUD's third heart covers 608–631 × 8–31 and is drawn on top.
  - At 1206 ms, id 3's glow showed (x 618–636, y 1–20), but its copy showed only 2 orange and 6 dark yellow pixels under 215 white heart pixels.
  - The contract check holds on those 2 pixels. To a player, the tilt can't be read. The scope promises a tilted copy, and Pillar 2 needs it.
  - GDD 10-ui.md rule 1 says the HUD must never hide a warning. Its margins are UI-01, an open TBD (90-open-questions.md).
  - The hearts and the warning place each follow their own contract (hud.md and drifters.md). So this is not a bug in any file, and I left the HUD and the warning as they are, as the main session asked.
  - My earlier report said this behaviour would fail on a re-run. I now list it here, not as a bug, because no file is at fault and the fix depends on a TBD only the Director can settle. If the Director wants it fixed before DRA-56 closes, the feature should not close.
- **2. Normal mode, "no (140, 140, 140) and no (240, 240, 240) pixel anywhere" (DRA-29 and DRA-39 wording).**
  - 54 of the 316 frames had 1 or 2 such pixels, all at (7, 31), (7, 32), (13, 31), (13, 32), (14, 32) and (15, 31).
  - These are the anti-aliased edges of the meters readout's digits. Nothing spawned.
  - If the Director wants it, the Architect could reword the check to leave out the readout's box. That is a suggestion, not pending work.
- **3. Earlier checks I did not re-run this time.**
  - DRA-5 and DRA-6: run modes with `?debug=yes`, click-to-start details, F3 overlay toggle, catch-up cap, desktop import-error checks.
  - DRA-13: starfield and readout rates, and overlay overlap.
  - DRA-19: no `-0.00`, and the null character.
  - DRA-23: blink, the 5 s wait, held key, Game Over box pixels, freeze, retry and new run.
  - DRA-29: warning and outline pixels.
  - DRA-39: satellite crossing pixel speeds.
  - DRA-47: charge rays, arcs, chain dim, outlines and screenshot.
  - Why: DRA-56 changed no frame loop, guard, start-up, HUD or overlay code. My changes are only in the loader and the spawn list, and I re-ran every loader and spawn-list check. The core change to `is_partly_on_screen` and `is_off_screen` keeps one footprint box for the older drifters, and their gone lines match the earlier numbers.
- **4. Pages thrown away.** Two pages were discarded for test-harness timing, as described in Browser run. They show no game fault.
- **5. Local build folder.** The ignored `game/build/web/` holds the last live build, made in chain lightning mode. `game/build/web.zip` is the fireball-mode build. Neither is committed. The next start of the script rebuilds `web/`.
- **6. Contract status.** `docs/contracts/systems/app.md` (v8) and `drifters.md` (v3) are both `Status: draft`.

## Decisions
- **The report is rewritten, not given a new round.** The main session asked for it. No fix was made in my files. The earlier blocked report was about the spawn list content, and the main session has now settled that.
- **The mode was switched for the run, then restored.** I switched to meteorite, satellite and chain lightning mode to re-run the earlier debug checks, then copied the saved file back. The main session allowed this, and app.md, DRA-39, DRA-47 and DRA-56 Background ("allows the Integration Engineer to switch it for the run and put it back after").
- **Observation 1 is an observation, not a bug.** Both sides follow their contracts, so no owner's file is wrong. The rule that settles it, 10-ui.md rule 1, waits on UI-01 (TBD). CLAUDE.md says a TBD value goes to the Director.
- **The fireball's file has its own loader branch** (`_load_fireball`), and its hitbox comes from core's `fireball_hitbox(head_width, tail_ratio, angle_degrees, False)`. The footprint check is not run on these shapes. Source: app.md, Rules, Tuning loader; fireball-tuning.schema.json; drifters.md, Rationale (DRA-56).
- **A spawn row may have no position.** The drifter's `start_position` refuses a coordinate it needs, through the load-time spawn, wrapped with the row path. Source: app.md, Rules, Debug test spawn list (Fireball rows); debug-spawn-list.schema.json.
