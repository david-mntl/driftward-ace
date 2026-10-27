Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-126-05-ui-developer (leaderboard rows in four aligned columns), started by /implement (Verify mode).
2. **Delivered:** docs/reports/qa/DRA-126-05-ui-developer.md. No test files (Verify saves none). Inline scripts, not in the repo: `/tmp/claude-1000/-workspace/306b4d78-3a59-4da7-966c-22967ac5773e/scratchpad/qa05.py` and `qa05b.py` (run with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 <script>` from `/workspace/game`).
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and ui (89) pass. `core` has 1 failure of 3288: `test_game_flow.py::test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first`, the one failure `docs/contracts/DRA-126/impact.md` expects until DRA-126-07 (Failures expected table). It is not in the task's file. Nothing else fails.
   - Acceptance check, empty page: `draw_leaderboard(surface)`, `draw_leaderboard(surface, [])` and the HEAD module's `draw_leaderboard(surface)` give identical pixels at 640 x 480, 800 x 600, 1024 x 768 and 333 x 271.
   - Acceptance check, filled pages: I wrote the layout again in the script from the contract alone (cells at the body size, each column as wide as its widest cell, 24 px gaps, table centered with `(width - table) // 2`, place and score right-aligned, nickname and level left-aligned, tops 24 apart, block centered above the footer, footer as on the instructions page). 150 random entry lists (1 to 10 rows, nicknames of 1 to 10 characters from the whole `NICKNAME_CHARACTERS` set, leading blanks, scores 0 to 12 digits, levels 1 to 8) on 640 x 480, 800 x 600 and 641 x 481: 450 draws, 0 pixel differences from the reference.
   - Widest case: ten rows of `WWWWWWWWWW`, 999 999 999, LV 8: table 276 px wide in 640, ink from x 183 to 457.
   - Rows' tops for 1 to 10 rows: last row's bottom and footer's top leave the block centered above the footer (first ink 206 for 1 row down to 98 for 10 rows, footer ink starts at 457 every time).
   - Footer band (the two body lines above the bottom) is pixel-identical on the filled page and the instructions page.
   - Leading blank in a nickname (` A`): the blank counts in the cell, columns still line up (matches the reference). More than ten entries (11, 15) draw without error, one row each. A 41-digit score draws without error (ink 114 to 524 in 640).
   - Same entries drawn twice: same bytes. A list and a tuple draw the same. The entries list is unchanged after the draw.
   - Cache: with `screen_font` wrapped to count renders, 5 draws of ten rows render 24 texts, 25 draws still 24. No log record at DEBUG from a draw.
4. **Assumptions:** The one core failure is treated as expected, as in the DRA-126-04 report, because `impact.md` names it and DRA-126-07 clears it.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. After DRA-126-07, `check.sh` should end `QA: pass`.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1, the one `impact.md` expects until DRA-126-07) · ui PASS (89)
QA: fail (core)
