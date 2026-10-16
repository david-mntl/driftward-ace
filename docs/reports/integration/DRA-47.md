Verdict: pass
Created by: integration-engineer

1. **Task:** integrate DRA-47 (chain lightning), Integrate mode, started by the main session while the Director is away.
2. **Delivered:** `game/app/tuning.py` (changed), `docs/reports/integration/DRA-47.md`. Nothing else in my paths changed: `game/main.py`, `game/app/frame.py`, `game/app/debug_spawns.py`, `game/scripts/`, `pygbag.ini` need no change (app.md, Impact, DRA-47).
3. **Checks:**
   - `game/tests/check.sh`: `QA: pass`. env, lint, format, typecheck, core and ui all PASS. The open typecheck failure at `game/app/tuning.py:250-251` is fixed.
   - Headless import (`SDL_VIDEODRIVER=dummy`, from `game/`): `import app.loop, app.frame` clean.
   - `load_tuning()` on the committed files: the seven variants come out at 140 × 12, 102.51 × 102.51, 12 × 140, 268 × 12, 193.02 × 193.02, 140 × 140 and 140 × 122.85, as in drifters.md, Layout table. `warning_layout` is the point-up `trio_triangle`. The spawn list puts the eight rows on offsets 0, 22, 45, 67, 90, 112, 135, 157, which are ticks 1, 23, 46, 68, 91, 113, 136, 158.
   - Bad chain lightning file (contract check, desktop, `DRIFTWARD_DEBUG=1`): the arcs of `trio_l` set to `[[0, 2]]` gives ERROR `unexpected error, showing the error screen` with `ValueError: tuning/drifters/chain_lightning.json: variants.trio_l.arcs[0] must join two nodes 1 unit apart`. `"telegraph_min": true` gives `ValueError: tuning/hazards.json: telegraph_min must be an integer >= 0`. No `error screen failed` in either. Both idled until the 4 s timeout.
   - 11 more broken copies, each rejected with the file and field named: duplicate arc, uncentered nodes, `arc_width` 13 > `node_size`, unknown `entry_warning_icon`, `charge_ticks: true`, a `width` field in a variant, 4 nodes, a bad `invert_mirror`, a missing `ray_width`, an arc joining a node to itself, and an arc naming node 5. `hazards.json` set to `{}` logs `rehit_cooldown=180 rehit_dim=0.75 telegraph_min=45`, the core defaults.
   - Build: `pygbag --archive game` gave `game/build/web.zip`, with clean package contents. Browser: every required check and every DRA-47 check that can run passed. See Browser run.
   - Logging is by event. The only app change to logging is `telegraph_min=%d` at the end of the one startup `tuning loaded` line. Nothing is logged per tick.
4. **Assumptions:** the wording of the new error messages. The contract gives two examples and I matched their form for the rest. Listed under Decisions.
5. **Documentation differences:** None.
6. **Next:** Director: run `scripts/close-out.sh DRA-47` to see open review findings and these Observations before close-out. To see the feature, run `game/scripts/start-driftward-ace.sh --debug` and open `http://localhost:6060/?debug=1`. The committed spawn list is in `"mode": "chain_lightning"`, as the main session set it, and I left it so. Normal mode: run the script with no argument and open `http://localhost:6060`. Build check: `pygbag --archive game` from the repo root gives `game/build/web.zip`. The frame loop and startup did not change, so no hand check of pygbag's click screen is due for this feature.
7. **Status:** done.

## Browser run
- **Build check:** `pygbag --archive game` (pygbag 0.9.3), from the repo root, gave `game/build/web.zip` (93270 bytes). It is git-ignored and not committed. The zip holds `index.html`, `favicon.png` and `game.apk`. `game.apk` holds 43 files, all under `assets/`:
  - `main.py`
  - `app/{debug_spawns,frame,guard,log,loop,mode,settings,tuning}.py`
  - `core/{collision,levels,run,scroll,ship,world}.py`
  - `core/drifters/{__init__,base,chain_lightning,meteorite,registry,satellite,spawner,tuning}.py`
  - `tuning/{debug_spawns,hazards,playtest}.json` and `tuning/drifters/{chain_lightning,meteorite,satellite}.json`
  - `ui/{debug_overlay,error_screen,game_over,hud,look,shapes,ship_view,starfield}.py`
  - `ui/drifters/{__init__,chain_lightning_view,entry_warning,meteorite_view,registry,satellite_view}.py`

  There is no `tests/`, `scripts/`, `CONTEXT.md`, `requirements.txt`, `ruff.toml`, `__pycache__` or tool cache. **Package contents: passed.**
