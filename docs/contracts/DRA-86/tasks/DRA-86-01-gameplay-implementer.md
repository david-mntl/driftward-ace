Feature: DRA-86
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-87

## Read in the contract
- Purpose (the Who builds what lines for DRA-86).
- Diagram: Floating island (the shapes, the triangle's points and its slope normals).
- Interface, `game/core/collision.py`: `Polygon`, `Shape`, `Direction`, `SURFACE_TOLERANCE`, the comments on `place_hitbox` and `grow_hitbox`, the TypeError comment, `deeply_overlaps`, `push_directions`, `exit_distance` and the comment after them.
- Rules: Collision (all of it, with the Polygon bullets and the new `grow_hitbox` and Unknown shape kind text); Push-out (all of it).
- Impact, the DRA-86 table (the `collision.py` and `test_collision.py` rows). Rationale, the DRA-86 lines on polygons, raw edge normals, the grown polygon, the push-out and `SURFACE_TOLERANCE`.

## Builds
- `game/core/collision.py` (changed)

## Depends on
None.

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.collision import Box, Circle, Polygon, deeply_overlaps, exit_distance, grow_hitbox, hitboxes_overlap, place_hitbox, push_directions
tri = place_hitbox((Polygon(((-160.0, -60.0), (160.0, 60.0), (-160.0, 60.0))),), 400.0, 330.0)
ship = (Box(320.0, 240.0, 12.0, 32.0), Box(320.0, 250.0, 32.0, 12.0))
print(hitboxes_overlap(tri, ship), hitboxes_overlap(tri, (Box(400.0, 330.0, 2.0, 2.0),)), hitboxes_overlap(tri, (Circle(560.0, 270.0, 5.0),)))
print(len(grow_hitbox(tri, 14.0)))
moving = (Box(0.0, 0.0, 10.0, 10.0),)
below = (Box(0.0, 8.0, 20.0, 10.0),)
print(exit_distance(moving, below, (0.0, -1.0)), exit_distance(moving, below, (0.0, 1.0)))
print(exit_distance(moving, below + (Box(0.0, -6.0, 20.0, 10.0),), (0.0, -1.0)))
print(exit_distance(moving, (Box(0.0, 20.0, 20.0, 10.0),), (0.0, -1.0)), deeply_overlaps(moving, (Box(0.0, 10.0, 20.0, 10.0),)))
directions = push_directions(ship, tri)
print(len(directions), tuple(round(v, 4) for v in directions[4]))
try:
    exit_distance((Circle(0.0, 0.0, 1.0),), below, (0.0, -1.0))
except TypeError as error:
    print(error)
"
```
It prints seven lines:
- `False True False`: the ship is clear of the triangle, a small box on its slope overlaps it, a circle in its empty top-right corner doesn't.
- `4`: the grown triangle is itself plus three edge lines.
- `2.0 18.0`: out of a box below, 2 px up or 18 px down.
- `16.0`: with a second box above, the way up runs through both.
- `0.0 False`: clear, and an edge touch is not deep.
- `6 (0.3511, -0.9363)`: up, down, left, right, then the slope's outward normal (and its inward one).
- `exit_distance takes boxes and polygons, not 'Circle'`.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. `typecheck` and the `core` tests fail only where the contract's DRA-86 Impact table says `test_collision.py` breaks (the guard test, `moved` and `anchor`); every other test passes unchanged.

## Out of scope
- The island drifter, the ship's block, the respawn spot and the run (tasks DRA-86-02 to DRA-86-04).
- `game/ui/shapes.py` (task DRA-86-05), `game/app/`, `game/tuning/`, tests.
- Circles and lines in the push-out functions: they take boxes and polygons only.
