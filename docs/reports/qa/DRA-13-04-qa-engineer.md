Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-13-04-qa-engineer: permanent tests for the world scroll and distance counter, started by the Director.
2. **Delivered:** `game/tests/core/test_scroll.py` (9 test cases covering the 7 listed behaviors; behavior 3 runs for n = 1, 60 and 6000). `game/tests/CONTEXT.md` needed no change: no new fixture, folder or convention.
3. **Checks:** `game/tests/check.sh` ends `QA: pass`. The `core` step runs 18 tests: 9 in `test_scroll.py` next to 9 in `test_ship.py`. Expected values come from `Fraction("1.1")` times the Level 1 multiplier, with exact floor arithmetic for meters (n = 0 to 1000). No test failed against the code.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Architect closes task DRA-13-04.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · core PASS (18 passed) · ui PASS (3 passed)
QA: pass
