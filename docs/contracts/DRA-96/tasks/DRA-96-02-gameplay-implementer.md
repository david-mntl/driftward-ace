Feature: DRA-96
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/ship.md
Status: open
Linear: DRA-98

## Read in the contract
- drifters.md: Purpose (the base paragraph).
- drifters.md: Diagram: the class shape (`Drifter`'s `gravity_well` and `start_size`, `Planet`), Birth (start size), Planet (the sketch, the timeline, the inner field rings table).
- drifters.md: Interface: `game/core/drifters/base.py` (the import line, `DrifterType.PLANET`, `gravity_well`, `start_size`, the DRA-96 sentence after the block); `game/core/drifters/spawner.py` (the DRA-96 comment); `game/core/drifters/planet.py` (all of it); `game/core/drifters/__init__.py`.
- drifters.md: Rules: Values (the planet sentence); The base (Start; Start size; Gravity field); Spawner (step 7); Planet (all of it but For wave_check); Tuning files (the planet's file: what `app.tuning` builds, so `born` gets what it expects); Logging.
- drifters.md: Impact, the DRA-96 table. Rationale, the DRA-96 lines on `start_size`, `FIELD_DRAW_MARGIN`, variant and type values, the rings in core and the rings' cycle.
- ship.md: Interface, `GravityWell`.

## Builds
- `game/core/drifters/base.py` (changed)
- `game/core/drifters/spawner.py` (changed)
- `game/core/drifters/planet.py` (new)
- `game/core/drifters/__init__.py` (changed)

## Depends on
DRA-96-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.drifters.base import DrifterType, TickContext
from core.drifters.planet import PlanetTypeExtra, PlanetVariantExtra, planet_hitbox
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.ship import spawn
variant = VariantTuning(width=64.0, height=64.0, hitbox=planet_hitbox(64.0), extra=PlanetVariantExtra(pull_radius=150.0, pull_max=0.2))
rings = PlanetTypeExtra(field_ring_trip=120, field_ring_gap=60, field_ring_fade=50.0, field_ring_count=2)
tuning = DrifterTuning(drifters={DrifterType.PLANET: DrifterTypeTuning(variants={'standard': variant}, default_variant='standard', speed_ratio=0.0, entry_warning_ticks=60, extra=rings)}, switches=PlaytestSwitches())
planet = spawn_drifter(Placement(DrifterType.PLANET, x=320.0), 8, tuning)
print(planet.phase.value, planet.y, planet.speed, planet.warning_center(), planet.gravity_well(), planet.inner_rings())
context = TickContext(ship=spawn(), scroll_step_px=1.1)
for _ in range(60):
    planet = planet.update(context).mark_entered()
print(planet.phase.value, planet.y, planet.has_entered, planet.current_hitbox())
print(planet.gravity_well())
print([(round(ring.radius, 2), round(ring.opacity, 4)) for ring in planet.inner_rings()])
planet = planet.update(context).mark_entered()
print(round(planet.y, 2), planet.has_entered, planet.drawn_parts()[0].w, planet.effect_on_touch().value)
for placement in (Placement(DrifterType.PLANET, x=100.0, speed=1.0), Placement(DrifterType.PLANET, x=100.0, invert=True), Placement(DrifterType.PLANET)):
    try:
        spawn_drifter(placement, 1, tuning)
    except ValueError as error:
        print(error)
"
```
It prints eight lines:
- `warning -151.0 0.0 (320.0, 12.0) None ()`: born in WARNING at Level 8 with no speed, its field ring's box touching the top edge, its warning at its x against the top edge, no field and no rings yet.
- `active -151.0 False (Circle(cx=320.0, cy=-151.0, r=32.0),)`: it appears where it was placed after 60 ticks, not yet on screen.
- `GravityWell(x=320.0, y=-151.0, surface_radius=32.0, pull_radius=150.0, pull_max=0.2)`: the field is on from the tick it appears.
- `[(150.0, 0.5), (91.0, 0.25)]`: the two inner rings on its first ACTIVE state.
- `-149.9 True 302.0 hit`: it moves with the scroll, has entered, its drawn box is the field ring's, and touching it is a hit.
- `planet has no speed`, `planet has no invert`, `planet placement needs x`.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones the drifters contract's DRA-96 Impact table expects until the view (task DRA-96-04), the planet's tuning file and the QA tasks exist; every other existing test passes unchanged, every drifter starting where it did.

## Out of scope
- `game/core/ship.py` (task DRA-96-01) and `game/core/run.py` (task DRA-96-03).
- The view (task DRA-96-04), `game/app/` and the tuning file `game/tuning/drifters/planet.json` (content), tests.
- Any change to the other drifters, `core/collision.py`, `core/levels.py` or `core/drifters/tuning.py`.
