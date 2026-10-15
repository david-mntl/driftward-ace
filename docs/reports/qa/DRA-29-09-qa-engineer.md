Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-29-09 (two UI guards: object lists match, ship drawn as its hitbox), `docs/contracts/DRA-29/tasks/DRA-29-09-qa-engineer.md`.
2. **Delivered:** `game/tests/ui/test_object_registry.py` (2 tests), `game/tests/ui/test_ship_view.py` (1 test at spawn, 1 test with 3 fractional positions).
3. **Checks:** `game/tests/check.sh` ends `QA: pass`. The `ui` step ran 17 tests, including both new files (2 + 4 passed). Spawn: exactly 624 white pixels, equal to the bar (x 314 to 325, rows 224 to 255) plus the foot (x 304 to 335, rows 244 to 255), upper corners black. Fractional positions (320.5, 240.5), (320.25, 240.75), (101.5, 99.5): T is 32 rows tall, no gap in any row, bar rows 12 wide, foot rows 32 wide, foot bottom row is the bar's bottom row, 624 pixels. Both tuning files exist, so no block.
4. **Assumptions:** Test 4 reads the T's shape from the pixels (row widths, no gaps, bar centered over the foot) and does not hard-code the rounded coordinates, since the task only asks for joined, no-gap, no-overlap. Extra fractional positions were added as parameters of the same test, not as new functionality. `CONTEXT.md` needed no change: no new fixture, folder or convention.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The Architect closes the task file.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (65 passed) · ui PASS (17 passed)
QA: pass
