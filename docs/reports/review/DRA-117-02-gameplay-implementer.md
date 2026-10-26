Status: reviewed
Created by: implementation-reviewer

1. **Task:** review DRA-117-02 (Linear DRA-119), the graze rule in core, from `docs/reports/implementation/gameplay/DRA-117-02-gameplay-implementer.md`, asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-117-02-gameplay-implementer.md`.
3. **Checks:** read `game/core/graze.py`, `game/core/popup.py` and `game/core/run.py` against `systems/run.md` (Interface "DRA-117: what graze adds and changes"; Rules steps 3a and 5b, the retry, Score, Logging; Rationale DRA-117 bullets), the graze fields in `game/core/drifters/base.py`, 06-scoring.md (Values, rules 3 to 8), `game/tuning/scoring.json`, `impact.md` and `game/ruff.toml`. Read `game/tests/core/test_ufo.py:1315-1334` to confirm the one failure the implementer reports. Ran nothing.
4. **Assumptions:** the implementer's `check.sh` results (lint, typecheck, core 3160/1, ui 46) are taken as reported; QA runs them.
5. **Documentation differences:** None.
6. **Next:** QA Engineer: the one core failure (F1) is outside `impact.md`'s table, but `impact.md` names this case and hands it to DRA-117-05. Treat it as that case, not as a bug in this task.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-117-02-F1 | note | game/tests/core/test_ufo.py:1324 | no action |
| DRA-117-02-F2 | note | docs/reports/implementation/gameplay/DRA-117-02-gameplay-implementer.md:69 | no action |
| DRA-117-02-F3 | note | game/core/run.py:386 | no action |

### DRA-117-02-F1
`test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds` now fails: the touched UFO is SPENT and its untouched twin is OUTSIDE. That is `systems/run.md`, step 5b.3. `impact.md` says no core test should change result, but its last paragraph sends this exact case to QA and DRA-117-05. Change: none.

### DRA-117-02-F2
The acceptance script builds the `Meteorite` directly instead of going through a tuning built in code and `add_drifters`. The task's Acceptance check asks for the tuning. The implementer states this under Assumptions. The values match the GDD and the default `graze_margin`, so the spawner path is left to QA's tests. Change: none.

### DRA-117-02-F3
Unlike `_apply_collect`, `_apply_graze` has no early return. It builds a popup, a ring and a new `Run` on every tick, even when nothing paid. The behavior is correct and the cost is tiny. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. F3
9. pass
10. F1, F2

## For QA
- The press that ends the respawn wait while the ship sits inside a zone it then leaves: pays on that tick (run.md, step 5b table).
- Protection runs out while the ship is inside a zone: the exit after it pays.
- A graze on a fall tick: it pays, and the popup starts where the ship fell (below the floor), before the respawn.
- A hazard that leaves the screen with the ship still inside its zone, and a chain lightning or electric ball that stops firing then: both pay once.
- Two hazards paid on one tick: two popups and two rings, `grazes` +2.
