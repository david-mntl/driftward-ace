Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-125-05-ui-developer (stand-in instructions page view `draw_instructions`), started by /implement. Verify mode, after review `Status: reviewed`.
2. **Delivered:** docs/reports/qa/DRA-125-05-ui-developer.md. No test saved (Verify mode). The PNG of the page is at `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/qa_instr.png`.
3. **Checks:**
   - `check.sh`: lint PASS, format PASS, ui PASS (65 passed). `typecheck` and `core` fail, and every failure is in the impact.md "Failures expected" table (7 `retry_armed` errors in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`; 26 core failures, all in `test_run.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_run_score.py`, `test_run_waves.py`, `test_coin.py`, cleared by DRA-125-09). None is in `game/ui/` and nothing imports `ui.instructions` yet. This task's acceptance check allows these failures.
   - Acceptance check reproduced (640 x 480 filled with `ui.look.BACKGROUND`, `draw_instructions`, ink bands read from `pygame.image.tobytes`). Eight bands: title rows 98-114, centered 320.0; six heading+line blocks at rows 132-158, 172-198, 212-238, 252-278, 292-318, 332-358, centers 319.5 to 320.5; footer rows 457-466, center 320.5. All inside the canvas, none overlapping. Footer top 456 = 480 - 2 x 12 (body linesize).
   - Icons: all six found as 16 x 16, 1-px outlines (hollow inside, all four edges white, clear outside), each ending 3 px (one space, `size(" ")` = 3) before its title's rect, text ink starting 1 px later (font bearing). Same square for all six.
   - Layout from metrics: title linesize 24, body 12. Block height 264, top = (footer_top - 264) // 2: measured 96 at 480 (title ink at 98), 156 at 600, 6 at 300. Matches the contract at 640 x 480, 800 x 600, 1000 x 300 and 320 x 480 (every row's center within 1 px of `width // 2`, footer 2 body lines above the bottom). At 320 wide the long lines exceed the surface; that is clipping of a surface narrower than the page, not a contract rule.
   - Only draws: on a (30, 60, 90) surface the page leaves that color around the text, so no fill.
   - Cache: two fresh draws are byte-identical; 5 more draws add 0 `_render` misses (14 texts, rendered once).
   - Review For QA lines: all four covered above. Review finding F1 is a note with no action (duplicate private helpers with `menu.py`), not a bug.
4. **Assumptions:** Contract wording, not a value, was read for the blank line under the title as one body line (12 px), which is what the code and the contract's "Lines and blank lines" say. Double-drawing on the same surface differs because antialiased text blends on top of itself; that is not a bug (the view has no state), so I compared two fresh draws.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer cannot yet use the page (the frame does not call it until integration); /implement continues with DRA-125-06. No open bug.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (7 errors, all `retry_armed`, expected by impact.md, cleared by DRA-125-09) · core FAIL (26 failed, 3205 passed, all expected by impact.md, cleared by DRA-125-09) · ui PASS (65 passed)
QA: fail (typecheck core)
