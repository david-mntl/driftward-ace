Feature: DRA-47
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-53

## Read in the contract
- Interface, `game/ui/drifters/`: `chain_lightning_view.py` and the `__init__.py` line.
- Interface, `game/core/drifters/chain_lightning.py`: the `ChainLightning` fields and methods the view reads (`nodes`, `arcs`, `node_size`, `arc_width`, `charge_rays`, `ray_length`, `ray_width`, `firing_arcs()`, `charge_ray_count()`).
- Presentation: the table rows for the chain lightning; Brightness; Chain lightning; Entry warning (Copy); Rules for every view.
- Rules, Chain lightning: Cycle, Charge rays, Firing arcs, Warning copy (what the core methods mean; the view only reads them).

## Builds
- `game/ui/drifters/chain_lightning_view.py` (new)
- `game/ui/drifters/__init__.py` (changed)

## Depends on
DRA-47-03, DRA-47-04, DRA-47-05

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
from dataclasses import replace
import pygame
pygame.init()
import ui.drifters
from core.drifters.base import Phase
from core.drifters.chain_lightning import ChainLightning, chain_hitbox
from ui.drifters.registry import render_drifter
nodes = ((-64.0, 0.0), (64.0, 0.0))
c = ChainLightning(uid=1, x=320.0, y=100.0, variant='pair_flat', width=140.0, height=12.0, speed=0.0, hitbox=chain_hitbox(nodes, ((0, 1),), 12, 6), warning_ticks=60, phase=Phase.ACTIVE, nodes=nodes, arcs=((0, 1),), node_size=12.0, arc_width=6.0, charge_ticks=120, fire_ticks=120, charge_rays=4, ray_length=6.0, ray_width=1.0)
def px(s, x, y): return tuple(s.get_at((x, y)))[:3]
RAY = (120, 200, 255)
def ray(s, x0, x1, y0, y1): return any(px(s, x, y) == RAY for x in range(x0, x1) for y in range(y0, y1))
s = pygame.Surface((640, 480))
render_drifter(s, c)
print(px(s, 256, 100), px(s, 320, 100), ray(s, 258, 267, 90, 99), ray(s, 246, 255, 90, 99))
s.fill((0, 0, 0))
render_drifter(s, replace(c, ticks_in_phase=90))
print(ray(s, 246, 255, 101, 110), ray(s, 258, 267, 101, 110))
s.fill((0, 0, 0))
render_drifter(s, replace(c, ticks_in_phase=120))
print(px(s, 320, 100), px(s, 320, 93), ray(s, 258, 267, 90, 99))
s.fill((0, 0, 0))
render_drifter(s, replace(c, ticks_in_phase=120, rehit_ticks_left=10))
print(px(s, 320, 100), px(s, 256, 100))
"
```
It prints four lines:
- `(0, 220, 255) (0, 0, 0) True False`: charging, first quarter: cyan nodes, no band, one ray up and to the right of each node.
- `True True`: last quarter: the down-left and down-right rays show too.
- `(220, 240, 255) (0, 0, 0) False`: firing: the band between the nodes, 6 px thick, and no rays.
- `(165, 180, 191) (0, 165, 191)`: during the re-hit cooldown, band and nodes at 0.75 brightness.

Put the command and its output in the implementation report. `game/tests/check.sh lint`, `typecheck` (apart from the files the drifters.md Impact still lists for later tasks) and `ui` pass; `test_drifter_registry.py` passes once `game/tuning/drifters/chain_lightning.json` exists.

## Out of scope
- Art, the jagged arc, glow, flicker and sound (scope report DRA-47, Out).
- `game/ui/shapes.py` and `game/ui/drifters/entry_warning.py` (tasks DRA-47-04 and DRA-47-05). `game/ui/debug_overlay.py`.
- Any core file, data file or test file.
