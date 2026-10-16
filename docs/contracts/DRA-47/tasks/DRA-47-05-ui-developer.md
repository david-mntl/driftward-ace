Feature: DRA-47
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-52

## Read in the contract
- Interface, `game/ui/drifters/`: `draw_entry_warning` (its DRA-47 comment).
- Interface, `game/core/drifters/base.py`: `warning_copy`.
- Presentation: the table rows for `obj.warning_copy()` and `obj.width`; Entry warning (all of it, R and Copy in particular).
- Rules, The base: Warning copy (what the core method means; the view only reads it).

## Builds
- `game/ui/drifters/entry_warning.py` (changed)

## Depends on
DRA-47-02

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
from core.drifters.meteorite import Meteorite
from ui.drifters.entry_warning import draw_entry_warning
class Wide(Meteorite):
    def warning_copy(self):
        return replace(self, variant='copy', width=80.0, height=80.0)
seen = []
def view(surface, obj, center, scale, brightness):
    seen.append((obj.variant, obj.width, scale, brightness))
def glow_span(s):
    xs = [x for x in range(200) for y in range(200) if tuple(s.get_at((x, y)))[:3] == (255, 220, 120)]
    return max(xs) - min(xs)
s = pygame.Surface((200, 200))
draw_entry_warning(s, Wide(uid=3, x=100.0, y=-10.0, variant='small', width=20.0, height=20.0, speed=0.0, hitbox=(Circle(0, 0, 10),), warning_ticks=60), view)
print(seen, glow_span(s) > 50)
seen.clear()
s.fill((0, 0, 0))
draw_entry_warning(s, Meteorite(uid=4, x=100.0, y=-10.0, variant='small', width=20.0, height=20.0, speed=0.0, hitbox=(Circle(0, 0, 10),), warning_ticks=60), view)
print(seen, glow_span(s) <= 20)
"
```
It prints two lines:
- `[('copy', 80.0, 0.5, 1.0)] True`: the warning draws the drifter's warning copy, at half size and full brightness, and is sized on the copy's 80 px width.
- `[('small', 20.0, 0.5, 1.0)] True`: a meteorite's copy is itself, and its warning is as before.

Put the command and its output in the implementation report. `game/tests/check.sh lint` and `ui` pass (apart from `test_drifter_registry.py` once task DRA-47-03 is done, until task DRA-47-06), and `typecheck` passes in `game/ui/drifters/`.

## Out of scope
- The chain lightning view (task DRA-47-06). `game/ui/shapes.py` (task DRA-47-04).
- `game/ui/drifters/registry.py`, `meteorite_view.py`, `satellite_view.py`: no change.
- Any core file or test file.
