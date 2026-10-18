Verdict: pass
Created by: qa-engineer

1. **Task:** test task `docs/contracts/DRA-61/tasks/DRA-61-05-qa-engineer.md`: tests for `score_text`, the Game Over box with and without its score line, and the two reworded HUD tests.
2. **Delivered:** `game/tests/ui/test_score_text.py` (new, 3 tests); `game/tests/ui/test_game_over.py` (new, 3 tests); `game/tests/ui/test_hud.py` (two tests reworded); `game/tests/CONTEXT.md` (three bullets).
3. **Checks:** `game/tests/check.sh` ends `QA: pass`; the `ui` step shows `test_game_over.py`, `test_hud.py` and `test_score_text.py` (41 ui tests pass, 1342 core). One test per `## Test` line:
   - `score_text`: the four scope-report examples, groups of zeros (`1 000`, `1 000 007`, `1 000 000`, `10 000`, `100 000`), a 30-digit number.
   - `draw_game_over` + `draw_final_score`: three bands of ink in the box, centered within 2 px, in order, the middle one the ink size of `score_text` rendered at 16 px, for scores 0, 999, 1234 and 1234567.
   - Only the score line's rows change between score 0 and 1234567; title and prompt bands are identical.
   - `draw_game_over` alone: two bands, the same title and prompt bands as with the score line, no ink between them.
   - HUD normal mode: ink at or right of `HUD_MARGIN` (4) and at or below `HUD_TOP` (4). Replaces `test_hud_normal_layout_leaves_line_one_empty`.
   - HUD debug mode: first ink at or below `overlay_text_bottom() + HUD_OVERLAY_GAP`. Replaces the line-2 offset in `test_hud_keeps_the_gap_below_the_overlay`.
   All pass against the current code; no code change was needed.
4. **Assumptions:** The Game Over tests draw on black so the 35% black box adds no ink. The score line's text is checked by its ink size against the same font at 16 px (the contract's `SCORE_FONT_SIZE`), not by position constants. Centering tolerance is 2 px for glyph side bearings. The reworded HUD test keeps the name idea but is renamed `test_hud_normal_layout_starts_inside_the_margin_and_top`. The two reworded tests should still pass once task DRA-61-06 puts SCORE on line 1: they only bound the first ink, not line 2.
5. **Documentation differences:** None.
6. **Next:** Architect / the lane's next step (DRA-61-06, UI Developer). No bugs open.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (includes `test_score_text.py`, `test_game_over.py`, `test_hud.py`)
QA: pass
