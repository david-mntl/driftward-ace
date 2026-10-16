Feature: DRA-47
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-48

## Read in the contract
- Interface, `game/core/collision.py`: `Line`, `Shape`, and the comments on `place_hitbox`, `hitboxes_overlap`, `grow_hitbox`.
- Rules, Collision: all of it, Line and Unknown shape kind included.
- Rationale: "The line is a capsule, measured squared".

## Builds
- `game/core/collision.py` (changed)

## Depends on
None

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.collision import Box, Circle, Line, grow_hitbox, hitboxes_overlap, place_hitbox
line = (Line(0, 0, 10, 0, 6),)
print(hitboxes_overlap(line, (Circle(5, 6, 3),)), hitboxes_overlap(line, (Circle(5, 5.9375, 3),)), hitboxes_overlap(line, (Circle(13, 4, 2),)), hitboxes_overlap((Circle(12.9375, 4, 2),), line))
print(hitboxes_overlap((Line(0, 0, 10, 10, 2),), (Line(0, 10, 10, 0, 2),)), hitboxes_overlap((Line(0, 0, 10, 0, 2),), (Line(0, 2, 10, 2, 2),)), hitboxes_overlap((Line(0, 0, 10, 0, 2),), (Line(0, 1.9375, 10, 1.9375, 2),)))
print(hitboxes_overlap((Line(-10, 0, 0, 0, 10),), (Box(4, 5, 2, 2),)), hitboxes_overlap((Box(3.9375, 5, 2, 2),), (Line(-10, 0, 0, 0, 10),)), hitboxes_overlap((Line(-10, 0, 10, 0, 1),), (Box(0, 0, 4, 4),)))
print(place_hitbox(line, 1, 2) == (Line(1, 2, 11, 2, 6),), grow_hitbox(line, 14) == (Line(0, 0, 10, 0, 34),))
"
```
It prints four lines:
- `False True False True`: a circle that only touches the line's side, or its round end (a 3-4-5 gap), doesn't overlap; a sixteenth closer, it does, in either order.
- `True False True`: crossing lines overlap; parallel lines whose edges touch don't; a sixteenth closer, they do.
- `False True True`: a line whose round end only touches a box corner (3-4-5) doesn't overlap; a sixteenth closer, it does; a thin line through a box does.
- `True True`: placing moves both ends; growing adds twice the margin to the thickness.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. `typecheck` and `core` fail only where the drifters.md Impact (DRA-47) says: `game/ui/shapes.py`, `game/app/tuning.py` and `game/tests/core/test_collision.py`, until tasks DRA-47-04 and DRA-47-07 and integration.

## Out of scope
- Drawing lines (task DRA-47-04). Any drifter that uses them (task DRA-47-03).
- The polygon shape (scope report DRA-47, Out).
- Any test file. Any file outside `game/core/collision.py`.
