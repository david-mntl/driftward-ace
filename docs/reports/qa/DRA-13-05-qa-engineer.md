Verdict: pass
Created by: qa-engineer

1. **Task:** DRA-13-05 test task: permanent HUD layout tests, started by the Director.
2. **Delivered:** `game/tests/ui/test_hud.py` (5 tests, one per behavior in the task). `CONTEXT.md` needed no change: no new fixture, folder or convention.
3. **Checks:** `check.sh` ends `QA: pass`. The ui step runs `test_error_screen.py` (3) and `test_hud.py` (5). Tests read pixels from the surface and use no font size or line height. Scroll is 130 ticks, 100 scrolled, 11 m. HUD constants are read from `ui.hud`, with an assert that they equal the scope report values (4, 20, 4, 4) and white.
4. **Assumptions:** "white" and "green" ink is counted as any non-black pixel for the overlay and the HUD bounds in tests 1, 2 and 3 where antialiasing would otherwise slip past (stricter than the task). Tests 3, 4 and 5 count exact white (255, 255, 255) for the HUD. Test 4 compares a HUD-only surface with an overlay-plus-HUD surface outside the overlay-only ink.
5. **Documentation differences:** None.
6. **Next:** Architect closes the task file. No bugs found.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · core PASS · ui PASS
QA: pass
