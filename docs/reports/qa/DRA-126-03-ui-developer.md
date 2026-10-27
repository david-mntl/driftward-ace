Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-126-03-ui-developer (`group_digits`, `best_text`, `BEST_LABEL`, BEST on HUD line 1), started by /implement (Verify mode).
2. **Delivered:** docs/reports/qa/DRA-126-03-ui-developer.md. No test files (Verify saves none). Inline script, not in the repo: `/tmp/claude-1000/-workspace/306b4d78-3a59-4da7-966c-22967ac5773e/scratchpad/qa126_03.py`.
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and ui (89 tests) pass. `core` has 1 failure of 3288: `test_game_flow.py::test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first`. It is the one failure `docs/contracts/DRA-126/impact.md` expects (cleared by DRA-126-07), in core, not in the task's files. So the task meets its Acceptance check on the harness.
   - Acceptance check reproduced (run `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=/workspace/game python3 <script>`): `group_digits` for 0, 999, 1000, 1234, 1000007 gives `0`, `999`, `1 000`, `1 234`, `1 000 007`; `best_text` gives `BEST 0`, `BEST 999`, `BEST 1 000`, `BEST 1 234`, `BEST 1 000 007`. `score_text(1234)` is `SCORE 1 234` and `graze_text(1234)` is `GRAZE 1 234`, unchanged.
   - BEST pixels on 640 x 480, `below_overlay` False and True, for `best` 0, 2345, 1000007 and 10^12: the whole surface equals the `best=None` HUD plus one lone blit of `best_text` in the 16 px default font at (200, 4) and at (200, 80) (overlay bottom 76 + gap 4). So the origin is exactly (`HUD_BEST_X`, `hud_top`), its rows are SCORE's rows (ink top at 5 in normal mode), and it moves with SCORE. The ink's first column is 201: the 1 px bearing of "B". On an 800 x 600 surface the BEST ink also starts at x 201 (the x does not follow the width).
   - Old call `draw_hud(surface, run, below_overlay)` equals `best=None` byte for byte in both modes: no ink right of SCORE.
   - Grouping limits: 0, 1, 9, 10, 99, 100, 999, 1000, 9999, 10000, 99999, 100000, 999999, 10^6, 1000007, 10^30 and a 20-digit number: stripping spaces gives the digits back, every group after the first has 3 digits, the first has 1 to 3.
   - Cache: with `best` cycling 11111, 11111, 11111, 22222, 22222, 11111, BEST rendered 3 times (on each change only). Switching `best` (None, 2345, 1000007, 2345, None, 0) with two scores (0 and 5000) and drawing each twice gave identical bytes: SCORE and GRAZE are not disturbed.
   - A score of 10^9 leaves BEST at x 201 (SCORE overlaps it, as the contract allows: stays with UI-01).
   - Same state drawn twice: identical bytes.
4. **Assumptions:** `HUD_BEST_X` 200 is taken from the implementation report and scope report DRA-126, Values needed; the contract's Interface gives the name only.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer can pick this task up (DRA-126-04 and -05 are separate tasks). The `core` failure above stays until DRA-126-07.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1, the one `impact.md` expects until DRA-126-07) · ui PASS (89)
QA: fail (core)
