Status: reviewed
Created by: implementation-reviewer

1. **Task:** review the satellite drifter (task `docs/contracts/DRA-39/tasks/DRA-39-03-gameplay-implementer.md`) from `docs/reports/implementation/gameplay/DRA-39-03-gameplay-implementer.md`, as the `/implement` skill asked.
2. **Delivered:** `docs/reports/review/DRA-39-03-gameplay-implementer.md` (this file).
3. **Checks:** by reading only, against `docs/contracts/systems/drifters.md` (Interface for `base.py`, `satellite.py` and `__init__.py`; Rules, Satellite; Rules, The base: Birth, Start, Warning tilt, Entering, Leaving; the Satellite timeline), `docs/design/gdd/drifters/02-satellite.md`, `CLAUDE.md`, `game/CONTEXT.md`, `game/ruff.toml` and `game/core/ruff.toml`. Files read: `game/core/drifters/satellite.py`, `game/core/drifters/base.py`, `game/core/drifters/__init__.py`, with `spawner.py`, `meteorite.py` and `core/world.py` for context. I worked the five acceptance lines by hand from the code: -18 + 2.4675 = -15.5325; 2.4675 × cos 20° ≈ 2.3187; 2.4675 × sin 20° ≈ 0.8439; x 658 and warning center (622, 200) with `invert`. All match the task. Nothing run.
4. **Assumptions:** the `ui` suite (`tests/ui/test_drifter_registry.py`) now fails until DRA-39-04 and `satellite.json` land, as the contract's Impact table says. The report doesn't claim the `ui` suite, so I don't count it against the report.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One note, no change asked.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-39-03-F1 | note | game/core/drifters/satellite.py:62 | no action |

### DRA-39-03-F1
`Satellite.born` repeats the base's specialty check (`satellite.py:62-64` matches `base.py:299-301`). The contract asks for this override because the base `born` refuses `invert` (Rules, Satellite, Born), and the Decisions explain it. Rule: no duplicated blocks (checklist item 8). Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. Smells: F1
9. pass
10. pass

## For QA
- Flat satellite with no x: starts at x -18 and its warning shows at (18, y). It is not dropped on the tick it turns ACTIVE, only after it has entered and fully passed x 640 (n = 274 at Level 1).
- Angled with `invert`: velocity_x is negative, velocity_y is positive, and the warning tilt is +20. Without `invert` the tilt is -20.
- A placement with no y raises `satellite placement needs y`. A variant with no `SatelliteVariantExtra` raises `satellite variant '<name>' has no angle`. `specialty_enabled=True` raises `satellite has no specialty`.
- `invert=True` with an explicit x keeps that x, and the satellite still flies left.
- Angled at Level 1 from y 300: it drops below the floor first, at n = 221, before it reaches the far wall.
