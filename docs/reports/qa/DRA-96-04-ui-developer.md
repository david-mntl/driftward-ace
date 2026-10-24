Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-96-04-ui-developer (the planet view and its import), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-96-04-ui-developer.md. No test files (Verify saves none).
3. **Checks:**
   - `game/tests/check.sh`: lint, format, typecheck and `ui` pass (46 passed, `test_drifter_registry.py` included). `core` fails, and only where the drifters contract's DRA-96 Impact table says it will (see Harness). Nothing in the planet view causes it.
   - Acceptance check from the task run as written (script kept in the scratchpad, `PYTHONPATH=/workspace/game`). It prints the six expected lines:
     ```
     (140, 70, 200) (140, 70, 200)
     True
     True True
     (0, 0, 0) (0, 0, 0)
     (105, 53, 150) True
     (140, 70, 200) True False
     ```
   - Edge cases, all correct:
     - Same state drawn twice: identical bytes. The drifter's `repr` is unchanged after drawing.
     - Non-planet drifter: `TypeError("render_planet draws a Planet")`.
     - Ticks 0 to 249 of ACTIVE, drawn at (320, 300) on black: every ink pixel lies inside the 302 px box. Each inner ring's pixel, within 1 px of its radius, matches `floor(255 * opacity + 0.5)` blended over black (both rings, through both restarts, including the ring at 150 over the outer ring).
     - Centers at (0, 0), (-100, -100), (639.4, 479.6), (1000, 1000) and half-pixel values: no error (the layer is clipped by the blit).
     - Two planets with overlapping fields: the second planet's pixels all survive in the shared picture, and the layer is cleared between draws.
     - Layer cache: one 303 px layer for the file's values. New sides (pull 50, 150.4, 300) each add one layer, none per frame.
     - Brightness 0.0, 0.5 and 1.0: body (0,0,0), (70,35,100), (140,70,200). The field dims with it.
     - Scale 0.0 and 0.001 draw nothing, 14/64 draws the 148 px disc and no ring, 0.999 is body only, 1.0 draws field and body.
     - A WARNING planet through `render_drifter`, placed at y 300 and at the default top start (y -151), on ticks 0, 30 and 59: a small purple disc, no ring-colored pixel.
     - `field_ring_count` 0, 1 and 5: no error.
   - Review items checked: all five **For QA** lines (half off screen, two planets, the hit dim, WARNING copy, the 120-tick ring cycle through tick 249).
4. **Assumptions:** The verdict is `blocked` and not `fail` because no bug is open, but `check.sh` does not end `QA: pass`. The only failing step is `core`, and every failure is in a test file that a queued later task (DRA-96-06, DRA-96-07) fixes. Scale above 1.0 (2.0) draws the field and a larger body. No rule covers it and no caller passes it.
5. **Documentation differences:** None.
6. **Next:** No bug to fix. The Director or `/implement` decides whether to treat this as a pass for DRA-96-04 and go on to the QA tasks `DRA-96-05`, `DRA-96-06` and `DRA-96-07`, then re-run `check.sh` once they land (the expected state is `QA: pass`). The Integration Engineer takes the planet after that.
7. **Status:** blocked: `check.sh core` fails on `game/tests/core/test_collision.py` and `game/tests/core/test_wave_files.py`, which wait for tasks DRA-96-06 and DRA-96-07.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL · ui PASS (46 passed)

`core` failures, both listed in the DRA-96 Impact table of `docs/contracts/systems/drifters.md`:
- `tests/core/test_collision.py:1676` `load_variant_cases` raises `KeyError: 'hitbox'` reading `planet.json` (collection error). Impact row for `game/tests/core/test_collision.py`, task DRA-96-06.
- With that file ignored (`check.sh core --ignore=tests/core/test_collision.py`): 504 passed, 3 failed, all `tests/core/test_wave_files.py::test_a_bad_set_raises_value_error_naming_the_file_and_the_problem` (placement type 'ufo', 'Meteorite', ''). The unknown-type message now lists `planet`. Impact row for `game/tests/core/test_wave_files.py`, task DRA-96-07.

QA: fail (core)

## Round 2 2026-10-22

1. **Task:** Re-run the acceptance check of `docs/contracts/DRA-96/tasks/DRA-96-04-ui-developer.md` now that tasks DRA-96-06 and DRA-96-07 rebuilt `test_collision.py` and `test_wave_files.py` (07's QA report reads `Verdict: pass`). Started by the Director.
2. **Delivered:** this report only. No test or game file changed.
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`. Core: 3072 passed. UI: 46 passed (`test_drifter_registry.py` included).
   - The task's acceptance command, run again as written from the task file (`PYTHONPATH=/workspace/game`). It prints the same six lines as round 1:
     ```
     (140, 70, 200) (140, 70, 200)
     True
     True True
     (0, 0, 0) (0, 0, 0)
     (105, 53, 150) True
     (140, 70, 200) True False
     ```
   - The round 1 edge cases still stand. Neither of the two core test files that failed in round 1 touches the planet view, and `game/ui/` has not changed since round 1.
4. **Assumptions:** The round 1 assumptions still stand (scale above 1.0 draws the field and a larger body; no rule covers it and no caller passes it).
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. The round 1 blocker is gone and no bug is open.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3072 passed) · ui PASS (46 passed)
QA: pass
