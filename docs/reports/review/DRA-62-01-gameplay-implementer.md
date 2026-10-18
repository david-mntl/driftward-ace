Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review the Gameplay Implementer's DRA-62-01 work (the coin, the points popup and the parked-drifter rules in `game/core/`) against `docs/contracts/DRA-62/tasks/DRA-62-01-gameplay-implementer.md` and `docs/contracts/systems/drifters.md` and `run.md`. Asked by the `/implement` skill.

2. **Delivered:** this report, `docs/reports/review/DRA-62-01-gameplay-implementer.md`. Files read: `game/core/popup.py`, `game/core/drifters/base.py`, `tuning.py`, `spawner.py`, `coin.py`, `__init__.py`.

3. **Checks:** Read only, nothing run. Compared every signature, field, default, error message and docstring of the six files with the contract's Interface and Rules (base, tuning, spawner, coin, popup). Traced the four acceptance lines by hand through `spawn_drifter`, `Coin.born`, `Coin.update`, `collect_points` and `collect_popup`: all four match. Checked the 100-column limit in `game/ruff.toml` by eye on the new long lines. Searched `game/core/` new code for wall-clock time, randomness, `pygame`, `ui` and `app` imports: none.

4. **Assumptions:** The implementer's `check.sh` results (lint, typecheck, 1342 and 45 passes, the two expected failures) are taken from its report. I did not run them.

5. **Documentation differences:** None.

6. **Next:** QA Engineer, with this report. Task DRA-62-05 and 06 own the tests. The coin has no tuning file or view yet, so the two expected test failures stay until those tasks land.

7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-62-01-F1 | note | game/core/drifters/coin.py:124 | no action |
| DRA-62-01-F2 | note | docs/reports/implementation/gameplay/DRA-62-01-gameplay-implementer.md:19 | no action |

### DRA-62-01-F1
`Coin.born` repeats the base's specialty and invert checks (lines 125 to 128). It is a small duplicated block. The implementer's Assumptions give the reason (the coin must not build through the base `born`, and slots dataclasses forbid zero-argument `super()`), and the contract's Born rule asks for the same messages. Rule: smells, duplicated blocks. Change: none.

### DRA-62-01-F2
The task asks for the acceptance command and its output in the report. The report gives the output and says the command is the task's, verbatim, but does not paste it. The command is in the task file and I traced it by hand. Change: none.

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
10. F2

## For QA
- Coin born at Level 8 with no `y`: ACTIVE, `y` -10, speed 0.0, no graze zone. A placement `speed` raises `coin has no speed`. `invert=True` and `specialty_enabled=True` raise.
- `update` with `scroll_step_px` 0.0 leaves the coin still. With 1.1 it moves 1.1 a tick and `x` never changes. A GONE coin does not move.
- `step_popups`: a popup with `lifetime_ticks` 60 shows on 60 states and is dropped on the 60th step. `y` is `start_y - age * rise`. Order is kept.
- `collect_popup` starts at the coin's center at age 0 with the type's ticks and rise. The rare coin pays 100 and has `glint` True.
- Placement without `x` raises `coin placement needs x`. A `parked` hazard-free drifter list still spawns the other four drifters as before.
