Verdict: pass
Created by: integration-engineer

1. **Task:** integrate and prove `drifter-sprites` (direct edit, no contract and no task files, as the Director chose) in the browser. Asked by the main session, with extra checks: build contents, startup time, frame rate on a busy scene against a reference, what the screen shows.
2. **Delivered:** `docs/reports/integration/drifter-sprites.md`. No code change: the hook in `game/app/frame.py` (`install_drifter_looks(tuning)` after `load_tuning()`) was already wired and needed no fix. `game/tuning/debug_spawns.json` was edited for the busy scene and restored (see Browser run).
3. **Checks:**
   - Headless import clean: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "import app.loop, app.frame, app.drifter_looks_tuning, ui.drifters.preload"` run in `game/`. (`import main` is not a usable check: it starts the game loop and never returns.)
   - Build: `python -m pygbag --template web/start.tmpl --archive game` from the repo root built `game/build/web.zip` (4,858,447 bytes, not committed, `game/build` is git-ignored). The archive holds the 15 new PNGs, `tuning/drifter_looks.json`, `ui/drifters/{looks,sprites,rays,preload}.py` and `app/drifter_looks_tuning.py`. No `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt` or `ruff.toml` in it.
   - Browser: loads, starts, plays, no console error beyond the known ones. All sprite types show and animate (details below).
   - Required arrow-key check in debug mode: ArrowUp held 400 ms, DEBUG key-down `y=240.00`, key-up `y=184.00` (y fell by 56, ship moved up). x stayed 320.00.
   - Frame rate: no drop that the sprites cause. The busy scene drops hard in this browser, but the placeholder build drops the same (numbers below).
   - Servers stopped, ports 6060 and 6061 free.
4. **Assumptions:** the headless browser here is software rendered on a shared machine, so absolute fps is low. Only the busy-versus-baseline comparison on the same machine means anything. The busy scene's `play` is `"list"` (the schema's value; `"spawns"` in the brief is not valid).
5. **Documentation differences:** None. Direct edit: no contract exists to differ from.
6. **Next:** Director: run `scripts/close-out.sh drifter-sprites` to see open review findings and these Observations before close-out. Read Observation 1 first (busy-scene frame rate is far below 60 here, with or without sprites). To open the build: `game/scripts/start-driftward-ace.sh`, then http://localhost:6060 (add `?debug=1` for debug mode). Build check: `python -m pygbag --template web/start.tmpl --archive game` gives `game/build/web.zip`.
7. **Status:** done.

## Browser run

Served with `game/scripts/start-driftward-ace.sh` (background, pid kept, polled with curl until 200), opened in the Playwright browser, clicked once, stopped with `kill` on the pid. Port 6060 free afterwards. Quick Playwright key presses are missed by the game (down and up in the same frame), so keys were sent as held `KeyboardEvent`s (100 ms and up) from `browser_evaluate`. Frame rate = `requestAnimationFrame` callbacks counted in the page; pygbag runs Python on the main thread, so a slow frame shows as fewer callbacks. Screens and times come from the game's own `core.game_flow` log lines.

**Required checks (all pass)**
- Build served and loads: HTTP 200, page title "pygame window" after the click.
- Start line in console: `INFO app.loop: start mode=normal` (and `mode=debug` with `?debug=1`).
- Console errors: only the known ones (404 for `browserfs.min.js`, `PyMain: BrowserFS not found`, and `MEDIA USER ACTION REQUIRED` before the click). No other ERROR and no traceback in any of the four sessions.
- Arrow key in debug mode: ArrowUp held 400 ms. `DEBUG app.frame: key down key=up x=320.00 y=240.00`, then `key up key=up x=320.00 y=184.00`. The log carries x/y with the key events, so there is no contract mismatch.

**Startup (item 2).** In the browser: `start mode=normal` at 3.3 s to 6.1 s page time (varies with pygbag fetching), then `drifter sprites ready in 208 ms` (first load, 12 strips plus 3 grounds, cold cache) and `115 ms` / `114 ms` on the next two loads. Natively it is about 30 ms, so the browser is about 4 to 7 times slower, one time only. From `start` to the last load line (waves loaded) it took about 1.6 s in the first session, of which the sprite step is 0.2 s. The menu shows right after. No visible hitch.

**Frame rate (item 3).** Reference first: 46 s of normal mode, few drifters (level 1 waves), same scripted pilot: mean 59.8 fps, worst 1 s window 57, median frame gap 16.7 ms, p99 16.8 ms, max 33.4 ms. Debug mode with the normal waves gave the same (36.8 s: 59.8 mean, worst 57).

Busy scene: `debug_spawns.json` temporarily set to `play: list`, `mode: all`, `loop_ticks: 420`, 47 rows (6 UFO both directions, 8 fireballs small and big both directions, 8 coins common and rare, 3 planets, 6 electric balls, 8 chain lightnings of every variant incl. invert, 8 islands: rectangle, box, l_shape, t_shape, triangle, with invert). A headless core simulation (hitbox on screen test) gave 25 to 39 active drifters on screen once ramped up (mean 34). The ship cannot survive longer than about 13 s there (best scripted pilot found by search), and each retry restarts the ramp, so the table uses seconds 6 and later of each run (23 or more drifters on screen), 26 to 29 one-second windows per case. The pilot and auto-retry are the same in every case. "Overlay" is the debug hitbox and label overlay (F3 toggles).

| Case | Mean fps (busy, run second 6+) | Worst 1 s window | p99 frame gap |
|---|---|---|---|
| Reference, normal mode, few drifters | 59.8 | 57 | 16.8 ms |
| Sprites, overlay off, run A | 30.0 | 7 | 150 ms |
| Sprites, overlay off, run B | 30.4 | 13 | 150 ms |
| Baseline (placeholder views, `git archive HEAD`), overlay off | 30.4 | 9 | 150 ms |
| Sprites, overlay on, run A | 23.0 | 5 | 200 ms (max) |
| Sprites, overlay on, run B | 28.5 | 11 | 150 ms |
| Baseline (placeholder views), overlay on | 25.2 | 10 | 133 ms |

Per run second (sprites, overlay off): 60 fps at second 0 to 1, 57 to 53 at 2 to 4, 46 at 5, 38, 31, 30, 33 at 6 to 9. The fps falls as drifters accumulate. A frozen busy scene on the game-over screen (no world ticks, same drawing) ran at 29 fps in the same build, so the cost is mostly drawing 25+ drifters in this browser, not the tick logic. The placeholder baseline shows the same curve. The sprite change is within run-to-run noise (30.0 and 30.4 against 30.4; 23.0 and 28.5 against 25.2). The game logged `tick cap hit` (DEBUG, event by event) in both builds when frames got slow: 28 times in the baseline session, 26 in the sprites session.

Baseline was served from a scratchpad copy on port 6061 with the same busy `debug_spawns.json`, then stopped.

**What the screen shows (screenshots outside the repo, in `/tmp/claude-1000/-workspace/75739b3e-6535-4442-883e-49f35bd4a13b/scratchpad/`)**
- `drifters_busy_0.png`, `drifters_busy_2.png`: busy scene, overlay off. `busy_seq_09.png`: chain arcs and grass island. `busy_seq_sheet.png`: 14 frames 330 ms apart (animation). `busy_off_0.png`: early scene. `busy1.png`: overlay on (labels cover the art). `menu.png`: menu.
- UFO: sprite with green dome, visible, flips with direction, frames change between shots.
- Fireball: orange head with trailing tail, small and big sizes, frames change.
- Coin: pink crystal sprites (common and rare), animate.
- Planet: purple marble sprite with the thin code-drawn field rings.
- Electric ball: calm look (small blue pinwheel with rays and an outline circle) while charging; on the pulse the pale jagged ring appears around a bright white core (seen in `drifters_busy_0.png` lower right and left, and in the sheet frames 2 to 6), then goes back to the calm look.
- Chain lightning: nodes with rays; when firing, bright nodes with a blue arc line between them, straight, horizontal, vertical and diagonal (`busy_seq_09.png`).
- Islands: ground texture cut to the shape: rectangle, box (grass look), L, T, triangle (diagonal edge), inverted ones too. Three ground looks seen (stone, grass).
- Not shown from stills: planet ring motion (the 2 px radius step, see Observation 3), and the direction of every mirrored fireball.

## Observations

1. **Busy-scene frame rate (needs a decision).** In this browser the busy scene runs at about 30 fps mean with dips to 5 to 13 fps in the worst second, against 60 for a few drifters. The goal "no drop below normal with many drifters" is not met, but it is not caused by the sprites: the placeholder build at HEAD gives the same numbers (30.4 mean, worst 9) in the same scene on the same machine. The frozen game-over screen with the same drifters also runs at about 29 fps, so drawing many drifters (and the full window, 856x518) dominates. The test machine is a software-rendered headless Chromium on a shared host, so the real-world figure on a Director's laptop will be higher. Real-GPU or real-laptop numbers were not measured. If this matters for later waves, it needs its own task; it is outside this feature.
2. **Startup cost.** The sprite load adds 115 to 208 ms once at start in the browser (30 ms native). Not noticeable next to pygbag's own load time.
3. **Planet ring step.** `field_ring_radius_step` is 2 (memory 2.3 MB). Whether the rings jump visibly in motion cannot be judged from stills. The Director should look at a planet in the browser. If it shows, set the key to 1 in `game/tuning/drifter_looks.json` (about 4.6 MB), no code change.
4. **Stand-in art.** The report says the strips are stand-ins. Shown as such: the fireball is a plain orange ball and the electric ball and ring are drawn stand-ins. Not a bug.
5. **Mirrored fireball direction not confirmed on screen.** The ui-developer reports checking both ways with hitbox circles. I saw fireballs moving both ways with tails behind them but did not zoom on each case.
6. **Import check note.** `import main` runs the game loop and never returns (that is its job), so the headless check imports the `app` and `ui` modules instead.
7. **Not mine, seen in passing.** `game/tests/CONTEXT.md` and `game/app/drifter_looks_tuning.py` show as modified or new in git: the QA agent and the ui-developer own them. I touched neither. `git diff --quiet game/tuning/debug_spawns.json` is clean (restored with `git checkout --`, and byte-identical to the copy I took first).
8. **Debug logging volume.** In debug mode with 47 rows the DEBUG lines (`drifter spawn`, `active`, `gone`) run at about 25 per second. They are by event and not per tick, and the baseline logs the same lines. Not a finding.

## Decisions
- No contract or task file exists for this feature (the Director chose direct edit). Wired nothing new: the hook in `game/app/frame.py` was already in place and passed. Source: the brief.
- Frame rate counted with `requestAnimationFrame` in the page plus the game's own screen log lines, because the game logs no frame timing and CONTEXT.md forbids adding per-tick logging. Source: `game/CONTEXT.md`, Logging.
- Busy-scene numbers use run seconds 6 and later and only "playing" seconds, because the ship dies after about 13 s and the scene needs about 6 s to fill. Retries are automatic in the test script. Two sprite runs per overlay setting plus one baseline, because single runs vary by 5 to 7 fps.
- The baseline is a build of `git archive HEAD` served on port 6061, so the placeholder views and the sprite views run through the same pygbag, the same browser and the same scene. Source: the brief ("the target is no drop below the game's normal rate").
- `debug_spawns.json` used `play: "list"` (valid schema value, `docs/contracts/schemas/debug-spawn-list.schema.json`), not `"spawns"`. Edit authorized by the main session, restored after.
- Keys sent as held key events (100 ms or more), because a Playwright press lasts less than one game frame and was missed.

## Round 2 2026-11-05

1. **Task:** repeat the integration proof for `drifter-sprites` after the meteorite look was wired in (4 rock skins with turn frames; core meteorite `drawn_parts` now uses `drawn_width` from `game/tuning/drifters/meteorite.json`). Asked by the coordinator. Direct edit, no contract and no task files. Correction taken: the fireball and the electric ball and ring are the Director's picked art, not stand-ins. The sentence in Round 1 Observation 4 and in the Round 1 chat note that calls them stand-ins is wrong and superseded by this one.
2. **Delivered:** this section only. No code change. `game/tuning/debug_spawns.json` was edited for the busy scene and restored (see Browser run).
3. **Checks:**
   - Headless import: not repeated (no code change by me); the build below imports and the browser ran it.
   - Build: `python -m pygbag --template web/start.tmpl --archive game` from the repo root gave `game/build/web.zip` (4,922,015 bytes, not committed). It holds `meteorite_rock_a.png` to `meteorite_rock_d.png`, the updated `tuning/drifters/meteorite.json` (with `drawn_width` 26, 36, 52), `tuning/drifter_looks.json` (with the `meteorite` block), `ui/drifters/meteorite_view.py`, `core/drifters/meteorite.py`, `app/drifters/meteorite_tuning.py`. No `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml`.
   - Browser normal mode: starts, plays 45 s, console shows only the known errors (browserfs 404, BrowserFS not found, MEDIA USER ACTION). `drifter sprites ready in 274 ms` on this load (earlier loads of the same build: 194 ms and 114 to 115 ms, so it floats with the machine; native about 38 ms).
   - Meteorites at the floor: they sink into the floor line and are cut by it; none vanishes while a real part is visible. Evidence below.
   - Frame rate: the sprites build is at parity with the placeholder build in the same busy scene, and the normal-mode reference is 59.8 fps. Numbers below.
   - My servers (ports 6070 and 6061) stopped and free. See Observation 1 about port 6060.
4. **Assumptions:** the busy scene now has 56 rows (the earlier 47 plus 9 meteorites: small, medium and big three times each at different x), `loop_ticks` 500 so the density stays near the old scene. A headless core count gives at most 36 drifters on screen, mean 28.7 over the first 40 s (the earlier scene peaked at 39).
5. **Documentation differences:** None. One note for the Architect, taken from the ui-developer's report: `docs/contracts/schemas/drifter-tuning.schema.json` still says the meteorite has no fields of its own, while `meteorite.json` now has `drawn_width`.
6. **Next:** Director: run `scripts/close-out.sh drifter-sprites` to see open review findings and these Observations. Build check: `python -m pygbag --template web/start.tmpl --archive game` gives `game/build/web.zip`. Read Observation 1 (a server on port 6060 I did not start).
7. **Status:** done.

### Browser run (round 2)

Served with `PORT=6070 game/scripts/start-driftward-ace.sh` (see Observation 1 for why not 6060), opened with the Playwright browser, keys sent as held key events as in Round 1, stopped with `kill` on the pid. The baseline (placeholder views, `git archive HEAD`, same busy list copied in) ran on port 6061 and was stopped.

**Required checks (pass)**
- Build served and loads: HTTP 200, title "pygame window" after the click.
- Start line: `INFO app.loop: start mode=normal` and `mode=debug`.
- Console errors: only the known ones, in every session. No traceback. Debug sessions also log `tick cap hit` at DEBUG when frames get slow (event by event, same as in Round 1).
- Arrow-key check in debug mode was not repeated; nothing in `game/app/` changed. Round 1 result stands (key down y=240.00, key up y=184.00).

**Meteorites reaching the floor (extra check, pass).** Method: a ring buffer of the last 14 frames of the bottom 60 px strip of the canvas, dumped when the game logs `drifter gone ... type=meteorite`. Files (outside the repo, in `/tmp/claude-1000/-workspace/75739b3e-6535-4442-883e-49f35bd4a13b/scratchpad/`):
- `r2_floor_busy.png`: 12 rocks in the busy scene (small, medium and big), one row per rock, 14 frames in time order, ending at the removal. Each rock sinks into the floor line and is cut by it, so half a rock below the floor is shown in the middle frames of every row. The last captured frame of a row is the one before the game removed the rock (the log comes from the tick, the draw comes after), and in it only a sliver is left (a few px, one tick of movement at most). No row shows a rock that is still mostly visible and then disappears.
- `r2_floor_waves.png`: the same for 12 rocks of the normal waves, captured by an earlier session of the same build (a first set of dumps taken against the server that was already on 6060; same code). Same picture.
- Removal values logged (center y, floor 480): small 493.37, medium 499.24, big 508.04. These match half the drawn width (13, 18, 26) past the floor, so the removal follows `drawn_width` as intended.
- Skins and turn: `r2_rock_strips.png` shows the four shipped strips (8 frames each, 36x36). In the dumps the rocks visibly turn between frames and several different looks appear: the triangular rock with a dark dot (rock_c), pink rocks with big craters, and blocky rocks. I can see at least three distinct looks clearly; I cannot match every rock to a skin letter from a still, so I do not claim all four were seen in the dumps. Full-field shots with rocks mid-field: `r2_busy_3.png` (busy scene, overlay off), `r2_normal_0.png` (normal mode), `r2_busy_sheet.png` (8 frames).
- Rocks draw over islands and under or over planets and electric rings depending on the layer order; nothing looked wrong.

**Frame rate.** Same method as Round 1 (rAF callbacks, scripted pilot with auto-retry, busy numbers from run second 6 on, overlay off).

| Case | Mean fps | Worst 1 s | p99 frame gap |
|---|---|---|---|
| Normal mode, few drifters (46 s) | 59.8 | 54 | 16.8 ms |
| Busy scene, sprites build incl. meteorites, run A | 27.0 | 10 | 117 ms |
| Busy scene, sprites build incl. meteorites, run B | 23.8 | 13 | 117 ms |
| Busy scene, placeholder baseline, run A (same list) | 19.6 | 9 | 183 ms |
| Busy scene, placeholder baseline, run B (same list) | 22.0 | 13 | 133 ms |
| Round 1, sprites (no meteorites, older list) | 30.0 and 30.4 | 7 and 13 | 150 ms |
| Round 1, placeholder baseline (older list) | 30.4 | 9 | 150 ms |

Reading: this machine was slower than in Round 1 (the placeholder baseline fell from 30.4 to 19.6 and 22.0 on a similar list), so only the same-session comparison counts. In it the sprites build ran at 27.0 and 23.8 against 19.6 and 22.0 for the placeholders, so the meteorite sprites add no measurable cost. Per run second the sprites build goes 60, 60, 57, 53, 40, 32, 32, 25, 26, 24, 21 (it falls as drifters accumulate, as in Round 1). Against the old Round 1 sprite figures (30.0 and 30.4) the new numbers are lower, but that is the slower machine plus 9 more drifters in the scene; the baseline moved by the same amount. As in Round 1 the busy scene is far below the 60 fps reference with or without sprites.

### Observations (round 2)
1. **A server on port 6060 that I did not start.** When I began this round, `game/scripts/start-driftward-ace.sh --debug` (pid 93688, `python -m pygbag ... --port 6060`, pid 93706) was already running; it is not mine and I left it running. Its page answered 200, so my first start (which printed "port already in use") went unnoticed and my first browser pages hit it: it served an older build with the original `debug_spawns.json` (that is where `r2_floor_waves.png` and the first dumps come from). I then noticed, started my own server on port 6070, and redid every measured step on it. Also, to force a rebuild I deleted `game/build/web/game.apk` and `game.tar.gz`, the files that server serves; my own build recreated them with the busy list inside, and I rebuilt them again after restoring `debug_spawns.json` (`pygbag --archive`, apk checked: `play: waves`, the committed file). If you use that server, restart it to be safe.
2. **pygbag does not rebuild when the apk is newer than your edit.** After `pygbag --archive`, a later start of the script served the old apk and ignored a changed `debug_spawns.json`. Delete `game/build/web/game.apk` before starting the script after editing tuning files. This matters for whoever tests tuning edits in the browser.
3. **Busy-scene frame rate** is still the open point from Round 1 and unchanged in nature: about 24 to 27 fps on this machine in the busy scene with sprites, 20 to 22 with the placeholders, 60 with few drifters. Not caused by the sprites. Real-GPU or laptop numbers were not measured.
4. **Sprite load time** floats from 114 ms to 274 ms in the browser across loads (16 strips now, one time at start).
5. **Meteorite skin coverage** is only partly shown (see above): at least three looks seen, all four strips ship and load (`meteorite_rock_a..d.png` listed in the load log).
6. **Floor removal sliver.** The last visible frame before removal can still show a sliver of a few px (one tick of movement). That follows from the core rule (removed when the drawn box is fully below the floor), so a player cannot see the rock pop out while a real piece is left.
7. **Drawing order of rocks** over islands is a ui matter; I saw no overlap problem.
8. Git state: `game/tuning/debug_spawns.json` clean after `git checkout --` and byte-identical to the copy taken before the edit. `game/build` is git-ignored.

### Decisions (round 2)
- Redid every measurement on a server I started (port 6070) once I found the foreign server on 6060; mixed numbers would not compare like with like. Source: `game/CONTEXT.md`, INTEGRATION ("Don't kill a process you did not start. Report it").
- Floor evidence from a ring buffer dumped on the game's own `drifter gone` DEBUG line, not from timed screenshots: in the busy scene tick time drifts from wall time (tick cap), so timing a screenshot to a rock is not reliable. No per-tick logging was added. Source: `game/CONTEXT.md`, Logging.
- Baseline rebuilt from `git archive HEAD` with the same busy list, because the scene changed since Round 1 and the machine speed changed. Source: the coordinator's request to compare like with like.

## Round 3 2026-11-05

1. **Task:** repeat the integration proof for `drifter-sprites` after the new meteorite art (4 strips, 32 frames of 36x36 each, tilted-axis turn) and `ticks_per_frame` 3 in `game/tuning/drifter_looks.json`. Asked by the coordinator. Direct edit, no contract, no task files. No code changed.
2. **Delivered:** this section and five screenshots in `docs/reports/integration/` (names under Browser run). No change to `game/main.py`, `game/app/`, `game/scripts/` or `pygbag.ini`. I did not touch `game/build/`: see Observation 1.
3. **Checks:**
   - Headless import: `python -I -c "import app.loop, app.frame, app.drifter_looks_tuning, ui.drifters.preload"` run in `game/` with dummy SDL drivers: clean.
   - Build: `python -m pygbag --template web/start.tmpl --archive game` run in a scratch copy of the repo (identical runtime files, see Observation 1) gave `web.zip`, 5,056,693 bytes (round 2: 4,922,015; the 4 new strips are 1152x36 each). The package holds `meteorite_rock_a..d.png` and `tuning/drifter_looks.json`; no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml`. Not committed.
   - Browser, 7 sessions on 3 builds: loads, starts, plays. Log shows `meteorite_rock_a..d.png loaded: 32 frames of 36x36 px` for all four, `drifter looks loaded strips=16`. Console: only the known errors (browserfs 404, `PyMain: BrowserFS not found`, `MEDIA USER ACTION` warning). No traceback and no game-level ERROR in any session.
   - Required arrow-key check in debug mode (`?debug=1`): ArrowUp held 400 ms, `key down key=up x=320.00 y=240.00`, `key up key=up x=320.00 y=223.90`. y fell 16.1 (ship moved up), x unchanged.
   - Meteorites: enter fully off screen, turn through all 32 frames with no jump at the seam, start at their own frame, leave only when nothing drawn is visible. Numbers below.
   - Frame rate: no extra cost from 32 frames that can be told apart from noise. The host was loaded by other jobs (see Observation 2), so absolute fps is below round 2. Numbers below.
   - Sprite load time in the browser: 272 to 679 ms (32 frames) against 199 to 251 ms (8-frame stand-in). One time, at start. See below.
   - My servers (6071, 6072, 6073, 6074) stopped, ports free. 6060 was free the whole time and I did not use it.
