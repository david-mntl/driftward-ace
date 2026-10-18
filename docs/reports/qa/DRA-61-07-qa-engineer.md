Verdict: pass
Created by: qa-engineer

1. **Task:** test task `docs/contracts/DRA-61/tasks/DRA-61-07-qa-engineer.md`: the SCORE line tests in `test_hud.py`.
2. **Delivered:** `game/tests/ui/test_hud.py` (five new tests), `game/tests/CONTEXT.md` (the `test_hud.py` entry), this report.
3. **Checks:** `check.sh` ends `QA: pass`; the `ui` step runs 46 tests, 13 in `test_hud.py`. The new tests:
   - `test_hud_score_is_on_line_one_at_the_left_margin`: the whole surface equals the SCORE text blitted at (4, hud_top), six scores, both modes.
   - `test_hud_score_pixels_follow_the_score`: pixels change with the score, repeat for the same score, text grows right.
   - `test_hud_line_two_is_empty_and_the_meters_are_gone`: no ink on line 2 or below with 11 m flown, both modes.
   - `test_hud_score_top_is_the_overlay_bottom_plus_the_gap`: first ink row is `overlay_text_bottom() + HUD_OVERLAY_GAP` plus the text's own ink offset; HUD_TOP in normal mode.
   - `test_hud_earlier_rules_hold_with_score`: with 3 lives and every score: no overlap, gap kept, no jump when the overlay is hidden, above the top line, hearts unchanged, SCORE clear of the hearts.
   No bug found against the code.
4. **Assumptions:** the SCORE text look comes from the contract (default font, 16 px, white, antialiased), so the tests render it with `HUD_FONT_SIZE` (asserted equal to 16) and `score_text` as the reference. The text's own top offset is read from that render, not hard-coded.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The task file stays `Status: open` for close-out.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (1342) · ui PASS (46)
QA: pass
