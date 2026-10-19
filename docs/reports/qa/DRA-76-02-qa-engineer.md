Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-76/tasks/DRA-76-02-qa-engineer.md`: tests for the speed per level and the two new level-table rows, started by the Director.
2. **Delivered:**
   - `game/tests/core/test_scroll.py` (changed): six new tests.
     - `test_scroll_speed_is_the_base_times_the_level_scroll_mult`
     - `test_a_step_at_a_level_moves_the_world_at_that_speed_once_the_delay_is_over`
     - `test_distance_over_several_levels_is_each_levels_ticks_times_its_speed_summed`
     - `test_scroll_step_px_equals_what_step_scroll_adds_at_every_level`
     - `test_with_no_level_both_behave_as_level_1`
     - `test_scroll_start_logs_once_per_scroll_at_every_level`
   - `game/tests/core/test_drifters.py` (changed): `test_level_table_matches_the_gdd` gains the scroll speed × and Rest gap × rows, and Levels 0, 9, -1 and 100 raise for both. The `level_at` import and its check are gone.
   - `game/tests/CONTEXT.md` (changed): one entry for the new tests and the table rows.
3. **Checks:** `game/tests/check.sh` ends `QA: pass`, with the new tests in the `core` step (1372 core tests passed). `grep level_at game/tests/core/test_drifters.py` finds nothing. Expected values are exact `Fraction`s built from `scroll_base` 1.1 and the 08-difficulty.md row. The existing tests pass unchanged. The distance test steps 8000 ticks across 3 level plans and checks the exact meters on every tick. It lands on whole-meter boundaries and asserts it did.
4. **Assumptions:** Both functions are tested at every level for the zero-before-tick-31 rule, and the "level outside 1 to 8" raise is checked on `step_scroll` during and after the start delay (contract Rules, The step, step 3). `scroll_step_px` is not tested for a bad level: the contract doesn't state it.
5. **Documentation differences:** None.
6. **Next:** Architect closes out the task (it stays `Status: open` here). DRA-76-05 can now remove `level_at` from `core/levels.py` without breaking `test_drifters.py`.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
