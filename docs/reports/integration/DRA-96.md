Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-96 (Planet), started by the Director's main session: the planet's tuning file and its escape check in the tuning loader, then build and prove it in the browser.
2. **Delivered:** `game/app/tuning.py` (planet branch: `_load_planet`, `_planet_variants`, `_PLANET_FIELDS`, `_PLANET_VARIANT_FIELDS`, `_PLANET_FADE_MAX`; module docstring names the file and schema), `docs/reports/integration/DRA-96.md`. No change to `game/main.py`, `game/scripts/` or `pygbag.ini`; app.md says the frame, the spawn list module and the wave loader don't change.
3. **Checks:**
   - `game/tests/check.sh all`: env, lint, format, typecheck, core, ui all PASS (`QA: pass`).
   - Headless import (`cd game && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "import main"`): no error. The log reads `tuning loaded drifters=meteorite,satellite,chain_lightning,fireball,coin,floating_island,planet hazard_speed_scaling=True timer_scaling=True rehit_cooldown=180 rehit_dim=0.75 telegraph_min=45`, word for word as app.md asks. The built planet record is `VariantTuning(width=64.0, height=64.0, hitbox=(Circle(0,0,32),), extra=PlanetVariantExtra(pull_radius=150.0, pull_max=0.2))`, `speed_ratio=0.0`, `entry_warning_ticks=60`, `PlanetTypeExtra(120, 60, 50.0, 2)`.
   - wave_check: `--changed --no-record` exits 0 ("No wave changed"). `--all --force --no-record`: 7 passed, 0 failed. It no longer stops on `speed_ratio is missing`.
   - Bad planet file and rows (headless, `DRIFTWARD_DEBUG=1`, scratch copy of `game/tuning/`): all six give ERROR `unexpected error, showing the error screen` with the expected `ValueError`, and no `error screen failed`. See Browser run.
   - Build: `pygbag --archive game` built `game/build/web.zip`. Package contents are clean. In the browser: the required checks pass on the real build, and the planet checks pass on a scratch copy with the contract's three planet rows.
4. **Assumptions:** the planet-mode checks need the three planet rows and `"mode": "planet"`, `"loop_ticks": 1200` in `debug_spawns.json`. Neither the Director nor the content producer has added them, and that file isn't mine. I ran those checks on a scratch copy of the repo outside the workspace, served by the copy's own start script. The committed `game/tuning/` was never edited.
5. **Documentation differences:** None. My code follows app.md as written. Two wording points in the app.md check list are under Observations for the Architect; they don't change what I built.
6. **Next:** Director: run `scripts/close-out.sh DRA-96` to see open review findings and these Observations before close-out. Two content items are still open, both by whoever the Director names: commit `game/tuning/drifters/planet.json` (it is untracked), and add the three planet rows to `game/tuning/debug_spawns.json` (app.md, Integration checks for DRA-96). To open the build: run `game/scripts/start-driftward-ace.sh` and open http://localhost:6060 (`?debug=1` for debug mode). Build check: `pygbag --archive game` -> `game/build/web.zip`.
7. **Status:** done.

## Browser run
- **Build check:** `pygbag --archive game` (from the repo root) -> `game/build/web.zip`, 144240 bytes, git-ignored, not committed. Zip holds `index.html`, `favicon.png`, `game.apk`. `game.apk` holds 73 files, including `core/drifters/planet.py`, `ui/drifters/planet_view.py` and `tuning/drifters/planet.json`. It holds no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml` or `__pycache__`.
- **Served:** `game/scripts/start-driftward-ace.sh` in the background, pid kept in the scratchpad. It answered on http://localhost:6060 after 2 s. Stopped with `kill <pid>`; the script logged "Server stopped" and the port was free. Then the scratch copy (see Decisions) was served the same way with its own copy of the script, and stopped the same way. Port 6060 was free at the end, with no pygbag process left.
- **Method:** keys are `KeyboardEvent`s on `#canvas`; a hold is a keydown every 50 ms, then one keyup. Pixels come from `getImageData` on the 640 x 480 canvas, read every animation frame. Times are page times from the `drifter spawn id=1` line (tick 1), so tick n is about (n - 1) / 60 s.

