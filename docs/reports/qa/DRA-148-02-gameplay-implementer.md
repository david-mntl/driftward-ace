Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-148-02-gameplay-implementer (the level-up banner in `core/run.py`: `level_up`, `hud_level`, `level_up_cue`, step 9b), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-148-02-gameplay-implementer.md. No test files (Verify saves none).
3. **Checks:** `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS (786 passed), `QA: pass`. Acceptance check reproduced with an inline headless script (synthetic book, 10 px waves, real tuning values: rest 150, arrival 124, banner 150). Edge cases hunted, all correct, none listed as bugs:
   - Rises on ticks 48 (1 to 2), 207 (2 to 3), 365 (3 to 4): banner at age 0, `previous_level` and `level` right, cue True only at age 0. `hud_level` is the old level for ages 0 to 123 and the new one from 124. Banner lives ages 0 to 149 (150 states), then None. Second banner starts only after the first is gone.
   - Same seed and inputs twice: identical traces.
   - Level 2 empty playlist: one banner, 1 to 3, shown level 3 from arrival.
   - `rest_ticks` 0 and `NO_LEVEL_UP`: no banner, no cue, `hud_level == level` on every tick through level 8.
   - No waves (`start_run()`): 300 ticks, no banner, `hud_level` 1, no cue.
   - A fall during the banner (lives 5 to 4, ship put below the screen at age 10): the banner keeps aging (11, 12, 13), cue False.
   - Last life lost on the very tick the level rises: `level` 2, `level_rose` True, burst set, `level_up` None, `hud_level` 2, cue False.
   - Last life lost at tick 6, level rises during the last life (1 to 2): `level_up` None, cue False and `hud_level == level` on every tick to game over.
   - `next_run` after game over: `level_up` None.
4. **Assumptions:** `game/core/waves.py`, `game/core/level_up.py` and `game/ui/` files have uncommitted changes in the tree (other DRA-148 tasks, not under test). check.sh passed with them present. Review note F1 (docstrings of `_step_playing` and `_step_last_life` omit 9b) is docs only, not a bug.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Task DRA-148-02 has no open bug.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (786 passed)
QA: pass
