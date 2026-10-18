Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-47-02-gameplay-implementer (telegraph floor, type extra, warning hooks, timer scaling, warning settle in `add_drifters`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-47-02-gameplay-implementer.md
3. **Checks:**
   - `check.sh`: `QA: fail (typecheck core ui)`. No failure comes from this task's files (`core/drifters/base.py`, `tuning.py`, `spawner.py`, `core/run.py`). Typecheck: 18 errors, only in `app/tuning.py` (4, integration), `tests/core/test_collision.py` (13, DRA-47-07) and `ui/shapes.py` (1, DRA-47-04), all from the `Line` shape. Core: 447 pass, 1 fail, `test_every_shape_kind_and_every_pair_of_kinds_has_a_table` (DRA-47-07). Ui: 16 pass, 1 fail, `test_drifter_lists_match_everywhere` (`chain_lightning.json` exists, `DrifterType.CHAIN_LIGHTNING` does not until DRA-47-03). lint and format pass. Same state as the DRA-47-01 QA report.
   - Acceptance check, run from `game/`, twice, identical:
     ```
     [120, 113, 107, 102, 98, 93, 89, 84] 45 84
     45 None True True 1
     ```
     Matches the task's two expected lines.
   - `scale_timer`: 200,000 random (ticks 0..600, multiplier k/100 for k 50..100) against exact `ceil(Fraction)`. 0 mismatches. 120 x 0.85 is 102. The `core.levels.TIMER_MULT` table gives 120, 113, 107, 102, 98, 93, 89, 84. Zero ticks and zero multiplier give 0.
   - `scale_telegraph`: 40 at Level 1 gives 45. 120 at 0.70 gives 84. 60 at 0.75 gives 45. 64 at 0.70 gives 45 and 65 gives 46 (exact floor edge). With a floor of 0 nothing is raised (40 stays 40).
   - Spawner: `Birth.telegraph_min_ticks` is 45 with default `HazardRules`, 7 when `hazards.telegraph_min_ticks=7`, 0 when 0. `Birth.type_extra` is the type's `extra` (an `X` record passes through) and None for the meteorite with no extra.
   - `add_drifters`: four placements in one call get uids 1..4, `next_uid` 5, and `settle_warning` runs once each, in order, with the uid already set and `ctx.ship` the run's ship. A second call continues at uid 5 and settles only the new one. No placements, or game over: the run comes back as the same object and `settle_warning` is never called. A later placement that raises in `spawn_drifter` (unknown variant), or a `settle_warning` that raises: the error rises and the input run is unchanged (5 drifters, `next_uid` 6).
   - Meteorite after `add_drifters`: equals the unsettled drifter with its uid set, `warning_copy()` is the drifter itself, phase WARNING, `ticks_in_phase` 0. Same inputs twice: equal runs.
   - Review "For QA" lines: all five checked above.
4. **Assumptions:** `blocked` follows the DRA-47-01 QA report: every failing check sits in a file a later DRA-47 task owns, as the main session said to expect. No bug is open in this task.
5. **Documentation differences:** None.
6. **Next:** No bug for the Gameplay Implementer. `QA: pass` can't print until DRA-47-03 (`DrifterType.CHAIN_LIGHTNING`), DRA-47-04 (`ui/shapes.py`), DRA-47-07 (`tests/core/test_collision.py`) and the `app/tuning.py` integration land. Re-check `check.sh` after those. This task can go on to the Integration Engineer queue once the Director or `/implement` accepts the later-task failures.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (18 errors: `app/tuning.py` 4, `tests/core/test_collision.py` 13, `ui/shapes.py` 1; none in `core/`) · core FAIL (447 pass, 1 fail: `test_every_shape_kind_and_every_pair_of_kinds_has_a_table`, DRA-47-07) · ui FAIL (16 pass, 1 fail: `test_drifter_lists_match_everywhere`, DRA-47-03)
QA: fail (typecheck core ui)

## Round 2 2026-10-16

1. **Task:** Re-test of DRA-47-02-gameplay-implementer after DRA-47-03 to 08 landed, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-47-02-gameplay-implementer.md (this round).
3. **Checks:**
   - `check.sh`: `QA: fail (typecheck)`. The only failures are the 4 `app/tuning.py` errors (lines 250 and 251, `Line` in the `Hitbox` union). The Integration Engineer fixes them during DRA-47 integration (docs/contracts/systems/app.md, Ownership). None sits in this task's files. Core: 1312 pass. Ui: 17 pass. lint and format pass.
   - The three earlier failures are gone: `ui/shapes.py` and `tests/core/test_collision.py` typecheck clean, `test_every_shape_kind_and_every_pair_of_kinds_has_a_table` and `test_drifter_lists_match_everywhere` pass.
   - Acceptance check, run twice from `game/`, identical, matches the task's two lines:
     ```
     [120, 113, 107, 102, 98, 93, 89, 84] 45 84
     45 None True True 1
     ```
   - `scale_timer` against exact `ceil(Fraction)`, 100,000 random cases: 0 mismatches.
   - New `core/test_chain_lightning.py` (26 tests) covers `warning_copy`, `settle_warning`, `scale_timer`, `scale_telegraph` and passes.
4. **Assumptions:** The remaining typecheck failure in `app/tuning.py` does not fail this task, as the main session said and as in the DRA-39 QA reports.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. It also updates `app/tuning.py` so `check.sh` ends `QA: pass`.
7. **Status:** done.

## Bugs
None open. No bug was filed in round 1.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (4 errors, all `app/tuning.py:250-251`, integration-owned) · core PASS (1312) · ui PASS (17)
QA: fail (typecheck)
