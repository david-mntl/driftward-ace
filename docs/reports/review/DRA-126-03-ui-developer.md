Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-126-03 (`group_digits`, `best_text`, `BEST_LABEL` in `game/ui/score_text.py`; BEST on HUD line 1 in `game/ui/hud.py`), built by the UI Developer from `docs/contracts/systems/hud.md`. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-126-03-ui-developer.md`.
3. **Checks:** By reading only. I compared both files in full with the contract parts the task names: Interface (DRA-126 block), Presentation (`flow.best` row, `group_digits` and `best_text`, BEST line, SCORE line, Both), Rules (BEST items, corner-warning override) and Rationale (`best` default, `group_digits` public). I checked `HUD_BEST_X = 200` against scope report DRA-126, Values needed; 10-ui.md, hud_best and rule 2; `docs/contracts/DRA-126/impact.md`; and the repo for leftover callers of the old `_grouped` (none). The draw script and the four PNGs the report names exist in the scratchpad. Nothing was run.
4. **Assumptions:** The 1 px gap between `HUD_BEST_X` and the BEST ink's left column is the font's side bearing, as the report says; the blit origin in `hud.py:82` is exactly (`HUD_BEST_X`, `hud_top`), which is what the contract sets.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. No findings. The `core` check has one expected failure until DRA-126-07 (`impact.md`).
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
- The BEST ink starts at x 201, not 200: the "B" glyph has a 1 px left bearing. A test of the left edge must check the blit origin or allow that 1 px.
- `draw_hud(surface, run, below_overlay)` with no `best` must draw exactly what it drew before DRA-126: no ink right of SCORE on line 1.
- With `below_overlay` True, BEST moves down with SCORE and stays clear of the overlay's text.
- Change `best` between draws (None, 2345, 1000007): the BEST text follows, and SCORE's cache is not disturbed.
- `group_digits(0)`, `(999)`, `(1000)`, `(1000007)` give `0`, `999`, `1 000`, `1 000 007`; `score_text` and `graze_text` output is unchanged.