### Required checks (real build, committed files)
- **Build served and loads:** pass.
- **Game started:** pass. `INFO app.loop: start mode=debug`, the `tuning loaded ... planet ...` line, `waves loaded waves=7 pool=3`, `debug spawns loaded mode=floating_island rows=8 loop_ticks=180 play=list`.
- **No console errors:** pass. On every page load the only errors were the two known pygbag ones (404 `browserfs.min.js`, "BrowserFS not found").
- **Arrow-key input (`?debug=1`):** pass. ArrowUp held 150 ms while the ship sat on island 1 and the scroll carried it down: `DEBUG app.frame: key down key=up x=320.00 y=307.90`, then `key up key=up x=320.00 y=306.10`. y fell by 1.80 px, so the ship rose off the island while the island moved down. x stayed at 320.00.

### Extra checks (scratch copy: committed files plus the three planet rows, `play=list`, `mode=planet`, `loop_ticks=1200`)
- **Spawn list loaded:** pass. `debug spawns loaded mode=planet rows=3 loop_ticks=1200 play=list`.
- **Warning and start:** pass.
  - Log: `drifter spawn id=1 type=planet variant=standard x=320.00 y=-151.00 speed=0.00 level=1`, then `drifter active id=1 type=planet x=320.00 y=-151.00` at 0.95 s.
  - During the warning, the 49 x 49 area around (320, 12) holds 81 px of glow (255, 220, 120), 127 px of disc (140, 70, 200), and 97 px of green label text.
  - Pixels, on planet 4, which repeats row 1 at level 1: the frame drawn from the active state has 0 planet-colored pixels. Two frames later, 24 lilac (180, 120, 255) pixels show on rows 0 to 2, x 250 to 390. Then the arc, the faint rings and the ball come in.
- **No pull in the wait, and a hit:** pass.
  - Log: `life lost lives=2` and `respawn from x=320.00 y=500.20 wait=True` at 1.00 s.
  - `drifter touch id=1 type=planet effect=hit` and `life lost lives=1` at 6.15 s, with no `respawn wait end`.
  - The waiting ship never moved through planet 1's pass: the next key line, 13.6 s in, reads `key down key=up x=320.00 y=240.00`.
  - Dimming: on the frame of the hit the ball turns (105, 53, 150) (2960 px) and the ring (135, 90, 191) (834 px). Full colors return 177 frames (2.99 s) later.
- **Leaving:** pass for the behavior, with a one-tick note under Observations.
  - Log: `drifter gone id=1 type=planet x=320.00 y=631.10` at 12.80 s.
  - With the overlay off (F3), rows 460 to 479 around x 250 to 390 held 72, 64, 54, 42, then 24 lilac pixels on the last five frames that showed the arc. That last frame was row 479 only, 24 px, which is pygame's arc at center y 629. The next frame (center 630) and the frames after held 0.
- **Two fields:** pass.
  - Log: `drifter spawn id=2 ... x=200.00 y=-151.00` at 6.62 s and `drifter active id=2 type=planet x=200.00 y=-151.00` at 7.62 s.
  - `drifter spawn id=3 type=planet variant=standard x=440.00 y=289.00 speed=0.00 level=1` at 13.28 s. Its warning shows 104 px of glow and 148 px of disc around (440, 289).
  - `drifter active id=3 type=planet x=440.00 y=289.00` at 14.28 s. Body pixels doubled (3148 -> 6000) on that frame, and the planet-colored area spanned x 50 to 589, both fields at once.
  - `drifter gone id=2 ... x=200.00 y=631.10` and `drifter gone id=3 ... x=440.00 y=631.10` on the same tick, at 19.47 s. No `drifter touch` for ids 2 or 3.
