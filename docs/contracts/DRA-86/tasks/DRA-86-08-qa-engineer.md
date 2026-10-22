Feature: DRA-86
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/ship.md, docs/contracts/systems/drifters.md
Status: open
Linear: DRA-94

## Read in the contract
- ship.md: Diagram: Islands (stand and ride, held and carried, slope) and The respawn spot table.
- ship.md: Interface: `Ship.against_island`, `Ground`, `NO_GROUND`, `spawn_clear`, `step`, `block_ship`.
- ship.md: Rules: the step (6, Then islands); Islands (all of it); Respawn spot (all of it); Logging (`island contact`).
- drifters.md: Interface, `island_hitbox`; Diagram, Floating island (the shapes); Rules, Push-out.

## Builds
- `game/tests/core/test_ship_islands.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-86-02, DRA-86-03

## Not in the contract
None.

## Test
- The ship is pushed out of every island variant and `invert` from above, below, the left and the right, and off the triangle's slope, to the surface and no further. Rules: Islands (1 to 3).
- The part of the speed going into the surface drops to 0 measured against the island's motion; the part along it stays; no bounce, for a still and a moving ground. Rules: Islands (4).
- Standing on top it keeps the island's speed tick after tick and rides down with it; up thrust lifts it off. Rules: Islands (On top).
- Held under an underside with up thrust it moves at the island's speed, never faster; side thrust slides it out; with no thrust it falls away. Rules: Islands (Underneath).
- On the triangle's slope, with no key, it slides down along the slope and gains speed. Rules: Islands (Slopes).
- A push never puts the ship past a side wall or above the top line; it takes the next shortest way, and straight down is always left. Rules: Islands (2).
- Ties go up, then down, then left, then right. Rules: Islands (2).
- One push clears the ship of the L's or the T's two boxes at their seam and of two overlapping islands; it never stops on the seam. Rules: Islands (Several islands).
- With no ground, or `NO_GROUND`, the step gives the same ship as before DRA-86, with `against_island` False; an edge touch is not a push. Rules: the step; Islands (1).
- `block_ship` alone pushes a ship at rest the same way. Rules: Islands.
- `spawn_clear`: the respawn point when no island holds the ship there (touching included); the spot just above; the spot below when above would pass the top line; above on a tie; at rest. Rules: Respawn spot.
- `island contact` is logged once when contact starts, not while it lasts, and again after a lift-off and a new landing, by `step` and by `block_ship`. Rules: Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with `test_ship_islands.py` in the `core` step. Until task DRA-86-09 is done, the only failure left is the type list in `test_wave_files.py`, which that task fixes (drifters.md, Impact).

## Out of scope
- Collision tables and the push-out measures alone (task DRA-86-07); the island drifter and islands in the run (task DRA-86-09).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
