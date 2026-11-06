Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-148-03-ui-developer (level-up look records and pure motion functions), Verify mode, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-148-03-ui-developer.md. Nothing saved in `game/tests/` (Verify mode).
3. **Checks:**
   - `game/tests/check.sh`: final run `QA: pass` (786 tests). Acceptance check: the script from the implementation report (lines 47-111), extracted and run with `python3 -I`: `ALL ASSERTS PASSED`. Shown: `band_shares` 0 before open, 1 while open, 0 after close, glass at 0 (age 100) before lines (age 120); `fall_offset` -200 up to fall_start, 8.0 at the peak, exactly 0.0 from fall_end; `pose_scales` (0.9, 1.1) falling, (1.25, 0.8) on landing, (1.0, 1.0) from age 40; `bump_offset` 0 before landing and from fall_end + 12, peak 4, never negative, 0 with 0 px; `fly_position` exactly start at share 0 and end at share 1; `pop_scale` 1.5 at 0 and exactly 1.0 from `pop.ticks`.
   - Edge hunt with the live `game/tuning/level_up.json`: glass reaches 0 at age 116, lines at 124 (`close_end`), lines 1.0 on every age 10..100; all shares inside 0..1; opening and closing monotone. `fall_offset` -distance on ages 0..4 (negative up to `fall_start` 4), then up to 9.998 at age 17, 0.0 from age 22 (`fall_end`) and age 23 on; it crosses 0 at age 17 on the way up (as the review noted, and the contract allows). `pose_scales` (0.92, 1.12) before 22, (1.2, 0.82) on 22, (1.0, 1.0) from 30. `bump_offset` live: 0 to age 22, then 2 3 3 3 3 3 2 2 1 1 1, 0 from age 36 (22 + 14); peak 3 = `bump.pixels`. `fly_share` 0 up to age 100, 0.5 at 112, 1.0 from 124. `pop_scale` 1.45 at 0, 1.0 from 24, never above 1.45, minimum 0.941 near the undershoot.
   - Property sweep of `bump_offset` over pixels 0, 1, 2, 3, 10, peak share 0.1 to 0.99, bump ticks 1, 2, 3, 7, 14, ages -5..79: never negative, never above `pixels`, 0 outside `[fall_end, fall_end + ticks)`, 0 always at 0 px. The peak falls short of `pixels` (by `round()`, 1 px or more) only for a 1, 2 or 3 tick bump (and `pixels` 2, 3, 10); the live bump (14 ticks) reaches its peak. Not a bug: the contract does not promise the peak on a short bump, and the schema/loader range for `bump.ticks` is not in this task.
   - `fly_position` exact start and end at share 0 and 1 for arcs 0 and 40, including equal points and large negative coordinates. Negative ages give the pre-start values on every function. Same inputs twice over ages 0..199: identical.
   - Review "For QA" lines: all five covered above.
4. **Assumptions:** The expected values come from the contract (`systems/level-up/view.md`, Interface) and `game/tuning/level_up.json`. Ticks count as the contract says.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Note for the Director: my first `check.sh` run showed `QA: fail (ui)` with 40 failures in `tests/ui/test_hud.py` and `tests/ui/test_window_view.py` (AttributeError). At that time `game/ui/hud.py` was being edited in the working tree (another DRA-148 task, DRA-148-05; it was not touched by this task). The next runs of that same tree were clean, and the final full run passed. If the DRA-148-05 QA sees the same failures, those belong to that task, not to DRA-148-03.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (final run; first run failed while another task's `hud.py` was mid-edit, see Next)
QA: pass
