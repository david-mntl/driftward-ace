Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-61-06-ui-developer (the SCORE line in `game/ui/hud.py`, line 2 empty), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-61-06-ui-developer.md
3. **Checks:**
   - `game/tests/check.sh`: all steps PASS, ends `QA: pass` (core 1342 passed, ui 41 passed).
   - Acceptance check run unchanged: prints `True True True` (all ink at x >= 4, y >= 4, y < 24; nothing on line 2).
   - Pixel compare: for scores 11, 1 010, 1 000 010, 1 000 011, a 31-digit score and 0 lives, `draw_hud` output equals a reference built from `Font(None, 16).render(score_text(run.score), True, white)` at (4, 4) plus the hearts. Identical bytes every time.
   - Group boundaries: score 999, 1000, 999999, 1000000 and 0 (coin points on a fresh scroll) draw `SCORE 999`, `SCORE 1 000`, `SCORE 999 999`, `SCORE 1 000 000`, `SCORE 0`, each on the same frame, same pixels as the reference.
   - Line 2 (rows 24 to 47, left of the hearts): no ink in any case.
   - Debug mode (`below_overlay=True`): first HUD ink row 57, left column 4. `overlay_text_bottom()` + `HUD_OVERLAY_GAP` = 56, so the ink is at or below it. Hearts unchanged between modes.
   - Cache: same score twice returns the same surface (`lru_cache` hits grow, `currsize` 1); a different score returns a new surface; going back to 0 re-renders.
   - 40-digit score: text is 343 px wide, ends at x 347, left of the hearts at x 544.
   - Surface 800 x 300: hearts end 8 px from the right edge (rightmost ink x 791).
   - `Run` state identical before and after `draw_hud` (`dataclasses.asdict`). Two draws of the same run give identical images.
   - Grep of `game/ui/hud.py` for sleep, threading, asyncio, display, event, key, image.load, mixer, random, mp3, wav: no hits. No ui import in `game/core/`.
   - `game/app/frame.py` `_draw` passes `below_overlay=debug`, not `overlay_visible`, so F3 does not move SCORE.
   - Game Over box and HUD both build the text with `score_text`, so they match by construction.
   - Review For QA lines: all covered above. No must-fix findings in the review.
   - No bugs found.
4. **Assumptions:** Scores were set with `dataclasses.replace(run, coin_points=...)`, as in `core/test_run_score.py`. Retry-to-0 was checked on the HUD side (score 0 draws `SCORE 0` after a higher score); the core reset is covered by `test_run_score.py`.
5. **Documentation differences:** None.
6. **Next:** Implementation is clear. Task DRA-61-07-qa-engineer (the exact SCORE line tests) can start. On the whole feature, the Integration Engineer takes the browser run once the Architect's remaining DRA-61 QA tasks are done.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
