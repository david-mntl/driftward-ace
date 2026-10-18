Feature: DRA-56
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-58

## Read in the contract
- Interface, `game/ui/drifters/`: `fireball_view.py` and `__init__.py`; `game/ui/shapes.py` (`draw_shape`, unchanged).
- Interface, `game/core/drifters/fireball.py` (what the view reads).
- Presentation: the table rows `obj.warning_tilt_degrees()`, `obj.warning_copy()`, `obj.hitbox`, `obj.brightness()`; Brightness; Fireball; Entry warning (Copy, Place).
- Rules, Fireball: Hitbox, Warning tilt, Warning copy.
- Rationale: "The fireball's look is its hitbox, drawn with `draw_shape`" and "The warning copy lies straight down and is turned by the tilt".

## Builds
- `game/ui/drifters/fireball_view.py` (new)
- `game/ui/drifters/__init__.py` (changed)

## Depends on
DRA-56-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame
pygame.init()
from dataclasses import replace
from core.drifters.base import DrifterType, Phase
from core.drifters.fireball import FireballTypeExtra, fireball_hitbox
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
import ui.drifters
from ui.drifters.registry import registered_views, render_drifter
def variant(w): return VariantTuning(width=w, height=w, hitbox=fireball_hitbox(w, 0.5, 35.0, False))
fire = DrifterTypeTuning(variants={'small': variant(21.0), 'big': variant(32.0)}, default_variant='small', speed_ratio=0.47, entry_warning_ticks=60, extra=FireballTypeExtra(angle_degrees=35.0, tail_ratio=0.5))
tuning = DrifterTuning(drifters={DrifterType.FIREBALL: fire}, switches=PlaytestSwitches())
F = DrifterType.FIREBALL
def shot(p, **changes):
    s = pygame.Surface((640, 480))
    render_drifter(s, replace(spawn_drifter(p, 1, tuning), **changes))
    return s
def rgb(s, x, y): return tuple(s.get_at((x, y)))[:3]
def mean(s, color):
    pts = [(x, y) for x in range(85, 116) for y in range(0, 31) if rgb(s, x, y) == color]
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
print(F in registered_views())
a = shot(Placement(F, x=100.0, y=100.0), phase=Phase.ACTIVE)
print(rgb(a, 100, 100), rgb(a, 91, 87), rgb(a, 100, 112))
d = shot(Placement(F, x=100.0, y=100.0), phase=Phase.ACTIVE, rehit_ticks_left=5)
print(rgb(d, 100, 100), rgb(d, 91, 87))
i = shot(Placement(F, x=100.0, y=100.0, invert=True), phase=Phase.ACTIVE)
print(rgb(i, 109, 87), rgb(i, 91, 87))
for p in (Placement(F, x=100.0), Placement(F, x=100.0, invert=True)):
    w = shot(p)
    (hx, hy), (tx, ty) = mean(w, (255, 140, 0)), mean(w, (200, 160, 0))
    print(hx > tx, hy > ty)
"
```
It prints six lines:
- `True`: the view registered itself.
- `(255, 140, 0) (200, 160, 0) (0, 0, 0)`: the orange head on its center, the dark yellow tail up and to the left, nothing 12 px below the head's center.
- `(191, 105, 0) (150, 120, 0)`: both parts dim during the re-hit cooldown.
- `(200, 160, 0) (0, 0, 0)`: with `invert` the tail is up and to the right.
- `True True`: in the warning, the copy's head is below and right of its tail.
- `False True`: with `invert`, below and left.

Put the command and its output in the implementation report. `game/tests/check.sh lint` and `typecheck` pass. `ui` passes except `test_drifter_registry.py` until `game/tuning/drifters/fireball.json` exists.

## Out of scope
- Any change to `ui/drifters/entry_warning.py`, `registry.py`, `ui/shapes.py` or the debug overlay: the warning, the tilt and the outlines already work through the core methods.
- Trail art, sprites, glow, sound (scope report DRA-56, Out).
- Core code, the data file, any test file.
