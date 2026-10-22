Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-76/tasks/DRA-76-08-qa-engineer.md`: tests for the wave files' load check (`build_wave_book`), from the Architect.
2. **Delivered:**
   - `game/tests/core/test_wave_files.py` (new): 5 test functions, 177 cases.
     - `test_the_good_set_builds_a_book`
     - `test_a_bad_set_raises_value_error_naming_the_file_and_the_problem` (one row per refusal, 165 rows in `REFUSALS`)
     - `test_a_hazard_below_120_px_is_refused_and_one_at_120_px_is_accepted` (meteorite and satellite)
     - `test_a_coin_triggers_anywhere_even_below_120_px`
     - `test_what_is_not_checked_at_load_is_accepted`
     - `test_build_wave_book_logs_nothing`
   - `game/tests/core/wave_files/` (new): `wave_0.json`, `l1_a.json`, `l1_b.json`, `l3_pool.json`, `l8_pool.json`, `playlist.json`.
   - `game/tests/CONTEXT.md` (changed): the new folder in the layout table and a paragraph for `core/test_wave_files.py`.
3. **Checks:** `game/tests/check.sh`: every step PASS, last line `QA: pass`, with `test_wave_files.py` in the `core` step (1567 core tests pass, 177 of them here). Refusals covered: bad wave id; wave or placement not an object; unknown field (`speed` on a placement included); each required field missing; each type or range broken (`bool` for a number or an integer included); `min_level` missing on a pool wave and present on a fixed one; unknown drifter type (the contract's message, types in enum order); unknown variant, missing coordinate, `invert` and specialty refusals, each named by the placement and keeping the spawner's `ValueError` as `__cause__`; playlist with 7 or 9 levels or a bad level; `wave_zero` or a `fixed` entry naming no wave; no pool wave at Level 1 and at Level 2; no pool wave at Level 8. The seam: a hazard at 0, 50, 100, 119.5 and 119.99 px refused with the exact message, at 120, 120.0, 120.5 and 600 accepted, a coin accepted at 0 to 3000 px. Not-checked cases accepted: a placement past the wave's length, a level with no slots, a pool wave in a `fixed` list, a satellite in Wave 0. No log record from `core.wave_files` on a good or a failing build. Every build in the run passed the code as written: no test failed against `game/core/wave_files.py`.
4. **Assumptions:**
   - For a refusal the contract gives no example for, the row checks the file prefix and the field path (`waves/l1_a.json: placements[0].x`), not the implementer's full wording. Where the contract gives an example, the row checks it exactly.
   - The spawner's own texts (`meteorite placement needs x`, `satellite has no specialty`) are checked as written, as `test_drifters.py` already pins them.
   - `NaN` and `Infinity` (refused by the code, not named in the contract) have no row.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer for this task's part; the Architect's task `DRA-76-09-qa-engineer` and the wave clock tests (task `DRA-76-07`) are separate.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
