Status: reviewed
Created by: implementation-reviewer

1. **Task:** review of `docs/reports/implementation/gameplay/DRA-86-01-gameplay-implementer.md` (task `docs/contracts/DRA-86/tasks/DRA-86-01-gameplay-implementer.md`), passed by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-86-01-gameplay-implementer.md` (this file).
3. **Checks:** read `game/core/collision.py` in full against `docs/contracts/systems/drifters.md` (Interface `game/core/collision.py`; Rules, Collision and Push-out; Impact DRA-86 table; Rationale DRA-86 lines), `game/CONTEXT.md` and `game/ruff.toml`. Traced the task's acceptance command by hand: all seven printed lines follow from the code. For example, the placed triangle has positive area sign, so its slope's outward normal is (120, -320) / 341.76 = (0.3511, -0.9363), and the up exit through both boxes is 16.0. Confirmed that `moved` (`game/tests/core/test_collision.py:589`), `anchor` (`:596`) and the guard test (`:691-693`) are the breaks the Impact table lists. Ran nothing.
4. **Assumptions:** no data file is read by this task, so no schema applies. `grow_hitbox` is called only with `GRAZE_MARGIN` (`game/core/drifters/base.py:261`), so a grown polygon's edge lines always have thickness > 0.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. No open findings.
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
- `exit_distance` through chained spans: an L's two boxes, two overlapping islands, and a box sunk into the triangle's slope along the slope normal (the result must leave `deeply_overlaps` False).
- An edge or corner touch: `hitboxes_overlap` False and `deeply_overlaps` False for polygon vs box and polygon vs polygon, in both argument orders.
- `push_directions` for the inverted triangle: 6 directions, the slope normal (0.3511, 0.9363) at index 4, no duplicates of the axis directions (including -0.0 forms).
- `grow_hitbox` on a polygon: 1 + edges shapes, in edge order, and the grown result's overlap with circles near each rounded corner.
- Per-tick cost: `exit_distance` recomputes unit normals (a `hypot` per edge) for every pair and every direction. Worth one look at frame time in the browser once the ship block (DRA-86-03) runs on islands.
