Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the line shape in collision (`docs/reports/implementation/gameplay/DRA-47-01-gameplay-implementer.md`), asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-47-01-gameplay-implementer.md` (this file).
3. **Checks:** Read `game/core/collision.py` (all of it) against `docs/contracts/systems/drifters.md` (Interface, `game/core/collision.py`; Rules, Collision; Rationale, "The line is a capsule, measured squared"), the task file, `docs/design/gdd/07-drifters.md` rule 8, `docs/design/gdd/91-decision-log.md` rows 47 and 60, `game/CONTEXT.md` and `game/ruff.toml`. Worked the task's acceptance cases by hand against the code: all four lines match the expected output. Ran nothing.
4. **Assumptions:** The longest new line (`collision.py:225`) is exactly 100 characters, so it fits `line-length = 100`.
5. **Documentation differences:** None.
6. **Next:** Gameplay Implementer, Review fix mode: one should-fix (F1). No must-fix.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-47-01-F1 | should-fix | game/core/collision.py:256 | fixed |

### DRA-47-01-F1
`_point_box_dist_sq` (`collision.py:256-262`) repeats the nearest-box-point step of `_circle_box_overlap` (`collision.py:180-184`) line for line. The two copies even spell "half" two ways: `/ 2` at 175 and 180-181, `* _HALF` at 258-259 and 267-270. If one copy changes later (an edge rule, a rounding fix), circle/box and line/box drift apart with no test pointing at it. The Decisions note keeps the circle/box code untouched, but this file is the task's only build target, and `x / 2` and `x * 0.5` give the same float, so the result can't change.
Rule: no duplicated blocks (checklist 8); keep functions short, follow one style in a file. Source: `game/CONTEXT.md`, Good practice.
Change: make `_circle_box_overlap` return `_point_box_dist_sq((circle.cx, circle.cy), box) < circle.r * circle.r`, and halve sizes one way across the file (either `/ 2` everywhere or `_HALF` everywhere).

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. Smells: DRA-47-01-F1
9. pass
10. pass

## For QA
- Line against circle, line, box: swap the arguments and confirm the same result every time (Rules: order never matters).
- A line whose A equals B: it must act exactly like a circle of radius `thickness / 2`, including the strict touch case.
- A line lying exactly along a box edge, and a line touching only a box corner: both must overlap.
- Collinear lines: overlapping, end-to-end touching (overlap), and gapped by exactly `h1 + h2` (no overlap).
- `grow_hitbox` on a line, then the graze test: a circle at exactly the grown reach past a round end must not overlap.

## Re-check 2026-10-16
1. **Task:** Re-check the answer to DRA-47-01-F1 (`## Review fix 2026-10-16` in `docs/reports/implementation/gameplay/DRA-47-01-gameplay-implementer.md`), asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-47-01-gameplay-implementer.md` (line 1, findings table, this section).
3. **Checks:** Read the changed code in `game/core/collision.py`: `_circle_box_overlap` (175-177), `_line_overlaps` (180-195), `_point_box_dist_sq` (249-255), `_box_corners` (258-264). Grep for `_HALF`, `Final` and `* 0.5`: no hits. Every halving is `/ 2`. The circle/box test is the same clamp and the same strict `< r * r` as before, so results can't change. Ran nothing.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, `docs/reports/review/DRA-47-01-gameplay-implementer.md`. No open findings.
7. **Status:** done.

- DRA-47-01-F1: fixed. `game/core/collision.py:177` returns `_point_box_dist_sq((circle.cx, circle.cy), box) < circle.r * circle.r`; `_HALF` and the `Final` import are gone, and the file halves with `/ 2` throughout (172, 184, 191, 251-252, 260-263).
