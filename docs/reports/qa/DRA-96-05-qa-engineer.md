Verdict: pass
Created by: qa-engineer

1. **Task:** test task `docs/contracts/DRA-96/tasks/DRA-96-05-qa-engineer.md` (the planet's pull on the ship), started by /implement.
2. **Delivered:** `game/tests/core/test_ship_pull.py` (new, 229 tests), `game/tests/CONTEXT.md` (a paragraph for the new file).
3. **Checks:** `game/tests/core/test_ship_pull.py` alone: 229 passed against `game/core/ship.py` as built by DRA-96-01, no bug found. Lint, format and typecheck pass. The full `core` step still fails on two test files outside this task, all listed in the contracts' Impact tables as expected failures that later tasks clear (see Harness). One test per behavior of the task's `## Test` list, with parametrized angles and distances:
   - no pull outside or on the edge (16 offsets, exact 3-4-5 lengths);
   - straight-line pull just inside, mid-field and at the surface at 15 angles;
   - `pull_max` inside the surface, none at the center;
   - two overlapping fields add up, and a field that does not hold the ship adds nothing;
   - the Diagram's table rows through `step`;
   - the pull measured before the move, drag on x, fall cap on y;
   - no wells gives the pre-DRA-96 step, with and without ground (5 grounds x 30 states x 7 thrusts);
   - escape with up held and with a side key held, until out of the field;
   - `check_escapable_pull`: today's value accepted, a tie and a pull past `thrust_up` refused, a pull at or past `thrust_side` refused (`THRUST_SIDE` lowered through `monkeypatch`), both messages word for word;
   - no log lines from `well_pull`, `check_escapable_pull` or a pulled `step`.
4. **Assumptions:** the escape tests read "moves the ship away" as the center's distance to the field's center growing on every tick (gravity also pulls the ship down during a side escape, so the move is not straight along x). A call of `check_escapable_pull` that must not raise is a bare call, because mypy refuses `assert f() is None`. Verdict is `blocked`, not `pass`, because `check.sh` does not end `QA: pass` yet; the cause is outside this task and the task's Acceptance check names it.
5. **Documentation differences:** None.
6. **Next:** the Gameplay Implementer's later tasks and the QA tasks `DRA-96-06-qa-engineer` (`test_collision.py`) and `DRA-96-07-qa-engineer` (`test_wave_files.py`) clear the expected failures. Re-run `game/tests/check.sh` after them: the Acceptance check is met when it ends `QA: pass`. The Director decides nothing here.
7. **Status:** blocked on the Impact table's expected failures only. The test task itself is done.

## Bugs
None in the tested code. The only failures are the ones the contracts announce (Impact tables), none caused by this task.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL · ui PASS
- core, `test_collision.py`: collection error `KeyError: 'hitbox'` in `load_variant_cases`, because `game/tuning/drifters/planet.json` has no `hitbox`. Expected: `docs/contracts/systems/drifters.md`, Impact, the DRA-96 table. Cleared by task `DRA-96-06-qa-engineer`.
- core, `test_wave_files.py`: 3 failures (`placement type 'ufo'`, `'Meteorite'`, `''`), the unknown-type message now ends `floating_island, planet)`. Expected: drifters.md Impact. Cleared by task `DRA-96-07-qa-engineer`.
- with `test_collision.py` left out: 733 passed, 3 failed (the `test_wave_files.py` ones). `test_ship_pull.py`: 229 passed.
QA: fail (core)

## Round 2 2026-10-22

1. **Task:** Re-run the acceptance check of `docs/contracts/DRA-96/tasks/DRA-96-05-qa-engineer.md` now that tasks DRA-96-06 and DRA-96-07 rebuilt `test_collision.py` and `test_wave_files.py` (both QA reports read `Verdict: pass`). Started by the Director's re-test request.
2. **Delivered:** this report only. No test or game file changed; `game/tests/core/test_ship_pull.py` is as in round 1.
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`. Core: 3072 passed. UI: 46 passed.
   - `check.sh core -k ship_pull`: 229 passed, `QA: pass`; the file runs in the `core` step.
   - `check.sh core -k "collision or wave_files"`: 2502 passed. The two files that blocked round 1 now pass: the `KeyError: 'hitbox'` collection error and the three unknown-type message failures are gone.
4. **Assumptions:** The two assumptions of round 1 still stand.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The round 1 blocker is gone.
7. **Status:** done.

## Bugs
None. The round 1 expected failures are cleared.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3072 passed) · ui PASS (46 passed)
QA: pass
