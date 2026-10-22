Status: ready-for-review
Created by: gameplay-implementer

1. **Task:** `docs/contracts/DRA-86/tasks/DRA-86-01-gameplay-implementer.md`, from the Architect: the `Polygon` shape, its overlap, place and grow rules, and the push-out functions in `game/core/collision.py`.

2. **Delivered:** `game/core/collision.py` (changed). New: `Polygon`, `Direction`, `SURFACE_TOLERANCE`, `deeply_overlaps`, `push_directions`, `exit_distance`. Changed: `Shape`, `place_hitbox`, `hitboxes_overlap`, `grow_hitbox`.

3. **Checks:**
   - IS_CE: true (pygame-ce 2.5.8).
   - `py_compile` clean. `ruff check game` and `ruff format --check game`: no findings. `game/tests/check.sh lint`: pass. `mypy --strict` on `core/collision.py`: no issues.
   - `check.sh typecheck` fails only in `tests/core/test_collision.py` lines 589 and 596 (6 errors, `moved` and `anchor` reading box fields from a `Polygon`). `check.sh core`: 1575 passed, 1 failed, the guard test `test_every_shape_kind_and_every_pair_of_kinds_has_a_table` (finds `Polygon` with no table). These are exactly the breaks the contract's DRA-86 Impact table lists. No other test fails.
   - Acceptance smoke, run from `game/` (command is the task's acceptance command, run with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "..."`). Output:
     ```
     False True False
     4
     2.0 18.0
     16.0
     0.0 False
     6 (0.3511, -0.9363)
     exit_distance takes boxes and polygons, not 'Circle'
     ```
   - Extra: a box sunk into the triangle's slope: exit up 18.25, then not overlapping; exit along the slope normal 17.088, then not deeply overlapping. Inverted triangle's slope normal (0.3511, 0.9363), 6 directions. A line crosses the polygon: True; a line clear of it: True only where it reaches. `place_hitbox` and `grow_hitbox` raise `TypeError("unknown shape kind 'str'")` for a stranger; `push_directions` raises the boxes-and-polygons message for a `Line`.
   - Determinism: the acceptance command run twice, output identical (diffed).
   - Grep of `game/core/collision.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `random.random(`, `.mp3`, `.wav`: no hits.

4. **Assumptions:** `_area_sign` returns -1.0 for a zero-area polygon. The contract says polygons are trusted and never degenerate, so nothing checks it. An axis with `k` exactly 0.0 is treated as square to the direction, as the contract says; no epsilon.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-86/tasks/DRA-86-01-gameplay-implementer.md`. Left alone: `game/ui/shapes.py` (DRA-86-05), the tests (DRA-86-07 fixes the 3 known breaks), the island, ship and run tasks.

7. **Status:** done.

## Decisions
- Overlap: separating axes on raw (non-unit) edge normals for polygon vs polygon and polygon vs box, strict `>` on the shared range. A box is turned into its four corners. Polygon vs circle and polygon vs line follow the contract's Collision bullets. Source: drifters.md, Rules, Collision.
- Line vs polygon uses `_segments_dist_sq` per edge, which is 0 when the segments meet, so "meets an edge" and "closer than h" are one test.
- `grow_hitbox`: `_grow_shape` now returns a tuple so a polygon can become itself plus one line per edge (thickness 2 x margin, edge order). Other shapes return a one-item tuple.
- Push-out: both hitboxes are checked for box/polygon only before anything else, `moving` first. Every pair is a pair of corner tuples (a box becomes its four corners). Unit outward normals use the area sign.
- `exit_distance`: builds each pair's open blocked span (intersection of its axes' intervals; an axis with k = 0 keeps all t or none), then steps `t` to the `high` of a span that contains it until none does. The first free point at or after 0 is unique, so span order doesn't matter.
- `deeply_overlaps` uses the pair's smallest overlap over unit normals against `SURFACE_TOLERANCE`.
- `push_directions` takes only `Polygon` instances for extra directions (solid first, then moving), each normal then its reverse, dropping any within tolerance of an earlier one on both parts.
- Numbers: `SURFACE_TOLERANCE` 1e-9 from the contract's Interface (not a tuning value, Rationale). No other number.
