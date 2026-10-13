Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-23-04-qa-engineer (run tests, two ship tests replaced), started by the Director's session.
2. **Delivered:**
   - `game/tests/core/test_run.py` (new): 14 test functions, 17 cases with the parametrized one, one per behavior 1 to 14 of the task.
   - `game/tests/core/test_ship.py`: `test_floor_respawns_at_spawn` replaced by `test_step_never_respawns_and_floor_check_reports_the_fall` (item 15); the respawn part of `test_events_log_once` replaced (item 16, no `respawn` line on `core.ship`). Import of `is_below_floor` added. Every other test untouched.
3. **Checks:** `game/tests/check.sh`: env, lint, format and core PASS. `core` runs 35 tests, all passing: 17 in `test_run.py`, 9 in `test_ship.py`, 9 in `test_scroll.py`. All expected numbers are copied constants with their GDD or scope-report source. None is imported from the code under test. Mutation check on a scratch copy outside the repo (never saved here): 10 mutants of `core/run.py` (held not stored, wait ends on any held arrow, wait-end log on any held arrow, protected fall restarts the timer, timer stops during wait, scroll stops during wait, retry always armed, retry ignores release, blink 5 ticks, duplicate log line). Each failed at least one new test. No test was weakened.
4. **Assumptions:**
   - The two `smoke` marks go on the tests that step 300 to 600 ticks. No `determinism` test was asked for, so none was written.
   - Item 5 is checked for both "held since before the fall" and "pressed on the fall tick itself", and item 11 also checks that a second arrow pressed while the first is held, and a partial release, do not retry.
   - `CONTEXT.md` needed no update: no new fixture, folder or convention.
5. **Documentation differences:** None.
6. **Next:** The only failing step is `ui`: the 5 `tests/ui/test_hud.py` tests that the hud change (DRA-23-02) broke (`AttributeError: 'Scroll' object has no attribute 'scroll'`). The Director said these are expected and that task DRA-23-05 replaces them, so the acceptance line "`check.sh` ends with `QA: pass`" can't be met until then. Verdict is `blocked` for that reason alone. No game-code bug found, none of my tests fails. Re-run `game/tests/check.sh` after DRA-23-05. The Architect closes the task file.
7. **Status:** blocked, waiting on DRA-23-05 for a green `ui` step. The core tests are done.

## Bugs
None. No new test fails against the code.

## Harness
env PASS · lint PASS · format PASS · core PASS (35 passed) · ui FAIL (5 failed, 3 passed: the expected `test_hud.py` failures, task DRA-23-05)
QA: fail (ui)

## Round 2 2026-10-13

1. **Task:** Re-test of DRA-23-04-qa-engineer, started by the Director's session. Round 1 was blocked only because the `ui` step failed on the 5 old `tests/ui/test_hud.py` tests. Task DRA-23-05 replaced them.
2. **Delivered:** this round appended to `docs/reports/qa/DRA-23-04-qa-engineer.md`. No test or game file changed.
3. **Checks:** `game/tests/check.sh` re-run by me: env, lint, format, core and ui PASS, last line `QA: pass`, exit 0. `core` runs 35 tests (17 in `test_run.py`, 9 in `test_scroll.py`, 9 in `test_ship.py`), all passing, the same as round 1. `ui` runs 11 tests (3 in `test_error_screen.py`, 8 in `test_hud.py`), all passing. The acceptance line "`check.sh` ends with `QA: pass`" is met.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** The Architect closes the task file DRA-23-04. Nothing else is open.
7. **Status:** done.

## Bugs
- Round 1 reported none. No new bug found.

## Harness
env PASS · lint PASS · format PASS · core PASS (35 passed) · ui PASS (11 passed)
QA: pass