4. **Assumptions:** the 8-frame comparison build is the same repo with every 4th frame of each strip (288x36) and `ticks_per_frame` 12 (same turn time, 96 ticks). It stands for the round 2 art, which is no longer in the tree. The busy scene is the round 2 shape (56 rows incl. 9 meteorites, `loop_ticks` 500, play `list`), rebuilt from my own generator, so absolute numbers are not the round 2 numbers.
5. **Documentation differences:** None. (Round 2 note stands: `docs/contracts/schemas/drifter-tuning.schema.json` still says the meteorite has no fields of its own.)
6. **Next:** Director: run `scripts/close-out.sh drifter-sprites` to see open review findings and these Observations. Build check: `python -m pygbag --template web/start.tmpl --archive game` gives `game/build/web.zip`. To look at the rocks: `game/scripts/start-driftward-ace.sh`, open http://localhost:6060/?debug=1 (your own server may need no restart: I did not rebuild `game/build/web`). The screenshots are listed under Browser run.
7. **Status:** done.

### Browser run (round 3)

How: three scratch copies of the repo under the scratchpad (`r3/work` busy scene, 32 frames; `r3/rock` rocks-only scene; `r3/proxy8` busy scene, 8-frame stand-in), each built and served by its own `game/scripts/start-driftward-ace.sh` on ports 6071, 6072 and 6073 (`PORT=...`), opened with the Playwright browser, stopped with `kill` on the pids. The test script (`h.js`, in the scratchpad) hooks `console.log` to read the game's own log lines, counts `requestAnimationFrame` callbacks, sends held key events and, when the game is over or paused, presses Enter (two Enters from game over start a new run). Keys: ArrowUp pulses (135 ms on, 165 ms off) plus a left or right drift on the busy scene. Overlay off (F3) for all measured runs. The Playwright toolset here has no screenshot tool, so screenshots are `canvas.drawImage` of the game canvas, saved as PNG.

