Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** Add the `Line` shape to collision (overlap, place, grow, unknown-shape guard), from `docs/contracts/DRA-47/tasks/DRA-47-01-gameplay-implementer.md`, by the Architect.
2. **Delivered:** `game/core/collision.py` (changed): `Line` dataclass, `Shape = Circle | Box | Line`, `place_hitbox` moves both ends, `grow_hitbox` adds twice the margin to thickness, `hitboxes_overlap` handles line against circle, line, box. Unknown kinds still raise `TypeError("unknown shape kind '<name>'")`.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: ok (pygame-ce 2.5.8). `python -m py_compile game/core/collision.py`: clean.
   - `ruff check game`, `ruff format --check game`, `game/tests/check.sh lint`: pass.
   - Acceptance smoke, run from `game/` (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <the task's command>`). Output:
     ```
     False True False True
     True False True
     False True True
     True True
     ```
     Matches the task's expected four lines. Extra cases I ran: degenerate line (A = B) behaves as a circle (True at 1.0625 gap-reach, False when touching); collinear segments overlap/touch/gap as expected; a diagonal line through a box and a line through a box center overlap; empty hitbox is False; `place_hitbox`, `grow_hitbox` and `hitboxes_overlap` raise the unknown-shape `TypeError` for a plain `object`.
   - Determinism: the same smoke run twice, outputs identical.
   - `typecheck`: errors only in `app/tuning.py` (4), `ui/shapes.py` (1) and `tests/core/test_collision.py` (13), the files the drifters.md Impact names. None in `core/collision.py` (`mypy --strict core/collision.py` clean for that file). `check.sh core`: 447 pass, 1 fails: `test_every_shape_kind_and_every_pair_of_kinds_has_a_table`, the guard test that expects `{Circle, Box}` (task DRA-47-07).
   - Grep of `game/core/` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: only hits are the ban messages in `game/core/ruff.toml`. None in code.
4. **Assumptions:** None beyond the contract. A line's thickness is not validated (contract says > 0; core trusts its values per `game/CONTEXT.md`).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-47/tasks/DRA-47-01-gameplay-implementer.md`. Left alone: `ui/shapes.py`, `app/tuning.py`, `tests/core/test_collision.py` (other owners; they fail typecheck/core until DRA-47-04, DRA-47-07 and integration).
7. **Status:** done.

## Decisions
- Overlap is strict (`<`) and squared, no square root, per Rules, Collision. Line against circle: point-to-segment distance squared < (h + r)^2. Line against line: segment distance squared < (h1 + h2)^2. Line against box: segment-to-box distance squared < h^2. `h = thickness / 2`.
- Point to segment uses the clamped projection; A equal to B falls back to point distance (a circle of radius h).
- Segments meet: cross-product signs for a proper crossing, plus collinear/on-segment checks for touching. If they don't meet, the distance is the smallest of the four end-to-other-segment distances.
- Segment against box: 0 when an end is inside or on the box, or the segment meets any of the four edges. Otherwise the smaller of the two end-to-box distances and the four corner-to-segment distances.
- Dispatch: `_shapes_overlap` sends any pair holding a line to `_line_overlaps(line, other)` first, so the result is order-independent and the existing circle/box code is untouched.
- `_HALF = 0.5` is a private constant for "half"; no game value is in code. Every other number comes from the caller's shapes.
- No logging, no randomness, stdlib only. The `Final` import is for the private constant.

## Review fix 2026-10-16: docs/reports/review/DRA-47-01-gameplay-implementer.md

Fixed: DRA-47-01-F1

1. **Task:** Answer the round 1 review of the line shape in collision (one should-fix), by the `/implement` skill.
2. **Delivered:** `game/core/collision.py` (changed): `_circle_box_overlap` now calls `_point_box_dist_sq`; every halving is `/ 2`; the private `_HALF` constant and the `Final` import are removed.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: ok. `python -m py_compile game/core/collision.py`: clean.
   - `ruff check game`, `ruff format --check game`, `game/tests/check.sh lint`: pass.
   - Smoke: the task's acceptance command, run from `game/` as `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <the task's command>`. Output unchanged:
     ```
     False True False True
     True False True
     False True True
     True True
     ```
     Plus a circle/box spot check (touching: False; inside by a hair: True; circle overlapping a box face: True): `True False True` for (circle at 0,0 r1 vs box at 1,0 2x2), (circle at -1,0 r1 vs same box), (circle r1.0625 vs box 1.5,0 1x1). Same run twice: identical output.
   - `game/tests/check.sh core`: 447 pass, 1 fails, the same guard test as before (`test_every_shape_kind_and_every_pair_of_kinds_has_a_table`, task DRA-47-07). No existing circle/box test broke.
   - Grep of `game/core/*.py` for the banned calls: no hits.
4. **Assumptions:** `x / 2` and `x * 0.5` give the same float, so circle/box results can't change. The core suite agrees.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, Re-check mode, review report `docs/reports/review/DRA-47-01-gameplay-implementer.md`.
7. **Status:** done.

**Decisions**
- Chose `/ 2` over `_HALF` because the pre-existing circle/box and box/box code already used it, so the diff stays small and the constant (and its `Final` import) goes away.
- The circle/box rule now lives in one place, `_point_box_dist_sq`; line/box and circle/box share it.

**Answers**
- DRA-47-01-F1. Fixed: `game/core/collision.py:175-177`, `_circle_box_overlap` returns `_point_box_dist_sq((circle.cx, circle.cy), box) < circle.r * circle.r`; halving is `/ 2` everywhere (`_HALF` removed, uses at `_line_overlaps`, `_point_box_dist_sq`, `_box_corners`).

## Fix 2026-10-16: docs/reports/qa/DRA-47-01-gameplay-implementer.md

1. **Task:** Fix bug B1 from QA: a slanted line that only touches a circle, line or box read as overlapping.
2. **Delivered:** `game/core/collision.py` (changed): `_point_segment_dist_sq` (now lines 203-221).
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: ok. `python -m py_compile game/core/collision.py`: clean.
   - `ruff check game`: pass. `ruff format --check game`: 50 files formatted.
   - Reproduction from the bug report, run from `game/` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python <the five B1 prints>`: before the fix `True` five times, after: `False` five times.
   - Acceptance check output unchanged: `False True False True` / `True False True` / `False True True` / `True True`.
   - Extra: 100,000 random line/circle pairs (quarter-unit coordinates) against an exact `Fraction` reference, both argument orders: 0 mismatches.
   - `game/tests/check.sh core`: 447 pass, 1 fail, the same guard test as before (DRA-47-07).
   - Same smoke run twice: identical output. Grep of `game/core/*.py` for the banned calls: no hits.
4. **Assumptions:** None. QA's proposed fix is applied as written.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, bug report `docs/reports/qa/DRA-47-01-gameplay-implementer.md`. Left alone: `ui/shapes.py`, `app/tuning.py`, `tests/core/test_collision.py`.
7. **Status:** done.

**Decisions**
- `_point_segment_dist_sq` tests the ends on the dot product (before A, past B) and uses the cross product inside the segment, so there is no projection `t`. With dyadic inputs `cross * cross` and `length_sq` are exact, and the division is exact, so touching cases equal `reach * reach` and the strict `<` gives no overlap. Source: drifters.md, Rules, Collision (touching is no overlap).
- The line/line and line/box paths share this helper, so one change fixes all five cases.
