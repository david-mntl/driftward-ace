Feature: DRA-104
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-107

## Read in the contract
- Diagram: UFO (the sketch), Views.
- Interface: `game/core/drifters/ufo.py` (`ufo_hitbox`: the hitbox order the view reads); `game/ui/drifters/` (`DrifterView`, `dim_color`, `register_view`, `ufo_view.py`, `__init__.py`); `game/ui/shapes.py` (`draw_shape`).
- Presentation: the table row for the UFO; Brightness (the UFO sentence); UFO (all of it); Entry warning (Copy and Place); Rules for every view.
- Rules: Values (the UFO sentence: what stays in the view).
- Rationale, the DRA-104 lines on the size being the disc and on `DOME_DRAW_MARGIN`.

## Builds
- `game/ui/drifters/ufo_view.py` (new)
- `game/ui/drifters/__init__.py` (changed)

## Depends on
DRA-104-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
from dataclasses import replace
import pygame
from core.drifters.base import DrifterType, Phase
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.drifters.ufo import UfoTypeExtra, ufo_hitbox
from ui.drifters.registry import render_drifter
from ui.drifters.ufo_view import render_ufo
pygame.init()
weave = UfoTypeExtra(weave_change_ticks_min=60, weave_change_ticks_max=96, weave_step_min=40.0, weave_step_max=120.0, weave_speed_max=1.6, weave_turn=0.1, band_top=188.0, band_bottom=440.0)
ufo_type = DrifterTypeTuning(variants={'standard': VariantTuning(width=40.0, height=10.0, hitbox=ufo_hitbox(40.0, 10.0, 9.0))}, default_variant='standard', speed_ratio=0.3, entry_warning_ticks=60, extra=weave)
tuning = DrifterTuning(drifters={DrifterType.UFO: ufo_type}, switches=PlaytestSwitches())
ufo = replace(spawn_drifter(Placement(DrifterType.UFO, x=320.0, y=300.0, seed=1), 1, tuning), phase=Phase.ACTIVE, uid=1)
def pixel(surface, column, row):
    return tuple(surface.get_at((column, row)))[:3]
screen = pygame.Surface((640, 480))
render_drifter(screen, ufo)
print(pixel(screen, 320, 300), pixel(screen, 300, 296), pixel(screen, 339, 304))
print(pixel(screen, 320, 290), pixel(screen, 314, 293))
print(pixel(screen, 320, 284), pixel(screen, 299, 300), pixel(screen, 340, 300), pixel(screen, 320, 306))
dim = pygame.Surface((640, 480))
render_ufo(dim, ufo, (320.0, 300.0), 1.0, 0.75)
print(pixel(dim, 320, 300), pixel(dim, 320, 290))
small = pygame.Surface((640, 480))
render_ufo(small, ufo, (320.0, 300.0), 0.35, 1.0)
pixels = [pixel(small, c, r) for c in range(300, 341) for r in range(280, 321)]
print(pixel(small, 320, 300), pixels.count((170, 170, 185)) < 80, (90, 220, 110) in pixels)
"
```
It prints five lines:
- `(170, 170, 185) (170, 170, 185) (170, 170, 185)`: the grey disc fills its 40 × 10 box, corners included.
- `(90, 220, 110) (90, 220, 110)`: the green dome above the disc.
- `(0, 0, 0) (0, 0, 0) (0, 0, 0) (0, 0, 0)`: nothing above the dome, beside the disc or below it.
- `(128, 128, 139) (68, 165, 83)`: during the re-hit cooldown disc and dome dim together.
- `(170, 170, 185) True True`: at the warning copy's scale, a small grey bar with green on top.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones the drifters contract's DRA-104 Impact table expects until the UFO's tuning file and the QA tasks exist.

## Out of scope
- The UFO itself and its weave (core, task DRA-104-01); the debug overlay, `ui/shapes.py`, the entry warning and the other views.
- `game/app/` (the frame draws UFOs through `render_drifter` already), tests, art and sound.
