Status: reviewed
Created by: implementation-reviewer

1. **Task:** Review of DRA-76-01 (the scroll speed follows the level), implemented by the Gameplay Implementer, against `docs/contracts/systems/scroll.md` v5 and `docs/contracts/systems/drifters.md` (levels rows).
2. **Delivered:** `docs/reports/review/DRA-76-01-gameplay-implementer.md`.
3. **Checks:** Read only, nothing run.
   - `game/core/scroll.py` and `game/core/levels.py` compared with the scroll.md Interface and Rules and the drifters.md levels Interface: names, defaults, formulas and rounding match.
   - Acceptance output re-derived by hand: 1.1 x (1 + 2 x 1.1 + 1.7) = 5.39 px, 0 m; Level 8 step 1.87; 110.0 px gives 11 m. All four lines match the task.
   - Grep of `game/` for the removed `LEVEL_1_SCROLL_MULT` and `SCROLL_PER_TICK`: only test files, which define their own copies, as the report says.
   - Values in `SCROLL_MULT` and `REST_GAP_MULT` match 08-difficulty.md lines 14 and 17.
4. **Assumptions:** The Decisions in the report were checked against the code, not against a run of `check.sh`.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, task DRA-76-02. `core/run.py` still calls both functions with no level, and `LEVEL_STARTS_M` and `level_at` stay until DRA-76-05. Both are allowed by the task's Out of scope.
7. **Status:** done.

## Findings
| ID | Severity | Where | Status |
|---|---|---|---|
| DRA-76-01-F1 | note | game/core/levels.py:1 | no action |

### DRA-76-01-F1
The module docstring still says "hazard speed and Timer multipliers per level". The file now also holds the scroll speed and Rest gap rows. Harmless, and `levels.py` is touched again in DRA-76-05, where the docstring can be updated. Change: none.

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
- Step `Scroll(ticks=30)` at levels 1, 2, 2, 8: expect ticks 34, `raised_level_ticks == (2, 0, 0, 0, 0, 0, 1)`, 5.39 px, 0 m.
- `step_scroll(s, l).distance_px - s.distance_px` equals `scroll_step_px(s, l)` within 1e-9 at every level and on every tick, including the start delay (0.0).
- Meters at a whole-meter boundary after mixed levels (the 6-decimal round): no tick shows one meter too few.
- A level of 0 or 9 raises `ValueError` from `step_scroll`, `scroll_step_px` and `scroll_speed`. `scroll_step_px` also raises during the start delay, which is beyond what the contract states.
- `Scroll(ticks=..., scrolled_ticks=...)` by keyword and `step_scroll(scroll)` with no level stay Level 1 only, so the existing tests pass unchanged.