- **Served** with `game/scripts/start-driftward-ace.sh` in the background, twice:
  - First run: script pid 1291156. Port 6060 was free first, and `curl` got 200 after 2 s. Stopped with `kill 1291156`; the trap logged `Stopping server` and `Server stopped`.
  - Second run, for one more extra check: pid 1295158. Stopped the same way.
  - Port 6060 answered nothing (`000`) after each stop. Log and pid files are in the scratchpad.
- **Pages:** 7 pages in total, one tab at a time, each closed before the next.
- **How inputs and reads were done,** as in DRA-29 and DRA-39:
  - Keys were sent as `KeyboardEvent`s on `#canvas` through `browser_evaluate`.
  - Console lines were timestamped in page ms by a `console.log` hook, put in 315 to 392 ms after navigation, before the start line.
  - Canvas pixels were read with `getImageData`.
  - Times below are ms after play start, which is the `drifter spawn id=1` line in debug mode.

**Required checks:**
- **Build is served and loads: passed.** pygbag logged `orig_argv [debug=1]` and `config.debug = false`. The page title went to `pygame window`.
- **Start line: passed.** `18:39:08 INFO app.loop: start mode=debug` on the first page. On each timed page it came 212 to 225 ms before play start. In `/`: `start mode=normal`.
- **No console errors: passed.** Every page had only the two known lines: `Failed to load resource: 404 //cdn/0.9.3//browserfs.min.js` and `PyMain: BrowserFS not found`. No game ERROR line on any page.
- **Arrow-key input with x/y (`?debug=1`): passed.** ArrowUp was held from 37 ms to 10015 ms:
  - `key down key=up x=320.00 y=240.96`
  - `top line stop x=320.00 y=184.00` at 406 ms
  - `key up key=up x=320.00 y=184.00`

  The y went from 240.96 to 184.00, so ArrowUp lifts the ship.
- **Click to start, recorded:** `navigator.userActivation.hasBeenActive` was already `true` before any click. The start line came at 2868 ms page time and play started at 3068 ms. My one click on `#canvas` came about 15 s later. The game starts before the click, which is the known headless result.

**DRA-47 checks (extra), chain lightning mode as committed:**
- **Tuning loaded, reworded (`/` and `?debug=1`): passed.** On every page: `tuning loaded drifters=meteorite,satellite,chain_lightning hazard_speed_scaling=True timer_scaling=True rehit_cooldown=180 rehit_dim=0.75 telegraph_min=45`. It comes about 50 ms before play start and before `scroll start`.
- **Spawn list loaded, reworded: passed.** `debug spawns loaded mode=chain_lightning rows=8 loop_ticks=180` comes 3 to 5 ms after `tuning loaded`. In `/` there is no such line.
- **Chain lightning warning: passed.** At 0 ms: `drifter spawn id=1 type=chain_lightning variant=pair_flat x=320.00 y=-6.00 speed=2.00 level=1`. The read at 153 ms:
  - 8428 glow (255, 220, 120) pixels, in a box from x 188 to 307 and y 9 to 121. The farthest is 68 px from (256, 70) in x and 61 px in y, so none is farther than 70.
  - Cyan (0, 220, 255) discs of 24 px each, centred at (223.5, 97.5), (255.5, 41.5) and (287.5, 97.5). That puts 24 cyan pixels within 3 px of each of (224, 98), (256, 42) and (288, 98).
  - 0 cyan pixels within 10 px of (384, 70).
- **The charge: passed, with a note.**
  - `drifter active id=1 type=chain_lightning x=320.00 y=-6.00` at 989 ms.
  - I read ray (120, 200, 255) pixels within 13 px of each clean node, about every 45 ms from 1.0 s to 3.05 s:
    - 1197 to 1464 ms: up-right only (1 ray).
    - 2096 to 2401 ms: up-right, up-left and down-left (3 rays).
    - 2496 to 2969 ms: all four diagonals (4 rays).
  - The 2-ray read at about 1.75 s could not be made; see Observations.
  - The cyan discs fall about 60 px each 0.5 s: right node y 125.5 at 2096 ms, 145.5 at 2271 ms, and 145.5 then 205.5 at 2253 and 2754 ms on the other page.
  - 0 band (220, 240, 255) pixels in columns 262 to 378 at 1251, 1754, 2253, 2502, 2754 and 2950 ms.
