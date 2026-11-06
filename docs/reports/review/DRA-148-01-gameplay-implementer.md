Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the DRA-148-01 gameplay work (level-up rules record, banner, shown level, level-up rest and rise flag in the wave clock) against its contract, by reading.
2. **Delivered:** `docs/reports/review/DRA-148-01-gameplay-implementer.md`. Code read: `game/core/level_up.py`, `game/core/waves.py`.
3. **Checks:** Read only, nothing run. Compared `level_up.py` and `waves.py` with `docs/contracts/systems/level-up/core.md` (Interface, Rules) and `docs/contracts/systems/waves.md` (`WaveRun`, `start_waves`, `next_run_waves`, wave clock steps 3.1, 3.2, 2a). Read the task file and `game/ruff.toml`. Interface, flag handling, rest sum and Wave 0 / Level 8 cases match the contract. The implementer's Decisions match the code.
4. **Assumptions:** The implementer's smoke run and check results were taken from its report. I did not run them.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, on this report. No finding asks for a change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-148-01-F1 | note | game/core/level_up.py:30 | no action |

### DRA-148-01-F1
`NO_LEVEL_UP` carries two literals, `arrival_ticks=1` and `banner_ticks=2`. The contract fixes only `rest_ticks` 0. The implementer chose the smallest values the record allows, and states this under Assumptions. They are inert: nothing reads them while `rest_ticks` is 0. Rule: every number traces to the GDD or tuning (CLAUDE.md, everything configurable). Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. Every number traces to the GDD or tuning: F1 (note only)
7. pass
8. pass
9. pass
10. pass

## For QA
- Run to a level rise with `rest_ticks` > 0: rest equals gap + the ended wave's extra rest + level-up rest, and `level_rose` is True on that one state only.
- End Wave 0: no flag and no level-up rest. End Level 8's last slot and later random waves: no rise, no level-up rest.
- A level with an empty playlist: the level-up rest is added once, for the level reached.
- `rest_ticks` 0 (or no rules): resting matches the old behavior; the flag still reads True on a rise.
- `next_run_waves` keeps the rules; a retry rises and rests the same way.