Required checks (all pass): build served and loads (HTTP 200, title "pygame window" after the click); start line `INFO app.loop: start mode=debug`; no console error beyond the known ones; arrow key in debug mode (numbers above).

**Meteorite checks (extra, all pass).** Rocks-only scene: `play list`, `mode meteorite`, `loop_ticks` 300, rows small x=130, medium x=230, big x=440 (the ship stays at x 320).
- *Appear fully off screen at the top.* Spawn log: `type=meteorite variant=medium x=351.00 y=-18.00` (small `y=-13.00`, big `-26.00`): the rock's center starts half its drawn width above the edge. Frames captured from the `drifter active` line on: `drifter-sprites-r3-top-entry.png` (6 rocks, 14 consecutive frames each, yellow line = top of the field). The first frames of every row are empty, the rock then comes in under the edge, and nothing is drawn on the frame art above the line.
- *Turn smoothly through all 32 frames, no jump at the loop seam.* Capture of 240 consecutive frames (16.7 ms apart, max gap 16.8 ms) of three columns, with each rock found in the picture and matched pixel for pixel to the game's own scaled frames (`Sprites.image`, 4 skins x 32 frames). 428 rock images, 420 matched with a mean error under 8 (median 0.19 on the 36 px rock; the 26 px rock sits near 4 because of the scaling). Over the 415 pairs of consecutive displayed images the frame index moved by 0 or +1 and by nothing else (278 times 0, 137 times +1). Each frame stays exactly 3 display frames (131 holds of 3, one of 4 from one slow frame), which is `ticks_per_frame` 3. The wrap 31 to 0 happened 5 times, always as +1. `drifter-sprites-r3-loop-seam.png` shows frames 28 to 7 in order, wrap included. One full turn is 96 ticks, 1.6 s.
- *Each rock starts at its own frame.* The three rocks I could see entering at the same height (center y 34 to 42) showed frames 17, 9 and 30. In the core the start frame is `loop_frame(uid + salt)`, so it differs per rock and per run. Not shown for every rock; see Observation 4.
- *Leave only once nothing drawn is visible at the floor.* 14 rocks of all three sizes, last 14 frames before each `drifter gone` line: `drifter-sprites-r3-floor-exit.png` (9 rows, yellow line = floor line of the field). Each rock sinks into the floor line and is cut by it, then shrinks to a sliver, then nothing. Big rocks show 2 or 3 empty frames before removal: the art has blank rows at its top, so the removal test (drawn box fully below the floor) runs a few px after the last visible pixel. No rock disappears while a real part of it is visible. Removal y logged: small 495.30, medium 500.17, big 506.98 (floor 480; drawn half widths 13, 18, 26 plus at most one tick of 2.47). Same rule as round 2.
- Skins: all four strips load. Three of the four skins were matched pixel for pixel in the captured rocks (rock_a, rock_b, rock_d). rock_c was not matched in this capture (it was seen by eye in round 2). I do not claim every rock was matched to a skin.
- Screens in play: `drifter-sprites-r3-rocks-in-play-window.png` (whole window: ship, a medium and a small rock, a warning icon at the top) and `drifter-sprites-r3-rocks-in-play-field.png` (two field shots 2.3 s apart with small, medium and big rocks).

