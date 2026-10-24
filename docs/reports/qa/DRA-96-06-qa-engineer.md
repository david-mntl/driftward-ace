Verdict: pass
Created by: qa-engineer

1. **Task:** test task `docs/contracts/DRA-96/tasks/DRA-96-06-qa-engineer.md` (the planet in `test_collision.py`), started by /implement.
2. **Delivered:** `game/tests/core/test_collision.py` (a `PlanetFacts` record, `load_planet_cases`, the planet branch in `load_variant_cases`, `PLANET_CASES`, and one new test), `game/tests/CONTEXT.md` (the planet in the `test_collision.py` paragraph).
3. **Checks:** `check.sh core -k "planet or touching_distance"`: 24 passed, `QA: pass`. The planet case `planet-standard` passes the touching-distance test (WARNING never overlaps, ACTIVE overlaps on the ship's center, each side just clear and 0.5 px inside; the spawned hitbox equals the circle the test writes from `size / 2`). `test_the_planet_field_never_counts_only_its_body_hits`: ship inside `pull_radius` (150) and just clear of the body on each side: no overlap, `effect_on_touch()` is `HIT`. Full `check.sh`: env, lint, format, typecheck, ui pass; core has only the 3 `test_wave_files.py` failures the Impact table announces. No bug found in the tested code.
4. **Assumptions:** the planet stays in `SHAPE_CASES` (plain hitbox, born in WARNING), so the existing touching-distance test covers the first two `## Test` items with no copy of it. `check_escapable_pull` is not called in the loader: it is `app.tuning`'s step and the task's build list doesn't name it. Verdict is `blocked`, not `pass`, because `check.sh` does not end `QA: pass` yet; the cause is outside this task.
5. **Documentation differences:** None.
6. **Next:** QA task `DRA-96-07-qa-engineer` (`test_wave_files.py`) clears the last expected failures. Re-run `game/tests/check.sh` after it: the Acceptance check is met when it ends `QA: pass`. The Director decides nothing here.
7. **Status:** blocked on the Impact table's expected failures only. The test task itself is done.

## Bugs
None in the tested code. The only failures are the ones the contract announces (Impact table), none caused by this task.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL · ui PASS
- core, `test_wave_files.py`: 3 failures (`placement type 'ufo'`, `'Meteorite'`, `''`), the unknown-type message now ends `floating_island, planet)`. Expected: drifters.md, Impact. Cleared by `DRA-96-07-qa-engineer`.
- core otherwise: 3058 passed, including the planet cases in `test_collision.py`.
QA: fail (core)

## Round 2 2026-10-22

1. **Task:** Re-run the acceptance check of `docs/contracts/DRA-96/tasks/DRA-96-06-qa-engineer.md` now that task DRA-96-07 (`test_wave_files.py`) has landed (its QA report reads `Verdict: pass`). Started by the /implement run.
2. **Delivered:** this report only. No test or game file changed; the round 1 tests in `game/tests/core/test_collision.py` are unchanged.
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`. Core: 3072 passed. UI: 46 passed.
   - `check.sh core -k "planet or touching_distance or wave_files"`: 212 passed, `QA: pass`. The planet case `planet-standard` still passes `test_ship_meets_every_variant_at_its_own_touching_distance`, and `test_the_planet_field_never_counts_only_its_body_hits` passes.
   - The 3 `test_wave_files.py` failures of round 1 (`placement type 'ufo'`, `'Meteorite'`, `''`) are gone: the unknown-type message now ends `floating_island, planet)` and DRA-96-07 expects it.
4. **Assumptions:** The round 1 assumptions still stand.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The round 1 blocker is gone.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3072 passed) · ui PASS (46 passed)
QA: pass
