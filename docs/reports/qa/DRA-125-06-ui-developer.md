Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-125-06-ui-developer (stand-in leaderboard page view `draw_leaderboard`), started by /implement. Verify mode, after review `Status: reviewed`.
2. **Delivered:** docs/reports/qa/DRA-125-06-ui-developer.md. No test saved (Verify mode). PNG of the page: `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/qa_lb.png`. Inline script: `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/qa_lb.py`.
3. **Checks:**
   - `check.sh`: lint PASS, format PASS, ui PASS (65 passed). `typecheck` and `core` fail, and every failure is in the impact.md "Failures expected" table (26 core failures in `test_run.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_run_score.py`, `test_run_waves.py`, `test_coin.py`, cleared by DRA-125-09; same 26 and 3205 passed as the DRA-125-05 round). None is in `game/ui/`. `mypy --strict game/ui/leaderboard.py` alone: no issues. The task's acceptance check allows these failures.
   - Acceptance check reproduced (640 x 480 filled with `ui.look.BACKGROUND`, `draw_leaderboard`, ink bands read from `pygame.image.tobytes`): title rows 206-222, cols 235-407, center 321.0; "No scores yet." rows 241-250, cols 280-360, center 320.0; footer rows 457-466, cols 227-414, center 320.5. All centered within 1 px (font bearings). The footer bands (rows and cols) are identical to `draw_instructions`' footer.
   - Layout from metrics: title linesize 24, body 12. Expected top = (footer_top - (24 + 2 x 12)) // 2 = 204 at 480 high (title ink at 206, empty line top 240, ink 241), footer top 456 = 480 - 2 x 12. Block bottom 252 is above the footer top 456.
   - Other sizes: 800 x 600 (centers 401.0, 400.0, 400.5; footer same as instructions), 1000 x 300 (501.0, 500.0, 500.5; footer same), 321 x 481 (161.0, 160.0, 160.5; footer same). Block ends above the footer in all. At 640 x 200 the footer differs from the instructions page only because the instructions block no longer fits; the leaderboard block still sits above its footer.
   - Only draws: on a (30, 60, 90) surface the corner and the margin keep that color, so no fill.
   - Cache and determinism: two fresh draws are byte-identical; first draw 3 misses, the next draw 3 hits and 0 new misses.
   - Imports: `ui/leaderboard.py` imports `logging`, `functools`, `typing`, `pygame`, `ui.screen_look`. After import and draw no `core` or `app` module is in `sys.modules`.
   - Review For QA lines: all four covered. Finding F1 is a note with no action (duplicate private helpers), not a bug.
4. **Assumptions:** The block's bottom is the empty-list line's `get_linesize()`, as the instructions page counts its last line. I did not test double-drawing onto one surface (antialiased edges blend twice; the view has no state).
5. **Documentation differences:** None.
6. **Next:** /implement continues with the next task. The frame does not call `draw_leaderboard` until integration (Integration Engineer). No open bug.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (7 errors, all `retry_armed`, expected by impact.md, cleared by DRA-125-09) · core FAIL (26 failed, 3205 passed, all expected by impact.md, cleared by DRA-125-09) · ui PASS (65 passed)
QA: fail (typecheck core)
