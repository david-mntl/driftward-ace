Verdict: pass
Created by: qa-engineer

1. **Task:** test task DRA-29-07 (hitboxes, ship hitbox, level table, spawner, meteorite), docs/contracts/DRA-29/tasks/DRA-29-07-qa-engineer.md, from the Architect.
2. **Delivered:** game/tests/core/test_collision.py (5 tests, items 1 to 5), game/tests/core/test_objects.py (12 tests, items 6 to 16 including 15a). Report: docs/reports/qa/DRA-29-07-qa-engineer.md.
3. **Checks:** check.sh ends `QA: pass`. The core step collects 52 tests, 17 of them new, all passing against the code. Expected values are typed in each test from the GDD (source line on each constant); no constant is imported from the code under test and `game/tuning/` is never read. Edge cases covered: strict touch at an edge and at a corner (3-4-5 case), both argument orders, first and last warning state, the 103-tick drop, the exact off-screen thresholds.
4. **Assumptions:** the ship tests (items 4 and 5) live in `test_collision.py` as the task says, and `test_ship.py` is untouched. The registry test builds its two bad classes inline and checks the registry is unchanged afterward. A `cast` is used so mypy accepts passing an abstract class to `register_object`. The tests don't check which error comes first for a class that is both a duplicate and abstract.
5. **Documentation differences:** None.
6. **Next:** Architect closes task DRA-29-07 (it stays `Status: open`). No bugs. No change to `game/tests/CONTEXT.md` was needed: no new fixture, folder or convention. The task DRA-29-08 and DRA-29-09 can proceed.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (52 passed) · ui PASS (11 passed)
QA: pass
