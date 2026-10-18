Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-39/tasks/DRA-39-05-qa-engineer.md`: rebuild `game/tests/core/test_collision.py` (shape tables, invariants, guards, ship against every variant). Started by the Director.
2. **Delivered:** `game/tests/core/test_collision.py` (rebuilt; the two ship tests at its end are unchanged). `game/tests/CONTEXT.md` (one line under Rules on the tables, the guard and the tuning-file reading).
3. **Checks:**
   - `check.sh core -k collision`: 370 passed. lint PASS, format PASS, mypy clean for `test_collision.py`.
   - Tables: circle-circle (19 cases), box-box (26), circle-box (26). Each case runs both ways round, moved by 5 offsets with `place_hitbox`, against an empty hitbox, with a shape added to either side, and grown by 0.5 and 14 px (overlaps only).
   - Guard: shape kinds from `typing.get_args(core.collision.Shape)` equal {Circle, Box}; every unordered pair has a table. `TypeError` is checked for `hitboxes_overlap` (either side, with an empty other side, mixed with known shapes), `place_hitbox` and `grow_hitbox`, and the message names the kind.
   - Ship against every variant: 5 cases, read from `game/tuning/drifters/*.json` (meteorite small, medium, big; satellite flat, angled). For each, 4 directions: no overlap at the exact touching distance, overlap 0.5 px closer, overlap centered on the ship, no overlap in WARNING. No test code names a drifter type or a variant. A missing file for a `DrifterType` fails its case.
   - Mutation check on a scratch copy (not saved in the repo): changing `<` to `<=` in the circle-circle, box-box and circle-box overlap tests made 16, 14 and 23 tests fail.
4. **Assumptions:**
   - The old three tests (shape overlap, any-shape and empty, grow values) were replaced by the tables and invariants, as the task says "rebuilt". The exact values `grow_hitbox` returns (r + margin, w and h + 2 margin, centers unchanged) are no longer asserted directly, only through the overlap invariant. The task's Test list doesn't ask for it; the Architect may want to add it.
   - A circle met off its axis (not in the current files) uses a Pythagorean gap with a 1e-9 slack instead of an exact touch. It only applies to a future circle variant that does not sit on the ship's center line.
   - The test builds `SatelliteVariantExtra` for any variant that has `angle_degrees`, as the task says. A future drifter with other own fields needs its extra built there.
5. **Documentation differences:** None.
6. **Next:** The acceptance check "`check.sh` ends with `QA: pass`" can't hold yet. The full run ends `QA: fail (typecheck core)` only because of other test files, not this task. `tests/core/test_drifters.py` and `tests/core/test_run_drifters.py` still read `hit_ship` and the old registry stubs, which the contract's Impact table says break and which tasks DRA-39-06 and DRA-39-07 rebuild (16 failing tests, 18 mypy errors, none in `test_collision.py`). Director: after DRA-39-06 and DRA-39-07 land, re-run `game/tests/check.sh`. No bug in game code was found.
7. **Status:** blocked: the acceptance check waits on tasks DRA-39-06 and DRA-39-07. The deliverable itself is complete and passes.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (18 errors in `test_drifters.py` and `test_run_drifters.py`, none in `test_collision.py`) · core FAIL (16 tests in `test_drifters.py` and `test_run_drifters.py`; all 370 collision tests pass) · ui PASS
QA: fail (typecheck core)

## Round 2 2026-10-16

1. **Task:** Re-run the acceptance check of `docs/contracts/DRA-39/tasks/DRA-39-05-qa-engineer.md` now that tasks DRA-39-06 and DRA-39-07 rebuilt `test_drifters.py` and `test_run_drifters.py` (both QA reports read `Verdict: pass`). Started by the Director.
2. **Delivered:** this report only. No test or game file changed; the round 1 tests in `game/tests/core/test_collision.py` are unchanged.
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`. Core: 448 passed. UI: 17 passed.
   - `check.sh core -k collision`: `QA: pass`; the rebuilt collision tests run in the `core` step.
   - One ship case per drifter type and variant in `game/tuning/drifters/` (`meteorite.json`, `satellite.json`), all passed: `meteorite-small`, `meteorite-medium`, `meteorite-big`, `satellite-flat`, `satellite-angled` (`test_ship_meets_every_variant_at_its_own_touching_distance`).
4. **Assumptions:** The three assumptions of round 1 still stand.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The round 1 blocker is gone.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (448 passed) · ui PASS (17 passed)
QA: pass
