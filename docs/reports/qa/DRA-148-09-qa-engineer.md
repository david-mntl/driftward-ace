Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-148-09 (level-up motion and HUD pop tests), started by the Director's pipeline.
2. **Delivered:**
   - `game/tests/ui/test_level_up_motion.py` (new, 66 tests)
   - `game/tests/ui/test_hud_level_up.py` (new, 36 tests)
   - `game/tests/CONTEXT.md` (changed: one paragraph for each new file)
3. **Checks:** `check.sh ui -k "hud_level_up or level_up_motion"`: 102 passed. ruff check and format pass on both files. `mypy --strict` has no error in either file. Mutation checks on a scratch copy of `game/` (the copy is deleted): showing the old level after the arrival, no pop scale, no box flash, no bar flash, a bump that never returns to 0, a bump that overshoots its pixels, lines closing with the glass, a flight that ends one tick late, and a `smoothscale` added to the pop draw were each caught by a named test. Four more mutations (an off-by-one at `bump.ticks`, `pop.ticks` and `fall_end`, and the no-look guard in `_active_pop`) give the same result as the original code, so no test can tell them apart. Full `check.sh`: `QA: fail (typecheck ui)`, both from one existing test outside this task, see Bugs B1.
4. **Assumptions:**
   - The task says `fall_offset` is "above the resting place before" the landing. The contract (view.md, `fall_offset`) has the number overshoot `fall_overshoot_px` past its place before it eases back to 0. The tests follow the contract: `-distance_px` up to `fall_start`, 0 exactly from `fall_end`, an overshoot of at most `fall_overshoot_px` in between, and above the place right after the fall starts.
   - The curves between the contract's end points (smoothstep, ease-out) are the Architect's choice (task DRA-148-03), so the tests check only direction, bounds and the end points.
   - The look is written in the test files with values that obey the schema and differ from `level_up.json`, so no tuning number is copied. The test look uses `box_corner_cut` 8, which the schema says must equal the panel art's cut.
5. **Documentation differences:** One, pending Director approval. The task line for `fall_offset` ("above the resting place before it") is looser than the contract's overshoot rule (view.md, Interface, `fall_offset`). Proposed change to the task text: "-distance_px up to `fall_start`, exactly 0 from the landing tick, and no further below the resting place than `fall_overshoot_px` before it". Also see B1: `impact.md`, section "Failures expected until each task lands", lists none, but one existing test breaks.
6. **Next:** Architect and Director, see B1. My two new test files pass and the acceptance check cannot reach `QA: pass` until `game/tests/ui/test_window_view.py` follows the `frame._draw` change. Owner of the fix is QA Engineer, but the task forbids editing other test files. Integration Engineer runs the browser build after the harness passes.
7. **Status:** blocked on B1. Everything that does not depend on it is done.

## Bugs
- **B1** `game/tests/ui/test_window_view.py:59`, owner: QA Engineer (the test file), cause in `game/app/frame.py:336` (Integration Engineer's file, working tree change, not committed). Reproduce: `game/tests/check.sh ui -k test_window_view` and `game/tests/check.sh typecheck`.
  Expected: no existing test changes result (impact.md, Failures expected: "none"; the app's change is listed as the Integration Engineer's, and the old callers must still work).
  Actual: `frame._draw` gained a required last parameter `level_up_view: LevelUpView`. The test's `draw` calls `frame._draw(...)` with 9 arguments and raises `TypeError: _draw() missing 1 required positional argument: 'level_up_view'`. Nine tests fail: `test_the_menu_pages_fill_the_whole_window` (3), `test_the_run_screens_fill_the_whole_window` (3), `test_pause_and_game_over_dim_the_panel_too`, `test_the_menu_pages_show_no_panel_and_no_frame`, `test_the_overlay_and_the_panel_never_share_a_pixel`. `mypy --strict` reports `test_window_view.py:59: Missing positional argument "level_up_view"`.
  Source of the expected value: `docs/contracts/DRA-148/impact.md` (the `test_window_view.py` caller of `frame._draw` is not in the table at all); `game/tests/CONTEXT.md`, Rules (never edit other test files outside a task).
  Proposed fix (a contract and task change, not a game code change): the Architect adds `game/tests/ui/test_window_view.py` to impact.md (it calls the app's `_draw` and `_build_level_up_view`) and gives QA a task, or extends DRA-148-09's `Builds`, to change the test's `draw`: build a `LevelUpView` (`app.frame._build_level_up_view(rules, look, hud)` with the loaded look, or the view the app builds) once in `__init__`, and pass it as the last argument. The tests then keep checking the whole-window draw with the new signature. If the Director prefers, the Integration Engineer's change gives `level_up_view` a default; that is a game code change and is the Director's call.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (B1, one error in `test_window_view.py`) · core PASS · ui FAIL (B1, 9 tests in `test_window_view.py`; 879 pass, including the 102 new ones)
QA: fail (typecheck ui)

## Round 2 2026-11-06

1. **Task:** Re-test of DRA-148-09 B1 after the Integration Engineer made `level_up_view` optional (default None) in `frame._draw` and `_draw_run`, started by the Director's pipeline.
2. **Delivered:** this appended round in `docs/reports/qa/DRA-148-09-qa-engineer.md`. No test or game file changed.
3. **Checks:** full `game/tests/check.sh`: 888 passed, `QA: pass`. `test_window_view.py` passes all 11 tests and `typecheck` passes, so B1 is gone. `test_hud_level_up.py` (36) and `test_level_up_motion.py` (66) still pass: 102 of 102. The main session's `band.alpha` 0 in `game/tuning/level_up.json` has no effect, since the tests build their own looks.
4. **Assumptions:** none.
5. **Documentation differences:** The Round 1 point about the task wording for `fall_offset` still stands, pending Director approval. B1's contract gap (`test_window_view.py` missing from impact.md) no longer blocks, because the default parameter keeps the old call working.
6. **Next:** Integration Engineer, browser build. Optional for the Architect: the `fall_offset` task wording from Round 1.
7. **Status:** done.

## Bugs
- **B1** fixed. `check.sh ui -k test_window_view` passes (11 tests) and `typecheck` passes.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (888 passed in the full run)
QA: pass
