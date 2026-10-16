Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-47-04-ui-developer (the line shape in `ui.shapes.draw_shape`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-47-04-ui-developer.md
3. **Checks:**
   - `check.sh`: `QA: fail (typecheck core ui)`. No failure comes from this task's file (`game/ui/shapes.py`). Each one sits in a file a later DRA-47 task or the integration owns, as the main session said to expect:
     - typecheck: 17 errors, down from 18 in the DRA-47-03 report: `app/tuning.py:250-251` 4 (integration), `tests/core/test_collision.py` 13 (DRA-47-07). None in `ui/shapes.py` any more, which is this task's acceptance line.
     - core: collection error in `tests/core/test_collision.py:383`, `KeyError: 'hitbox'` (DRA-47-07 owns it, as in the DRA-47-03 report).
     - ui: 16 pass, 1 fail, `test_drifter_registry.py::test_drifter_lists_match_everywhere`: registered views lack `chain_lightning` (DRA-47-06, named in the task).
     - env, lint and format pass.
   - Acceptance check, run from `game/` twice as written in the task (from a script file in the scratchpad, `PYTHONPATH=.`). Both runs identical:
     ```
     True True True True True True
     True True True True
     unknown shape kind 'object'
     ```
   - Inline edge runs (nothing saved in `game/tests/`):
     - Filled band over 24 angles (0 to 345 deg, step 15) at thickness 1, 2, 3, 6, 7, 12: one solid shape with round ends. Worst deviation from the ideal capsule is about 2 px (pygame's polygon and circle rasterization, which the contract names), no gap at the polygon-to-disc join, nothing past the ends.
     - A == B: filled gives a disc (24 px for thickness 6, filled at 3 px, empty at 7 px, no crash); outline gives a 1 px ring (12 px), hollow at the center.
     - Thickness 0, 0.5, 0.9, 1, 1.2, with A != B and A == B, filled and outline: nothing raises (radius 0 case from the review's For QA).
     - Lines far off the surface (-50,-50 to 300,400; x from -10000 to 10000): clipped, no error.
     - Outline at 9 angles, thickness 12: hollow along the length (no pixel near the axis), pixels at both outer ends (beyond A and beyond B), no pixel inside the end discs.
     - `draw_shape` with `None`, a `str`, a `tuple`, an `object`: `TypeError("unknown shape kind '<class name>'")` each time. `draw_hitbox` with a mixed Line, Circle, Box tuple draws all three. A hitbox grown with `grow_hitbox` and drawn as outline: no error.
     - The `Line` passed in is unchanged after drawing. Same line drawn twice into two surfaces: identical bytes.
     - Callers: `ui/debug_overlay.py:70,73` and `ui/ship_view.py:28` call `draw_hitbox` with width 0 or 1 only, so the review's F1 (other widths read as 1 px outline) has no effect.
   - Observation, not a bug: at some angles (for example 225 deg, thickness 12) the outline has a 1 px break where a side meets its end arc, from integer rounding of the end centers. The contract fixes the method (1 px side lines plus a 1 px arc) and does not promise a closed ring. The debug outline stays readable.
   - Grep of `game/ui/shapes.py` for fill, flip, sleep, threading, asyncio, event, key, random, logging calls: none.
4. **Assumptions:** `pass` follows the main session's instruction: the failing harness steps come only from files a later DRA-47 task or the integration owns, and this task's own code has no bug. `check.sh` does not print `QA: pass` yet.
5. **Documentation differences:** None.
6. **Next:** No bug for the UI Developer. Integration Engineer queue once the Director or `/implement` accepts the later-task failures. Re-run `check.sh` after DRA-47-05 to 07 and the `app/tuning.py` integration land; it should end `QA: pass`.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (17 errors: `app/tuning.py` 4, `tests/core/test_collision.py` 13; none in `ui/shapes.py`) · core FAIL (collection error in `tests/core/test_collision.py:383`, DRA-47-07) · ui FAIL (16 pass, 1 fail: `test_drifter_lists_match_everywhere`, DRA-47-06)
QA: fail (typecheck core ui)
