Feature: DRA-96
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/ship.md
Status: open
Linear: DRA-97

## Read in the contract
- Purpose (the planet pull paragraph).
- Diagram: the step flowchart (step 2, then planet pull), Planet pull (the table), the run's calls (wells, the escape check).
- Interface, `game/core/ship.py`: `GravityWell`, `NO_WELLS`, `well_pull`, `check_escapable_pull`, `step`, and the DRA-96 paragraph after the block.
- Rules: Values (the DRA-96 line); the step (2, Then planet pull); Planet pull (all of it); Escape (all of it); Other rules (the no frame time line); Logging (the planet pull line).
- Impact, the DRA-96 table. Rationale, the DRA-96 lines.

## Builds
- `game/core/ship.py` (changed)

## Depends on
None.

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.ship import NO_WELLS, GravityWell, Ship, Thrust, check_escapable_pull, spawn, step, well_pull
well = GravityWell(x=320.0, y=400.0, surface_radius=32.0, pull_radius=150.0, pull_max=0.2)
for y in (250.0, 280.0, 309.0, 368.0, 390.0, 400.0):
    ship = step(Ship(x=320.0, y=y, vx=0.0, vy=0.0), Thrust(), wells=(well,))
    print(y, round(ship.vx, 6), round(ship.vy, 6))
side = step(Ship(x=229.0, y=400.0, vx=0.0, vy=0.0), Thrust(), wells=(well,))
print(round(side.vx, 4), round(side.vy, 4))
print(round(step(Ship(x=320.0, y=368.0, vx=0.0, vy=0.0), Thrust(up=True), wells=(well,)).vy, 4))
two = well_pull(Ship(x=320.0, y=300.0, vx=0.0, vy=0.0), (GravityWell(320.0, 391.0, 32.0, 150.0, 0.2), GravityWell(411.0, 300.0, 32.0, 150.0, 0.2)))
print(round(two[0], 4), round(two[1], 4))
print(step(spawn(), Thrust(left=True)) == step(spawn(), Thrust(left=True), wells=NO_WELLS))
check_escapable_pull(0.2)
print('0.2 accepted')
try:
    check_escapable_pull(0.3)
except ValueError as error:
    print(error)
"
```
It prints twelve lines:
- `250.0 0.0 0.16`, `280.0 0.0 0.210847`, `309.0 0.0 0.26`, `368.0 0.0 0.36`, `390.0 0.0 0.36`, `400.0 0.0 0.16`: no pull on the field's edge, the straight line to `pull_max` at the surface, `pull_max` inside it, none at the center.
- `0.094 0.16`: a sideways pull, slowed by drag.
- `-0.06`: up thrust still climbs out from the surface.
- `0.1 0.1`: two fields add up.
- `True`: with no wells the step is the old step.
- `0.2 accepted`, then `pull_max is too strong: pull_max + gravity must stay below thrust_up (0.3 + 0.16 >= 0.42)`.

Put the command and its output in the implementation report. `game/tests/check.sh` passes: every existing ship and run test passes unchanged.

## Out of scope
- `game/core/run.py`: gathering the wells and passing them to `step` is task DRA-96-03.
- The planet drifter and its `gravity_well` (task DRA-96-02), views, `game/app/` (the loader's call to the escape check is the Integration Engineer's), tests.
- Any change to thrust, drag, the fall cap, the walls, the islands, the top line, the floor test or the ship's constants.