- **The look (overlay off):** pass, measured on planet 2 at center (200, 236).
  - The ball's center row holds 64 px of (140, 70, 200); 3176 body pixels in all.
  - The outer ring is (180, 120, 255), 844 px, at pixel distances 148 to 150 from the center.
  - 0 planet-colored pixels lie outside the outer ring.
  - The inner rings are blends of the ring color: (82, 55, 117), about 0.46 x (180, 120, 255). Each slides inward about 1 px a tick (34 px in 35 frames) and fades as it goes.
  - The game-over frame shows two inner rings at radius 78 and 137, 59 px apart (the 60-tick gap). Their brightness ratio is 2.3; 2.27 is expected.
- **The pull (`?debug=1`, fresh page):**
  - Planet 1 hit the waiting ship as above. When planet 2's ring-measured center reached (200, 241), I tapped ArrowUp: `key down key=up x=320.00 y=240.00`, `respawn wait end`, `key up key=up x=319.95 y=239.74`. One tick moved x by -0.05.
  - No side key for 0.4 s: `key down key=right x=309.16 y=282.24`. The ship drifted 10.84 px left toward the ball, faster than a steady -0.05 px a tick would give (about 1.2 px), so the tug grew.
  - ArrowRight held 1.5 s: `key up key=right x=466.71 y=496.59`. The ship moved right out past the ring; thrust beats the pull. With nothing holding it up it fell: `life lost lives=0`, `game over meters=93`.
- **Outlines (overlay on, planet 4 at (320, 150)):** pass. Green (0, 255, 0) pixels counted by distance from the center peak at radius 31 to 32 (166 px) and 45 to 46 (249 px): the hitbox (r 32) and the graze zone (r 46). There is no green circle on the field: only 28 scattered green pixels lie at radius 140 to 153, which is label text.
- **Normal mode (`/`):** pass. `start mode=normal`, `tuning loaded ... planet ...`, `waves loaded waves=7 pool=3`, `game over meters=59` with no key. Only the two known errors.
- **Bad planet file and bad rows (headless, not browser):** pass. ERROR `unexpected error, showing the error screen` each time, and no `error screen failed`:
  - `pull_max` 0.3: `tuning/drifters/planet.json: variants.standard.pull_max is too strong: pull_max + gravity must stay below thrust_up (0.3 + 0.16 >= 0.42)`, raised from the core error.
  - `pull_radius` 30: `tuning/drifters/planet.json: variants.standard.pull_radius must be more than size / 2`.
  - `speed_ratio` added: `tuning/drifters/planet.json: speed_ratio is not a known field`.
  - Row with `speed`: `tuning/debug_spawns.json: rows[33]: planet has no speed`.
  - Row with no `x`: `tuning/debug_spawns.json: rows[33]: planet placement needs x`.
  - Row with `invert: true`: `tuning/debug_spawns.json: rows[33]: planet has no invert`.

