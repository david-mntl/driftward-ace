Status: reviewed
Created by: implementation-reviewer

1. **Task:** review of `docs/reports/implementation/gameplay/DRA-47-02-gameplay-implementer.md` (task `docs/contracts/DRA-47/tasks/DRA-47-02-gameplay-implementer.md`), passed by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-47-02-gameplay-implementer.md`.
3. **Checks:** by reading only. I compared `game/core/drifters/base.py`, `game/core/drifters/tuning.py`, `game/core/drifters/spawner.py` and `game/core/run.py` with `docs/contracts/systems/drifters.md` (Interface for base.py and tuning.py; Rules, The base: Warning copy, Warning settle, Timers; Spawner steps 5 and 8; Diagram, Birth) and `docs/contracts/systems/run.md` (Rules, `add_drifters`; Rationale). I checked the numbers against 07-drifters.md (telegraph_min 45, locked) and 08-difficulty.md (Timer × row, rule 4: round up). I worked the acceptance values out by hand: `ceil` of 120 × each Timer × gives 120, 113, 107, 102, 98, 93, 89, 84, which matches the reported output. A grep of `game/` finds `Birth(` only in `spawner.py`, so no test builds a `Birth` that the two new required fields would break. I ran nothing.
4. **Assumptions:** I took the reported typecheck failures (`ui/shapes.py`, `app/tuning.py`, `tests/core/test_collision.py`) as coming from DRA-47-01's `Line`, outside this task. `game/ui/shapes.py` has no `Line` handling yet, which fits that claim. I did not check those files further.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One open note, no action needed. `check.sh typecheck` fails outside this task's files until the `Line` shape reaches `ui/shapes.py` (task DRA-47-04) and `app/tuning.py` (Integration Engineer). The Director should confirm who fixes `app/tuning.py`.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-47-02-F1 | note | game/core/drifters/base.py:38 | no action |

### DRA-47-02-F1
`TIMER_ROUND_DIGITS` is a public module constant that the drifters.md Interface for `base.py` doesn't list. It names the 6 that the Timers rule writes into the formula, so it does not add a value, and the Decisions say so. Rule: drifters.md, Interface ("Every constant above has its value and source on its line"). Change: none.

## Checklist
1. Interface matches exactly: F1
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
- `scale_timer` at every Timer × with 120 ticks: 120, 113, 107, 102, 98, 93, 89, 84. 120 × 0.85 must give 102, not 103.
- `scale_telegraph` with a tuning value below 45 (40 at Level 1): it comes out 45. With `hazards.telegraph_min_ticks` set in `hazards.json`, the spawner hands over that value, not 45.
- `add_drifters` with several placements in one call: uids run in order, and each drifter goes through `settle_warning` once, after it gets its uid.
- Meteorite and satellite after `add_drifters`: they equal the unsettled drifter with its uid set, and `warning_copy()` is the drifter itself.
- `add_drifters` at game over or with no placements: the run comes back unchanged and `settle_warning` is never called.