- **Nothing hits while it charges, the fire does (no key held): passed.**
  - `life lost lives=2` and `respawn from x=320.00 y=500.20 wait=True` at 1023 ms, then `invulnerable end` at 1523 ms. The ship then waits at (320, 240).
  - No `drifter touch` while id 1 charged. At 2950 ms there was still no band and no touch.
  - `drifter touch id=1 type=chain_lightning effect=hit` at 2973 ms, then `life lost lives=1` at 2974 ms. No `respawn from` after it.
  - `drifter touch id=9 ...` at 5974 ms, then `life lost lives=0` and INFO `game over meters=36` at 5975 ms.
  - Exactly 2 `drifter touch` lines on the page, ids 1 and 9.
- **The arcs: passed.** At 4154 and 4200 ms there were band (220, 240, 255) pixels in columns 40 to 150 (521 px) and 170 to 280 (535 px), 5 rows deep: rows 295 to 299 at 4154 ms and 302 to 306 at 4200 ms. Cyan discs sat on those rows, centred near x 31.5, 159.3 and 287.3.
- **The whole chain dims after a hit: passed.** At 3555 ms:
  - id 1's nodes show (0, 165, 191), centred at (255.5, 299.4) and (383.3, 299.4), with 0 (0, 220, 255) pixels within 6 px of either.
  - In columns 300 to 340, rows 298 to 302: 205 (165, 180, 191) band pixels and 0 (220, 240, 255).
  - Rows are about 5 below the contract's 294 because the read came 55 ms late; the chain falls 2 px a tick.
- **Outlines: passed, with a note.**
  - During id 4's fire, at 4200 ms, in columns 40 to 150: green (0, 255, 0) full rows (111 px each) at 301 and 307, which are the arc edges around the band centre at 304.
  - Full rows also at 287 and 321, the graze outline, 17 px from the centre: the 3 px half-width plus 14.
  - Green outlines ring every node.
  - While id 1 charged (2096 to 2271 ms), its right node had 0 green pixels within 8 px. The left node had 8 to 21; see Observations.
- **Every variant (ArrowUp held 10 s): passed.**
  - Ids 1 to 8 each logged one `drifter spawn` with its row's variant and x: pair_flat 320, pair_diagonal 120, pair_vertical 580, trio_line 160, trio_diagonal 520, trio_l 120, trio_triangle 520, trio_triangle 520.
  - Each also logged one `drifter active` and one `drifter gone`, with y 486.00, 533.54, 551.81, 487.50, 577.12, 551.81, 543.11 and 543.11. id 8 was gone last, at 7689 ms.
  - No `drifter touch` in the 10 s.
  - Read at 5801 ms:
    - id 7's nodes at (453.7, 372), (519.5, 260.1) and (581.9, 371): the middle node is highest, so it points up.
    - id 8's nodes at (455.2, 205.3), (519.5, 316.6) and (585.4, 203.9): it points down.
    - id 6 (`trio_l`, inverted) at (183.4, 299.5), (182.4, 426.4) and (55.5, 427.4): the corner is at the bottom right.
- **An arc fires only while both its nodes are on screen (scope report, Feature): passed.**
  - id 3 (`pair_vertical`, x 580) went active at 1692 ms. Column x 580, between its two nodes, had 92 band pixels from about tick 121 of its active phase (its fire starts at 120).
  - The band went to 0 at about tick 202, when the lower node's centre reached y 493, past 486, so off screen. The top node was still on screen, at about y 365, and the fire would have run to tick 239.
  - Ticks are worked out from the page clock and may be off by 1 or 2.
- **Normal mode spawns nothing, reworded (`/`): passed.**
  - In 98 full-canvas reads over 5 s: 0 node (0, 220, 255), 0 ray (120, 200, 255), 0 band (220, 240, 255), 0 glow, 0 blue and 0 green.
  - 8 (240, 240, 240) and 10 (140, 140, 140) pixels appeared, all at x 7 to 19 on rows 31 and 32. That is the meters readout's anti-aliased edge, as in DRA-39.
- **Bad chain lightning file (desktop, headless): passed.** See Checks.
- **Package contents: passed.** See Build check.

**Console messages besides the game lines:**
- The known pygbag 404 and BrowserFS lines.
- pygbag's own warnings: iframe features, `ScriptProcessorNode is deprecated`, `wasm mimetype unsupported` in the server log.
- Two `tick cap hit, dropped ... s` lines on the first timed page, at 18.2 s and 33.2 s. They came while my long pixel-analysis calls held the page's main thread. Each is one line per capped stretch, as the cap rule says.

