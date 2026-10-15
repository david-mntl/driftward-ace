Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-29-06-ui-developer (`draw_debug_hitboxes` in the debug overlay), started by /implement in Verify mode.
2. **Delivered:** docs/reports/qa/DRA-29-06-ui-developer.md. Nothing saved in `game/tests/`.
3. **Checks:**
   - `game/tests/check.sh`: QA: pass (core 35 passed, ui 11 passed, `test_hud.py` unchanged).
   - Acceptance check from the task file, run from `game/`, prints exactly `active True True False` and `True True`. The rock's hitbox ring (rows 105-107) and graze ring (rows 91-93) are green at x 320, the center is not filled, the ship's outline is on column 314, and the label ink sits in rows 134-155 past x 350.
   - Edge cases, all correct (inline headless runs, scratchpad scripts):
     - Meteorite in WARNING at (320, -14): `current_hitbox()` and `graze_zone()` are `()`, no outline drawn, label ink in rows 0-10 (against the top edge).
     - Objects at x 0, 3, 5 (left wall): label ink starts at column 0. Objects at x 620, 635, 640 (right wall): label ink ends at column 639. No part cut off.
     - Object at y 470 and 475 (bottom): label top clamps to row 469 (480 minus label height 11), ink reaches row 479.
     - Surface 50x10, smaller than the label: no error, label clamps to 0.
     - No objects: only the ship's outline is drawn (bbox 304,224 to 335,255).
     - `repr(run)` identical before and after every draw: the core is not mutated.
     - Same run drawn twice, two objects close together: pixel bytes identical.
     - Code read: the ship hitbox is drawn from `ship_hitbox(run.ship)` with no visibility check (blink is not read). Draw order is graze, ship hitbox, object hitboxes, labels. `draw_debug_overlay` and `overlay_text_bottom` unchanged, and `test_hud.py` passes.
   - Review finding 1 (docstring wording, "changes the ship") is a note with no change asked. It's wording only and doesn't affect behavior.
4. **Assumptions:** The expected clamp values come from the contract, Presentation, Label place. The blink case was checked by reading the code, because `ship_hitbox` takes only the ship and `Run` holds the blink state separately.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Add the `draw_debug_hitboxes(surface, run)` call in `game/app/frame.py`, right before `draw_debug_overlay`, as `systems/app.md` says.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (35 passed) · ui PASS (11 passed)
QA: pass
