Feature: DRA-39
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md
Status: done
Linear: DRA-40

## Read in the contract
- drifters.md: Interface, `game/core/collision.py`; Rules, Collision (Unknown shape kind).
- drifters.md: Interface, `game/core/drifters/base.py` (everything marked DRA-39 except `DrifterType.SATELLITE`); Rules, The base (Entering, Leaving, Warning tilt, Re-hit cooldown, Birth, Start, Variants).
- drifters.md: Interface, `game/core/drifters/tuning.py` (`VariantTuning.extra`, `HazardRules`, `DrifterTuning.hazards`).
- drifters.md: Interface, `game/core/drifters/spawner.py`; Rules, Spawner (steps 4, 7 and 8, and the notes under them).
- drifters.md: Interface, `game/core/drifters/meteorite.py`; Rules, Meteorite (Start, Hitting again, No specialty, no telegraph, no invert).
- drifters.md: Diagram, Re-hit cooldown of one hazard and Meteorite timeline.
- run.md: Diagram (one tick, re-hit cooldown); Rules, a playing tick, steps 3, 7, 8, 9 and 10; Other rules (game over); Logging (no new lines).
- drifters.md and run.md: Impact (the existing tests this task is expected to break).

## Builds
- `game/core/collision.py` (changed)
- `game/core/drifters/base.py` (changed)
- `game/core/drifters/tuning.py` (changed)
- `game/core/drifters/spawner.py` (changed)
- `game/core/drifters/meteorite.py` (changed)
- `game/core/run.py` (changed)

## Depends on
None.

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from dataclasses import replace
from core.collision import Circle, hitboxes_overlap
from core.drifters.base import DrifterType
from core.drifters.spawner import Placement, spawn_drifter
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, PlaytestSwitches, VariantTuning
from core.run import add_drifters, start_run, step_run
from core.ship import Ship, Thrust
medium = VariantTuning(width=28, height=28, hitbox=(Circle(0, 0, 14),))
rock = DrifterTypeTuning(variants={'medium': medium}, default_variant='medium', speed_ratio=0.375, entry_warning_ticks=60)
tuning = DrifterTuning(drifters={DrifterType.METEORITE: rock}, switches=PlaytestSwitches())
m = spawn_drifter(Placement(DrifterType.METEORITE, x=320.0), 1, tuning)
print(m.y, m.rehit_cooldown_ticks, m.rehit_dim, m.may_hit_ship(), m.brightness(), m.has_entered)
print(spawn_drifter(Placement(DrifterType.METEORITE, x=0.0, speed=1.0, as_level=8), 1, tuning).speed)
for bad in (Placement(DrifterType.METEORITE), Placement(DrifterType.METEORITE, x=0.0, invert=True)):
    try:
        spawn_drifter(bad, 1, tuning)
    except ValueError as err:
        print(err)
try:
    hitboxes_overlap(('not a shape',), (Circle(0, 0, 1),))
except TypeError as err:
    print(err)
still = [Placement(DrifterType.METEORITE, x=320.0, y=240.0, speed=0.0), Placement(DrifterType.METEORITE, x=-14.0, y=200.0, speed=0.0)]
run = add_drifters(start_run(), still, tuning)
hits, seen = [], {}
for tick in range(1, 301):
    lives = run.lives
    run = replace(step_run(run, Thrust()), ship=Ship(x=320.0, y=240.0, vx=0.0, vy=0.0))
    if run.lives < lives:
        hits.append(tick)
    if tick in (60, 239, 240):
        seen[tick] = (run.drifters[0].rehit_ticks_left, run.drifters[0].brightness())
print(hits, seen)
print(len(run.drifters), run.drifters[0].has_entered, run.drifters[1].has_entered)
"
```
It prints seven lines:
- `-14.0 180 0.75 True 1.0 False`: a new rock has the default cooldown and dim, may hit, is at full brightness and has not entered.
- `1.42`: a placement speed of 1.0 at Level 8 gets × 1.42.
- `meteorite placement needs x`
- `meteorite has no invert`
- `unknown shape kind 'str'`
- `[60, 241] {60: (180, 0.75), 239: (1, 0.75), 240: (0, 1.0)}`: a still rock on a held ship hits the tick it appears, can't hit for the next 180 ticks, is dim until its count reaches 0, and hits again on tick 241.
- `2 True False`: the rock just outside the left wall never entered, so it was never dropped.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. `check.sh core` and `check.sh typecheck` fail only in `game/tests/core/test_drifters.py` and `game/tests/core/test_run_drifters.py`, on the tests named under Impact (tasks DRA-39-06 and DRA-39-07 update them); every other test passes.

## Out of scope
- The satellite and `DrifterType.SATELLITE` (task DRA-39-03).
- Views, `dim_color`, the tilted warning copy (task DRA-39-02).
- `game/app/` (the hazards file, the spawn list): the Integration Engineer.
- Any test file. Any data file in `game/tuning/`.
- Line and polygon shapes, coins, specialties, timers that scale.
