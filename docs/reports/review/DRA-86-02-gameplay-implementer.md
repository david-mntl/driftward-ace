Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-86-02 (the floating island drifter, `DrifterType.FLOATING_ISLAND`, `TouchEffect.BLOCK`) against `docs/contracts/systems/drifters.md`, asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-86-02-gameplay-implementer.md`.
3. **Checks:** By reading only. Compared `game/core/drifters/base.py`, `game/core/drifters/floating_island.py` and `game/core/drifters/__init__.py` with the contract's Interface (`base.py`, `floating_island.py`, `__init__.py`), Rules (The base: Parked and moving, Block; Spawner, parked rule; Floating island; Tuning files, the island's file; Logging), the Diagram's island shapes and timeline, `drifters/05-floating-islands.md`, `game/CONTEXT.md` and `game/ruff.toml`. Worked the acceptance check's seven lines by hand from the code: all seven match the task's expected output.
4. **Assumptions:** The ruff, mypy and test results in the implementation report are taken as reported; QA runs them. The first `match` in `game/core/` (`island_hitbox`) has no wildcard case; with a `return` in every case over an exhaustive enum, neither ruff's RET503 nor mypy should flag it, which agrees with the reported clean `ruff check` and typecheck.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. The implementer notes a stale docstring in `game/core/drifters/spawner.py` (`spawn_drifter`, "or ACTIVE for the coin"), outside this task's files; not a finding here.
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
- Inverted L, T and triangle hitboxes: check each box's `cy` and the triangle's points against the contract's Diagram, Floating island (bar on top for the L, bar at the bottom for the T).
- `invert` on `rectangle` and `box` raises `floating_island variant '<name>' has no invert`; a placement `speed` raises `floating_island has no speed`; a missing x raises `floating_island placement needs x`.
- Island timeline: y −60 at birth, +`scroll_step_px` per ACTIVE tick, x never changes, still at Level 8 (speed 0.0).
- `graze_zone()` is `()`, `collect_points()` is 0 and `collect_popup()` is None for every variant.
- `born` check order: a placement that has both a missing variant extra and `invert` reports the shape error first.
