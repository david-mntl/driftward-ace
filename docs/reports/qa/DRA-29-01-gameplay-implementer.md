Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-29-01-gameplay-implementer (hitbox shapes and overlap in `core/collision.py`, ship inverted-T hitbox and `TOP_SIDE_SPEED` in `core/ship.py`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-29-01-gameplay-implementer.md. No files saved in `game/tests/` (Verify mode; the tests belong to task DRA-29-07).
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck, core (35 passed), ui (11 passed) all PASS. Ends `QA: pass`.
   - Acceptance check from the task, run from `game/`. Output: `6.58` / `False True` / `False True`. All three lines match the task.
   - Spawned ship hitbox: `Box(320, 240, 12, 32)` and `Box(320, 250, 32, 12)`. Bar x 314 to 326, y 224 to 256; foot x 304 to 336, y 244 to 256.
   - Strict touch, one pixel at a time (circle r 14): bar right side tangent False, 0.1 px further in True. Bar left side, same. Foot right edge, foot left edge and foot bottom tangent False, 0.1 px in True. Foot outer corner (45 degree tangent) False, 0.1 px in True. A rock at (344, 230) in the T's empty corner False.
   - Box-box: sharing only an edge False, sharing only a corner False, 0.01 px overlap True.
   - Circle center inside the bar True, inside the foot True, outside the T (335, 230, r 1) False.
   - Empty hitbox on either side or both: False. `place_hitbox((), x, y)` and `grow_hitbox((), m)` return `()`.
   - `SHIP_HITBOX` unchanged after `place_hitbox` and `grow_hitbox`; both return new tuples. Grown by 14: bar `Box(0, 0, 40, 60)`, foot `Box(0, 10, 60, 40)` (centers kept, w and h plus 2 x margin). Grown by 0 keeps the shape.
   - Wall and top line: ship at the left wall gives hitbox left edge 0.0; at the top line gives top edge 168.0 (`TOP_LINE_Y`); at the right wall gives right edge 640.0; bottom edge equals the ship's 32 x 32 bottom edge. The T never leaves the square.
   - Determinism: the inline script run twice gave identical output (diff empty); `ship_hitbox(spawn())` equals itself across calls.
   - Review items: the one note (docstring "about 6.58") is not a bug and needs no fix. No must-fix findings. The ship diff only adds constants, `ship_hitbox`, the import and docstring text, as the task requires.
4. **Assumptions:** The ship hitbox sizes (12, 12) are `guess` values in 04-ship.md, used as given.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer cannot start on this task alone; the DRA-29 test task DRA-29-07 (QA Engineer) can now be written against this code. No open bugs.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (35 passed) · ui PASS (11 passed)
QA: pass
