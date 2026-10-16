Feature: DRA-39
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-43

## Read in the contract
- Interface, `game/ui/drifters/`: `game/ui/drifters/satellite_view.py` and `game/ui/drifters/__init__.py`.
- Presentation: the table row for `obj.hitbox`; Satellite; Brightness; Entry warning (Copy and Place, for how the half-size copy is used); Rules for every view.
- Rules, Satellite: Variants and Warning (which box is which, and the tilt it gets).

## Builds
- `game/ui/drifters/satellite_view.py` (new)
- `game/ui/drifters/__init__.py` (changed)

## Depends on
DRA-39-02, DRA-39-03

## Not in the contract
- The guard test `game/tests/ui/test_drifter_registry.py` passes only once `game/tuning/drifters/satellite.json` exists. That file is content, filled by whoever the Director names (drifters.md, Purpose, Who builds what). If it is missing when this task runs, report it; don't write it.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
from dataclasses import replace
import pygame
pygame.init()
from core.collision import Box
from core.drifters.base import DrifterType, Phase
from core.drifters.satellite import SatelliteVariantExtra
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
import ui.drifters
from ui.drifters.registry import render_drifter
boxes = (Box(0, 0, 12, 12), Box(0, 0, 36, 6))
def variant(angle): return VariantTuning(width=36, height=12, hitbox=boxes, extra=SatelliteVariantExtra(angle_degrees=angle))
sat = DrifterTypeTuning(variants={'flat': variant(0), 'angled': variant(20)}, default_variant='flat', speed_ratio=0.375, entry_warning_ticks=60)
tuning = DrifterTuning(drifters={DrifterType.SATELLITE: sat}, switches=PlaytestSwitches())
s = replace(spawn_drifter(Placement(DrifterType.SATELLITE, x=100.0, y=50.0), 1, tuning), uid=1, phase=Phase.ACTIVE)
surface = pygame.Surface((640, 480))
render_drifter(surface, s)
print([tuple(surface.get_at(p))[:3] for p in ((100, 50), (115, 50), (100, 54), (115, 54))])
surface.fill((0, 0, 0))
render_drifter(surface, replace(s, rehit_ticks_left=5))
print([tuple(surface.get_at(p))[:3] for p in ((100, 50), (115, 50))])
a = replace(spawn_drifter(Placement(DrifterType.SATELLITE, y=200.0, variant='angled', invert=True), 1, tuning), uid=2)
surface.fill((0, 0, 0))
render_drifter(surface, a)
blue = [(x, y) for x in range(640) for y in range(480) if tuple(surface.get_at((x, y)))[:3] == (60, 110, 220)]
left, right = min(x for x, y in blue), max(x for x, y in blue)
print(600 <= left and right <= 640, max(y for x, y in blue if x == left) > max(y for x, y in blue if x == right))
"
```
It prints three lines:
- `[(240, 240, 240), (60, 110, 220), (240, 240, 240), (0, 0, 0)]`: the white body over the middle of the blue bar; the bar is 6 px tall, the body 12.
- `[(180, 180, 180), (45, 83, 165)]`: the same satellite during its re-hit cooldown, at 0.75.
- `True True`: the angled, inverted satellite's warning copy sits against the right wall and runs down to the left.

Then in debug mode, once the Integration Engineer has wired DRA-39 (`docs/contracts/systems/app.md`, Integration checks for DRA-39), a satellite crossing the screen is a white square on a blue bar. Put the command and its output in the implementation report. `game/tests/check.sh lint` and `ui` pass (the guard test needs `satellite.json`, see above).

## Out of scope
- Any core file, the entry warning code (task DRA-39-02), `game/ui/shapes.py`, the debug overlay.
- Sprite art (scope report DRA-39, Out).
- Any test file, any data file.
