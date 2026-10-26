Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-117-01 (graze margin, graze state and per-drifter graze zone on the drifter base) against its task file and contract. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-117-01-gameplay-implementer.md`. Code reviewed: `game/core/drifters/base.py`, `game/core/drifters/tuning.py`, `game/core/drifters/spawner.py`.
3. **Checks:** Read against `systems/drifters/shared/base-interface.md` (Interface, closing paragraph), `base.md` (Values, Graze zone, Graze state), `spawner-registry-tuning.md` (HazardRules, Spawner step 8, Tuning files), `rationale.md` (DRA-117 bullets), 06-scoring.md (graze_margin 14, locked) and scope report DRA-117, Limits. Grep of `game/core/drifters`: every subclass `born` goes through `born_drifter`, so `graze_margin` reaches every drifter; no subclass overrides `graze_zone` or touches `graze_state`. Nothing run.
4. **Assumptions:** The order of `GrazeState` before `TouchEffect` in `base.py` is not part of the Interface; the contract lists names and fields, not class order.
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
- A meteorite spawned with `HazardRules(graze_margin=30)`: its ACTIVE graze zone radius is the hitbox radius + 30.
- Default `HazardRules()`: every existing graze-zone test (meteorite, satellite, chain lightning, electric ball, collision) keeps its result.
- A drifter that goes through a subclass `born` (satellite, chain lightning, UFO, electric ball) carries the tuned `graze_margin`, not the constant.
- WARNING hazards, coins and floating islands: `graze_zone()` is `()`, `graze_state` stays OUTSIDE.
- `graze_state` survives an `update` unchanged (each subclass uses `replace`).
