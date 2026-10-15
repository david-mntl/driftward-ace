Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-29-04-ui-developer (ship drawn as its inverted-T hitbox through `ui/shapes.py`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-29-04-ui-developer.md
3. **Checks:**
   - `game/tests/check.sh`: QA: pass (env, lint, format, typecheck, core 35 passed, ui 11 passed).
   - Acceptance check, exact command from the task, run from `game/`. Output: `[True, False, False, True, True, True, True, False, False]` and `624`. Matches the task.
   - Walls: ship at x 16 draws columns 0 to 31, at x 624 draws columns 608 to 639. 624 px lit each time, none lost or added.
   - Half-pixel positions (x 15.5, 17.5, 320.49, 320.5, 320.51, 321.5, 322.5, 624.5; y 100.5, 101.5, 463.5 and others): the bar and foot never split. A sweep of 10,248 ship positions (x 16 to 624 in 0.25 steps, 8 y values, 277 of them pixel-counted): every one draws 624 px, a 32 x 32 bounding box, a 32 wide foot over the bottom 12 rows, and a 12 wide bar starting 10 px in from the left edge. No failures.
   - Clipping: ship partly below the floor (y 470, 480), at the top (y 0, -10) and fully off (y 500) draws the visible part with no error. y 500 draws nothing.
   - `draw_shape` width=1: box outline has red edges and a black center (edge pixels at 40 and 59 on a 20 px box at 50). Circle outline has a red edge and a black center. width=0 circle fills its center. Empty hitbox and shapes far off the surface: no error.
   - Same ship drawn twice gives identical bytes. The ship's `repr` is unchanged by drawing.
4. **Assumptions:** None. Two observations, no bug, both follow the task's exact `round(...)` text:
   - Python's `round` is half-even. At an exact .5 x, the drawn T jumps: x 320.5 draws left edge 304, 321.5 draws 306, 322.5 also 306. Physics positions rarely land on an exact .5, so this isn't visible in play. If the Director wants smoother drawing at .5, the contract's rounding rule would change. I'm not asking for it.
   - A circle with r below 0.5 rounds to radius 0 and draws nothing. No object has one.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The reviewer's docstring note on `draw_ship` ("Boxes are centered on the ship") is wording only, and I did not count it as a bug.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (35 passed) · ui PASS (11 passed)
QA: pass
