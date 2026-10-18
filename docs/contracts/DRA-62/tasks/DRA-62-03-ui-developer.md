Feature: DRA-62
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-72

## Read in the contract
- Diagram: Coin (the pixel map) and the views flowchart.
- Interface, `game/core/drifters/coin.py`: the `Coin` fields the view reads (built by DRA-62-01).
- Interface, `game/ui/drifters/`: `dim_color`, `register_view`, the `coin_view.py` block and the `__init__.py` comment.
- Presentation: the table rows for `obj.brightness()` and the three coin rows; Brightness; Coin (all of it); Rules for every view.
- Rules, Coin (Drawn parts: the view keeps every pixel inside those boxes).
- Impact, the DRA-62 table (the `ui/drifters` rows). Rationale, the DRA-62 lines on the 12 × 20 pixels and on what stays in the view.

## Builds
- `game/ui/drifters/coin_view.py` (new)
- `game/ui/drifters/__init__.py` (changed)

## Depends on
DRA-62-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame
from core.drifters.base import Phase
from core.drifters.coin import Coin, coin_hitbox
from ui.drifters.registry import render_drifter
pygame.init()
surface = pygame.Surface((640, 480))
coin = Coin(x=440.0, y=210.0, variant='rare', width=12.0, height=20.0, speed=0.0, hitbox=coin_hitbox(12, 10), warning_ticks=0, phase=Phase.ACTIVE, points=100, glint=True, body_height=10, ring_width=22, ring_height=8, glint_size=2, glint_left=3, glint_top=3, popup_ticks=60, popup_rise_per_tick=0.5)
render_drifter(surface, coin)
for point in ((437, 203), (436, 210), (442, 210), (434, 209), (445, 209)):
    print(point, tuple(surface.get_at(point))[:3])
ink = [(x, y) for x in range(640) for y in range(480) if tuple(surface.get_at((x, y)))[:3] != (0, 0, 0)]
print(min(x for x, _ in ink), max(x for x, _ in ink), min(y for _, y in ink), max(y for _, y in ink))
"
```
It prints the glint (255, 220, 240), the lit side (200, 30, 90), the shade side (70, 0, 60), the rim twice (255, 80, 150), then `429 450 200 219`: every pixel inside the ring's columns and the crystal's rows, as the contract's pixel map says. Put the command and its output in the implementation report. `game/tests/check.sh lint` and `typecheck` pass; `test_drifter_registry.py` passes once `game/tuning/drifters/coin.json` exists.

## Out of scope
- The points popup's view (task DRA-62-04).
- Any core file, `game/app/`, `game/tuning/`, tests.
- The galaxy core, cloud, swirl, shine, glint animation, sprites, sound.
- Any change to the entry warning, the registry or the other views.
