Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-76 (wave system), Integration mode, second run. The wave files now exist, so I ran the full browser checks and rewrote this report.
2. **Delivered:** `game/app/waves.py` (new), `game/app/frame.py`, `game/app/debug_spawns.py` (all from the first run, unchanged this run), `docs/reports/integration/DRA-76.md`. `game/main.py`, `game/app/loop.py`, `pygbag.ini` and `game/tuning/debug_spawns.json` were not touched this run. The Director's `"play": "waves"` stays set.
3. **Checks:**
   - Headless import (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, under `timeout 5`, since `import main` starts the game): clean. Log shows `start mode=normal`, `tuning loaded`, `waves loaded waves=3 pool=1`, then quit on the timeout.
   - `game/tests/check.sh lint` pass, `format` pass, `typecheck` pass.
   - Build: `pygbag --archive game` from the repo root built `game/build/web.zip` (119097 bytes, gitignored, not committed). `game.apk` holds `core/waves.py`, `core/wave_files.py`, `app/waves.py`, `waves/playlist.json`, `waves/wave_0.json`, `waves/l1_a.json`, `waves/l1_b.json`, and every `tuning/` file. It holds no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt` or `ruff.toml`. `pygbag.ini` needs no change.
   - Browser: served by `game/scripts/start-driftward-ace.sh`, opened in Playwright, then stopped. All required checks pass. Every extra check that a browser can show passes. Details in Browser run.
   - Logging is by event only. The app adds the one `waves loaded` line. Nothing is logged per tick.
4. **Assumptions:** `app.waves.WAVES_DIR` is `Path(__file__).resolve().parent.parent / core.wave_files.WAVES_FOLDER`. In `frame._run_ticks` the due placements are the spawn list's when `plays_list`, else `run.wave_spawns_due`. The game starts by itself on page load in this pygbag build: it logged `start mode=...` before any click. I still clicked once in the first page as CONTEXT.md says.
5. **Documentation differences:** None.
6. **Next:** Director: run `scripts/close-out.sh DRA-76` to see open review findings and the Observations below before close-out. To look at it yourself, run `game/scripts/start-driftward-ace.sh`, open `http://localhost:6060/?debug=1` (waves play, overlay shows wave and level) or `http://localhost:6060/` (normal mode). Release package check: `pygbag --archive game` from the repo root, output `game/build/web.zip`.
7. **Status:** done.

## Browser run
Build and serve:
- Build check: `pygbag --archive game` from `/workspace` -> `game/build/web.zip`, not committed.
- Started with `game/scripts/start-driftward-ace.sh` in the background (log and pid in the scratchpad). `http://localhost:6060` answered after 2 s. No `--bind`. Stopped with `kill` on the script's pid. The script logged `Server stopped`, and the port no longer answers.
- Key events were sent with `browser_evaluate` (KeyboardEvent on the canvas). Canvas reads used `drawImage` into a scratch canvas and `getImageData`. Game log lines were collected by wrapping `console.log` in the page. Times below are seconds from the `wave start id=wave_0` line.

Required checks (`?debug=1`, committed file with `play: waves`):
- Build served and loads: pass. Page title `pygame window`, the game ran.
- Start line: pass. `INFO app.loop: start mode=debug`, then `tuning loaded ...`, `waves loaded waves=3 pool=1`, `debug spawns loaded mode=coin rows=4 loop_ticks=180 play=waves`, `wave start id=wave_0 level=1 random=False`, then `scroll start tick=31`. The order matches the contract.
- No console errors: pass. Two errors on every load, both the known pygbag ones: the 404 for `browserfs.min.js` and `PyMain: BrowserFS not found`. No other error or warning from the game, and no `ERROR` or `WARNING` game log line in a full 105 s run.
- Arrow input: pass. ArrowUp pressed on the first frame, held 0.5 s, released: `key down key=up x=320.00 y=240.00`, then `core.ship: top line stop x=320.00 y=184.00`, then `key up key=up x=320.00 y=184.00`. y went from 240 to 184, up the screen as it should. The key lines carry x/y, so no contract mismatch.

