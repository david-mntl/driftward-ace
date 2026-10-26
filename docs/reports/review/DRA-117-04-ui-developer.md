Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-117-04 (GRAZE line on HUD line 2, `graze_text`) against `docs/contracts/systems/hud.md`. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-117-04-ui-developer.md`.
3. **Checks:** Read `docs/reports/implementation/ui/DRA-117-04-ui-developer.md`, `docs/contracts/DRA-117/tasks/DRA-117-04-ui-developer.md`, the hud.md parts the task names, `docs/contracts/DRA-117/impact.md` (expected test failures), `game/core/run.py` (`grazes` field), `game/ui/score_text.py` and `game/ui/hud.py`. Traced `_grouped` by hand for 0, 999, 1000, 1234567: the output matches the contract's examples. Ran nothing.
4. **Assumptions:** The implementer's ink left edge at column 5 (font side bearing) meets "its left at the margin", since the blit origin is `HUD_MARGIN`. I accept that reading.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. No findings.
7. **Status:** done.

## Findings
None.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. pass
9. pass
10. pass

## For QA
- Start a run in normal mode: `GRAZE 0` shows at (4, 24), under SCORE, from the first frame.
- Debug mode: GRAZE sits one HUD line below SCORE, under the overlay's six lines, and does not move when F3 hides the overlay.
- Graze past 999: the line reads `GRAZE 1 000`, grouped like SCORE, and grows right without overlapping the hearts.
- Retry after Game Over: GRAZE reads `GRAZE 0` again; GRAZE stays visible while the Game Over box shows.
- The three `test_hud.py` failures listed in impact.md for DRA-117-04 are expected until DRA-117-07; `test_hud_score_pixels_follow_the_score` was reported passing.
