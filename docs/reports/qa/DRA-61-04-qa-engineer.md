Verdict: pass
Created by: qa-engineer

1. **Task:** test task `docs/contracts/DRA-61/tasks/DRA-61-04-qa-engineer.md`: tests for the run's score, started by the Director's agent.
2. **Delivered:** `game/tests/core/test_run_score.py` (new, 8 tests); `game/tests/CONTEXT.md` (one bullet for the new file).
3. **Checks:** `game/tests/check.sh` ends `QA: pass`; `test_run_score.py` runs in the `core` step (1342 core tests pass, 35 ui). One test per `## Test` line: new run score 0 and coin points 0; score = whole meters at 1 point/m (0 for 30 ticks and until 10 px scrolled, 1 at tick 40, 11 at tick 130, 106 at tick 1000); meters plus coin points; coin points unchanged through falls, the wait and game over; score never down and counting through falls and waits (checked against the meters formula on every tick of a scripted run of 3 falls, waits and game over); score frozen on every game-over tick (arrows released and held); retry gives 0 (coin points do not carry over); no log line names score or coin, and `game over meters=%d` keeps its text. No test needed a code change, and all pass against the current `game/core/run.py`.
4. **Assumptions:** The scripted pilot (hold up, fall, wait, press) is test-only and uses no tuning file. Game over is reached by falls only; hits are covered by `test_run_drifters.py`. Meters are worked out in whole numbers (`ticks * 11 // 100`) to avoid float rounding.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer / the lane's next step. No bugs open.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (includes `test_run_score.py`) · ui PASS
QA: pass
