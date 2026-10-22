Feature: DRA-86
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-91

## Read in the contract
- Interface, `game/core/collision.py`: `Polygon` (built by DRA-86-01).
- Interface, `game/ui/shapes.py`: the `draw_shape` comment.
- Presentation: Polygon shape (all of it); Rules for every view.
- Impact, the DRA-86 table (the `ui/shapes.py` row).

## Builds
- `game/ui/shapes.py` (changed)

## Depends on
DRA-86-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame
from core.collision import Polygon, place_hitbox
from ui.shapes import draw_shape
pygame.init()
surface = pygame.Surface((640, 480))
tri = place_hitbox((Polygon(((-160.0, -60.0), (160.0, 60.0), (-160.0, 60.0))),), 320.0, 300.0)[0]
draw_shape(surface, (255, 255, 255), tri)
def row(r):
    return [x for x in range(640) if tuple(surface.get_at((x, r)))[:3] == (255, 255, 255)]
print(row(240), min(row(355)), max(row(355)), max(row(359)), row(360))
draw_shape(surface, (255, 0, 0), Polygon(((100.0, 100.0), (110.0, 100.0), (110.0, 110.0), (100.0, 110.0))))
red = [(x, y) for x in range(90, 120) for y in range(90, 120) if tuple(surface.get_at((x, y)))[:3] == (255, 0, 0)]
print(len(red), min(red), max(red))
surface.fill((0, 0, 0))
draw_shape(surface, (0, 255, 0), tri, 1)
print(tuple(surface.get_at((160, 300)))[:3], tuple(surface.get_at((300, 330)))[:3])
"
```
It prints three lines:
- `[160] 160 467 478 []`: the filled triangle by the pixel-center rule: one pixel on its top row, row 355 from 160 to 467, the bottom row to 478, nothing on row 360.
- `100 (100, 100) (109, 109)`: a square polygon fills exactly what a box with the same edges fills.
- `(0, 255, 0) (0, 0, 0)`: the outline is drawn on the left edge and the inside stays empty.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes; `typecheck`, `core` and `ui` fail only where the contract's DRA-86 Impact table expects.

## Out of scope
- The island's view (task DRA-86-06).
- Any core file, `game/app/`, `game/tuning/`, tests.
- Any change to how circles, boxes and lines are drawn, or to the debug overlay.
