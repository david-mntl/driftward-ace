Feature: DRA-39
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-42

## Read in the contract
- Interface, `game/core/drifters/base.py`: `DrifterType.SATELLITE`, `VariantExtra`, `born_drifter`.
- Interface, `game/core/drifters/satellite.py` and `game/core/drifters/__init__.py`.
- Rules, Satellite (all of it).
- Rules, The base: Birth, Start, Warning tilt, Entering and Leaving.
- Diagram: Satellite timeline and the angled numbers under it.

## Builds
- `game/core/drifters/base.py` (changed: the `SATELLITE` member)
- `game/core/drifters/satellite.py` (new)
- `game/core/drifters/__init__.py` (changed)

## Depends on
DRA-39-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.collision import Box
from core.drifters.base import DrifterType, TickContext
from core.drifters.registry import available_drifters
from core.drifters.satellite import SatelliteVariantExtra
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.ship import spawn
boxes = (Box(0, 0, 12, 12), Box(0, 0, 36, 6))
def variant(angle): return VariantTuning(width=36, height=12, hitbox=boxes, extra=SatelliteVariantExtra(angle_degrees=angle))
sat = DrifterTypeTuning(variants={'flat': variant(0), 'angled': variant(20)}, default_variant='flat', speed_ratio=0.375, entry_warning_ticks=60)
tuning = DrifterTuning(drifters={DrifterType.SATELLITE: sat}, switches=PlaytestSwitches())
print(sorted(t.value for t in available_drifters()))
s = spawn_drifter(Placement(DrifterType.SATELLITE, y=300.0), 1, tuning)
print(s.variant, s.x, s.y, s.warning_center(), s.warning_tilt_degrees() == 0, s.current_hitbox())
ctx = TickContext(ship=spawn())
for _ in range(61):
    s = s.update(ctx)
print(s.phase.value, round(s.x, 4), s.y, len(s.current_hitbox()))
a = spawn_drifter(Placement(DrifterType.SATELLITE, y=200.0, variant='angled', invert=True), 1, tuning)
print(a.x, a.warning_center(), a.warning_tilt_degrees(), round(a.velocity_x, 4), round(a.velocity_y, 4))
try:
    spawn_drifter(Placement(DrifterType.SATELLITE, x=0.0), 1, tuning)
except ValueError as err:
    print(err)
"
```
It prints five lines:
- `['meteorite', 'satellite']`: the satellite registered itself.
- `flat -18.0 300.0 (18.0, 300.0) True ()`: default variant, just outside the left wall at its y, warning against the left wall, no tilt, no hitbox while warning.
- `active -15.5325 300.0 2`: 60 updates to appear in place, then one step of 2.4675 px to the right, with its two boxes.
- `658.0 (622.0, 200.0) 20.0 -2.3187 0.8439`: the angled one with `invert` starts outside the right wall, warns against it with its copy turned 20°, and flies left and down.
- `satellite placement needs y`

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes; `core` and `typecheck` fail only as listed for task DRA-39-01 until tasks DRA-39-06 and DRA-39-07 are done.

## Out of scope
- The satellite view and its look (task DRA-39-04).
- `game/tuning/drifters/satellite.json` and its loader in `game/app/` (content and the Integration Engineer).
- Any test file.
- The fireball, chain lightning, coin and islands (scope report DRA-39, Out).