Extra checks:
- **Wave flow (waves debug, ArrowUp and ArrowRight held, ship pinned at x=624, y=184, clear of every hazard column): pass.** First frame overlay `wave wave_0`, `level 1`. Log: `wave end id=wave_0` at 20.51 s then `wave start id=l1_a level=1 random=False`. `wave end id=l1_a` at 40.51 s then `wave start id=l1_b level=1 random=True`. `wave end id=l1_b` at 60.51 s, `level up level=2`, `wave start id=l1_a level=2 random=False`. Contract: about 20.5, 40.5 and 60.5 s. No `wave rest` ever. Spawn lines after the level-up read `speed=2.62 level=2` (level 1: `speed=2.47 level=1`). No life was lost in the 65 s run. Screenshots (scratchpad, not in the repo): `wave l1_a` / `level 1` at about 25 s, `wave l1_a` / `level 2` at about 66 s.
- **Stars speed up (same run): pass.** Star pixels (90, 100, 140) matched across two reads: at 25 s, 67 px in 1.008 s (66.5 px/s); at 55.6 s, 66 px in 1.005 s (65.7 px/s); at 65.1 s, 72 px in 1.006 s (71.6 px/s). Contract: about 66, then about 72.6 px/s. The read is whole pixels over a browser-timed second, so about 1 px of slack.
- **F3 (waves debug): pass.** Before: 354 green pixels in the top-left 120 x 100 area. After F3: 0, and the white HUD text bounds there stayed put (x 7..64 vs 7..63, y 81..88; the only change is the SCORE digits). After F3 again: 423. Log: `overlay visible=False`, then `overlay visible=True`.
- **Game over freezes the waves (waves debug): pass.** Keys released, ship fell, two taps after the first two losses, then `life lost lives=0` and `INFO game over meters=624`. Two full canvas reads 2 s apart: 0 bytes differ. No log line of any kind in those 2.5 s, so no `wave ` line. (The Game Over box is in the read, the overlay lines too.)
- **Retry restarts the waves (waves debug): pass.** One arrow tap: `INFO new run`, then `wave start id=wave_0 level=1 random=False`, overlay `wave wave_0` and `level 1` (screenshot), stars 66 px in 1.007 s (65.5 px/s), the Level 1 speed again.
- **Normal mode plays the waves (`/`): pass.** Log: `start mode=normal`, `tuning loaded`, `waves loaded waves=3 pool=1`, and nothing else (INFO only). 246 canvas reads over 22 s with the ship held at the top right. Meteorite grey (140, 140, 140) first seen at 1.9 s and pink coin (255, 80, 150) at 2.8 s after the log line. No (0, 255, 0) pixel in any read. Console: only the two known errors.
- **Waves loaded (`/` and `?debug=1`): pass.** `waves loaded waves=3 pool=1` after `tuning loaded` and before the first `scroll start`. This proves the `waves/` folder is listed and read inside pygbag's packed file system.
- **Bad wave files, normal mode and debug mode (desktop, headless, scratch copies in the scratchpad pointed at through `app.waves.WAVES_DIR`, no code change): pass, all 12 runs.** Each shows the start line, `tuning loaded`, then ERROR `unexpected error, showing the error screen`, and no `error screen failed` line. Messages (the same in both modes):
  1. `waves/l1_a.json: placements[0]: a hazard (satellite) at 100 px is inside the first 120 px`
  2. `waves/playlist.json: wave_zero names 'wave_00', which is not a wave`
  3. `waves/playlist.json: levels[0] (level 1) has random_count 1 but no pool wave with min_level <= 1`
  4. `waves/wave_0.json: placements[0]: unknown field 'speed'`
  5. `waves/wave_0.json: placements[0]: unknown variant 'huge' for drifter type 'meteorite'`
  6. `waves/l1_a.json: not valid JSON: Expecting value: line 5 column 1 (char 60)`
