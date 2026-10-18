Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-47-01-gameplay-implementer (the `Line` shape in `game/core/collision.py`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-47-01-gameplay-implementer.md
3. **Checks:**
   - `check.sh`: `QA: fail (typecheck core ui)`. Every failure sits in a file the drifters.md Impact (DRA-47) names, owned by a later task: typecheck errors only in `ui/shapes.py` (DRA-47-04), `app/tuning.py` (integration) and `tests/core/test_collision.py` (DRA-47-07); core: 447 pass, 1 fail, the shape-kind guard test (DRA-47-07); ui: `test_drifter_lists_match_everywhere` fails because `game/tuning/drifters/chain_lightning.json` exists and `DrifterType.CHAIN_LIGHTNING` does not yet (DRA-47-03). None come from `core/collision.py`. lint and format pass.
   - Acceptance check, run from `game/`, output matches the task's four expected lines:
     ```
     False True False True
     True False True
     False True True
     True True
     ```
   - Edge cases that behave correctly: unknown shape raises `TypeError("unknown shape kind 'object'")` in `place_hitbox`, `grow_hitbox` and `hitboxes_overlap` (also against an empty hitbox); empty hitbox overlaps nothing; A equal to B acts as a circle (touch False, a sixteenth closer True); argument order never changes the result; grow adds twice the margin to thickness.
   - Fuzz: 200,000 random line/circle, line/line and line/box pairs (quarter-unit coordinates, degenerate and axis-aligned lines included) against an exact `Fraction` reference, both argument orders. 5 mismatches, all exact-touch cases that must be "no overlap" and return overlap. See B1. Same seed, same result on re-run.
4. **Assumptions:** The reference treats overlap as strict (`<`) on the exact squared distance, as the contract's Rules, Collision says.
5. **Documentation differences:** None.
6. **Next:** Gameplay Implementer, Fix mode, bug B1 in this report. Then re-test.
7. **Status:** done.

## Bugs
- **B1** `game/core/collision.py:203-213` (`_point_segment_dist_sq`), Gameplay Implementer. A slanted line that only touches a circle, another line or a box reads as overlapping. The projection `t` is a non-dyadic float, so the closest point is rounded and the squared distance lands a hair under the exact value.
  Reproduce (from `game/`):
  ```
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python -c "
  from core.collision import *
  print(hitboxes_overlap((Line(-1,-3,1.5,3,1.5),),(Circle(-2,-1.5,0.75),)))
  print(hitboxes_overlap((Line(-1,-2,2,-6,1),),(Box(0.25,0,0.5,5),)))
  print(hitboxes_overlap((Line(5,-3,2,1,0.5),),(Line(-5,0.5,1.5,0,1.5),)))
  print(hitboxes_overlap((Line(0,1,-2,-0.5,2),),(Box(0,-2.5,2,3),)))
  print(hitboxes_overlap((Line(-1.5,3,-0.25,2,0.75),),(Line(-0.75,-0.5,0.5,2.5,0.25),)))
  "
  ```
  Expected: `False` five times. First case: the segment direction is (2.5, 6), length 6.5, the circle center is exactly 1.5 from the segment (cross 9.75 / 6.5), and h + r = 0.75 + 0.75 = 1.5, so the shapes touch. Actual: `True` five times.
  Source: drifters.md, Rules, Collision (overlap is strict: touching is no overlap; Line and circle: distance < h + r; Line and box: distance < h; Line and line: distance < h1 + h2) and Rationale, "The line is a capsule, measured squared" (squared comparison keeps whole numbers and halves exact, so the line's collision tables can hold exact edge cases).
  Proposed fix: in `_point_segment_dist_sq`, keep the clamp as an ends test on the dot product and use the cross product inside the segment, with no `t`:
  ```
  dot = (p[0]-a[0])*abx + (p[1]-a[1])*aby
  if length_sq == 0.0 or dot <= 0.0: return squared distance p to a
  if dot >= length_sq:               return squared distance p to b
  cross = (p[0]-a[0])*aby - (p[1]-a[1])*abx
  return cross * cross / length_sq
  ```
  With dyadic inputs `cross * cross` and `length_sq` are exact, and one correctly rounded division of an exactly representable quotient is exact, so touching cases come out equal to `reach * reach` and the strict `<` returns False. I patched a scratch copy this way (not in the repo) and re-ran the same 200,000 pairs: 0 mismatches, and the acceptance check output is unchanged. The line/line and line/box paths call this helper, so one change fixes all five cases.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (18 errors, all in `ui/shapes.py`, `app/tuning.py`, `tests/core/test_collision.py`, as the task allows) · core FAIL (447 pass, 1 fail: the guard test, DRA-47-07) · ui FAIL (`test_drifter_lists_match_everywhere`, DRA-47-03)
QA: fail (typecheck core ui)

## Round 2 2026-10-16

1. **Task:** Re-test of bug B1 after the Fix 2026-10-16 section in `docs/reports/implementation/gameplay/DRA-47-01-gameplay-implementer.md`, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-47-01-gameplay-implementer.md (this round appended).
3. **Checks:**
   - B1 reproduce command re-run from `game/`: `False` five times (expected `False`). Fixed.
   - Acceptance check unchanged by the fix (the Round 1 output still holds; the fuzz below covers the same shapes).
   - Fuzz, new seed: 300,000 random line/circle, line/line and line/box pairs (quarter-unit coordinates, degenerate A = B, vertical and horizontal lines included) against an exact `Fraction` reference, both argument orders. 1,102 of them are exact touches. 0 mismatches. Run twice: identical.
   - Neighbors of the fix: a line end exactly at the circle edge past A reads no overlap, a hair more reads overlap; A = B line acts as a circle; a zero-radius circle touching the line's end cap reads no overlap, radius 0.0001 reads overlap. All correct.
   - `check.sh`: same state as Round 1. Remaining failures sit only in files owned by later DRA-47 tasks (see Harness). Nothing comes from `core/collision.py`.
4. **Assumptions:** Same as Round 1: overlap is strict on the exact squared distance.
5. **Documentation differences:** None.
6. **Next:** No bug is open in `core/collision.py`. `QA: pass` can't print until DRA-47-03 (`DrifterType.CHAIN_LIGHTNING`), DRA-47-04 (`ui/shapes.py` typecheck), DRA-47-07 (`tests/core/test_collision.py` guard test and typecheck) and the `app/tuning.py` integration land. Verdict is `blocked` for that reason only. Re-check `check.sh` once those land. This task can go on to the Integration Engineer queue once the Director or `/implement` accepts the later-task failures.
7. **Status:** done.

## Bugs
- **B1** `game/core/collision.py:203-221`, Gameplay Implementer. Fixed. Same reproduce command now prints `False` five times; fuzz shows 0 mismatches.
- No new bugs.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (18 errors: `app/tuning.py` 4, `tests/core/test_collision.py` 13, `ui/shapes.py` 1; none in `core/`) · core FAIL (447 pass, 1 fail: `test_every_shape_kind_and_every_pair_of_kinds_has_a_table`, DRA-47-07) · ui FAIL (16 pass, 1 fail: `test_drifter_lists_match_everywhere`, DRA-47-03)
QA: fail (typecheck core ui)

## Round 3 2026-10-16

1. **Task:** Re-test of DRA-47-01 (the `Line` shape in `game/core/collision.py`) after DRA-47 tasks 03 to 08 landed, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-47-01-gameplay-implementer.md (this round appended).
3. **Checks:**
   - `check.sh`: env, lint, format, core (1312 pass) and ui (17 pass) all PASS. Only typecheck fails: 4 errors, all in `app/tuning.py:250-251` (`Line` has no `w`, `h`, `cx`, `cy`). The Integration Engineer updates that file during DRA-47 integration (docs/contracts/systems/app.md, Ownership). It is not this task's code, so it does not fail the task.
   - Acceptance check re-run from `game/`: output matches the task's four expected lines (`False True False True` / `True False True` / `False True True` / `True True`).
   - B1 reproduce cases (circle and box touches) still print `False`.
   - Fuzz, new seed: 150,000 random line/circle and line/line pairs (quarter-unit coordinates, zero radius included) against an exact `Fraction` reference, circle both argument orders. 323 are exact touches. 0 mismatches.
4. **Assumptions:** Overlap is strict on the exact squared distance (drifters.md, Rules, Collision). The `app/tuning.py` typecheck errors don't fail this task, as the main session instructed.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Update `game/app/tuning.py:250-251` so it handles `Line` (typecheck errors above) as part of DRA-47 integration.
7. **Status:** done.

## Bugs
- **B1** `game/core/collision.py`. Fixed (Round 2), still fixed.
- No open bugs. No new bugs.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (4 errors, all `app/tuning.py`, Integration Engineer's file, allowed) · core PASS (1312) · ui PASS (17)
QA: fail (typecheck)
