Feature: DRA-86
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/run.md, docs/contracts/systems/ship.md
Status: open
Linear: DRA-90

## Read in the contract
- run.md: Purpose.
- run.md: Diagram: one tick, `step_run` (steps 4 and 6).
- run.md: Interface, `game/core/run.py`: `island_ground` and the paragraph after the block.
- run.md: Rules: a playing tick, steps 3, 4, 5a, 6 (with the DRA-86 paragraph) and 7; Other rules (Islands never hit and never pay; drifters never touch each other); Logging (`respawn clear of island`, the order inside one tick, the island's lines).
- run.md: Impact, the DRA-86 table. Rationale, the DRA-86 lines.
- ship.md: Interface, `Ground`, `NO_GROUND`, `block_ship`, `spawn_clear`, `step`; Rules, Islands (what the block does to a waiting ship) and Respawn spot.

## Builds
- `game/core/run.py` (changed)

## Depends on
DRA-86-02, DRA-86-03

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from dataclasses import replace
from core.drifters.base import DrifterType
from core.drifters.floating_island import IslandShape, IslandTypeExtra, IslandVariantExtra, island_hitbox
from core.drifters.spawner import Placement
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.run import add_drifters, island_ground, start_run, step_run
from core.ship import NO_GROUND, Ship, Thrust
sizes = {'rectangle': ('rectangle', 320, 120), 'box': ('rectangle', 120, 120)}
variants = {n: VariantTuning(width=float(w), height=float(h), hitbox=island_hitbox(IslandShape(s), float(w), float(h), 40.0, False), extra=IslandVariantExtra(shape=IslandShape(s))) for n, (s, w, h) in sizes.items()}
tuning = DrifterTuning(drifters={DrifterType.FLOATING_ISLAND: DrifterTypeTuning(variants=variants, default_variant='rectangle', speed_ratio=0.0, entry_warning_ticks=0, extra=IslandTypeExtra(arm=40.0))}, switches=PlaytestSwitches())
land = add_drifters(start_run(), [Placement(DrifterType.FLOATING_ISLAND, x=320.0, y=330.0)], tuning)
for _ in range(13):
    land = step_run(land, Thrust())
print(round(land.ship.y, 2), land.ship.against_island, land.lives)
fall = add_drifters(replace(start_run(), ship=Ship(x=100.0, y=495.0, vx=0.0, vy=5.5)), [Placement(DrifterType.FLOATING_ISLAND, x=320.0, y=250.0, variant='box')], tuning)
fell = step_run(fall, Thrust())
print(fell.ship.y, fell.waiting, fell.lives)
carry = add_drifters(replace(start_run(), waiting=True), [Placement(DrifterType.FLOATING_ISLAND, x=320.0, y=163.0)], tuning)
for _ in range(32):
    carry = step_run(carry, Thrust())
print(round(carry.ship.y, 2), carry.waiting, round(carry.ship.vy, 2))
ground = island_ground(carry.drifters, 1.1)
print(len(ground.hitbox), ground.velocity_y, island_ground((), 0.0) == NO_GROUND)
"
```
It prints four lines:
- `254.0 True 3`: the ship falls onto the island on tick 13 and stands on it; no life lost.
- `326.0 True 2`: a fall respawns the ship below the box that covers the respawn point, because the spot above would pass the top line.
- `241.2 True 1.1`: a ship standing in the respawn wait is carried down by the island above it once the world scrolls, and still waits.
- `1 1.1 True`: the ground is the island's one shape, moving with the scroll; no island, no ground.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones the drifters contract's DRA-86 Impact table expects until the QA tasks, the view and the island's tuning file exist; every existing run test passes unchanged.

## Out of scope
- `game/core/ship.py` (task DRA-86-03), `game/core/collision.py`, the island drifter, views, `game/app/`, tests.
- Any change to the collect, hit, cooldown, drop or wave steps, or to how a fall costs a life.
