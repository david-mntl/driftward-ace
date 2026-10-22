Feature: DRA-86
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md, docs/contracts/systems/waves.md
Status: open
Linear: DRA-95

## Read in the contract
- drifters.md: Diagram, the island timeline; Interface, `game/core/drifters/floating_island.py`; Rules: The base (Phase; Parked and moving; Block); Spawner (step 4 Parked); Floating island (all of it but For wave_check).
- run.md: Interface, `island_ground`; Rules: a playing tick, steps 4, 5a, 6 and 7; Other rules (Islands never hit and never pay); Logging (`respawn clear of island`, the island's lines, the order inside one tick).
- waves.md: Rules, The wave files (Drifter type: the type list in enum order).
- drifters.md: Impact, the DRA-86 table (the `test_wave_files.py` row).

## Builds
- `game/tests/core/test_floating_island.py` (new)
- `game/tests/core/test_wave_files.py` (changed: the type list in the unknown-type refusal)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-86-02, DRA-86-04

## Not in the contract
- Like `test_coin.py`, the new file builds its own `DrifterTuning` for the island from the GDD values at the top of the file, the way `app.tuning` builds it, and reads no `game/tuning/` file. Source: tests/CONTEXT.md, Rules.

## Test
- The island is born ACTIVE with no warning and speed 0 at every level; `as_level` changes nothing. Rules: Floating island (Born; No warning; Scales).
- Its start: x required, y the placement's or just above the top edge. Rules: Floating island (Start).
- It moves only by the scroll step, never sideways, and stands still before the scroll starts. Rules: Floating island (Update).
- `invert` is taken by the L, the T and the triangle and refused by the rectangle and the box; `speed` and a specialty are refused, each with its message. Rules: Floating island (Born; It accepts ...).
- It enters on its first state on screen and is dropped once its top edge is at or below the floor, never before it has entered, as the island timeline says. Rules: Floating island (Leaving).
- In the run, a ship falls onto an island, stands and rides down with it, and falls off the floor when the island leaves. Rules: run.md, steps 4 and 6.
- An island never hits and never pays: no life lost, no `drifter touch`, no cooldown, no coin points, invulnerable or not, and an invulnerable ship is still blocked. Rules: run.md, Other rules; step 4.
- A ship standing in the respawn wait is carried down by an island and keeps waiting; carried off the floor, it has fallen like any fall. Rules: run.md, steps 4 and 6.
- A fall respawns the ship clear of an island over the respawn point: below when above would pass the top line, above otherwise, on a protected fall too, with the `respawn clear of island` line after `respawn from`; with no island there, no such line. Rules: run.md, step 6; Logging.
- An island logs `drifter spawn` and `drifter gone` only. Rules: run.md, Logging.
- `island_ground` holds every ACTIVE island's shapes in order and the scroll step, and is empty with no island. Rules: run.md, Interface.
- The wave loader's unknown-type message lists `floating_island` last. Rules: waves.md, The wave files (Drifter type).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with `test_floating_island.py` and the updated `test_wave_files.py` in the `core` step.

## Out of scope
- Collision and the ship's block alone (tasks DRA-86-07 and DRA-86-08).
- wave_check and its tests (`tools/wave_check/`, the main session).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
