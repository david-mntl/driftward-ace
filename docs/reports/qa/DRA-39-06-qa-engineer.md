Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-39-06-qa-engineer (base, spawner, meteorite, satellite, registry tests), started by the Director.
2. **Delivered:**
   - `game/tests/core/test_drifters.py` (changed): DRA-29 tests brought up to the contract (no `hit_ship`, no `default_y`, `is_off_screen` with entered rocks, registry stubs with `start_position`); "hits once" removed; new tests for the missing x, the placement speed, invert refused, the re-hit values from `hazards`, `may_hit_ship` and `brightness`, `mark_entered`, and the registry holding both drifters.
   - `game/tests/core/test_satellite.py` (new): start position, specialty and no-angle refusals, re-hit values, the 60-state warning, movement (flat, angled, invert, whole crossings 274, 292 and 221 ticks), touch and graze zone, warning tilt for the meteorite and the satellite.
   - `game/tests/CONTEXT.md`: one line on how these two files build their tuning.
3. **Checks:** 22 tests in the two files, all pass (`pytest core/test_drifters.py core/test_satellite.py`). Ruff lint and format pass. Mypy shows no error in either file. Full `check.sh` ends `QA: fail (typecheck core)`; every failure is in `game/tests/core/test_run_drifters.py` (12 test failures, 15 mypy errors, all `hit_ship`), the file of task DRA-39-07. The task's acceptance check allows this ("only their own files failing"). The `core` step runs both new files.
4. **Assumptions:**
   - The meteorite's warning tilt test sits in `test_satellite.py`, next to the satellite's, with a one-variant meteorite tuning.
   - The whole-crossing tick counts (274, 292, 221) come from the contract's satellite timeline and are checked in the movement test, in run order (update, then `mark_entered`).
   - Meteorite tests keep the DRA-29 fixed speed ratio 0.75; satellite tests use 0.375 from `drifters/02-satellite.md`.
5. **Documentation differences:** None.
6. **Next:** Task DRA-39-07 (QA Engineer) still has to bring `test_run_drifters.py` up to the contract. The harness stays red on that file until then. No bug found in game code, so no fix is owed to the Gameplay Implementer. The Integration Engineer is not affected by this task alone.
7. **Status:** done.

## Bugs
None. Every new test passes against the code.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (only `test_run_drifters.py`, task DRA-39-07) · core FAIL (12 tests, only `test_run_drifters.py`; 428 pass, including all 22 new) · ui PASS
QA: fail (typecheck core)
