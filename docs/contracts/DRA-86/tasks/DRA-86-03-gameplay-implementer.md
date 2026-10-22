Feature: DRA-86
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/ship.md, docs/contracts/systems/drifters.md
Status: open
Linear: DRA-89

## Read in the contract
- ship.md: Purpose.
- ship.md: Diagram: the step flowchart (6b islands), the run's calls, Islands (stand and ride, held and carried, slope) and The respawn spot table.
- ship.md: Interface, `game/core/ship.py`: `Ship.against_island`, `Ground`, `NO_GROUND`, `spawn`, `spawn_clear`, `step`, `block_ship`, and the two paragraphs after the block.
- ship.md: Rules: Values (the DRA-86 line); the step (6, Then islands); Islands (all of it); Respawn spot (all of it); Other rules; Logging (the `island contact` line and the last line).
- ship.md: Impact, the DRA-86 table. Rationale, the DRA-86 lines.
- drifters.md: Rules, Push-out (the measures the block uses).

## Builds
- `game/core/ship.py` (changed)

## Depends on
DRA-86-01

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.collision import Box, Polygon, place_hitbox
from core.ship import NO_GROUND, Ground, Ship, Thrust, block_ship, spawn, spawn_clear, step
rest = step(Ship(x=320.0, y=282.9, vx=0.0, vy=1.1), Thrust(), Ground(hitbox=(Box(320.0, 360.0, 320.0, 120.0),), velocity_y=1.1))
print(round(rest.y, 2), round(rest.vy, 2), rest.against_island)
lift = step(rest, Thrust(up=True), Ground(hitbox=(Box(320.0, 361.1, 320.0, 120.0),), velocity_y=1.1))
print(round(lift.vy, 2), lift.against_island)
held = step(Ship(x=320.0, y=214.9, vx=0.0, vy=1.1), Thrust(up=True), Ground(hitbox=(Box(320.0, 140.0, 320.0, 120.0),), velocity_y=1.1))
print(round(held.y, 2), round(held.vy, 2), held.against_island)
side = step(Ship(x=380.0, y=240.0, vx=6.0, vy=0.0), Thrust(), Ground(hitbox=(Box(460.0, 240.0, 120.0, 120.0),)))
print(round(side.x, 2), side.vx, round(side.vy, 2))
slope = place_hitbox((Polygon(((-160.0, -60.0), (160.0, 60.0), (-160.0, 60.0))),), 400.0, 330.0)
slide = step(Ship(x=320.0, y=278.0, vx=0.0, vy=0.0), Thrust(), Ground(hitbox=slope))
print(round(slide.vx, 4), round(slide.vy, 4), slide.against_island)
wait = block_ship(spawn(), Ground(hitbox=(Box(320.0, 164.4, 320.0, 120.0),), velocity_y=1.1))
print(round(wait.y, 2), round(wait.vy, 2), wait.against_island)
print(spawn_clear(Ground(hitbox=(Box(320.0, 300.0, 120.0, 120.0),))).y, spawn_clear(Ground(hitbox=(Box(320.0, 250.0, 120.0, 120.0),))).y, spawn_clear(NO_GROUND) == spawn())
print(step(spawn(), Thrust(left=True)) == step(spawn(), Thrust(left=True), NO_GROUND))
"
```
It prints eight lines:
- `284.0 1.1 True`: standing on top, riding at the island's speed.
- `0.84 False`: up thrust lifts it off.
- `216.0 1.1 True`: held under an underside, carried at the island's speed, never faster.
- `384.0 0.0 0.16`: stopped at an island's side, no bounce; its fall goes on.
- `0.0526 0.0197 True`: on the slope its speed turns along the slope.
- `240.4 1.1 True`: a ship standing in the respawn wait is carried down.
- `224.0 326.0 True`: the respawn spot moved up, moved down because up would pass the top line, and left alone with no island.
- `True`: with no ground the step is the old step.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones the drifters contract's DRA-86 Impact table expects until later tasks and the island's tuning file exist; every existing ship and run test passes unchanged.

## Out of scope
- `game/core/run.py`: building the ground, blocking the waiting ship and respawning with `spawn_clear` are task DRA-86-04.
- `game/core/collision.py` (task DRA-86-01), the island drifter (task DRA-86-02), views, `game/app/`, tests.
- Any change to thrust, gravity, drag, the fall cap, the walls, the top line or the floor test.
