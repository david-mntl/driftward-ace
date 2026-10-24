Feature: DRA-96
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-100

## Read in the contract
- Diagram: Planet (the sketch and the inner field rings table), Views.
- Interface: `game/core/drifters/planet.py` (the fields and methods the view reads: `width`, `pull_radius`, `inner_rings()`, `FieldRing`); `game/ui/drifters/` (`DrifterView`, `dim_color`, `register_view`, `planet_view.py`, `__init__.py`).
- Presentation: the table rows for the planet; Brightness (the planet sentence); Planet (all of it); Entry warning (Copy, how the copy is drawn); Rules for every view.
- Rules: Planet (Field rings, Drawn parts) and Values (the planet sentence: what stays in the view).
- Rationale, the DRA-96 lines on the alpha layer, the warning copy and the field dimming.

## Builds
- `game/ui/drifters/planet_view.py` (new)
- `game/ui/drifters/__init__.py` (changed)

## Depends on
DRA-96-02

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
from dataclasses import replace
import pygame
from core.drifters.base import DrifterType, Phase
from core.drifters.planet import PlanetTypeExtra, PlanetVariantExtra, planet_hitbox
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from ui.drifters.planet_view import render_planet
from ui.drifters.registry import render_drifter
pygame.init()
variant = VariantTuning(width=64.0, height=64.0, hitbox=planet_hitbox(64.0), extra=PlanetVariantExtra(pull_radius=150.0, pull_max=0.2))
rings = PlanetTypeExtra(field_ring_trip=120, field_ring_gap=60, field_ring_fade=50.0, field_ring_count=2)
tuning = DrifterTuning(drifters={DrifterType.PLANET: DrifterTypeTuning(variants={'standard': variant}, default_variant='standard', speed_ratio=0.0, entry_warning_ticks=60, extra=rings)}, switches=PlaytestSwitches())
planet = replace(spawn_drifter(Placement(DrifterType.PLANET, x=320.0, y=300.0), 1, tuning), phase=Phase.ACTIVE, uid=1)
def near(surface, column, row, test):
    return any(test(tuple(surface.get_at((column + dx, row + dy)))[:3]) for dx in (-1, 0, 1) for dy in (-1, 0, 1))
screen = pygame.Surface((640, 480))
render_drifter(screen, planet)
print(tuple(screen.get_at((320, 300)))[:3], tuple(screen.get_at((300, 300)))[:3])
print(all(near(screen, c, r, lambda p: p == (180, 120, 255)) for c, r in ((320, 150), (470, 300), (320, 450), (170, 300))))
print(near(screen, 320, 209, lambda p: 0 < p[2] < 255 and p != (180, 120, 255)), near(screen, 229, 300, lambda p: 0 < p[2] < 255 and p != (180, 120, 255)))
print(tuple(screen.get_at((320, 140)))[:3], tuple(screen.get_at((320, 230)))[:3])
dim = pygame.Surface((640, 480))
render_planet(dim, planet, (320.0, 300.0), 1.0, 0.75)
print(tuple(dim.get_at((320, 300)))[:3], near(dim, 320, 150, lambda p: p == (135, 90, 191)))
copy = pygame.Surface((640, 480))
render_planet(copy, planet, (320.0, 300.0), 14 / 64, 1.0)
pixels = [tuple(copy.get_at((c, r)))[:3] for c in range(640) for r in range(480)]
print(tuple(copy.get_at((320, 300)))[:3], pixels.count((140, 70, 200)) < 200, any(p[2] == 255 for p in pixels))
"
```
It prints six lines:
- `(140, 70, 200) (140, 70, 200)`: the body fills its 64 px circle.
- `True`: the opaque outer ring, 150 px out, all round.
- `True True`: the faint inner ring at 91 px, blended over the black background, above and to the left of the center.
- `(0, 0, 0) (0, 0, 0)`: nothing outside the outer ring, nothing between the inner ring and the body.
- `(105, 53, 150) True`: during the re-hit cooldown the body and the rings dim together.
- `(140, 70, 200) True False`: the warning copy's scale draws a small disc and no ring.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones the drifters contract's DRA-96 Impact table expects until the planet's tuning file and the QA tasks exist.

## Out of scope
- The planet and its rings' radii and opacities (core, task DRA-96-02); the debug overlay, `ui/shapes.py`, the entry warning and the other views.
- `game/app/` (the frame draws planets through `render_drifter` already), tests, art and sound.
