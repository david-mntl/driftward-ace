Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the DRA-148-02 implementation (the level-up banner in `core/run.py`) against `docs/contracts/DRA-148/tasks/DRA-148-02-gameplay-implementer.md`, `systems/level-up/core.md` and `systems/run.md` (asked by the `/implement` skill).
2. **Delivered:** this report, `docs/reports/review/DRA-148-02-gameplay-implementer.md`. Code read: `game/core/run.py` (all), `game/core/level_up.py` (the functions it calls), `game/core/waves.py` (`level_rose`, `level_up_rules` only).
3. **Checks:** by reading only, nothing run. Interface, step 9b order, previous level, burst clearing, `next_run` and the tick paths compared with the contract line by line. Lines are under the 100 limit of `game/ruff.toml`.
4. **Assumptions:** The check results in the implementation report (lint, typecheck, smoke output) are taken as its claims. I read the code and found nothing that would stop them passing.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, on `docs/reports/review/DRA-148-02-gameplay-implementer.md`.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-148-02-F1 | note | game/core/run.py:367-373, 680-687 | no action |

### DRA-148-02-F1
The docstrings of `_step_playing` ("steps 1 to 10 with 3a, 5a, 5b and 9a") and `_step_last_life` do not name step 9b, which both now run through `_step_run_waves`. Small gap in the docs, no effect on behavior. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. F1 (docstring only)
9. pass
10. pass

## For QA
- Reach a level rise with rules on: the banner is at age 0 and the cue True on the state after the rise tick only; `hud_level` stays the old level until age `arrival_ticks`, then the new one.
- Lose a life by hit or fall during the banner (lives above 1): the banner keeps aging, the ship keeps control.
- Lose the last life during the banner: `level_up` is None at once and `hud_level` equals `level`. No banner starts on later last-life ticks even when the level rises.
- `rest_ticks` 0 or no waves: no banner, no cue, `hud_level` equals `level`.
- `next_run` after game over: no banner, `hud_level` 1.
