Status: reviewed
Created by: implementation-reviewer

1. **Task:** review of `docs/reports/implementation/gameplay/DRA-86-04-gameplay-implementer.md` (task `docs/contracts/DRA-86/tasks/DRA-86-04-gameplay-implementer.md`: the islands in `core.run`), passed by the `/implement` skill.
2. **Delivered:** `docs/reports/review/DRA-86-04-gameplay-implementer.md` (this file).
3. **Checks:** read `game/core/run.py` in full against `docs/contracts/systems/run.md` (Purpose, Diagram, Interface `island_ground`, Rules steps 3 to 7, Other rules, Logging, Impact DRA-86, Rationale DRA-86) and `docs/contracts/systems/ship.md` (Interface `Ground`, `NO_GROUND`, `block_ship`, `spawn_clear`, `step`; Rules, Islands and Respawn spot). Checked the `core.ship` signatures in `game/core/ship.py` and `TouchEffect.BLOCK` in `game/core/drifters/base.py`. Matched the reported test failures against `docs/contracts/systems/drifters.md`, DRA-86 Impact table (lines 1706 and 1707). Ran nothing.
4. **Assumptions:** the four smoke lines in the implementation report are the real output; I checked line 2 (`326.0`) by hand against the respawn-spot rule and it agrees.
5. **Documentation differences:** None.
6. **Next:** Gameplay Implementer, Review fix mode, for DRA-86-04-F1. F2 asks for no change.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-86-04-F1 | should-fix | docs/reports/implementation/gameplay/DRA-86-04-gameplay-implementer.md:19 | fixed |
| DRA-86-04-F2 | note | game/core/run.py:193 | no action |

### DRA-86-04-F1
The acceptance check asks for the failures in `typecheck`, `core` and `ui` to be only the expected ones. The report says "I did not run `ui`." `game/tests/ui/` holds tests that build runs (`test_hud.py`, `test_game_over.py`), so `ui` is part of what the task must show.
Rule: the task's Acceptance check is what done means for the task. Source: `docs/contracts/DRA-86/tasks/DRA-86-04-gameplay-implementer.md`, Acceptance check. Checklist item 10.
Change: run `tests/check.sh ui` and add its result to **Checks**. If it fails, name each failure and the Impact row that expects it.

### DRA-86-04-F2
The `scroll_step_px` parameter of `island_ground` shadows the imported `core.scroll.scroll_step_px` inside that function. Nothing breaks today, and the contract's Interface names the parameter that way. Change: none.

## Checklist
1. pass
2. pass
3. pass
4. pass
5. pass
6. pass
7. pass
8. F2
9. pass
10. F1

## For QA
- A ship in the respawn wait under an island, no press: it is carried down at the scroll speed, stays waiting, and a carry off the floor counts as a fall. In the first 30 ticks that fall is protected, so it respawns with `waiting` False.
- Respawn point covered by an island: check the log order on that tick: `life lost`, `respawn from`, `respawn clear of island`. With no island, no `respawn clear of island` line.
- An island over a coin or a hazard: the island logs no `drifter touch`, costs no life and pays nothing. The coin and the hazard still act on the ship as before.
- A stack that pushes the respawn spot past the floor: the ship falls again on the next tick and costs a life as a normal fall.
- Run `ui` too: the implementer did not (F1).

## Re-check 2026-10-21
1. **Task:** re-check of the answer to DRA-86-04-F1 in `docs/reports/implementation/gameplay/DRA-86-04-gameplay-implementer.md`, section `## Review fix 2026-10-21`, passed by the `/implement` skill.
2. **Delivered:** this section, plus line 1 and the findings table of `docs/reports/review/DRA-86-04-gameplay-implementer.md`.
3. **Checks:** read the Review fix section (no code changed). Checked the failure it names against `docs/contracts/systems/drifters.md:1708`, which expects `game/tests/ui/test_drifter_registry.py` to fail from DRA-86-02 until DRA-86-06 and the island tuning file exist. Confirmed the test `test_drifter_lists_match_everywhere` exists at `game/tests/ui/test_drifter_registry.py:22`. Ran nothing.
4. **Assumptions:** the `ui` result (45 passed, 1 failed) is the real output.
5. **Documentation differences:** None.
6. **Next:** QA Engineer. No must-fix or should-fix open.
7. **Status:** done.

- DRA-86-04-F1: fixed. The Review fix section's Checks now reports `tests/check.sh ui`: 45 passed, 1 failed, the one failure (`test_drifter_registry.py::test_drifter_lists_match_everywhere`) matched to the Impact row at `docs/contracts/systems/drifters.md:1708`. The For QA line "Run `ui` too" still stands as a check for QA to repeat.
