Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-39-03-gameplay-implementer (the satellite: `DrifterType.SATELLITE`, `satellite.py`, its import), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-39-03-gameplay-implementer.md. No test files saved (Verify mode).
3. **Checks:**
   - `check.sh` ends `QA: fail (typecheck core ui)`. All three are failures the task and the `drifters.md` Impact table expect, not bugs:
     - `typecheck`: errors only in `tests/core/test_drifters.py` and `tests/core/test_run_drifters.py` (`hit_ship`), the DRA-39-01 list.
     - `core`: 16 failed, 49 passed, the same two files and the same 16 as in the DRA-39-01 and DRA-39-02 QA reports. No new failure. Tasks DRA-39-06 and DRA-39-07 rebuild them.
     - `ui`: 1 failed, `test_drifter_lists_match_everywhere` (`registered views ['meteorite'] vs DrifterType ['meteorite', 'satellite']`). `drifters.md` Impact table (line 649) says it fails from task DRA-39-03 until `satellite_view.py` (DRA-39-04) and `satellite.json` exist. 16 other ui tests pass.
     - env, lint, format pass.
   - Acceptance check reproduced from `game/` (SDL dummy, `PYTHONPATH=.`), all five lines as the task expects:
     ```
     ['meteorite', 'satellite']
     flat -18.0 300.0 (18.0, 300.0) True ()
     active -15.5325 300.0 2
     658.0 (622.0, 200.0) 20.0 -2.3187 0.8439
     satellite placement needs y
     ```
   - Edge cases, all correct:
     - Warning: 60 updates keep x and y fixed and ticks_in_phase counts; the 61st update moves it by 2.4675 (x -15.5325). A GONE satellite is unchanged by `update`.
     - Drop timing through `step_run`-style stepping (`update` then `mark_entered`, then `is_off_screen`): flat from y 300 is dropped 274 ticks after it appears (334 in all), as the contract says (n = 274). Angled from y 300 is dropped below the floor on n = 221 (281 in all), x 494.43, y 486.51, as the contract says. `invert` flat gives the same 334, ending at x -18.09. A flat one at y 480 is dropped at the far wall like the one at y 300.
     - Through the real run: `add_drifters` then `step_run`, the flat and the angled `invert` satellite are removed from `run.drifters` (ticks 333 and 280, i.e. 60 + n - 1 as `step_run` counts the add tick).
     - Speed: along-path speed is 2.4675 at Level 1 and 3.50385 at Level 8, for the angled variant too, so the angle never scales. A placement speed 2.0 gives 2.0 along the path.
     - `invert` with an explicit x 100: x stays 100, velocity_x negative, warning center (100, 50).
     - Tilt: flat gives -0.0, which equals 0 and hashes like 0.0. Angled `invert` +20.0, angled without `invert` -20.0.
     - Errors: `specialty_enabled=True` raises `satellite has no specialty`. An unknown variant raises `unknown variant 'nope' for drifter type 'satellite'` (spawner). A variant with no extra raises `satellite variant 'flat' has no angle`. A missing y raises `satellite placement needs y`.
     - Hits through `step_run`: a satellite placed at y 480 with speed 0 hits the falling ship at tick 59 for x 300 and 310 (body or bar overlap) and x 345 (panel bar only, the body is clear). At x 360 and x 270 (nothing overlaps) there is no hit.
     - Same seed and inputs run twice: identical state (flat, angled, in the run).
4. **Assumptions:** I treat the three harness failures as met, not as bugs, as the task, the Impact table and the earlier DRA-39 QA reports do. The `QA: pass` last line returns when DRA-39-04, DRA-39-06 and DRA-39-07 are done.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. `satellite.json` and its loader in `game/app/` are still open until integration, and `load_tuning` raises until then, as the contract says.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (expected, DRA-39-06/07) · core FAIL (expected, 16, DRA-39-06/07) · ui FAIL (expected, 1, DRA-39-04)
QA: fail (typecheck core ui)
