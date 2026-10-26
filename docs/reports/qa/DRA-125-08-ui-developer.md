Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-125-08-ui-developer (game-over screen in `game/ui/game_over.py`: box, title, score line, RETRY and MENU with the marker), started by /implement. Verify mode, after review `Status: reviewed` with no findings.
2. **Delivered:** docs/reports/qa/DRA-125-08-ui-developer.md. No test saved (Verify mode). Inline script: `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/qa08.py`.
3. **Checks:**
   - `check.sh`: env, lint and format PASS. `typecheck` fails with 7 errors, all `retry_armed` in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`. `core` fails with 26 failed, 3205 passed, in `test_run.py` (6), `test_run_drifters.py` (4), `test_run_graze.py` (3), `test_run_score.py` (5), `test_run_waves.py` (6), `test_coin.py` (2). `ui` fails with 3 failed, 62 passed: `test_game_over_with_score_shows_three_centered_lines_in_the_box`, `test_game_over_only_the_score_line_changes_with_the_score`, `test_game_over_alone_leaves_the_score_line_place_empty`. All of these are in the impact.md "Failures expected" table (DRA-125-09 and DRA-125-11 clear them), and the task's acceptance check allows them. The numbers are the same as in the DRA-125-07 round and the implementation report. None is a bug in `game/ui/game_over.py`.
   - Acceptance check reproduced with my own script on a 640 x 480 surface filled (128, 128, 128). The box covers cols 160-479, rows 160-319 (320 x 160), centered on (320, 240). Pixel inside the box is (83, 83, 83); the pixels just outside each edge are (128, 128, 128). The whole surface equals a reference built in the script from the contract's layout (box at `((w - 320) // 2, (h - 160) // 2)`, the title and body fonts' `get_linesize()`, block = title line + 2 x body line + body `get_height()` centered in the box, marker right edge one `size(" ")` left of the label), for `draw_game_over` + `draw_final_score` + `draw_game_over_choices` at 640 x 480, 800 x 600, 641 x 481, 320 x 160 and 300 x 100, with scores 0, 1234, 10**12 and 10**30, and both selections. No mismatch.
   - `draw_game_over` alone equals the reference with the title only (no score, no labels, no marker) at all five sizes.
   - Review **For QA**, line 1: on black, each function drawn alone puts its ink where the full draw has it. The byte-wise max of the three single draws equals the full draw, 0 differing bytes, at all five sizes.
   - **For QA**, line 2: RETRY against MENU selection differs only in cols 292-300, left of both labels (RETRY label starts at 302, MENU label at 305). The RETRY label (cols 302-338) and the MENU label (cols 305-334) are pixel-identical in both runs.
   - **For QA**, line 3: score 10**12 draws centered (rect 250-390, no error). 10**30 draws centered too (rect 184-457, width 273, inside the 320 box). No error on an SRCALPHA surface or a 0 x 0 surface.
   - **For QA**, line 4: after 20 frames of all three draws with both selections, `_score_line` 1 miss, `_box` 1 miss, `_title` 1 miss, `_label` 3 misses (RETRY, MENU, marker). A new score 78 makes a second `_score_line` miss; going back to 77 renders again (cache holds the last score only, as the contract says).
   - **For QA**, line 5: 800 x 600 box and lines re-center (covered by the pixel equality above). 641 x 481 uses floor division.
   - Determinism: the same draws twice give identical bytes. Drawing never alters the cached surfaces.
   - Values: `BOX_SIZE` (320, 160), `TITLE_TEXT` "GAME OVER", `RETRY_TEXT` "RETRY", `MENU_TEXT` "MENU", `PROMPT_TEXT` gone; `GameOverChoice` members in order RETRY, MENU. No other `game/` file imports a removed name.
   - `game/core/` has no change from this task (`git diff` shows only DRA-125-01's `run.py`).
4. **Assumptions:** None beyond the contract. The ink sits slightly off the box's vertical middle by the fonts' bearings; the contract centers the block by font line heights, not by ink.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer for this task once the queue's remaining tasks are done. `draw_game_over_choices` is not called by the frame until integration. DRA-125-11 (QA Engineer) clears the 3 `test_game_over.py` failures. No open bug.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (7 errors, all `retry_armed`, expected by impact.md, cleared by DRA-125-09) · core FAIL (26 failed, 3205 passed, all expected by impact.md, cleared by DRA-125-09) · ui FAIL (3 failed, 62 passed, the three `test_game_over.py` tests expected by impact.md, cleared by DRA-125-11)
QA: fail (typecheck core ui)
