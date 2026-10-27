Status: reviewed
Created by: implementation-reviewer

1. **Task:** review DRA-126-05 (UI Developer, leaderboard rows in four columns), asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-126-05-ui-developer.md`.
3. **Checks:** read `game/ui/leaderboard.py` against `docs/contracts/systems/game-flow.md` (Interface, the DRA-126 `ui/leaderboard.py` block; Presentation, shared items and Leaderboard page), `docs/contracts/systems/saves.md` (`ScoreEntry`), `group_digits` in `game/ui/score_text.py`, scope report DRA-126 (Values needed, Leaderboard rows), `docs/reports/DRA-126-away-log.md` (Decisions, 5), `docs/contracts/DRA-126/impact.md` and `game/CONTEXT.md`. Ran nothing.
4. **Assumptions:** none.
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
7. n/a
8. pass
9. pass
10. pass

## For QA
- `draw_leaderboard(surface)` and `draw_leaderboard(surface, ())` against the DRA-125 page: pixel for pixel the same.
- Ten entries with a 10-character nickname and score 999 999 999: the table stays inside 640 px, place and score right edges and nickname and level left edges line up on every row.
- A nickname with a leading or trailing blank: the blank counts in the cell's width and the columns still line up.
- Footer on the filled page sits on the same rows as on the instructions page.
- Drawing the same entries on many frames renders each cell text once (the `_render` cache), never per frame.
