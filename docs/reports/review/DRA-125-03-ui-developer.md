Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the burst view for DRA-125 (`docs/reports/implementation/ui/DRA-125-03-ui-developer.md`, task `docs/contracts/DRA-125/tasks/DRA-125-03-ui-developer.md`), from the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-125-03-ui-developer.md` (this file).
3. **Checks:** Read `game/ui/burst_view.py` (49 lines) against `docs/contracts/systems/run.md`: Interface (DRA-125, the `core/last_life.py` and `ui/burst_view.py` blocks), Presentation (the `run.burst`, `run.last_life` row and Burst), Rules (Burst) and Rationale ("The burst lives in core, its look in the view"). Compared it with `game/core/last_life.py` (`opacity`, `particle_centers`, `particle_size`), `game/ui/graze_view.py` (the same cache pattern), `game/tuning/last_life.json`, scope report DRA-125 line 96 (Burst values) and `game/CONTEXT.md`. Confirmed the headless script and the five PNGs the report names exist in the scratchpad. Ran nothing.
4. **Assumptions:** The scope report's "white" is the source for `BURST_COLOR`, as the contract's Interface says. The unbounded `@cache` is fine because the contract's Cache rule caps it at one alpha per state.
5. **Documentation differences:** None in the code. The task's acceptance check says "12 blobs" for every burst, but the contract's Rules put every square on the origin at age 0 (F1). The code follows the contract. This is for the Architect to word, not a change to the code.
6. **Next:** QA Engineer. No finding asks for a change. The implementer names 8 core test failures that `impact.md` does not list by name; DRA-125-09 should confirm they are the last-life change and nothing else.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-125-03-F1 | note | docs/contracts/DRA-125/tasks/DRA-125-03-ui-developer.md:26 | no action |

### DRA-125-03-F1
The acceptance check expects 12 blobs at age 0, but `run.md`, Rules, Burst, Place says "Every square is on the origin at age 0", so age 0 shows one 3 x 3 blob. The implementer reports this under Assumptions; `game/ui/burst_view.py:36` draws every center core gives, as the contract says. Change: none.

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
- Lose the last life by a hit: 12 white squares fly out from the ship's center and fade to nothing over the 2-second delay, then the game-over screen shows.
- Lose the last life by a fall: the burst sits on the bottom edge; the lower half of the squares is off screen at once.
- The burst never moves with the scroll while the world keeps scrolling under it.
- Press keys and leave the window during the last life: nothing pauses, the burst runs on to game over.
- Confirm the 8 unnamed core failures in the implementation report (Checks) come only from DRA-125-01's last-life tick.
