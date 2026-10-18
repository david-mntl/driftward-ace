Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-56-02-ui-developer (the fireball view, `game/ui/drifters/fireball_view.py`, and its import in `game/ui/drifters/__init__.py`), started by /implement. Review status `reviewed`.
2. **Delivered:** docs/reports/qa/DRA-56-02-ui-developer.md
3. **Checks:**
   - `check.sh`: `QA: fail (core ui)`. Both failures are the ones the task's Acceptance check names as expected until `game/tuning/drifters/fireball.json` and DRA-56-03 exist: ui 34 pass, 1 fail (`test_drifter_registry.py::test_drifter_lists_match_everywhere`: tuning files lack `fireball`); core 1312 pass, 1 fail (`test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[fireball-None]`: "no tuning file for 'fireball'"). env, lint, format and typecheck pass. Neither failure touches the two files this task builds.
   - Acceptance check: the task's command body saved as a script in the scratchpad and run from `game/` with `PYTHONPATH=.`. Output, all six lines matching the task:
     ```
     True
     (255, 140, 0) (200, 160, 0) (0, 0, 0)
     (191, 105, 0) (150, 120, 0)
     (200, 160, 0) (0, 0, 0)
     True True
     False True
     ```
     Run twice: identical (`cmp`).
   - Edge cases that behave correctly:
     - Pixel parity with the debug outlines, small and big, with and without `invert`, at whole and fractional positions (200, 200 and 200.37, 150.81): the head's orange pixels equal a `draw_shape` Circle at the head's hitbox position, and the tail's pixels equal the tail circle minus the head. 8 of 8 cases exact. Head 308 px and tail 76 px (small), 780 and 188 (big).
     - Draw order: head over tail. The two circles touch, so no pixel shows both.
     - Re-hit dim: `rehit_ticks_left` 180 and 1 draw (191, 105, 0); 0 draws (255, 140, 0). Brightness 0.0 draws (0, 0, 0). Both parts dim together.
     - GONE draws nothing (all 640 x 480 pixels stay black). ACTIVE at (-5, -5) and (650, 490) draws without error (clipped).
     - `scale` 0.5 halves the look (head still on center, tail at (-5, -6) from it).
     - TypeError `render_fireball draws two circles, head then tail` for hitboxes of 0, 1 and 3 circles, circle then box, and box then circle.
     - Warning copy: small and big draw byte-identical warnings (both with and without `invert`), a head of 76 px (77 with `invert`) and a tail of 12 px, the head below the tail and right of it (left with `invert`). The whole comet spans x -6 to +4 and y -6 to +6 from the warning center, inside the 12 px radius. Two draws of the same drifter give identical bytes.
     - Warning center is (200, 12) for a top entry at x 200.
   - Review For QA lines: all five covered above (outline parity, dim and recovery, warning direction, small and big same copy, `invert` tail). Review finding F1 is a note with no action (the parameter is named `drifter`, as in every other view).
   - Not a bug, for the Architect's information: the turned copy sits a little off the ideal turn about its center. The contract's offsets (head 2.33 px below the copy's center, tail 4.67 px above) hold before the turn. After `pygame.transform.rotate`, measured on the 25 px warning image, the non-inverted copy lies about 1.5 px left of the ideal turn (head x 11.89 against 13.34), and the inverted copy about 0.4 px left (10.26 against 10.66). It comes from the contracted path in `entry_warning.py` (`transform.rotate`, blitted on the middle pixel), not from the view. Everything stays well inside the warning, and the contract states the result only as "head down and to the right (left with `invert`)", which holds.
4. **Assumptions:** The red `check.sh` core and ui steps are accepted because the task's Acceptance check lists the ui one as expected until `fireball.json` exists, and the core one is the same fireball ship case that waits on DRA-56-03 (same call as in the DRA-56-01 and DRA-39 reports). If the Director wants the strict rule (`QA: pass` required), this verdict moves to blocked until `fireball.json` and DRA-56-03 exist.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer can proceed on this task. `check.sh` returns `QA: pass` only after `game/tuning/drifters/fireball.json` (content) and DRA-56-03 (collision test) exist.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1312 passed, 1 failed: `test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[fireball-None]`, no `fireball.json` yet) · ui FAIL (34 passed, 1 failed: `test_drifter_registry.py::test_drifter_lists_match_everywhere`, no `fireball.json` yet, expected by the task)
QA: fail (core ui)
