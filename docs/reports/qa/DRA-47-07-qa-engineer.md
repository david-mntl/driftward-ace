Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-47-07 (line tables, three-kind guard, chain lightning ship cases), started by the main session.
2. **Delivered:** `game/tests/core/test_collision.py` (changed), `game/tests/CONTEXT.md` (the `test_collision.py` line updated). This report: `docs/reports/qa/DRA-47-07-qa-engineer.md`.
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, core, ui PASS. Core runs 1286 tests. Typecheck FAILS with 4 errors, all in `game/app/tuning.py:250-251` (`Line` has no `cx`, `cy`, `h`). The Integration Engineer updates that file during DRA-47 integration (`systems/app.md`, Ownership), so the main session said it doesn't fail or block this task. The 13 typecheck errors that were in `test_collision.py` are gone. Last line: `QA: fail (typecheck)`. Run on its own, `check.sh core` ends `QA: pass`.
   - Line tables, each case run both ways round, moved by five offsets, with an empty hitbox, with a shape added, grown: line and line 43 cases, circle and line 36, box and line 46. Each has side touch, hair inside and outside, round-end touch on the axis and at a 3-4-5 angle, crossing, parallel edges touching, one inside the other, identical, far apart, and point lines. Box and line also has a line through the box with both ends outside and a round end on a box corner.
   - A line with both ends on one point against every circle case in every table gives the same result as the circle (`test_a_line_with_both_ends_on_one_point_acts_as_a_circle`).
   - `grow_hitbox` on a line: thickness plus twice the margin, ends unchanged (`test_growing_a_line_adds_twice_the_margin_to_its_thickness_and_keeps_its_ends`).
   - Guard: shape kinds equal `{Circle, Box, Line}` and `TABLES` has all six unordered pairs. Unknown shape kind raises `TypeError` from the three functions, with a line on the other side too.
   - Chain lightning ship cases: 14, one per variant and `invert` value in `game/tuning/drifters/chain_lightning.json` (7 variants x 2). No variant is named in the test. Per place: WARNING never touches, charging never touches (first and last charge state), firing (first and last fire state) matches the contract's hitbox (arcs, then nodes) and overlaps the ship at the middle of each arc, at each node, and with the nearest edge 0.5 px inside the ship's 32 x 32 square on four sides; it doesn't overlap when 1e-6 px clear on those four sides. Node and arc numbers come from the file; mirroring uses the file's own `invert_mirror`.
   - Meteorite and satellite ship cases still run from their files (5 cases). A type with no tuning file still fails the first test and names the type.
   - Mutation check on a copy of `game/` in the scratchpad (not saved in the repo): 14 mutations of `collision.py` and `chain_lightning.py` (non-strict touches, no segment clamp, wrong node radius, wrong arc width, `invert` ignored, firing while charging, line grown by one margin, a line placed by one end, hitbox order, corners skipped, crossings skipped). 12 were caught. Two survived: a node-on-screen widening (the on-screen rule is task DRA-47-08) and removing the collinear-touch branch of `_segments_meet`, which is redundant (an end of one collinear or T-joined segment always lies on the other, so the end distance gives 0).
4. **Assumptions:**
   - The chain lightning is moved to a firing or charging state with `dataclasses.replace(ticks_in_phase=...)` on a chain made ACTIVE, so its position is exact. The cycle itself is task DRA-47-08.
   - The ship's 32 x 32 square (`SHIP_W`, `SHIP_H`, `FOOT_H`) is the GDD value already used in the file (04-ship.md, guess).
   - Clear placements sit 1e-6 px past touching, because the diagonal and triangle layouts have irrational node positions.
   - The chain lightning branch sits in the file's loader, keyed on `DrifterType.CHAIN_LIGHTNING`, because its file has no `hitbox` list.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer: `game/app/tuning.py` still fails typecheck on `Line` (lines 250-251); that is the expected DRA-47 integration change. Architect and Scope Guardian: nothing open from this task. Task file stays `Status: open` for close-out.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (4 errors, all `game/app/tuning.py`, expected until integration) · core PASS (1286 tests) · ui PASS (17 tests)
QA: fail (typecheck)