**Frame rate (rAF callbacks per run second, scripted pilot with auto-retry, run second 4 and later, overlay off).** The first seconds are left out as the scene fills.

| Case | Windows | Mean fps | Worst 1 s | p99 gap | Max gap |
|---|---|---|---|---|---|
| Rocks-only scene, 32 frames, 40 s, run second 0 on | 39 | 60.0 | 59 | 17 ms | 33 ms |
| Normal mode, few drifters, 50 s (round 2: 59.8) | 37 | 44.2 | 31 | 50 ms | 83 ms |
| Busy scene, 32 frames, run A | 31 | 31.0 | 9 | 133 ms | 167 ms |
| Busy scene, 8-frame stand-in, run A | 38 | 30.7 | 8 | 117 ms | 167 ms |
| Busy scene, 8-frame stand-in, run B | 49 | 17.4 | 4 | 233 ms | 383 ms |
| Busy scene, 32 frames, run B | 33 | 23.4 | 6 | 167 ms | 400 ms |
| Busy scene, 32 frames, very first try (this page was loaded first; windows from run second 5; host busiest) | 20 | 8.8 | 4 | 300 ms | 400 ms |

Order of runs: rocks-only, 32 run first try, normal, 32 A, 8 A, 8 B, 32 B. Reading: the host was busy with other work (load average 8.5 on 8 cores; a `wave_editor` python process at about 1.4 cores and a `pytest` run at about 1.1 cores while I measured), and the normal-mode reference fell from 59.8 (round 2) to 44.2. Absolute numbers are therefore below round 2's (27.0 and 23.8 busy, 59.8 normal) and move by more than 10 fps between runs of the same build. Same session, A and B pairs: 32 frames is 31.0 and 23.4, 8 frames is 30.7 and 17.4. There is no sign that 32 frames costs frames. The rocks-only scene with all four 32-frame skins and all three sizes runs at a flat 60.0 fps with no gap over 33 ms from the first second on, which is where a hitch from first-time scaled copies would show.

