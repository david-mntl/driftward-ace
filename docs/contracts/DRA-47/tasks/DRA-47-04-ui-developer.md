Feature: DRA-47
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-51

## Read in the contract
- Interface, `game/ui/shapes.py`.
- Interface, `game/core/collision.py`: `Line` (the fields the view reads).
- Presentation: Line shape; Rules for every view.

## Builds
- `game/ui/shapes.py` (changed)

## Depends on
DRA-47-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame
pygame.init()
from core.collision import Line
from ui.shapes import draw_shape
def px(s, x, y): return tuple(s.get_at((x, y)))[:3]
s = pygame.Surface((100, 100))
draw_shape(s, (255, 255, 255), Line(20, 50, 80, 50, 6))
W = (255, 255, 255)
print(px(s, 50, 50) == W, px(s, 50, 40) != W, px(s, 50, 60) != W, px(s, 18, 50) == W, px(s, 14, 50) != W, px(s, 86, 50) != W)
s.fill((0, 0, 0))
draw_shape(s, (0, 255, 0), Line(20, 50, 80, 50, 6), 1)
G = (0, 255, 0)
print(px(s, 50, 50) != G, any(px(s, 50, y) == G for y in range(45, 50)), any(px(s, 50, y) == G for y in range(51, 56)), any(px(s, x, 50) == G for x in range(14, 19)))
try:
    draw_shape(s, G, object())
except TypeError as err:
    print(err)
"
```
It prints three lines:
- `True True True True True True`: the filled band is 6 px thick, with a round end reaching past A, and nothing beyond the ends.
- `True True True True`: the outline is hollow, with both long sides and the outer round end.
- `unknown shape kind 'object'`

Put the command and its output in the implementation report. `game/tests/check.sh lint` and `ui` pass (apart from `test_drifter_registry.py` once task DRA-47-03 is done, until task DRA-47-06), and `typecheck` no longer fails in `game/ui/shapes.py`.

## Out of scope
- The chain lightning view (task DRA-47-06). The entry warning (task DRA-47-05).
- `game/ui/debug_overlay.py`: it draws line outlines through this module with no change.
- Any core file or test file.
