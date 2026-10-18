# game/tests: context for agents

Read this before you write or run a test.

## Purpose
This folder is the QA gate. Code reaches the Integration Engineer only after the Implementation Reviewer has read it and this folder passes. Tests prove the game behaves the way the contracts in `docs/contracts/` and the GDD in `docs/design/gdd/` say it should.

## Layout
| Path | What goes there |
|---|---|
| `core/` | tests for `game/core/`. A test for `game/core/ship.py` goes in `core/test_ship.py`. |
| `ui/` | tests for `game/ui/`. Same naming. |
| `conftest.py` | shared fixtures |
| `pytest.ini` | pytest config |
| `check.sh` | the only way to run checks |

Test files are `test_<module>.py`. Test functions are `test_<behavior>`, for example `test_ship_falls_with_no_input`.

## How to run
Run from any directory:

| Command | Does |
|---|---|
| `game/tests/check.sh` | everything: env, lint, format, typecheck, core, ui |
| `game/tests/check.sh lint` | `ruff check` and `ruff format --check` on `game/` |
| `game/tests/check.sh typecheck` | `mypy --strict` on `game/` |
| `game/tests/check.sh core [pytest args]` | core tests only, e.g. `core -k ship -v` |
| `game/tests/check.sh ui [pytest args]` | ui tests only |

Read the last line:
- `QA: pass`: every step passed or was skipped.
- `QA: fail (lint, core)`: those steps failed. The output above it says why.

Exit codes: 0 pass, 1 a check failed, 2 usage or environment error. `SKIP (no tests yet)` means that folder has no tests. It's not a failure.

Never run `check.sh fix`. It edits code you don't own.

## Fixtures
- `rng`: a `random.Random` with a fixed seed. Pass it to any code that takes randomness.
- `pygame_headless`: initialises pygame once per session. Use it in UI tests that need fonts or surfaces.
- `caplog` (built into pytest): for event-log tests. Set DEBUG on the module's logger only (`caplog.set_level(logging.DEBUG, logger="core.ship")`) and count lines by message prefix. Example: `core/test_ship.py`.

Every test runs headless (SDL dummy drivers). Import game code the way the game does: `from core.ship import Ship`.

## Markers
Only these exist. Any other marker is an error.
- `@pytest.mark.smoke`: steps a system for many ticks and checks the result.
- `@pytest.mark.determinism`: runs the same seed and inputs twice and asserts the state matches.

## What gets a test
Tests are written only when an Architect test task (`Assignee: qa-engineer`) asks for them. One test per functionality its **Do** lists, not one per function. No pile of unit tests. Until a task asks, the folder can stay empty and `check.sh` still passes.

Everything else QA checks with inline headless runs (`SDL_VIDEODRIVER=dummy python -c "..."`) that are never saved here.

