Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-86-01-gameplay-implementer (the `Polygon` shape, its overlap, place and grow rules, and `deeply_overlaps`, `push_directions`, `exit_distance` in `game/core/collision.py`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-86-01-gameplay-implementer.md
3. **Checks:**
   - `check.sh` ends `QA: fail (typecheck core)`. Both failures are the three breaks the contract's DRA-86 Impact table names for `game/tests/core/test_collision.py`: mypy at lines 589 and 596 (6 errors, `moved` and `anchor` read box fields from a `Polygon`) and the guard test `test_every_shape_kind_and_every_pair_of_kinds_has_a_table` (finds `Polygon` with no table). 1575 core tests pass, 46 ui pass, lint and format pass. Nothing else fails. Task DRA-86-07-qa-engineer fixes those tests.
   - Acceptance check reproduced from `game/` (PYTHONPATH set to `game/`). Output, identical on two runs (diffed):
     ```
     False True False
     4
     2.0 18.0
     16.0
     0.0 False
     6 (0.3511, -0.9363)
     exit_distance takes boxes and polygons, not 'Circle'
     ```
   - Edge touch (triangle's bottom edge, left edge, bottom-right corner, polygon on polygon), both argument orders: `hitboxes_overlap` False, `deeply_overlaps` False, `exit_distance` 0.0.
   - Box sunk into the slope, all 6 directions: each exit leaves no overlap and no deep overlap (up 6.875, slope normal 6.4373).
   - L of two boxes, four directions (up 23, down 13, left 33, right 13): the chain is walked as one surface and the result is clear.
   - Two overlapping triangles, ship across both: every direction ends not deeply overlapping.
   - Inverted triangle: 6 directions, slope normal (0.3511, 0.9363) at index 4, no duplicate or `-0.0` forms.
   - `grow_hitbox` on a triangle: 1 + 3 shapes, polygon first, then its three edge lines in edge order, thickness 28 for margin 14. Fuzz of 20,000 random convex polygons and margins: result length is 1 + edges, and a tiny circle hits the grown shape exactly when its distance to the polygon is under the margin.
   - Fuzz against an independent reference (Sutherland-Hodgman clipping, 20,000 cases each): polygon vs polygon, polygon vs box, polygon vs circle (720-gon), polygon vs line (sampled capsule), either point order. No missed overlap, no asymmetry, no touch counted as overlap.
   - Fuzz of `exit_distance` (1,200 cases, both single and two-polygon solids, every direction `push_directions` returns): at the result the shapes are clear and not deeply overlapping, and every sampled `t` before it is still overlapping. No hang. 20,000 float-position boxes on a triangle: 0 deep overlaps after the exit.
   - TypeError text: `place_hitbox`, `grow_hitbox`, `hitboxes_overlap` give `unknown shape kind 'str'` (also with the other hitbox empty); the three push-out functions give `<name> takes boxes and polygons, not 'Line'`, in either hitbox. Empty hitboxes: no overlap, 0.0, the four axis directions.
   - Review findings: none. Each **For QA** line is covered above. Frame time per tick is left for the browser run (Integration Engineer), as the review says.
4. **Assumptions:** `exit_distance` with a zero direction (0.0, 0.0) returns `inf`. The contract says the direction is a unit vector, so this is not filed.
5. **Documentation differences:** None.
6. **Next:** No bug is open in `game/core/collision.py`, and the Gameplay Implementer has nothing to fix. The verdict is blocked only because `check.sh` cannot end `QA: pass` until `game/tests/core/test_collision.py` is updated by DRA-86-07-qa-engineer, a later queued task the contract already names. Director / `/implement`: continue with that task and re-check this report after it, then the Integration Engineer once the harness ends `QA: pass`.
7. **Status:** blocked. The harness is red only from the tests the contract says this change breaks.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (tests/core/test_collision.py:589 and :596, 6 errors, the contract's named break) · core FAIL (1575 passed, 1 failed: the Shape guard test, the contract's named break) · ui PASS (46 passed)
QA: fail (typecheck core)

## Round 2 2026-10-21

Verdict for this round: pass.

1. **Task:** Re-test of DRA-86-01-gameplay-implementer after the later queued tasks (DRA-86-06, 07, 08, 09 and the island tuning file) landed. No code changed in this task since round 1. Started by /implement.
2. **Delivered:** this round, appended to docs/reports/qa/DRA-86-01-gameplay-implementer.md.
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`: env, lint, format, typecheck, core and ui all PASS (ui 46 passed). The round 1 failures (mypy at `test_collision.py:589` and `:596`, and the shape guard test) are gone, fixed by DRA-86-07.
   - Acceptance check re-run from `game/` on a right triangle (0,0), (40,30), (0,30): touching box no overlap; a box sunk into the slope overlaps and deeply overlaps; `push_directions` gives 6 directions; `exit_distance` gives 19.25, 36.0, 41.0, 25.6667, 15.4, 45.0. Two runs are identical. `exit_distance` on a circle raises `exit_distance takes boxes and polygons, not 'Circle'`.
   - Neighbor check, 20,000 random ship positions around the triangle, every direction `push_directions` returns (46,446 exits): 0 are still deeply overlapping after the exit. A hair strict overlap within `SURFACE_TOLERANCE` (1e-9) can remain, which the contract counts as touching.
   - Round 1 edge cases are unchanged; no code in `game/core/collision.py` changed for this task.
   - DRA-86-03 B1 (one-frame overlap after the top-line clamp) is accepted by the Director and is not filed here.
4. **Assumptions:** None new. Round 1's zero-direction note stands.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, for the browser run, including the frame time per tick the review left for it.
7. **Status:** done.

### Bugs
None open. Round 1 listed none.

### Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (46 passed)
QA: pass
