Feature: DRA-86
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-93

## Read in the contract
- Interface, `game/core/collision.py`: `Polygon`, `Shape`, `Direction`, `SURFACE_TOLERANCE`, `grow_hitbox`, `deeply_overlaps`, `push_directions`, `exit_distance`.
- Interface, `game/core/drifters/floating_island.py`: `IslandShape`, `IslandVariantExtra`, `IslandTypeExtra`, `island_hitbox`.
- Diagram: Floating island (the shapes, points and slope normals).
- Rules: Collision (all of it, the Polygon bullets in particular); Push-out (all of it); Floating island (Variants; Hitbox; Born; Touch); Tuning files (The floating island's file: what the loader builds from it).
- `docs/contracts/schemas/floating-island-tuning.schema.json`: the file the ship test reads.
- Impact, the DRA-86 table (the `test_collision.py` row: why the file breaks today).

## Builds
- `game/tests/core/test_collision.py` (changed)
- `game/tests/CONTEXT.md` (changed: the `core/test_collision.py` paragraph)

## Depends on
DRA-86-01, DRA-86-02, and `game/tuning/drifters/floating_island.json` filled to its schema (content, by whoever the Director names; contract Impact).

## Not in the contract
- Like the coin's, the island gets its own branch in `load_variant_cases`, built from the file the way `app.tuning` builds it (contract, Tuning files), one case per variant and per `invert` value the variant's shape allows, with no variant named in test code. Source: tests/CONTEXT.md, Rules (the `core/test_collision.py` paragraph).

## Test
- Exact-number tables for polygon and polygon, polygon and box, polygon and circle, polygon and line, through every existing table test (both orders, moved, empty, a shape added, grown). Rules: Collision (Polygon).
- A triangle against shapes on its slope, at each corner and along each flat side: sharing area overlaps, touching an edge or a corner doesn't. Rules: Collision (Polygon).
- A polygon given in the other point order gives the same results. Rules: Collision (Polygon).
- A grown polygon is the polygon then one line per edge, thickness twice the margin, and meets a shape within the margin of a corner and not one just beyond it. Rules: Collision (`grow_hitbox`).
- The guard: every shape kind, `Polygon` included, has its tables. Rules: Collision (Unknown shape kind).
- `deeply_overlaps` is False for touching shapes and for an overlap no deeper than `SURFACE_TOLERANCE`, True just deeper. Rules: Push-out.
- `exit_distance`: a box out of a box in each of the four directions with exact numbers; through two shapes that chain (the L's boxes, two overlapping boxes); 0.0 when not deep; along the triangle's slope normal it equals the depth across the slope. Rules: Push-out.
- `push_directions` for the ship against each island variant: the four axis directions first, then the triangle's slope normal out and in, with no repeat. Rules: Push-out.
- The three push-out functions raise `TypeError` naming the function and the kind for a circle or a line on either side. Rules: Push-out.
- The ship meets every island variant and `invert` at its own touching distance on each outer side, and on the triangle's slope: just clear doesn't overlap, 0.5 px inside does. An island overlaps the ship on the state it is spawned on (no WARNING), its touch is BLOCK, and it has no graze zone. Rules: Floating island (Hitbox; Born; Touch).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with the polygon tables, the push-out tests and the island cases in `test_collision.py` in the `core` step and `typecheck` passing on it. Until task DRA-86-09 is done, the only failure left is the type list in `test_wave_files.py`, which that task fixes (contract, Impact); `test_drifter_registry.py` passes once DRA-86-06 and the island's file are in.

## Out of scope
- The ship's block, the respawn spot and the run (tasks DRA-86-08 and DRA-86-09).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
