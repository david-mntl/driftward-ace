Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-86-02-gameplay-implementer (`DrifterType.FLOATING_ISLAND`, `TouchEffect.BLOCK`, `game/core/drifters/floating_island.py` and its import), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-86-02-gameplay-implementer.md
3. **Checks:**
   - `check.sh` ends `QA: fail (typecheck core ui)`. Every failure is one the contract's DRA-86 Impact table names for a later queued task, and none comes from `game/core/`:
     - typecheck: 6 errors, all `tests/core/test_collision.py:589` and `:596` (`Polygon` read as a box). Task DRA-86-07-qa-engineer.
     - core: 5 failed, 1572 passed. `test_collision.py`: the shape-kind guard test and `test_ship_meets_every_variant_at_its_own_touching_distance[floating_island-None]` (no `floating_island.json` yet), task DRA-86-07. `test_wave_files.py`: three unknown-type message cases, which now list `floating_island`, task DRA-86-09.
     - ui: 1 failed, 45 passed. `test_drifter_registry.py::test_drifter_lists_match_everywhere` (no tuning file, no view yet), tasks DRA-86-06 and the tuning file, as the Impact table says.
     - lint and format pass. `ruff check` and `ruff format --check` on `game/core/drifters` pass.
   - Acceptance check reproduced from `game/` (PYTHONPATH set, SDL dummy drivers). Output, identical on two runs (cmp):
     ```
     active -60.0 0.0 block ()
     -58.9 320.0
     (Box(cx=0.0, cy=-40.0, w=320.0, h=40.0), Box(cx=-140.0, cy=0.0, w=40.0, h=120.0))
     (Polygon(points=((-160.0, 60.0), (160.0, -60.0), (-160.0, -60.0))),)
     floating_island variant 'box' has no invert
     floating_island has no speed
     floating_island placement needs x
     ```
   - Edge cases, all correct (inline runs, nothing saved):
     - All five variants, both `invert` values: hitbox equals the Diagram's numbers exactly (rectangle, box, L, T, triangle, upright and inverted). `rectangle` and `box` with invert raise `has no invert`. `current_hitbox()` is the hitbox placed at (x, y).
     - Born: `specialty_enabled` True raises `floating_island has no specialty`; False and None are fine. Missing variant extra raises `variant '<name>' has no shape`, missing type extra raises `tuning has no type values`. A placement with a missing variant extra and `invert` on `box` reports the shape error first (the review's For QA line).
     - Start: y None gives -60 (`-height/2`; the box also -60 at 120 tall), a given y is kept, an int x is kept.
     - Timeline at Level 8: still y -60 after ticks 1 to 30 (scroll step 0.0), -58.9 on tick 31, x never changes, `ticks_in_phase` counts each ACTIVE tick, `has_entered` True on tick 31, `is_off_screen()` first True on tick 576 (y 540.6, top edge at or below 540). No log line written by `update`. WARNING and GONE states come back unchanged (same object) with `()` hitbox.
     - `speed` 0.0 and `warning_ticks` 0 at every level 1 to 8 and with `as_level`, and with `hazard_speed_scaling` off. Levels 0 and 9 raise as before.
     - Every variant: `graze_zone()` is `()`, `collect_points()` 0, `collect_popup()` None, `effect_on_touch()` BLOCK, `drawn_parts()` one footprint box. The ship in `ctx` is never read (same result for a different ship). `update` does not mutate its input.
     - Registry: `drifter_class(FLOATING_ISLAND)` is `FloatingIsland`, and it is in `available_drifters()`.
   - Review findings: none, and each For QA line is covered above.
4. **Assumptions:** The `Placement` field is `specialty_enabled`, not `specialty`; I tested the specialty refusal through it.
5. **Documentation differences:** None.
6. **Next:** No bug is open in `game/core/`, and the Gameplay Implementer has nothing to fix. The verdict is blocked only because `check.sh` cannot end `QA: pass` until later queued tasks the contract already names land (DRA-86-07, DRA-86-09, DRA-86-06 and the island's tuning file). Director / `/implement`: continue with those tasks and re-check this report after them. The stale `spawn_drifter` docstring in `spawner.py` ("or ACTIVE for the coin") is not a bug in this task's files.
7. **Status:** blocked. The harness is red only from the tests and files the contract says this change breaks.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (tests/core/test_collision.py:589 and :596, 6 errors, the contract's named break) · core FAIL (1572 passed, 5 failed: all named in the Impact table, tasks DRA-86-07 and DRA-86-09) · ui FAIL (45 passed, 1 failed: `test_drifter_registry.py`, no tuning file or view yet)
QA: fail (typecheck core ui)

## Round 2 2026-10-21

1. **Task:** Re-test of DRA-86-02-gameplay-implementer after the later queued tasks (DRA-86-06, 07, 08, 09 and `game/tuning/drifters/floating_island.json`) landed. No code changed in this task. DRA-86-03 B1 is accepted by the Director as a known issue and is not part of this report.
2. **Delivered:** this round in docs/reports/qa/DRA-86-02-gameplay-implementer.md
3. **Checks:**
   - `check.sh` ends `QA: pass`: env, lint, format, typecheck, core and ui all PASS (ui: 46 passed). Every failure from round 1 is gone.
   - Acceptance check re-run from `game/` (SDL dummy drivers, PYTHONPATH set). Same seven lines as round 1, identical on two runs (cmp): `active -60.0 0.0 block ()`, `-58.9 320.0`, the L upside down, the triangle upside down, and the three refusals (`variant 'box' has no invert`, `has no speed`, `placement needs x`).
   - Timeline at Level 8 re-run with `mark_entered` after each update: y -60.0 on tick 30, -58.9 on tick 31 with `has_entered` True, `is_off_screen()` first True on tick 576 (y 540.6). Same as round 1.
   - Round 1 edge cases are unchanged: `git diff` shows no edit to `game/core/drifters/floating_island.py` since then, and no bug was open.
4. **Assumptions:** The round 1 edge-case runs still hold because the island file is untouched. The island's tuning file lists the five variants with the sizes the acceptance check uses.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. No bug is open.
7. **Status:** done.

## Bugs
None open. None filed in round 1.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (46 passed)
QA: pass
