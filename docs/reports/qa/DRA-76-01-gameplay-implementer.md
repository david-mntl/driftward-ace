Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-76-01-gameplay-implementer (the scroll speed follows the level), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-76-01-gameplay-implementer.md
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS, ends `QA: pass`.
   - Acceptance check from `game/`, the task's command, printed:
     ```
     1.0 1.7 1.0 0.48
     1.1 1.87
     34 4 (2, 0, 0, 0, 0, 0, 1) 5.39 0
     0.0 1.87 11
     ```
     All four lines match the task.
   - Edge cases, inline, none saved:
     - 300 seeds of 1500 ticks with random level changes (rises and jumps): `step_scroll(s, l).distance_px - s.distance_px` vs `scroll_step_px(s, l)`: 0 differences over 1e-9 (max 8.7e-13). The input scroll is never mutated.
     - `meters` against an exact `Fraction` reference (1.1 times the multiplier, per moving tick) on every tick of those runs: 0 mismatches, so no tick shows one meter too few at a whole-meter boundary. 110.00000000000001 px gives 11 m.
     - Start delay: ticks 29 and 30 give step 0.0 and `scrolled_ticks` 0; tick 31 is the first move (1.32 px at Level 3, `raised_level_ticks[1] == 1`). A bad level during the delay still raises, as the report states.
     - Levels 0, -1 and 9 raise `ValueError` from `step_scroll`, `scroll_step_px` and `scroll_speed`.
     - `step_scroll(a)` equals `step_scroll(a, 1)`; `Scroll(ticks=..., scrolled_ticks=...)` has all-zero `raised_level_ticks` (Level 1 only).
     - A step inside the start delay keeps existing `raised_level_ticks`.
     - Log: `scroll start tick=31` once per scroll; `scroll_step_px` logs nothing.
     - Same inputs run twice (400 ticks, level cycling 1 to 8): identical state.
     - Level 8 only, 565 ticks: 1000.45 px, 100 m, 535 scrolled ticks.
     - Grep of `game/`: `LEVEL_1_SCROLL_MULT` and `SCROLL_PER_TICK` appear only as copies inside `game/tests/core/test_scroll.py` and `test_run_score.py`; no game code imports them.
   - Review `For QA` lines: all checked above. Review F1 is a note with no action.
4. **Assumptions:** None. The implementer's extra check (`scroll_step_px` raises on a bad level during the start delay) is beyond the contract's text but harmless, and the review flagged it as a For QA item only.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer is not due yet: DRA-76 has later tasks. The next QA step is task DRA-76-02-qa-engineer (tests for the speed per level in `game/tests/core/test_scroll.py`). `core/run.py` still calls both functions with no level, and `LEVEL_STARTS_M` and `level_at` stay until DRA-76-05, both allowed by the task.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
