Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-23-05-qa-engineer: update `tests/ui/test_hud.py` for `draw_hud(surface, run, below_overlay)` and add the heart tests. Started by the caller.
2. **Delivered:** `game/tests/ui/test_hud.py` (changed). `game/tests/CONTEXT.md` needed no change: no new fixture, folder or convention.
3. **Checks:** `game/tests/check.sh` ends `QA: pass`. The `ui` step runs 11 tests: 3 in `test_error_screen.py` and 8 in `test_hud.py` (5 updated, 3 new). All pass against the current `ui/hud.py`.
   - Updated (existing 5): every call builds `Run(ship=spawn(), scroll=SCROLL, lives=0)`, `SCROLL` unchanged (100 scrolled ticks, 11 m). 0 lives keeps the readout the only white ink. Each test checks what it checked before.
   - New 1, `test_hud_draws_one_heart_per_life`: lives 3, 2, 1, 0. Boxes at (608, 8), (576, 8), (544, 8) hold white exactly when the slot is filled. No white in x 536 to 639, rows 0 to 39 outside the filled boxes.
   - New 2, `test_hud_lost_life_removes_the_leftmost_heart_only`: pixels of slots 0 and 1 are identical at lives 3 and 2. Slot 2 is empty at lives 2.
   - New 3, `test_hud_hearts_ignore_the_overlay`: heart area pixels identical with `below_overlay` True and False. Heart pixels and green overlay text pixels (top and floor lines excluded) share no position.
   - Heart constants are read from `ui.hud` and asserted against the scope report numbers (white, 24, 8, 8) at module level, as the file does for the readout values.
   - Positions come from drawn pixels. No font size or line height is hard-coded. The 4 slot lefts and the area bounds come from hud.md, Presentation.
4. **Assumptions:** The hearts area for "no stray white" and "same pixels" is x >= 536 (leftmost box 544 minus the 8 px margin). The readout sits at x 4 and is far left of it.
5. **Documentation differences:** None.
6. **Next:** Architect closes task DRA-23-05. No bugs. Out of scope as the task says: heart shape, Game Over box, `game/app/` draw order.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · core PASS (35 tests; `tests/core/` belongs to DRA-23-04) · ui PASS (11 tests)
QA: pass
