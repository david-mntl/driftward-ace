Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/gameplay/DRA-39-01-gameplay-implementer.md` against task `docs/contracts/DRA-39/tasks/DRA-39-01-gameplay-implementer.md`, the parts of `docs/contracts/systems/drifters.md` and `docs/contracts/systems/run.md` it names, the GDD and `CLAUDE.md`. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-39-01-gameplay-implementer.md`.
3. **Checks:** By reading only. I read all six delivered files: `game/core/collision.py`, `game/core/drifters/base.py`, `tuning.py`, `spawner.py`, `meteorite.py` and `game/core/run.py`. I compared them with the Interface and Rules sections the task names, `docs/design/gdd/05-lives-and-damage.md` (rule 1.5, rehit_cooldown 180, rehit_dim 0.75, Edge cases), `docs/design/gdd/07-drifters.md` (rules 12 to 14), `game/CONTEXT.md` and `game/ruff.toml`. I traced the acceptance script's cooldown timeline through `_apply_hit` and `_cool_down` by hand: hits on ticks 60 and 241, `rehit_ticks_left` is 1 after tick 239 and 0 after tick 240, which matches the seven expected lines. I grepped `game/` for `hit_ship`, `default_y`, `Placement(`, `VariantTuning(` and `DrifterTuning(`. Outside tests, nothing uses the removed names. `game/app/` still builds placements and tuning with the new defaults. Nothing was run.
4. **Assumptions:** `tick_warning`'s parameter name (`drifter`, not `obj`) dates from DRA-29, so it is outside this task's DRA-39 delta. I did not check it again.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One note, no action. No must-fix or should-fix.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-39-01-F1 | note | game/core/drifters/meteorite.py:34 | no action |

### DRA-39-01-F1
`return x, -height / 2 if y is None else y` is correct: it parses as `(x, (-height / 2 if y is None else y))`. A reader could still take it as `(x, -height / 2) if ... else y`. Rule: keep names and code plain (`game/CONTEXT.md`, Good practice). Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. F1
9. pass
10. pass

## For QA
- A still rock on a held ship: hits on ticks 60 and 241 only, `brightness()` is 0.75 through the state after tick 239 and 1.0 from tick 240.
- Two hazards touching on one tick: one life lost, both start their cooldown. A hit by a second hazard never restarts a cooling one's count.
- The cooldown counts down on protected ticks, during the respawn wait and on a fall tick. It freezes from the tick after game over.
- A rock placed with its edge touching the left wall from outside (x -14) never enters and is never dropped. A rock that falls on screen is dropped once its top edge reaches y 480.
- `place_hitbox`, `grow_hitbox` and `hitboxes_overlap` raise `TypeError("unknown shape kind '<name>'")`, including when the other hitbox is empty.
