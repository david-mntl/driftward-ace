Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-148-01-gameplay-implementer (level-up rules record, banner state, shown level, level-up rest and rise flag in the wave clock), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-148-01-gameplay-implementer.md. No test files (Verify saves none).
3. **Checks:** `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS, `QA: pass`. Acceptance check reproduced with an inline headless script (waves 10 px, 1 px per tick, rules rest 20 / arrival 6 / banner 15, Wave 0 extra rest 5, wave `a` extra rest 3, gap 0). Edge cases hunted, all correct, none listed as bugs:
   - Rise on tick 25: `level=2 level_rose=True resting=True rest_ticks_left=23` (0 gap + 3 extra + 20 level-up). Tick 26 shows `level_rose=False`, left 22. The flag is True on tick 25 and tick 58 (next rise) only.
   - Same book with `NO_LEVEL_UP`: rise on tick 25, left 3 (gap and extra only), flag True. Rules with `rest_ticks` 0 (other values odd) give a run identical to `NO_LEVEL_UP` over 200 ticks.
   - Wave 0 ends on tick 10: no flag, level stays 1, rest 5 (its own extra rest only).
   - Empty Level 2 playlist: rise 1 to 3 on tick 25, rest 23, added once. Levels 2 to 7 empty: one rise 1 to 8, rest 23, one flag.
   - Level 8 with fixed and random slots: no further rise, no flag, rest after its wave is 3 (extra only).
   - One call crossing several waves: with rest 0 the flag stays True to the end of the call (level 8, not resting); with rest 20 the call stops at the rise (level 2, left 20, flag True), and the next call shows flag False, left 19.
   - `next_run_waves` keeps the same rules object; a retry rises at tick 25 with rest 23.
   - Rest equal to banner ticks (15 = 15): rest 15 on the rise state. Banner states 15, shown level 1 for ages 0 to 5, 2 from age 6; `step_level_up` returns None on the 15th step. Smallest rules (arrival 1, banner 2): shown previous at age 0, new at age 1, None next step. `shown_level(None, 5)` is 5.
   - Same book, seed and inputs twice: identical output over 300 ticks.
4. **Assumptions:** `game/core/run.py` has uncommitted changes in the tree (task DRA-148-02, not under test). check.sh passed with it present. My smoke books use pool waves only so the picker has a candidate.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Review note F1 (`NO_LEVEL_UP` carries `arrival_ticks=1`, `banner_ticks=2`) is inert: nothing reads them while `rest_ticks` is 0.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (786 passed)
QA: pass
