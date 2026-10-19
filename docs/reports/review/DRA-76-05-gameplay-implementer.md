Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review `docs/reports/implementation/gameplay/DRA-76-05-gameplay-implementer.md` (task `DRA-76-05-gameplay-implementer`, asked by the `/implement` skill): the run's waves in `core/run.py`, and `LEVEL_STARTS_M` and `level_at` removed from `core/levels.py`.
2. **Delivered:** this report, `docs/reports/review/DRA-76-05-gameplay-implementer.md`.
3. **Checks:** read-only, nothing run. Read `game/core/run.py` and `game/core/levels.py` against `docs/contracts/systems/run.md` (Interface, Rules steps 3, 5, 9a, game-over tick, `add_drifters`, Logging order, Rationale), `waves.md` (Interface, wave clock) and the task file. Grepped `game/` for `level_at` and `LEVEL_STARTS_M`: no code hit (one match in `game/tests/CONTEXT.md`, a doc line, not code). Worked the acceptance numbers by hand against `core/scroll.py` (30-tick start delay, 1.1 px base, 1.0 and 1.1 multipliers): Wave 0 (11 px) ends on tick 40, the pool wave on tick 50, tick 51 moves at 1.21 px, distance 20 x 1.1 + 1.21 = 23.21. This matches the four lines the report claims.
4. **Assumptions:** The report's `check.sh` and smoke results are taken as claimed. I did not run them, and the code can pass them.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, report `docs/reports/review/DRA-76-05-gameplay-implementer.md`.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-76-05-F1 | note | game/core/run.py:6 | no action |

### DRA-76-05-F1
The module docstring says "No frame time, no randomness, no run mode." From DRA-76 the only randomness in `step_run` is the waves' random pick, drawn from a seed held in `run.waves` (run.md, Other rules). `run.py` itself draws nothing, so the line is still true of this file, but it reads wider than the contract's wording. Rule: docstrings match the contract (run.md, Other rules). Change: none.

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
- Level rise tick: the tick that ends the last Level 1 wave still scrolls at 1.1 px (steps 3 and 5 read `run.level` going in). The next tick scrolls at 1.21 px. `add_drifters` after the rise tick uses the risen level.
- Tick on which lives reach 0 (fall and hit): step 9a still runs, so `wave_spawns_due` and the waves' state can advance on it. The next tick (game over) changes nothing.
- Retry: log order is `new run`, then Wave 0's `wave start`. The seed differs from the old `run_seed`, and the same first seed gives the same picks. A run with no waves retries to `start_run()` with `waves` None.
- Run with no waves: `level` is 1, `wave_spawns_due` is `()` and every existing run test is unchanged.
- Respawn wait and protected ticks: the wave clock keeps running through both.