## Rules
- Test behavior through the contract's Interface. Don't test private helpers or internals.
- Every expected number comes from the GDD or `game/tuning/`. Never invent one.
- Tests are deterministic. Time is ticks, never the wall clock. Randomness comes only from `rng`.
- Tests follow `game/ruff.toml`, including type hints (`-> None` on every test).
- UI tests read positions from the drawn pixels (`pygame.image.tobytes`), never from a hard-coded font size. Example: `ui/test_error_screen.py`.
- Test files go only inside `game/tests/`. Never edit game code to make a test pass.
- Never edit `check.sh`, `pytest.ini` or the fixtures in `conftest.py` to get a pass. Change them only when the Director asks. Never use `skip`, `xfail` or `# noqa` to hide a failure. If the harness itself is wrong, report it to the Director.
- When a test task adds a fixture, folder or convention, update this file in the same run.
- `core/test_collision.py` keeps one table of exact-number cases per unordered pair of shape kinds (`TABLES`): circle and circle, box and box, circle and box, and, from DRA-47, line and line, circle and line, box and line (`Line` is a capsule: a segment with a thickness and round ends). Each case runs both ways round, moved by the same offsets, with an empty hitbox, with a shape added and grown. One test checks a line with both ends on one point against the circle of the same size. A guard test fails when `core.collision.Shape` gains a kind with no table: add the table and its cases first. Its ship-against-every-variant tests read `game/tuning/drifters/*.json` (one file per `DrifterType`) and build the tuning records themselves, so a new drifter or variant is covered by its file alone. A type with a plain `hitbox` list is met on each side at its own touching distance. The chain lightning (its file lists nodes and arcs, not a hitbox) has its own test and branch in the loader: one case per variant and `invert` value, built with `ChainLayout`, `layout_size` and `chain_hitbox` from the contract's Interface, the node positions mirrored by the file's own `invert_mirror`. It is moved to a state with `dataclasses.replace(ticks_in_phase=...)` and must overlap the ship only while firing, with the middle of an arc or a node on the ship's center and with its nearest edge 0.5 px inside the ship's 32 x 32 square on each side, and must not overlap when just clear of it (arc width and node size from the file). The fireball (its file lists `head_width` per variant and the type's `tail_ratio` and `angle_degrees`, not a hitbox) has its own branch in the loader, from DRA-56: one case per variant and `invert` value, built with `FireballTypeExtra` and `fireball_hitbox` from the contract's Interface, so it goes through the same touching-distance test as the plain-hitbox types (WARNING never overlaps, ACTIVE does on the ship's center, each side just clear and 0.5 px inside). A second test, `test_ship_meets_the_fireball_tail_alone`, puts only the tail circle on the ship, 0.5 px inside the foot's bottom edge and 0.5 px inside its outer side edge (the right without `invert`, the left with it), asserts the head is clear there, and moves the tail just clear. The coin (its file lists `points` and `glint` per variant and the crystal's, body's and ring's sizes at the type, not a hitbox) has its own branch in the loader, from DRA-62: one case per variant, built the way `app.tuning` builds it (`coin_hitbox`, `CoinVariantExtra`, `CoinTypeExtra`, `speed_ratio` 0.0, `entry_warning_ticks` 0) and kept out of `SHAPE_CASES`, because the coin is born ACTIVE and the WARNING steps of the first test don't apply. Four tests (`COIN_CASES`): the ship meets the coin's box on each side, touching (no overlap) and 0.5 px inside (overlap); the coin overlaps the ship on the state it is spawned on, ACTIVE with `ticks_in_phase` 0 and `warning_ticks` 0; only the box counts, with the coin put so that a point or the ring (worked out from the file's sizes) crosses the ship's edge while the box touches it or is a hair clear (no overlap), and a hair inside (overlap); `effect_on_touch()` is `COLLECT`, never `HIT`, and `graze_zone()` is `()`. No test code names a variant. A type with no file fails the first test and names the type. It never imports `app`.
- `core/test_drifters.py` (base, spawner, meteorite, registry) and `core/test_satellite.py` (satellite, and the warning tilt) build their own `DrifterTuning` from the GDD values at the top of each file (`make_tuning`, `hazards=` optional, left out means the default `HazardRules`). They never read `game/tuning/` and import no expected number from the code. Each stands alone; the shared `place`, `advance` and `active` helpers are repeated, not imported.
- `core/test_chain_lightning.py` (the chain lightning, the base hooks it uses `warning_copy`, `settle_warning`, `scale_timer`, `scale_telegraph`, and chain lightnings inside the run: hits, the re-hit cooldown, drops, logs) builds its own `DrifterTuning` for the chain lightning, the meteorite and the satellite from the GDD values at the top of the file (`make_tuning`, `hazards=`, `switches=`, `charge_ticks=` and `fire_ticks=` optional), the seven layouts in units of `node_spacing` from the contract's Layout table. It reads no `game/tuning/` file and imports no expected number from the code under test. Like `test_satellite.py` it repeats its own `place`, `advance` and `active` helpers.
- `core/test_fireball.py` (the fireball, the base rules it relies on `drawn_parts`, `is_partly_on_screen`, `mark_entered`, `is_off_screen`, `warning_center`, `warning_tilt_degrees`, `warning_copy`, and fireballs inside the run: hits, the tail alone, the re-hit cooldown, drops, logs) builds its own `DrifterTuning` for the fireball and the meteorite (for the footprint case) from the GDD values at the top of the file (`make_tuning`, `hazards=`, `switches=` and `extra=` optional; `extra=None` builds a tuning with no type values). The head and tail circles, the velocities and the drawn boxes are worked out in the file from head width, `tail_ratio` and the angle (`expected_tail`, `expected_velocity`, `parts_of`), never taken from `fireball_hitbox`. It reads no `game/tuning/` file and imports no expected number from the code under test. Like `test_chain_lightning.py` it repeats its own `place`, `advance` and `active` helpers. A sweep walks each entry (corner, along the top, side) for both variants and `invert` values tick by tick and checks `has_entered` and `is_off_screen` against boxes worked out in the file; the contract's drop points (n 202, 208, 150) and the corner timeline states 258, 261 and 262 are checked by name. The cooldown test uses a fireball at 0.02 px/tick so the ship stays in it for the whole cooldown, and clears `invuln_ticks_left` before each tick.
- `core/test_coin.py` (the coin, the base rules it relies on `parked`, `scroll_step_px`, `collect_points`, `collect_popup`, `drawn_parts`, and coins inside the run: collecting, the popup, the score, logs), from DRA-62, builds its own `DrifterTuning` for the coin and the meteorite (for the hit on the same tick) from the GDD values at the top of the file (`make_tuning`, `switches=` optional): the coin's records the way `app.tuning` builds them (every variant the crystal's 12 x 20 and one 12 x 10 box, `speed_ratio` 0.0, `entry_warning_ticks` 0). It reads no `game/tuning/` file and imports no expected number from the code under test. Like `test_fireball.py` it repeats its own helpers (`coin`, `rock`, `resting`, `run_of`). `run_of` builds a run whose scroll is already moving (`SCROLLING`, so the world moves 1.1 px a tick), with drifters numbered from 1; the ship is put back with `replace(run, ship=...)` before each tick that must not move it. A meteorite for the same-tick tests is an ACTIVE one with speed 0. The ship that falls on its next step is `Ship(320, 495, vy=5.5)`; a coin at y 487.8 ends that tick on the fallen ship. Meters are worked out in whole numbers (`meters_after_step`). The box tests (`is_partly_on_screen`, `is_off_screen`) use the crystal's and the ring's edges worked out in the file; the timeline test (`smoke`) walks the coin from the top for 455 ticks and from (440, 210) for 255, and checks the contract's drop points. The one test for `scroll_step_px` is in `core/test_scroll.py`: it walks 300 steps and checks it is 0.0 to tick 30, then the scroll speed, equal to what `step_scroll` adds, and logs nothing.
- `core/test_run_drifters.py` (drifters inside `core.run`: entering, hits, the re-hit cooldown, drops, logs) builds its own `DrifterTuning` for the meteorite and the satellite from the GDD values at the top of the file (`make_tuning`, `hazards=` optional). It reads no `game/tuning/` file and imports no expected number from the code under test. `rock()` builds a meteorite directly; a satellite goes in through `add_drifters`. A test that must see the cooldown alone clears `invuln_ticks_left` before each tick (`replace(run, invuln_ticks_left=0)`), so protection can't hide a missed hit.
- `core/test_run_score.py` (the run's score: meters plus coin points, never down, frozen at game over, 0 after a retry, and no log line naming it) takes every expected number from the GDD values at the top of the file (`POINTS_PER_METER`, `PX_PER_METER`, the scroll speed in tenths of a px, the start delay) and works the meters out in whole numbers in `_meters_after`. It imports no expected number from the code under test. A scripted pilot (`_scripted_run`) flies one whole run to game over: it holds up, lets the ship fall, stands in each respawn wait, then presses up. A fall, a respawn wait and the game over are all in that run. Coin points are set with `dataclasses.replace(run, coin_points=...)` because no rule adds them yet. A held arrow at game over needs `retry_armed=False`: with it armed, any press is a retry.
- `ui/test_score_text.py` (the score's text) is plain text, no pygame: the scope report's four examples, a group of zeros inside the number, and a number of 30 digits, each against a string written out in the file.
- `ui/test_game_over.py` (the Game Over box) draws on a black 640 x 480 surface, where the box (black at alpha 90) adds no ink, so the ink is the text alone. It reads each line as a band of ink rows (`_bands`) and takes every place from those pixels: three bands inside the box and centered after `draw_game_over` then `draw_final_score`, the middle one the size of `score_text` rendered in the default font at 16 px; only the score line's rows change with the score; `draw_game_over` alone gives the same title and prompt bands and no ink between them. The box's size and top-left (320 x 120, (160, 180)) are written at the top of the file from the contract.
- `ui/test_hud.py`, from DRA-61: two tests hold with the meters readout on line 2 and with SCORE on line 1. In normal mode the HUD's ink starts at or right of `HUD_MARGIN` and at or below `HUD_TOP`; in debug mode its first ink is at or below `overlay_text_bottom() + HUD_OVERLAY_GAP`. The exact SCORE line tests (DRA-61-07) build the SCORE text as the contract sets its look (`score_text(score)` in the default font at `HUD_FONT_SIZE`, white, antialiased) and compare the whole drawn surface with it blitted at (`HUD_MARGIN`, `hud_top`), for six scores (0 to 12 digits) in both modes, with 0 lives so only SCORE is drawn. `_score_run` sets the score through `coin_points` on a run with no scroll. Other tests: SCORE's pixels change with the score (and come back for the same score, so the one-slot cache can't serve a stale text), the text grows to the right; line 2 and everything below is empty with meters flown; SCORE's first ink row is `overlay_text_bottom() + HUD_OVERLAY_GAP` plus the text's own ink offset; and with 3 lives, the overlap, gap, no-jump, top-line and hearts rules hold for every score.

## When something fails
A failing test or a wrong inline run is a finding, not something for you to fix. Write it up in `docs/reports/qa/` with the failing test name or the inline command that reproduces it, the expected and actual values, and the source of the expected value (contract or GDD section). Then hand it to the agent that owns the broken file.
