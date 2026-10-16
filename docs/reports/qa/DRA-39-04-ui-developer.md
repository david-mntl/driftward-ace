Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-39-04-ui-developer (the placeholder satellite view and its registration), Verify mode, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-39-04-ui-developer.md. No test files saved (Verify mode).
3. **Checks:**
   - `check.sh` ends `QA: fail (typecheck core)`. Both are the failures the DRA-39 task files and the `drifters.md` Impact table expect, the same two files and the same counts as in the DRA-39-01, -02 and -03 QA reports, not bugs: `typecheck` errors only in `tests/core/test_drifters.py` and `tests/core/test_run_drifters.py` (`hit_ship`), `core` 16 failed and 49 passed, all 16 in those two files. Tasks DRA-39-06 and DRA-39-07 rebuild them. Nothing in `game/ui/`. `ui`: 17 passed, including `test_drifter_registry.py` (the one failure DRA-39-03 reported, the registry mismatch, is gone now that the view and `satellite.json` exist). env, lint and format pass. `QA: pass` returns when DRA-39-06 and DRA-39-07 are done.
   - Acceptance check reproduced from `game/` (SDL dummy, `PYTHONPATH=.`), all three lines as the task expects:
     ```
     [(240, 240, 240), (60, 110, 220), (240, 240, 240), (0, 0, 0)]
     [(180, 180, 180), (45, 83, 165)]
     True True
     ```
   - Edge cases, all correct:
     - Active flat at (100, 50): blue bar x 82..117, y 47..52 (36 × 6, 144 px), white body x 94..105, y 44..55 (12 × 12, 144 px). The body sits over the middle of the bar.
     - Scale: 0.5 gives bar 18 × 3 and body 6 × 6, 1.0 gives 36 × 6 and 12 × 12, 2.0 gives 72 × 12 and 24 × 24, all centered on the same point. Scale 0.0 draws nothing and does not raise.
     - Brightness 0.0 draws black. Re-hit (0.75) gives (180, 180, 180) and (45, 83, 165).
     - Entry warning copy: the flat one stays upright (blue bar x 9..26, 18 × 3; white body 6 × 6). The angled one without `invert` has its right end lower (y 202 at x 26, 197 at x 9). With `invert` its left end is lower, against the right wall at x 600..640.
     - A hitbox of one box, three boxes, no shapes, circle then box, or box then circle raises `TypeError` each time.
     - Centers far off screen (-100, -100) and (700, 500) draw without raising.
     - A GONE satellite draws nothing. Drawing leaves `repr(drifter)` identical. Two draws of the same state give identical pixels.
4. **Assumptions:** The debug-mode crossing check in the task waits on the Integration Engineer wiring DRA-39 in `app`; not run here (QA tests headless only). The reviewer's note F1 (`drifter` for the contract's `obj`) is a naming match with `render_meteorite` and has no effect, so I log no bug.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer for the DRA-39 wiring and the debug-mode crossing check. The two core test files stay red until DRA-39-06 and DRA-39-07 land.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (18 errors, only in `tests/core/test_drifters.py` and `tests/core/test_run_drifters.py`, expected by the DRA-39 tasks) · core FAIL (16 failed, 49 passed, only those two files, expected) · ui PASS (17 passed)
QA: fail (typecheck core)