## Observations
- **The 2-ray read in "The charge" can't be made as written in chain lightning mode.** From 1.5 s to 2.05 s both of id 1's nodes sit under other chains' entry warnings:
  - id 4's warning covers x 218 to 358 from 1.12 s to 2.12 s.
  - id 5's warning covers about x 360 to 500 from 1.5 s to 2.5 s.

  Both are drawn after id 1 because `render_drifter` runs in `run.drifters` order (drifters.md, Presentation), so this is no bug. The 1-, 3- and 4-ray phases were read cleanly and in the right order. The contract's 1.25 s read on the left node is also covered (id 4's warning); the right node was clear. The Architect may want to reword the check: read the right node only, or read the 2-ray phase on another chain.
- **The left node during the charge had 8 to 21 green pixels within 8 px.** I take them to be id 1's debug label below the chain, which spans about x 195 to 445. I did not match the text pixel by pixel. The right node, outside the label's rows, had none, and no outline shows on id 1 until it fires.
- **Earlier checks that use the meteorite or satellite numbers were not re-run.** The committed list is in `"mode": "chain_lightning"`, as the main session set it, and I left it so. These are the DRA-29 and DRA-39 rock and satellite timings, the dim-after-a-hit rock pixels, and the satellite checks. DRA-47 changed only `game/app/tuning.py` in my paths. The frame loop, guard, mode and spawn list code are unchanged from DRA-39, which passed them.
- **Other earlier checks not re-run this round,** for the same reason (no code change there):
  - `?debug=yes`, F3 toggling, the hidden-tab cap and the blink.
  - Game over and retry by pixels, and text matches against reference fonts.
  - The import-error and null-character headless checks.

  What did run covers the start, the mode lines, the key lines, the top line stop, fall, respawn, invulnerable end, game over and console errors.
- The Playwright tool writes its snapshots and console logs to `/workspace/.playwright-mcp/`, which is git-ignored.

## Decisions
- **The chain lightning gets its own branch in `_load_drifter`, keyed on `DrifterType.CHAIN_LIGHTNING`, not a row in `_OWN_FIELDS`.**
  - `_OWN_FIELDS` adds fields to a variant that still has `width`, `height` and `hitbox` (the satellite).
  - The chain lightning's file differs at the top level (nine more type fields) and in every variant (`nodes`, `arcs`, `invert_mirror` instead of a footprint and a hitbox).
  - Source: app.md, Rules, Tuning loader ("checked against `chain-lightning-tuning.schema.json` instead of `drifter-tuning.schema.json`").
- **`_shape` and `_check_inside` now take and return `Circle | Box`, not `Shape`.** They only ever see JSON shapes, which are circles or boxes. The chain lightning's `Line`s are built by `chain_hitbox` and never reach them. That is the typecheck fix. Source: app.md, Impact, DRA-47 ("`_check_inside` ... must not see a `Line`").
- **Check order in the chain lightning file:**
  1. The fields.
  2. The type numbers, then `arc_width <= node_size`.
  3. The variants.
  4. `default_variant` and `entry_warning_icon`.
  5. Then the records are built.

  The hitbox needs `node_size` and `arc_width`, so they are checked first.
- **Arc rules are checked in node units, before the `node_spacing` multiply:** each arc's nodes 1 unit apart, and the node box centred on (0, 0), each within 1e-6. Within one arc the order is: an arc names two different nodes that exist, then it isn't a repeat of an earlier pair, then its length. Source: app.md, Rules, Tuning loader; chain-lightning-tuning.schema.json, description.
- **`width`, `height` and `hitbox` come from core.** `layout_size` and `chain_hitbox` from `core.drifters.chain_lightning`, so the hitbox rule has one home. The meteorite and the satellite keep `extra=None` on `DrifterTypeTuning` (the dataclass default). Source: app.md, Rules (What the loader builds) and Rationale.
- **`telegraph_min` defaults to `DEFAULT_TELEGRAPH_MIN_TICKS` from `core.drifters.base`.** The loader holds no copy of the number. A new `_integer` helper checks it, and the chain lightning's int fields: an int, never a bool, at least the minimum. Source: app.md, Rules, Hazards file.
- **Error message wording:** I followed the contract's two examples. The new forms are:
  - `<path> must be a list of 2 or 3 points`
  - `must be a list of two numbers`
  - `must be a list of two integers >= 0`
  - `must name two different nodes of its variant`
  - `must not join the same two nodes as another arc`
  - `nodes must be centered on 0, 0`
  - `invert_mirror must be 'left_right' or 'top_bottom'`
  - `arc_width must be <= node_size`
  - `<field> must be an integer >= <n>`

  Source: app.md, Rules, Tuning loader ("Errors name the field the same way").
- **The spawn list file was not touched,** and its mode stays `chain_lightning`. Source: main session instruction for this run; app.md, Integration checks for DRA-47 (the mode switch is the Director's or the session's call).
