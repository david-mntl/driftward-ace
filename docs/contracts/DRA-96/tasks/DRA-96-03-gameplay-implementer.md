Feature: DRA-96
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/run.md, docs/contracts/systems/ship.md
Status: done
Linear: DRA-99

## Read in the contract
- run.md: Purpose (the planets sentence).
- run.md: Diagram: one tick, step 4.
- run.md: Interface: `gravity_wells` and the paragraph after the block.
- run.md: Rules: a playing tick, step 4; Other rules (Planets); Logging (the planet sentence).
- run.md: Impact, the DRA-96 table. Rationale, the DRA-96 lines.
- ship.md: Interface, `GravityWell`, `NO_WELLS` and `step`'s `wells` argument; Rules, Planet pull (When it applies).

## Builds
- `game/core/run.py` (changed)

## Depends on
DRA-96-01, DRA-96-02

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from dataclasses import replace
from core.drifters.base import DrifterType, Phase
from core.drifters.planet import PlanetTypeExtra, PlanetVariantExtra, planet_hitbox
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.run import gravity_wells, start_run, step_run
from core.ship import Ship, Thrust
variant = VariantTuning(width=64.0, height=64.0, hitbox=planet_hitbox(64.0), extra=PlanetVariantExtra(pull_radius=150.0, pull_max=0.2))
rings = PlanetTypeExtra(field_ring_trip=120, field_ring_gap=60, field_ring_fade=50.0, field_ring_count=2)
tuning = DrifterTuning(drifters={DrifterType.PLANET: DrifterTypeTuning(variants={'standard': variant}, default_variant='standard', speed_ratio=0.0, entry_warning_ticks=60, extra=rings)}, switches=PlaytestSwitches())
planet = replace(spawn_drifter(Placement(DrifterType.PLANET, x=320.0, y=400.0), 1, tuning), phase=Phase.ACTIVE, uid=1)
flying = replace(start_run(), ship=Ship(x=320.0, y=309.0, vx=0.0, vy=0.0), drifters=(planet,), next_uid=2)
print(round(step_run(flying, Thrust()).ship.vy, 4))
waiting = step_run(replace(flying, waiting=True), Thrust())
print(waiting.ship.y, waiting.ship.vy, waiting.waiting)
print(round(step_run(replace(flying, waiting=True), Thrust(up=True)).ship.vy, 4))
print(round(step_run(replace(flying, invuln_ticks_left=30), Thrust()).ship.vy, 4))
print(gravity_wells(flying.drifters), gravity_wells(()))
"
```
It prints five lines:
- `0.26`: a flying ship inside the field, 91 px above the planet, is pulled down 0.1 on top of gravity.
- `309.0 0.0 True`: a ship standing in the respawn wait is not pulled.
- `-0.16`: on the press that ends the wait, the pull starts with gravity: −0.42 + 0.16 + 0.1.
- `0.26`: an invulnerable ship is pulled too.
- `(GravityWell(x=320.0, y=400.0, surface_radius=32.0, pull_radius=150.0, pull_max=0.2),) ()`.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones the drifters contract's DRA-96 Impact table expects; every existing run test passes unchanged.

## Out of scope
- `game/core/ship.py` (task DRA-96-01), the planet and the base hooks (task DRA-96-02).
- Views, `game/app/`, tests.
- Any change to another step of `step_run`, to `add_drifters` or to the run's log lines.