- **Bad `play` (desktop, headless, debug): pass.** `"play": "both"` in a scratch copy: ERROR `unexpected error...` with `ValueError: tuning/debug_spawns.json: play must be "list" or "waves"`. The waves had loaded first, as the contract orders it.
- **The list plays when `play` is left out (desktop, headless, debug, scratch copy with `play` removed): pass.** `debug spawns loaded mode=coin rows=4 loop_ticks=180 play=list`, the four coin rows spawn on ticks 1, 46, 91, 136 and repeat, `level=1` on every spawn line, and no `wave ` line in 6 s. This is the desktop log, not a browser run.
- Package contents: pass, see Checks.

## Observations
- Not shown in a browser: the overlay lines `wave none` and `level 1` with the spawn list playing, and the browser run of the list default. The committed `game/tuning/debug_spawns.json` has `play: waves`, which the Director asked to keep, so a browser run of the list needs the file changed. I checked the list behaviour on desktop from a scratch copy (see Browser run) and did not touch the file. This does not block `pass`. If the Director wants it in a browser, allow a one-run switch of `play` and I put it back.
- Because `play` is `waves` in the committed file, the list-based checks of earlier features (the DRA-29 to DRA-62 debug rows, coin mode) no longer run in `?debug=1` without that switch. Debug spawns lines in the log now read `play=waves`.
- The first `drifter spawn` of `wave_0` comes about 2.7 s after play starts, not at once, because its first placement is at 150 px and the scroll starts at tick 31. That follows the schema and the files.
- With the ship held at x=624, y=184 for the whole run, the placeholder waves never hit it in 65 s. At the default x=320 column wave_0's big meteorite (x=300, 410 px) and medium (x=330, 700 px) hit a ship held on the top line. In an earlier no-input page load (separate from the checks above) the ship fell once, then wave_0's big meteorite (x=300) took a second life at about 9 s after the respawn. That is placeholder content, not a bug.
- The star speed checks read whole pixels over a browser-timed second, so they carry about 1 px of slack. Level 2 read 71.6 px/s against 72.6 expected.
- This pygbag build starts the game on page load, with no click needed. I did not add a start screen.
- pygbag prints `Black not found` and `ffmpeg: not found` when it builds. Both are build-machine messages and do not affect the package.
- The Playwright tool left a `beforeunload` dialog after a reload of a running page; closing the page and navigating again cleared it. This is a test-harness matter, not the game.
- The three wave files carry `Verdict: provisional` critic reports in `docs/reports/waves/`, as the contract expects. Each must pass `wave_check` before the MVP ships.

## Decisions
- `app/waves.py` lists, reads and decodes only. Core's `build_wave_book` does every check, so file errors name `waves/<file>`. Source: `app.md`, Rationale (wave files are read in the app and checked in core).
- One `add_drifters` call per tick, with the spawn list's or the waves' placements, never both. Source: `app.md`, Rules, Tick.
- One seed per page load: `random.getrandbits(64)` once, before the first frame. The app never restarts the waves; `step_run` does that on retry. Source: `app.md`, Rules, Frame loop.
- `debug_spawns.py`: `play` is optional and defaults to `list`. Anything else raises `tuning/debug_spawns.json: play must be "list" or "waves"`. The load line ends with `play=%s`. Source: `app.md`, Rules, Debug test spawn list (What plays, Log).
- Wave lines are drawn right after `draw_debug_overlay`, inside the `overlay_visible` block, so F3 hides them with the rest. Source: `app.md`, Rules, Draw.
- Did not edit `game/tuning/debug_spawns.json`. The Director said to keep `play: waves`, and the list and bad-`play` checks were done on desktop with scratch copies. Source: Director's message for this run; `app.md`, Integration checks for DRA-76 (scratch copies, no code change).
- Held ArrowUp and ArrowRight in the long runs so the ship sits at the top right, clear of every placeholder hazard column, to reach the Level 2 part of the flow without losing the run. The required arrow check was made first, in the same page, from the first frame. Source: `app.md`, Integration checks for DRA-76 (the wave flow, and the fallback if the run ends early).
- Key events were sent as `KeyboardEvent`s on the canvas and the DEBUG key lines (which carry x/y) read from the console, not from screenshots. Source: my role file; `app.md` arrow-key log lines.
