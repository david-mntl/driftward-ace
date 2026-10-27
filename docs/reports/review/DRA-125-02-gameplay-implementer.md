Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review DRA-125-02 (`game/core/game_flow.py`) against `systems/game-flow.md` version 0 and `systems/run.md` (DRA-125 part). Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-125-02-gameplay-implementer.md`.
3. **Checks:** Read the implementation report, the task file, `systems/game-flow.md` (Purpose, Diagram, Interface, Rules, Rationale), `impact.md`, `game/core/game_flow.py` (all 245 lines), the `core/run.py` signatures it calls, `ship.Thrust`, 02-game-flow.md rows menu_items, menu_start_selection, menu_navigation, game_over_choices, fresh_press and rule 2, `game/CONTEXT.md` and `game/ruff.toml`. Compared the acceptance output with each case in the task's Acceptance check. Cross-checked the claimed `typecheck` and `core` failures against the DRA-125-01 QA report (same 7 errors, same 26 failed / 3205 passed). Nothing run.
4. **Assumptions:** The implementer's claim that a PLAYING flow with a `game_over` run is unreachable holds: every way into PLAYING gives a live run (`next_run`, or the first run, or a resume of a run that was not over). PEP 695 generics (`_moved[E: Enum]`) are already used in `game/core/` and ruff targets py312, so they are not a new browser risk.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One note (F1) is a wording gap in `systems/game-flow.md` about `run_stepped` on the tick that enters GAME_OVER. The code follows the tick flowchart. The Director may want the Architect to align the Rules sentence; nothing waits on it.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-125-02-F1 | note | game/core/game_flow.py:218 | no action |

### DRA-125-02-F1
On the tick that steps the run into `game_over`, the flow enters GAME_OVER with `run_stepped` True (`game_flow.py:218-222`; acceptance output t=337 and t=663). This follows the tick flowchart ("run_stepped: True only after STEP", GO2 after STEP). The Rules text in `systems/game-flow.md` (`run_stepped`) also says False "after every tick that changed the screen", which reads the other way for this one tick. No player effect: `add_drifters` returns the run unchanged when `run.game_over` (`core/run.py:254`). Source: `systems/game-flow.md`, Diagram and Rules, `run_stepped`. Change: none.

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
- The tick that enters GAME_OVER: `run_stepped` is True (F1). A test that asserts False there tests the Rules sentence, not the flowchart the code follows.
- Up and down pressed on the same tick on the menu and on GAME_OVER: no move, no `select` log line.
- Confirm plus an arrow pressed on the same tick on the menu: the pick uses the old selection and the selection does not move.
- Confirm and `focus_lost` on one PLAYING tick: one `pause by=key` line, then `screen paused`.
- GAME_OVER, MENU, Play: exactly one `new run` line, logged before `screen playing`. The first Play from `start_flow` logs no `new run`.
