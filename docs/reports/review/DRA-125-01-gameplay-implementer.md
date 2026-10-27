Status: reviewed
Created by: implementation-reviewer

1. **Task:** review DRA-125-01 (`core/last_life.py` new, `core/run.py` changed: last life, game over, `next_run`, `hold_arrows`) against `docs/contracts/systems/run.md` v11. Asked by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-125-01-gameplay-implementer.md`.
3. **Checks:** read the implementation report, the task file, `impact.md`, `systems/run.md` (Purpose, Diagram, Interface incl. the DRA-125 block, Rules, Logging, Rationale), `02-game-flow.md`, `05-lives-and-damage.md` rule 5, scope report DRA-125 (Values needed, Burst), `game/CONTEXT.md`, `game/tuning/last_life.json`, `game/core/last_life.py` (all 122 lines) and `game/core/run.py` (all 657 lines). Grepped `game/` for `retry_armed`, `_any_arrow`, `_step_game_over`, `_end_run` and `game over meters`: hits only in test files that DRA-125-09 owns. Opened the eight extra failing tests the report names under the general rule: each loses the last life and asserts `game_over` on that tick or retries by arrow, as claimed. Ran nothing.
4. **Assumptions:** the `burst is None` guard in `_end_last_life` exists for type narrowing (F1). The implementer's `lint` and `typecheck` results are taken as reported; QA runs them.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. One note, no action.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-125-01-F1 | note | game/core/run.py:646 | no action |

### DRA-125-01-F1
`_end_last_life` tests `run.burst is None`, a branch that can't run: its only caller, `_step_last_life`, always sets the burst. It narrows the type for mypy. Passing the stepped burst in, as `step_run` does for `_step_last_life`, would drop it. Rule: no dead code (game/CONTEXT.md, Good practice). Change: none.

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
10. pass

## For QA
- A coin collected or a graze paid on the tick lives reach 0: `final_score` includes it, and `score` then stays there while `scroll.meters` keeps growing.
- A hit on the last life while the ship stands in the respawn wait: `waiting` goes False, `invuln_ticks_left` 0, burst at the ship's center.
- `delay_ticks=1`: game over on the tick right after the death tick, `opacity` 1.0 then 0.0.
- `add_drifters` during the last life adds drifters; at game over it returns the run unchanged.
- `next_run` on a run that is not over (mid-run or last life), and on a run with `waves=None`: a fresh run, the graze and last-life values kept, `new run` logged first.
