Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-76-06-ui-developer (debug overlay wave and level lines, six-line `overlay_text_bottom`), started by /implement.
2. **Delivered:** `docs/reports/qa/DRA-76-06-ui-developer.md`
3. **Checks:** `game/tests/check.sh` ends `QA: pass` (ui: 46 passed, `test_hud.py` 13 passed unchanged). Acceptance check run inline from `game/` (same code as the task): prints `True True True` then `True`. Edge cases, all correct:
   - Lines 5 and 6 byte-identical to the expected render for `wave none`, `wave wave_0`, `wave rest` (level 3, `current_wave_id` None).
   - Level 1, 2, 5, 8, 9 and 12 each render `level <n>` from `run.level` (byte-identical to the expected render).
   - A wave id of 205 characters is drawn whole, never cut. An empty id, a blank id and an upper-case id draw without error. A 50 x 50 surface draws without error.
   - The lowest ink row of lines 1 to 6 is row 72 and `overlay_text_bottom()` is 76, so no text pixel is on or below it (four runs: no waves, playing, resting, long id).
   - Lines 1 to 4: pixels above line 5's top row are identical with and without `draw_debug_wave_lines`.
   - Same run drawn twice gives identical bytes. The resting run's `repr` is identical before and after the draw (no state change).
   - Review's For QA list covered. The one open item (`frame.py` does not yet call `draw_debug_wave_lines`: `app/frame.py:170-171` still calls only the hitboxes and the overlay) is the Integration Engineer's task per the contract Impact table, not a bug in this task.
4. **Assumptions:** The 4 px margin and 6 line height are taken from the code's own font through the contract's formula; no number was invented.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. It must add `draw_debug_wave_lines(surface, run)` right after `draw_debug_overlay` in `game/app/frame.py` (`systems/app.md`); until then lines 5 and 6 are not drawn in the browser and the HUD sits two empty lines lower in debug mode.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
