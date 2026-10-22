Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-86-06-ui-developer (the floating island view and its registration), started by /implement. Review is `reviewed`, 0 must-fix, 0 should-fix, 1 note (parameter name `drifter`, contract says `obj`; no action).
2. **Delivered:** docs/reports/qa/DRA-86-06-ui-developer.md
3. **Checks:**
   - `check.sh` ends `QA: fail (typecheck core)`, so it can't be `pass`. Both failures come from `game/tests/core/test_collision.py` and `test_wave_files.py`, which the DRA-86 Impact table gives to later queued tasks, and none comes from `game/ui/`. Typecheck: 6 errors, all `tests/core/test_collision.py:589,596` (`Polygon` has no `cx`; task DRA-86-07). Core: `test_collision.py` fails at collection (`KeyError: 'hitbox'` at line 1038, the loader reads the island file's `hitbox`; task DRA-86-07). With that file left out, core has 3 failed, 349 passed; the 3 are the `test_wave_files.py` unknown-type message cases (`placement type 'ufo'`, `'Meteorite'`, `''`; task DRA-86-09). The same list as the DRA-86-05 round. Lint and format pass. ui: 46 passed, including `test_drifter_registry.py`.
   - Acceptance check: the task's command run from `game/` (`PYTHONPATH=.`, SDL dummy drivers) matches all six expected lines. I also ran the same points through `render_drifter` myself, plus every contract example, all matching:
     ```
     rectangle: edge on columns 160,161,478,479 and rows 240,241,358,359; fill on every pixel of columns 162..477 x rows 242..357; (159,300) and (320,360) empty
     L:  [(35,90,45), (35,90,45), (70,160,80), (70,160,80), (0,0,0)]   L invert: [(70,160,80), (0,0,0)]
     T:  [(70,160,80), (35,90,45), (0,0,0)]
     triangle: row 240 = column 160 only; row 355 = 160..467 with (461) fill, (462..467) edge, (468) empty; row 359 = 160..478; (170,350) fill
     triangle invert: row 359 = (160) only; row 244 = 160..467
     ```
   - Edge cases that behave correctly (inline runs, nothing saved):
     - Exact footprint: for every shape (rectangle, L, T, triangle), both `invert` values, three sizes (320 x 120 arm 40, 120 x 120, 200 x 80 arm 30) and three centers (whole, fractional, shifted): every drawn pixel is a pixel whose center lies inside or on the shape placed at the rounded center, and every such pixel is drawn. 0 mismatches in all runs; all ink inside the footprint box.
     - Seam: no edge-colored pixel lies more than 2 px (Chebyshev) from an undrawn pixel, for all eight shape/`invert` pairs. No dark line across the L's or T's joint.
     - Triangle slope edge: 2 px along the vertical, about 1.9 px perpendicular (one column of 3 at the pixel-center rounding, expected for the rule).
     - Brightness 0.75: fill (53, 120, 60), edge (26, 68, 34), as `dim_color`. Brightness 0 draws black. Dimmed and full draws never mix.
     - Cache: 7 images after 5 shapes x 2 `invert` x 4 centers x 3 draws each (rectangle has one hitbox for both `invert`, L, T and triangle two each). Rebuilt after `_IMAGES.clear()`: byte-identical picture (same input twice, same output).
     - Clipping: centers at y -100, -60, 0, 480, 540, x -100, 700, and (-1000, -1000), (5000, 5000), every shape and `invert`: no error.
     - `scale` 0.5 raises `ValueError("render_floating_island draws at full size only")`; a non-island raises `TypeError("render_floating_island draws a FloatingIsland")`.
   - Observation, not filed as a bug (see Assumptions): the debug overlay's outline of the triangle spills outside the drawn footprint.
4. **Assumptions:** Verdict is `blocked`, as for DRA-86-01 to 05, because `check.sh` can't end `QA: pass` until the later queued tasks DRA-86-07 and DRA-86-09 land. No bug is open against `game/ui/drifters/floating_island_view.py` or `__init__.py`. The reviewer's For QA line "the debug outline sits on the drawn edge" has no source in the contract: it holds for the rectangle, L and T (outline drawn by `pygame.draw.rect` on exactly the drawn box, distance 0). For the triangle, the contract's Polygon shape rule sets the outline as `pygame.draw.polygon(..., [(round(px), round(py))...], 1)`, so the code is right as written. A line through the corner points (160, 240), (480, 360), (160, 360) also lights row 360 and column 480, one px past the footprint (rows 240 to 359, columns 160 to 479), and the slope outline sits 1 to 2 px off the drawn slope (at centers 300.0, 300.4, 299.6 alike; 401 outline pixels are not drawn). This only affects the debug overlay in `game/ui/shapes.py` (DRA-86-05). I filed no bug, because the code follows the contract. If the Director wants the outline on the drawn edge, that is a contract change for the Architect (outline polygon corners pulled to the pixel-center grid, or drawn as the filled shape's border).
5. **Documentation differences:** None from QA. The reviewer's pending note stands (contract names the view's second parameter `obj`, all six views use `drifter`); it changes nothing in behavior.
6. **Next:** `/implement` continues with the test tasks DRA-86-07 and DRA-86-09. Re-run `check.sh` after them; if it ends `QA: pass`, this task needs no further change and goes to the Integration Engineer. No fix owed by the UI Developer. The Director may decide on the triangle's debug outline (Assumptions).
7. **Status:** blocked: only because the harness fails on files owned by later queued tasks. Nothing in `game/ui/drifters/floating_island_view.py` is wrong.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (6 errors, `test_collision.py`, DRA-86-07) · core FAIL (collection error in `test_collision.py`, DRA-86-07; 3 failed and 349 passed with it left out, `test_wave_files.py`, DRA-86-09) · ui PASS (46 passed)
QA: fail (typecheck core)

## Round 2 2026-10-21

1. **Task:** Re-test of DRA-86-06-ui-developer after the later queued tasks DRA-86-07, 08 and 09 landed, started by /implement. No code changed for this task. DRA-86-03 B1 is a known issue accepted by the Director and does not count here.
2. **Delivered:** this round in docs/reports/qa/DRA-86-06-ui-developer.md
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`: env, lint, format, typecheck, core and ui all PASS (ui: 46 passed, including `test_drifter_registry.py`).
   - Acceptance check re-run from `game/` with the task's command (`PYTHONPATH=.`, SDL dummy drivers). Output matches all six expected lines:
     ```
     rectangle: edge, edge, fill, edge, fill, edge; ink box 160 479 240 359
     L:         edge, edge, fill, fill, (0,0,0); ink box 160 479 240 359
     triangle:  edge, fill, fill, edge, edge, (0,0,0); ink box 160 478 240 359
     ```
   - `game/ui/` and `game/core/drifters/floating_island.py` have no change since round 1, so the round 1 edge-case runs (exact footprint, seam, brightness, cache, clipping, refusals, same input twice gives the same picture) still stand.
4. **Assumptions:** The triangle debug-outline observation from round 1 is unchanged and stays a Director decision (contract change for the Architect if wanted). It is not a bug: the code follows the contract.
5. **Documentation differences:** None. The reviewer's note (contract names the second parameter `obj`, the views use `drifter`) is pending and changes no behavior.
6. **Next:** Integration Engineer.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (46 passed)
QA: pass
