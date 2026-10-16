Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the line shape in `draw_shape`, from `docs/reports/implementation/ui/DRA-47-04-ui-developer.md` (task `docs/contracts/DRA-47/tasks/DRA-47-04-ui-developer.md`), asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-47-04-ui-developer.md`.
3. **Checks:** Read `game/ui/shapes.py` (146 lines) against `docs/contracts/systems/drifters.md` (Interface, `game/core/collision.py` `Line` and `game/ui/shapes.py`; Presentation, Line shape and Rules for every view), `docs/design/gdd/07-drifters.md` rule 8, `game/CONTEXT.md`, `game/ruff.toml` and `game/tests/check.sh`. Traced the acceptance command by hand against the code: the filled band covers y 47..53 and x 17..83, the outline's sides fall on y 47 and 53 and the arc at A reaches x 17. All three printed lines match. Nothing run.
4. **Assumptions:** The contract defines `width` 0 and 1 only. I read any other width as undefined, not as a break (see F1).
5. **Documentation differences:** None.
6. **Next:** QA Engineer, for `docs/reports/review/DRA-47-04-ui-developer.md`. Open findings: 0 must-fix, 0 should-fix, 1 note (no action).
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-47-04-F1 | note | game/ui/shapes.py:82 | no action |

### DRA-47-04-F1
`_draw_line` draws the 1 px outline for any non-zero `width`, while circles and boxes pass `width` straight to pygame, so a width of 3 would give a 3 px circle ring but a 1 px line outline. The contract (Interface, `game/ui/shapes.py`) defines only 0 and 1, every current caller passes 0 or 1, and the implementer states it under Assumptions. Change: none.

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
- A diagonal line (for example 45 degrees), filled: the band is solid along its length with round ends and no gap at the polygon-to-disc join.
- A line with A equal to B: filled gives one disc of radius `round(t / 2)`; outline gives a 1 px ring, no crash (no divide by zero).
- Debug overlay on a firing chain lightning: the arc hitbox and its graze zone show as hollow outlines with both long sides and round outer ends.
- `draw_shape` with a non-shape object raises `TypeError("unknown shape kind '<class name>'")`.
- A line whose thickness rounds to radius 0 (thickness below 1): confirm nothing raises.
