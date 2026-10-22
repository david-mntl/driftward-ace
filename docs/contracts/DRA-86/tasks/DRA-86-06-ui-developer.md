Feature: DRA-86
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-92

## Read in the contract
- Diagram: Floating island (the shapes) and the views flowchart.
- Interface, `game/core/drifters/floating_island.py`: the `FloatingIsland` fields the view reads (built by DRA-86-02).
- Interface, `game/ui/drifters/`: `dim_color`, `register_view`, the `floating_island_view.py` block and the `__init__.py` comment.
- Presentation: the table rows for `obj.brightness()` and the floating island; Brightness; Floating island (all of it); Polygon shape; Rules for every view.
- Rules, Floating island (Drawn parts: the view keeps every pixel inside the footprint).
- Impact, the DRA-86 table (the `ui/drifters` rows). Rationale, the DRA-86 lines on the pre-rendered look, the edge as the shape less its inset, and what stays in the view.

## Builds
- `game/ui/drifters/floating_island_view.py` (new)
- `game/ui/drifters/__init__.py` (changed)

## Depends on
DRA-86-02, DRA-86-05

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame
from core.drifters.base import Phase
from core.drifters.floating_island import FloatingIsland, IslandShape, island_hitbox
from ui.drifters.registry import render_drifter
pygame.init()
def look(shape, points):
    surface = pygame.Surface((640, 480))
    island = FloatingIsland(x=320.0, y=300.0, variant=shape.value, width=320.0, height=120.0, speed=0.0, hitbox=island_hitbox(shape, 320.0, 120.0, 40.0, False), warning_ticks=0, phase=Phase.ACTIVE, shape=shape, arm=40.0)
    render_drifter(surface, island)
    print([tuple(surface.get_at(point))[:3] for point in points])
    ink = [(x, y) for x in range(640) for y in range(480) if tuple(surface.get_at((x, y)))[:3] != (0, 0, 0)]
    print(min(x for x, _ in ink), max(x for x, _ in ink), min(y for _, y in ink), max(y for _, y in ink))
look(IslandShape.RECTANGLE, ((160, 300), (161, 300), (162, 300), (320, 241), (320, 300), (479, 359)))
look(IslandShape.L_SHAPE, ((199, 250), (198, 320), (198, 330), (300, 340), (200, 250)))
look(IslandShape.TRIANGLE, ((160, 240), (170, 350), (461, 355), (462, 355), (467, 355), (468, 355)))
"
```
It prints six lines, three pairs. For each, the colors at the points, then `160 479 240 359` (the triangle: `160 478 240 359`), every pixel inside the footprint:
- rectangle: edge (35, 90, 45) twice, fill (70, 160, 80), edge, fill, edge.
- L: edge, edge, fill, fill, then (0, 0, 0): nothing drawn in the notch.
- triangle: edge, fill, fill, edge, edge, (0, 0, 0).

These are the points of the contract's Presentation, Floating island, Examples. Put the command and its output in the implementation report. `game/tests/check.sh lint` passes; `test_drifter_registry.py` passes once `game/tuning/drifters/floating_island.json` exists.

## Out of scope
- `game/ui/shapes.py` (task DRA-86-05).
- Any core file, `game/app/`, `game/tuning/`, tests.
- Grass, rock texture, shadows, sprites, sound.
- Any change to the entry warning, the registry, the debug overlay or the other views.
