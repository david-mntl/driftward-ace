Verdict: pass
Created by: qa-engineer

1. **Task:** test task DRA-148-07 (level-up rest, rise flag and banner core state in `core.waves` and `core.level_up`), from the Architect's task file.
2. **Delivered:** `game/tests/core/test_level_up_waves.py` (new, 15 test cases from 10 test functions, one per behavior in the task's `## Test` list) and `game/tests/CONTEXT.md` (a paragraph for the new file).
3. **Checks:** `game/tests/check.sh` ends `QA: pass` (786 passed). The new file is in the `core` step and all its tests pass. Its books and rules are built in the file; no `game/tuning/` or `game/waves/` file is read. The GDD's rest gap base is 0, so the scaled-gap tests set `core.waves.REST_GAP_BASE_TICKS` to 10 with `monkeypatch` and compute the expected gap in exact fractions from the Rest gap x row of 08-difficulty.md. Behaviors covered: the rest after a rise is gap + extra rest + unscaled level-up rest and counts down on exactly that many states; the unscaled rest added at Levels 2 to 8; a wave end with no rise adds nothing; Wave 0 and every Level 8 end after the playlist (random waves too) add nothing; an empty-playlist level (one, two or six passed) is skipped on the same tick and the rest is added once; `NO_LEVEL_UP` and a rest of 0 play as before; `level_rose` is True on the rise state alone, also with no rest after it and when one call ends several waves; `next_run_waves` keeps the rules; the banner ages one tick a step and is None at its lifetime; `shown_level` below and from the arrival age.
4. **Assumptions:** the banner values in the test rules (arrival 1, banner 2) are the smallest legal ones, since only `rest_ticks` matters to the waves. When a rise has no rest after it, the next wave can end in another rise on the next tick, so the flag tests compare the flagged states with the rise states instead of assuming a False neighbour.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer is not due from this task alone. Tasks DRA-148-08 (the run's step 9b) and DRA-148-09 (views and HUD) are still queued; no bug is open.
7. **Status:** done.

## Bugs
None. No test failed against the code.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
