Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-6-04-ui-developer (debug overlay view), Verify mode, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-6-04-ui-developer.md
3. **Checks:** all inline headless runs from `game/` (`SDL_VIDEODRIVER=dummy`), nothing saved in `game/tests/`.
   - check.sh: `QA: pass`.
   - Acceptance check: 640×480 filled with `ui.look.BACKGROUND`, `draw_debug_overlay(surface, spawn())`. Full-width (0, 255, 0) rows: `[168, 479]`. Rows 167, 169, 478 untouched. Four text bands at the top-left, ink rows 5..12, 17..26, 29..36, 41..50, ink x 4..48. Every text pixel is a green shade (R 0, B 0), 96 pure (0, 255, 0). The draw is byte-identical to a reference built straight from the contract: lines on rows 168 and 479, then `pygame.font.Font(None, 16)` rendering `x 320.00`, `y 240.00`, `vx 0.00`, `vy 0.00` at (4, 4 + i × 12). Image: `/tmp/claude-1000/-workspace/bb96ec7a-9d42-4f32-a24b-9859640cd1af/scratchpad/qa_overlay_spawn.png`.
   - Text values, each byte-identical to the contract reference: negatives (`vx -3.25`, `vy -0.26`), tiny negative vx -0.001 (`vx -0.00`, as the contract's `f"{value:.2f}"` gives), zero and wall positions (`x 0.00`, `x 640.00`, `y 480.00`), fall cap (`vy 5.50`), rounding (0.005 to `0.01`), 1e6 and -1e6, and a ship with `wall` and `at_top_line` set (only x, y, vx, vy shown).
   - Surface width: 800×600 lines span all 800 px on rows 168 and 479, row 599 untouched. 100 px and 1 px wide surfaces: both rows green. 640×100 (floor row off the surface): no error.
   - No fill: on a (10, 20, 30) background, 0 pixels change outside the text box and the two rows.
   - Ship unchanged after the draw (equals a deep copy). Same state drawn twice: identical bytes. 600 ticks of `step` plus draw, run twice with the same inputs: identical SHA-256 over every frame.
   - Font built once: after `cache_clear()` and 200 calls, `hits=199, misses=1`, one object. SRCALPHA surface: line pixel (0, 255, 0, 255). Returns `None`.
   - Imports: `logging`, `functools`, `pygame`, `core.ship`, `core.world`. No `app`. No `ui` import in `game/core/`.
   - Review For QA list: all five lines checked above. Review must-fix count was 0.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The view is ready to be called from `game/app/frame.py` behind `overlay_visible` (contract DRA-6-debug-overlay.md, Rules). Review note 1 (`vx -0.00` after releasing Left) is contract-conforming and stays with the Architect and the Director, as the review routed it.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · core PASS (9 passed) · ui PASS (3 passed)
QA: pass
