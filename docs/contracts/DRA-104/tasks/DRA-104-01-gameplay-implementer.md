Feature: DRA-104
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-105

## Read in the contract
- Purpose (the base paragraph: seeded drifters, speed and timer factors).
- Diagram: the class shape (`Drifter.seeded`, `Ufo`), Birth (`seed?`, `hazard_speed_mult`), UFO (the sketch, the UFO timeline, One ACTIVE tick of a UFO, Easing).
- Interface: `game/core/drifters/base.py` (`DrifterType.UFO`, `seeded`, the two new `Birth` fields, the DRA-104 sentence after the block); `game/core/drifters/spawner.py` (`Placement.seed`, `MAX_SEED`, `placement_seed`, `DEBUG_SPAWNS_SOURCE`, the DRA-104 comment and the note after the block); `game/core/drifters/ufo.py` (all of it); `game/core/drifters/__init__.py`.
- Rules: Values (the UFO sentence); The base (Seeded; Timers; Birth; the `update` rule on randomness); Spawner (step 8, Placement seed); UFO (all of it but For wave_check); Tuning files (the UFO's file: what `app.tuning` builds, so `born` gets what it expects); Logging.
- Impact, the DRA-104 table. Rationale, the DRA-104 lines.

## Builds
- `game/core/drifters/base.py` (changed)
- `game/core/drifters/spawner.py` (changed)
- `game/core/drifters/ufo.py` (new)
- `game/core/drifters/__init__.py` (changed)

## Depends on
None

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.collision import Circle
from core.drifters.base import DrifterType, TickContext
from core.drifters.spawner import Placement, placement_seed, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.drifters.ufo import UfoTypeExtra, ufo_hitbox, weave_brake_speed, weave_stop_distance
from core.ship import spawn
weave = UfoTypeExtra(weave_change_ticks_min=60, weave_change_ticks_max=96, weave_step_min=40.0, weave_step_max=120.0, weave_speed_max=1.6, weave_turn=0.1, band_top=188.0, band_bottom=440.0)
ufo_type = DrifterTypeTuning(variants={'standard': VariantTuning(width=40.0, height=10.0, hitbox=ufo_hitbox(40.0, 10.0, 9.0))}, default_variant='standard', speed_ratio=0.3, entry_warning_ticks=60, extra=weave)
rock_type = DrifterTypeTuning(variants={'small': VariantTuning(width=20.0, height=20.0, hitbox=(Circle(0.0, 0.0, 10.0),))}, default_variant='small', speed_ratio=0.375, entry_warning_ticks=60)
tuning = DrifterTuning(drifters={DrifterType.UFO: ufo_type, DrifterType.METEORITE: rock_type}, switches=PlaytestSwitches())
context = TickContext(ship=spawn())
ufo = spawn_drifter(Placement(DrifterType.UFO, y=300.0, seed=7), 1, tuning)
print(ufo.phase.value, ufo.x, ufo.y, round(ufo.velocity_x, 4), ufo.warning_center(), ufo.weave_change_ticks_min, ufo.weave_change_ticks_max)
high = spawn_drifter(Placement(DrifterType.UFO, y=300.0, seed=7, invert=True), 8, tuning)
print(high.x, round(high.velocity_x, 4), round(high.weave_speed_max, 3), round(high.weave_turn, 3), high.weave_change_ticks_min, high.weave_change_ticks_max)
for _ in range(80):
    ufo = ufo.update(context).mark_entered()
print(ufo.phase.value, round(ufo.x, 2), ufo.y, ufo.weaving, ufo.has_entered)
ufo = ufo.update(context)
print(round(ufo.x, 2), ufo.weaving, ufo.weave_up is not None, 60 <= ufo.weave_ticks_left <= 96, abs(ufo.velocity_y) == 0.1, 188.0 <= ufo.target_y <= 440.0, 40.0 <= abs(ufo.target_y - 300.0) <= 120.0)
def path(seed):
    drifter = spawn_drifter(Placement(DrifterType.UFO, y=300.0, seed=seed), 1, tuning)
    heights = []
    for _ in range(400):
        drifter = drifter.update(context)
        heights.append(drifter.y)
    return heights
print(path(7) == path(7), path(7) != path(8), min(path(7)) >= 188.0, max(path(7)) <= 440.0)
print(round(weave_brake_speed(12.0, 0.1), 6), round(weave_stop_distance(2.272, 0.142), 3))
for placement in (Placement(DrifterType.UFO, y=300.0), Placement(DrifterType.UFO, y=100.0, seed=1), Placement(DrifterType.UFO, seed=1), Placement(DrifterType.UFO, y=300.0, seed=1, specialty_enabled=True), Placement(DrifterType.METEORITE, x=100.0, seed=1)):
    try:
        spawn_drifter(placement, 1, tuning)
    except ValueError as error:
        print(error)
print(placement_seed('l1_a', 0) == placement_seed('l1_a', 0), placement_seed('l1_a', 0) != placement_seed('l1_a', 1), 0 <= placement_seed('debug_spawns', 3) <= 4294967295)
"
```
It prints twelve lines:
- `warning -20.0 300.0 1.974 (12.0, 300.0) 60 96`: born in WARNING just outside the left wall at its y, its warning against that wall, Level 1 values.
- `660.0 -2.8031 2.272 0.142 42 68`: with `invert` at Level 8, just outside the right wall, flying left, every scaled value scaled.
- `active 19.48 300.0 False True`: it has appeared, entered and crossed 20 ticks, still flying level.
- `21.45 True True True True True True`: fully on screen, it picks its first height 40 to 120 px away inside the band and takes one 0.1 px/tick step toward it.
- `True True True True`: the same seed flies the same path, another seed another one, inside the band.
- `1.5 19.312`: the brake speed and the stopping distance of the contract's examples.
- `ufo placement needs seed`, `ufo placement y 100 is outside its band 188 to 440`, `ufo placement needs y`, `ufo has no specialty`, `meteorite has no seed`.
- `True True True`: default seeds are fixed per source and index, and in range.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones the drifters contract's DRA-104 Impact table expects until the view (task DRA-104-03), the UFO's tuning file and the QA tasks exist; every other existing test passes unchanged.

## Out of scope
- `game/core/wave_files.py` (task DRA-104-02).
- The view (task DRA-104-03), `game/app/` and the tuning file `game/tuning/drifters/ufo.json` (content), tests.
- Any change to the other drifters, `core/collision.py`, `core/levels.py`, `core/drifters/tuning.py`, `core/run.py` or `tools/`.