## Observations
- **The committed spawn list has no planet rows.** `game/tuning/debug_spawns.json` still reads `mode=floating_island`, 33 rows, with none for the planet, so the Director can't see planets in debug mode yet. app.md (Integration checks for DRA-96) names the three rows; they are content, by whoever the Director names. I did not edit the file.
- **`game/tuning/drifters/planet.json` is untracked.** It is in the build and loads, but it needs committing with the feature.
- **Planet checks ran on a scratch copy.** The copy holds the committed game files plus the three rows and planet mode. The required checks ran on the real build. Planet code, views and tuning are byte-identical between the two; only `debug_spawns.json` differs.
- **Leaving, one tick off the contract's wording.** app.md says the outer ring's top arc "still shows" on the frame before `drifter gone`. In the browser the last arc pixels (row 479, 24 px) show two ticks before `gone`. On the frame just before it (center y 630.0) pygame draws the r 150 arc at row 480, off the canvas, so nothing shows. This comes from `FIELD_DRAW_MARGIN` (1 px) keeping the planet one tick past its last drawn pixel. The player can't see it, and the scope behavior holds ("stays, still pulling, until the ring is fully below the floor"). For the Architect: reword the check.
- **In debug mode with the overlay on, the floor line on row 479 covers the arc's last row.** The leaving check only shows with F3 off.
- **The look check names planet 1 "crossing the middle", but planet 1 is dimmed then.** It hits the waiting ship at tick 373 (center y about 192) and stays dimmed for 180 ticks, through the middle. I measured the look on planet 2, which is never hit, at center y 236. For the Architect: name planet 2 in the check.
- **Not read:** the debug label text (`planet standard x ... warning/active`) and the overlay's `x/y/vx/vy` numbers. Green label text is present at the warning (97 px) and under the ball, but I did not match the text. The waiting ship's position and the pull's direction and size are shown by the key log lines instead.
- **One extra console error, from the page shell, not the game:** `Blocked confirm('Are you sure you want to navigate away from this page ?') during beforeunload`, once. It is pygbag's leave-page prompt, fired when I re-navigated a running page instead of closing it first.
- **Seen in `floating_island` mode, not DRA-96:** after a life lost under an island, the ship rode islands below the floor and logged 24 `respawn from ... wait=False` / `respawn clear of island` pairs within about 1 s before game over. That crowded list loops 8 islands every 180 ticks. It is DRA-86 behavior and I did not chase it. The Director may want it looked at.
- **Invulnerability:** `invulnerable end` comes about 30 ticks after each `life lost` in planet mode. That is outside DRA-96; noted only because it showed up in the logs.

## Decisions
- **The planet gets its own loader branch** (`_load_planet`), dispatched from `_load_drifter` like the chain lightning, fireball, coin and floating island. Its file has its own schema, with no `width`/`height`/`hitbox` and no `speed_ratio`. Source: app.md, Rules, Tuning loader (The planet's file; What the loader builds for the planet); planet-tuning.schema.json.
- **The record is built exactly as app.md gives it:**
  - per variant: `VariantTuning(width=float(size), height=float(size), hitbox=planet_hitbox(float(size)), extra=PlanetVariantExtra(pull_radius=float(...), pull_max=float(...)))`;
  - for the type: `DrifterTypeTuning(speed_ratio=0.0, entry_warning_ticks=..., extra=PlanetTypeExtra(..., field_ring_fade=float(...)))`.
  
  The footprint check is not run again, because the circle passes it by construction (app.md says so).
- **Escape check:** `core.ship.check_escapable_pull(pull_max)` runs for every variant, after the `pull_radius > size / 2` check. On failure the loader raises `ValueError(f"{file}: variants.<name>.{core message}") from err`, so the message reads `variants.standard.pull_max is too strong: ...` as app.md shows. Source: app.md, Rules, Tuning loader; ship.md, Rules, Escape.
- **Check order and messages** follow the coin and island loaders: fields, `entry_warning_ticks`, the four ring values, the variants, then `default_variant`. Messages use the existing helpers (`_even_size`, `_integer`, `_positive`, `_warning_ticks`), so they read as app.md lists them. `_PLANET_FADE_MAX = 100.0` is the schema's bound for a percent, not a game value.
- **The scratch copy for the planet-mode checks:** app.md says the Director switches the spawn list or lets the Integration Engineer switch it. Neither happened, and the rows are content outside my lane. A copy outside the repo let me run every planet check without touching `game/tuning/`. It was served by the same start script logic on the same port, never with `--bind`.
- **F3 off** for the leaving and look checks, because the overlay draws over row 479 (debug-overlay.md, floor line) and adds outlines on the ball's edge. **F3 on** for the outlines check.
- **Planet centers come from the outer ring's pixel box** (299 px across for pygame's r 150 ring). The ring is never covered by the outlines, the labels or the ship, unlike the ball.
