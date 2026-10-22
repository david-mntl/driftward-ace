Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-86-05-ui-developer (the `Polygon` shape in `ui.shapes.draw_shape`), started by /implement. Review is `reviewed`, no findings.
2. **Delivered:** docs/reports/qa/DRA-86-05-ui-developer.md
3. **Checks:**
   - `check.sh` ends `QA: fail (typecheck core ui)`, so it can't be `pass`. Every failure is one the drifters contract's DRA-86 Impact table gives to a later queued task, and none comes from `game/ui/shapes.py`: typecheck 6 errors, all `tests/core/test_collision.py:589,596` (task DRA-86-07); core 5 failed, 1572 passed (`test_collision.py` guard test and `[floating_island-None]`, task DRA-86-07; three `test_wave_files.py` unknown-type message cases, task DRA-86-09); ui 1 failed, 45 passed (`test_drifter_registry.py`, no `floating_island.json` and no view yet, task DRA-86-06 and the tuning file). Lint and format pass. Every `ui/test_*.py` test other than the registry one passes. The failure list is identical to the DRA-86-04 round.
   - Acceptance check reproduced from `game/` (the task's command, `PYTHONPATH=.`, SDL dummy drivers):
     ```
     [160] 160 467 478 []
     100 (100, 100) (109, 109)
     (0, 255, 0) (0, 0, 0)
     ```
     All three lines match the task.
   - Edge cases that behave correctly (inline runs, nothing saved):
     - Brute-force check against an exact `Fraction` pixel-center test: 180 random convex polygons (3 to 6 corners, corners on 1, 0.5 and 0.25 px grids, both winding orders): 0 pixels differ in any of them.
     - Inverted triangle (`Polygon(((-160,60),(160,-60),(-160,-60)))` at (320, 300)): row 359 is the single pixel (160, 359), row 244 runs 160 to 467, rows 240 to 359 only. Equals the brute-force fill.
     - Triangle at non-whole centers (320.5, 300.5), (320.3, 299.7), (100.25, 100.75): equals the brute-force fill, no gaps, no empty rows.
     - Clipping: polygons partly past the top-left, past the bottom-right, and one far larger than the surface (corners at -1000 and 3000), filled and outlined: no error. A polygon at 1e6 px: no error.
     - Slivers with no pixel center inside (height 0.4 px, 0.0001 px): draw nothing, no error.
     - Same polygon drawn twice: identical bytes; `points` unchanged.
     - Outline (`width` 1, and 3): draws, no error. `draw_hitbox` with a polygon, box, circle and line together: no error. Every `island_hitbox` shape (four shapes, `invert` both ways, at x.5 centers), and its `grow_hitbox(…, 10)` (polygon plus edge lines), filled and outlined: no error.
     - A non-shape (`object()`, a tuple): `TypeError: unknown shape kind 'object'` and `'tuple'`.
4. **Assumptions:** Verdict is `blocked`, as for DRA-86-01 to 04, because `check.sh` can't end `QA: pass` until the later queued tasks land. It is not a contract problem and no bug is open against `shapes.py`. Re-test after DRA-86-06, 07, 09 and the island tuning file.
5. **Documentation differences:** None.
6. **Next:** `/implement` continues with DRA-86-06 (view, and the tuning file) and the test tasks DRA-86-07 and 09. Re-run `check.sh` after them; if it ends `QA: pass`, this task needs no further change. No fix owed by the UI Developer.
7. **Status:** blocked: only because the harness fails on files owned by later queued tasks. Nothing in `game/ui/shapes.py` is wrong.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (6 errors, `test_collision.py`, DRA-86-07) · core FAIL (5 failed, 1572 passed; DRA-86-07 and DRA-86-09) · ui FAIL (1 failed, 45 passed; DRA-86-06 and the tuning file)
QA: fail (typecheck core ui)

## Round 2 2026-10-21

1. **Task:** Re-test of DRA-86-05-ui-developer (`Polygon` in `ui.shapes.draw_shape`) after the later queued tasks (DRA-86-06, 07, 08, 09 and the island tuning file) landed. DRA-86-03 B1 is a Director-accepted known issue and is not counted here.
2. **Delivered:** docs/reports/qa/DRA-86-05-ui-developer.md (this round).
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`: env, lint, format, typecheck, core and ui all PASS (ui: 46 passed, including `test_drifter_registry.py`, which failed in round 1).
   - No implementation report gained a `## Fix` section and `game/ui/shapes.py` is unchanged since round 1; round 1 had no open bug.
   - Acceptance check reproduced from `game/` (same command, `PYTHONPATH=.`, SDL dummy drivers):
     ```
     [160] 160 467 478 []
     100 (100, 100) (109, 109)
     (0, 255, 0) (0, 0, 0)
     ```
     All three lines match the task.
   - Edge cases re-run inline: a polygon far larger than the surface (corners at -1000 and 3000), filled and outlined, draws without error; the same outline drawn twice gives identical bytes; a non-shape raises `TypeError: unknown shape kind 'object'`. Round 1's wider edge cases (brute-force pixel-center comparison, slivers, non-whole centers, `draw_hitbox`, `grow_hitbox`) stand; the island view (DRA-86-06) now draws through this code and its ui tests pass.
4. **Assumptions:** The block in round 1 came only from later queued tasks, so with the harness at `QA: pass` and no open bug the verdict is `pass`.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. No fix owed by the UI Developer.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (46 passed)
QA: pass
