Feature: DRA-86
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-88

## Read in the contract
- Purpose.
- Diagram: the class diagram, the life of one drifter, Floating island (the shapes and the island timeline).
- Interface, `game/core/drifters/base.py`: `DrifterType.FLOATING_ISLAND`, `TouchEffect.BLOCK`.
- Interface, `game/core/drifters/floating_island.py` (all of it) and `game/core/drifters/__init__.py`.
- Rules: The base (Phase; Parked and moving; Block); Spawner (step 4 with Parked, steps 7 and 8); Floating island (all of it but For wave_check); Tuning files (The floating island's file, for what the loader will hand over); Logging.
- Impact, the DRA-86 table. Rationale, the DRA-86 lines on even sizes, a variant as a shape kind and a size, `invert` refused on the rectangle and the box, and `BLOCK`.

## Builds
- `game/core/drifters/base.py` (changed)
- `game/core/drifters/floating_island.py` (new)
- `game/core/drifters/__init__.py` (changed)

## Depends on
DRA-86-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.drifters.base import DrifterType, TickContext
from core.drifters.floating_island import IslandShape, IslandTypeExtra, IslandVariantExtra, island_hitbox
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.ship import spawn
sizes = {'rectangle': ('rectangle', 320, 120), 'box': ('rectangle', 120, 120), 'l_shape': ('l_shape', 320, 120), 't_shape': ('t_shape', 320, 120), 'triangle': ('triangle', 320, 120)}
variants = {n: VariantTuning(width=float(w), height=float(h), hitbox=island_hitbox(IslandShape(s), float(w), float(h), 40.0, False), extra=IslandVariantExtra(shape=IslandShape(s))) for n, (s, w, h) in sizes.items()}
tuning = DrifterTuning(drifters={DrifterType.FLOATING_ISLAND: DrifterTypeTuning(variants=variants, default_variant='rectangle', speed_ratio=0.0, entry_warning_ticks=0, extra=IslandTypeExtra(arm=40.0))}, switches=PlaytestSwitches())
island = spawn_drifter(Placement(DrifterType.FLOATING_ISLAND, x=320.0), 8, tuning)
print(island.phase.value, island.y, island.speed, island.effect_on_touch().value, island.graze_zone())
moved = island.update(TickContext(ship=spawn(), scroll_step_px=1.1)).update(TickContext(ship=spawn()))
print(round(moved.y, 2), moved.x)
print(spawn_drifter(Placement(DrifterType.FLOATING_ISLAND, x=480.0, variant='l_shape', invert=True), 1, tuning).hitbox)
print(spawn_drifter(Placement(DrifterType.FLOATING_ISLAND, x=480.0, variant='triangle', invert=True), 1, tuning).hitbox)
for placement in (Placement(DrifterType.FLOATING_ISLAND, x=1.0, variant='box', invert=True), Placement(DrifterType.FLOATING_ISLAND, x=1.0, speed=2.0), Placement(DrifterType.FLOATING_ISLAND)):
    try:
        spawn_drifter(placement, 1, tuning)
    except ValueError as error:
        print(error)
"
```
It prints seven lines:
- `active -60.0 0.0 block ()`: born ACTIVE with no warning, just above the top edge, no speed even at Level 8, a blocker with no graze zone.
- `-58.9 320.0`: it moved with the scroll step and not without one, never sideways.
- `(Box(cx=0.0, cy=-40.0, w=320.0, h=40.0), Box(cx=-140.0, cy=0.0, w=40.0, h=120.0))`: the L upside down, bar on top, upright still at the left.
- `(Polygon(points=((-160.0, 60.0), (160.0, -60.0), (-160.0, -60.0))),)`: the triangle upside down.
- `floating_island variant 'box' has no invert`, `floating_island has no speed`, `floating_island placement needs x`.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones the contract's DRA-86 Impact table expects until later tasks and `game/tuning/drifters/floating_island.json` exist (`test_collision.py`, `test_wave_files.py`'s type list, `test_drifter_registry.py`); every other test passes unchanged.

## Out of scope
- The ship's block, the respawn spot and the run (tasks DRA-86-03 and DRA-86-04).
- The views (tasks DRA-86-05 and DRA-86-06).
- `game/app/`, `game/tuning/` (the island's file is content, named by the Director), tests, wave_check.
- Islands that move on their own, break or hurt; graze; sound; final art; any change to the other drifters.
