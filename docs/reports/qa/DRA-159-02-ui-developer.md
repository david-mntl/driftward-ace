Verdict: fail
Created by: qa-engineer

1. **Task:** QA of DRA-159-02-ui-developer (`MuteIconLook` and `MuteIconView`, `game/ui/mute_icon.py`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-159-02-ui-developer.md
3. **Checks:** The task's own code passes. `check.sh` fails on one test that has nothing to do with this task (B1).
   - Acceptance check reproduced headless with `margin` 8 and `size` 24 from `game/tuning/mute_icon.json`, 856 x 518 window:
     - `draw(window, False)`: every pixel unchanged (True).
     - `draw(window, True)`: 576 pixels changed, all inside Rect(824, 486, 24, 24), which is 8 px from the right and bottom edges (True).
     - A second `draw(window, True)`: same pixels (True).
     - Stand-in with a transparent half: the transparent pixel keeps the window color (10, 20, 30). The opaque pixel takes (244, 241, 255).
   - Edge cases, all correct:
     - Window 1000 x 700: rect (968, 668, 24, 24), 576 pixels changed, all inside.
     - Window 200 x 100: rect (168, 68, 24, 24), all inside.
     - `margin` 0: rect (832, 494, 24, 24), flush to the corner.
     - `size` 1: exactly 1 pixel changed, at (847, 509).
     - Half-alpha picture (200, 200, 200, 128) on black blends to (100, 100, 100), so alpha is honored.
     - `draw(window, False)` is a no-op in every case above.
   - Review `For QA` list: every line covered above. The draw-before-dim point is frame-loop wiring and is not built yet, so it is for the Integration Engineer.
   - No state, no allocation per call, and no scaling in the view (read of `game/ui/mute_icon.py`). Rule 18 holds.
4. **Assumptions:** The `test_drifter_registration.py` failure is counted against this task because the contract for the verdict says `check.sh` must end `QA: pass`. It comes from the uncommitted working tree, not from DRA-159.
5. **Documentation differences:** None.
6. **Next:** Director, for B1. The file is `tools/wave_editor/bench.py`, which no crew lane owns (the roster gives the Wave Designer only `tools/wave_editor/sandbox/drafts/`). Whoever has the wave-editor changes open applies the fix. Then re-run QA on this task (Re-test mode). The Director may also decide that this unrelated failure should not hold DRA-159-02. DRA-159-02 itself has no open bug. The Integration Engineer should draw the icon before the dim when wiring.
7. **Status:** done.

## Bugs
- **B1** `tools/wave_editor/bench.py:302`, owner: not in the roster (Director names it). Unrelated to DRA-159-02, caused by the uncommitted edit to the wave editor bench.
  Reproduce: `game/tests/check.sh core -k test_only_a_drifters_own`.
  Expected: only a drifter's own modules name its `DrifterType` member. Actual: `tools/wave_editor/bench.py:302 names DrifterType.CHAIN_LIGHTNING` (the new `follows_ship` check, with `DrifterType` newly imported at line 19). `tests/core/test_drifter_registration.py::test_only_a_drifters_own_modules_name_its_type` fails, so `check.sh` ends `QA: fail (core)`.
  Source: `game/tests/core/test_drifter_registration.py:74` (its assert message: register by type, or ask the drifter for a flag or a hook).
  Proposed fix: drop the `DrifterType.CHAIN_LIGHTNING` comparison and the `DrifterType` import from the bench. Ask the drifter instead, through a flag or hook on the drifter's own module. I found no existing flag, so one may need adding there. The architect decides whether that is a contract change. The cheapest alternative is to key the cache on the ship for every drifter. That is slower but names no type.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1 failed, 2381 passed with -x; B1) · ui PASS (888 passed in the ui and core run, 183 s)
QA: fail (core)