Hitches: in the rocks-only run there is none (no gap over 100 ms in 40 s, nothing at run second 0 to 3 when every size and skin first appears). The busy runs show 100 to 400 ms gaps from run second 4 or 5 on, same as the 8-frame build and as the placeholder build in rounds 1 and 2; they follow the drawing load, not a first appearance of a size or a dim level. Reason it is safe: all 4 skins x 3 sizes x 32 frames are built before the game starts, at full brightness and at the re-hit dim level (768 surfaces; native check: 1,112 cached surfaces in total). Other dim levels build one 36 px frame on demand.

Sprite load, logged `drifter sprites ready in N ms`: 32-frame build 679, 632, 311, 309, 272 ms; 8-frame stand-in 199 and 251 ms. The two slowest 32-frame loads were the first cold loads while the host was busiest. Natively, 83 ms (idle host: 30 to 40 ms). This is a one-time cost at start, on top of pygbag's own 7 to 12 s page load. Memory for the meteorite caches: about 4.8 MB (32 frames) against about 1.2 MB (8 frames), estimated from the sizes.

### Observations (round 3)
1. **I did not rebuild `game/build/web`.** The Director's debug server may run on port 6060 and serves that folder. I built and served from copies in the scratchpad instead, so nothing in `game/build/` changed and no restart is needed because of me. Port 6060 was free during this round. The copies' runtime files equal the repo's (`diff -rq`: only `tuning/debug_spawns.json` (my busy and rock lists) and two test files changed in the repo after I copied). Your own `game/tuning/debug_spawns.json` change (`play list`, `mode planet`, shown modified in git) is untouched. The release package listing was taken from the copy's `web.zip`, not from the repo's `game/build/web.zip`.
2. **Busy host.** Another process (`tools/wave_editor/main.py`) was using about 1.4 cores and a `pytest` run another core during the measurements. Frame rate numbers are only good for same-session comparison. The conclusion "32 frames do not cost frames" rests on A and B pairs and the flat 60 fps rocks-only run, not on the absolute numbers. Real-GPU or laptop numbers were not measured.
3. **Busy-scene frame rate** is still far below 60 with or without these sprites. The open point from rounds 1 and 2 is unchanged.
4. **Start frames.** Three entries were clean enough to read (frames 17, 9, 30). Rocks overlapping in one column or rocks that left the band blurred the others. The core rule gives each rock its own start; I did not read every rock's start frame in the browser.
5. **Skin coverage.** Skins matched from the rock images: rock_a (index 0), rock_b (1) and rock_d (3). rock_c was not matched in this round's capture. All four load and are chosen by the core's seed, so I expect it in longer play, but I did not show it.
6. **Browser tools.** This toolset has no screenshot or dialog tool; the game page sets a `beforeunload` prompt that blocks `browser_navigate` until the tab is closed with `browser_close`. I closed the tab before each new page.
7. **Early scratch mistake.** My first scratch server had no `web-cache` folder (I deleted it), so its page 404'd `pythons.js`; I restored the folder and reloaded. Nothing from that load is used. The final sessions have only the known errors.
8. **Git state.** `game/tuning/debug_spawns.json` in the repo is as I found it. `.playwright-mcp/` in the repo root holds the browser tool's own logs and snapshots; it is git-ignored.

### Decisions (round 3)
- Built and served from scratch copies on separate ports (6071 to 6073) so the Director's server and `game/build/web` stay untouched. Source: the coordinator's instruction for this round; `game/CONTEXT.md`, INTEGRATION ("Don't kill a process you did not start").
- 8-frame stand-in for the same-session comparison, because the earlier art is no longer in the tree and the machine speed changed, as in round 2. Source: the coordinator's request to compare with round 2.
- Rock frame identity by pixel matching to the game's own scaled frames, instead of timing screenshots: under a loaded host the game's ticks do not follow wall time, and a match against `Sprites.image` output proves which frame was on screen. No per-tick logging added. Source: `game/CONTEXT.md`, Logging.
- Floor and top evidence from a 14-frame ring buffer read on the game's own `drifter gone` and `drifter active` log lines. Same method as round 2.
