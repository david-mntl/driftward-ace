Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-125-07-ui-developer (stand-in pause box view `draw_pause_box`), started by /implement. Verify mode, after review `Status: reviewed`.
2. **Delivered:** docs/reports/qa/DRA-125-07-ui-developer.md. No test saved (Verify mode). Inline scripts: `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/qa07.py`, `qa07b.py`, `qa07c.py` (same folder).
3. **Checks:**
   - `check.sh`: lint PASS, format PASS, ui PASS (65 passed). `typecheck` and `core` fail, and every failure is in the impact.md "Failures expected" table: 7 mypy errors, all `retry_armed` in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`; 26 core failures (3205 passed) in `test_run.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_run_score.py`, `test_run_waves.py`, `test_coin.py`, cleared by DRA-125-09. Same numbers as the DRA-125-06 round. None is in `game/ui/`. The task's acceptance check allows these failures.
   - Acceptance check reproduced (640 x 480 filled with (128, 128, 128), `draw_pause_box` once, changed pixels read back): the box covers cols 160-479, rows 180-299 (320 x 120), centered on (320, 240); gray inside (83, 83, 83), outside (128, 128, 128), the pixels just outside every edge unchanged; the PAUSE ink covers cols 284-356, rows 230-246, center (320.5, 238.5), within 1.5 px of the box center (font bearings).
   - Exact pixel check: the whole surface equals a reference built in the script (box at `((w - 320) // 2, (h - 120) // 2)` filled (0, 0, 0, 90), `Font(None, 32)` "PAUSE" white antialiased, rect centered on the box center) at 640 x 480, 800 x 600 and 641 x 481.
   - Other sizes: 800 x 600 box cols 240-559, rows 240-359; 641 x 481 box cols 160-479, rows 180-299 (floor division, as the contract says); 320 x 120 box fills the surface. 300 x 100 and 1 x 1 surfaces and a 0 x 0 surface draw with no error.
   - World shows through: on a horizontal color gradient the box pixels still follow the gradient (129, 64, 129 then 130, 64, 129). On an SRCALPHA surface the box pixel is (83, 83, 83, 255).
   - Cache and determinism: two fresh draws are byte-identical; after 10 draws `_box` and `_text` each show 1 miss; the cached box is still (0, 0, 0, 90) and 320 x 120 after drawing, so a draw never alters it. Drawing twice on one surface blends the box twice ((53, 53, 53)); the view has no state and the frame draws it once.
   - Review For QA lines: the three are covered (world visible, other window size centered, cache). The HUD-on-top order is the frame's, at integration.
   - `game/core/` has no change from this task (`git status` shows only DRA-125-01's `run.py`).
4. **Assumptions:** The ink sitting 1.5 px above the box center is the font's ascent room above the capitals, not a bug: the contract centers the text's rect, not its ink.
5. **Documentation differences:** None.
6. **Next:** /implement continues with the next task (DRA-125-08). The frame does not call `draw_pause_box` until integration (Integration Engineer). No open bug.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (7 errors, all `retry_armed`, expected by impact.md, cleared by DRA-125-09) · core FAIL (26 failed, 3205 passed, all expected by impact.md, cleared by DRA-125-09) · ui PASS (65 passed)
QA: fail (typecheck core)
