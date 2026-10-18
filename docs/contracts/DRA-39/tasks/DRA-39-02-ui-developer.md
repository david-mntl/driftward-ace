Feature: DRA-39
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-41

## Read in the contract
- Interface, `game/ui/drifters/`: `DrifterView` (the new `brightness` argument), `dim_color`, `render_drifter`, `draw_entry_warning`, `render_meteorite`.
- Presentation: the table rows for `obj.warning_tilt_degrees()` and `obj.brightness()`; Brightness; Meteorite; Entry warning (Copy and Pre-rendered); Rules for every view.
- Rules, The base: Warning tilt and Re-hit cooldown (what the two core methods mean; the view only reads them).

## Builds
- `game/ui/drifters/registry.py` (changed)
- `game/ui/drifters/entry_warning.py` (changed)
- `game/ui/drifters/meteorite_view.py` (changed)

## Depends on
DRA-39-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
from dataclasses import replace
import pygame
pygame.init()
from core.collision import Circle
from core.drifters.base import Phase
from core.drifters.meteorite import Meteorite
from ui.drifters.registry import dim_color, render_drifter
from ui.drifters.entry_warning import draw_entry_warning
rock = Meteorite(uid=1, x=50.0, y=50.0, variant='big', width=40, height=40, speed=0.0, hitbox=(Circle(0, 0, 20),), warning_ticks=60, phase=Phase.ACTIVE)
s = pygame.Surface((100, 100))
render_drifter(s, rock)
print(tuple(s.get_at((50, 50)))[:3])
s.fill((0, 0, 0))
render_drifter(s, replace(rock, rehit_ticks_left=5))
print(tuple(s.get_at((50, 50)))[:3])
print(dim_color((60, 110, 220), 0.75))
class Tilted(Meteorite):
    def warning_tilt_degrees(self):
        return -20.0
def bar(surface, obj, center, scale, brightness):
    pygame.draw.rect(surface, (255, 255, 255), pygame.Rect(round(center[0]) - 9, round(center[1]), 19, 1))
w = Tilted(uid=2, x=50.0, y=-20.0, variant='big', width=40, height=40, speed=0.0, hitbox=(Circle(0, 0, 20),), warning_ticks=60)
s.fill((0, 0, 0))
draw_entry_warning(s, w, bar)
white = sorted((x, y) for x in range(100) for y in range(100) if tuple(s.get_at((x, y)))[:3] == (255, 255, 255))
print(white[0][1] < white[-1][1])
"
```
It prints four lines:
- `(140, 140, 140)`: an active rock at full brightness.
- `(105, 105, 105)`: the same rock during its re-hit cooldown, at 0.75.
- `(45, 83, 165)`: `dim_color` rounds half up.
- `True`: a warning copy with tilt −20 is turned clockwise, so its right end is lower than its left.

Put the command and its output in the implementation report. `game/tests/check.sh lint`, `typecheck` (apart from the test files named in the drifters.md Impact) and `ui` pass.

## Out of scope
- The satellite view (task DRA-39-04).
- Any core file. `game/ui/shapes.py`, `game/ui/debug_overlay.py`.
- Any test file.
