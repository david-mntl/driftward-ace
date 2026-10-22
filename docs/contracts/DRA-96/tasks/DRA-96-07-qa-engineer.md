Feature: DRA-96
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md, docs/contracts/systems/waves.md
Status: done
Linear: DRA-103

## Read in the contract
- drifters.md: Diagram, Planet (the timeline and the inner field rings table); Interface, `game/core/drifters/base.py` (`gravity_well`, `start_size`) and `game/core/drifters/planet.py`; Rules: The base (Start size; Gravity field; Re-hit cooldown); Spawner (steps 4 Parked and 7); Planet (all of it but For wave_check).
- run.md: Interface, `gravity_wells`; Rules: a playing tick, steps 4, 7 and 8; Other rules (Planets); Logging (the planet sentence, the order inside one tick).
- waves.md: Rules, The wave files (Drifter type: the type list in enum order).
- drifters.md: Impact, the DRA-96 table (the `test_wave_files.py` row).

## Builds
- `game/tests/core/test_planet.py` (new)
- `game/tests/core/test_wave_files.py` (changed: the type list in the unknown-type refusal)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-96-02, DRA-96-03

## Not in the contract
- Like `test_floating_island.py`, the new file builds its own `DrifterTuning` for the planet (and a meteorite where a test needs one) from the GDD values at the top of the file, the way `app.tuning` builds it, and reads no `game/tuning/` file. Source: tests/CONTEXT.md, Rules.

## Test
- The planet is born in WARNING with the shared entry warning and speed 0 at every level, with both switch sets; `as_level` changes nothing. Rules: Planet (Born; Scales).
- Its start: x required; y the placement's, or the field ring's box touching the top edge from above; its warning at (x, 12). A meteorite still starts where it did before DRA-96. Rules: The base (Start size); Planet (Start; Warning).
- It stays put while warning, then moves only by the scroll step, never sideways, still before the scroll starts. Rules: Planet (Update).
- `invert`, a specialty, `speed`, a missing x and tuning with the wrong extras are refused, each with its message. Rules: Planet (Born; It accepts ...).
- `gravity_well()` is None in WARNING and GONE and the field at its center while ACTIVE. Rules: Planet (Field).
- `inner_rings()` gives the table's radii and opacities at `ticks_in_phase` 0, 30, 60, 119 and 120, and `()` outside ACTIVE. Rules: Planet (Field rings); Diagram (inner field rings table).
- Its drawn box and timeline: not entered when it appears, entered on the next tick, kept on T+770, dropped on T+771 with its `drifter gone` line, as the planet timeline says; never dropped before it has entered. Rules: Planet (Drawn parts; Leaving).
- In the run, a flying ship inside a field is pulled, also while invulnerable; a ship standing in the respawn wait inside a field is not; the pull starts on the press that ends the wait. Rules: run.md, step 4.
- Touching the body is a hit: one life, the planet's re-hit cooldown starts, and a ship the pull holds against the body is not hit again until the cooldown ends; inside the field but clear of the body, no hit. Rules: run.md, steps 7 and 8, Other rules (Planets); Planet (Touch).
- `gravity_wells` holds every ACTIVE planet's field in drifter order, leaves out a warning planet and other drifters, and is `()` with none. Rules: run.md, Interface.
- A planet logs `drifter spawn`, `drifter active`, `drifter touch ... effect=hit` per hit and `drifter gone`, and nothing from `core.drifters` or `core.ship` for its pull. Rules: run.md, Logging.
- The wave loader's unknown-type message lists `planet` last. Rules: waves.md, The wave files (Drifter type).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once the Impact table's expected failures are cleared, with `test_planet.py` and the updated `test_wave_files.py` in the `core` step and all their tests passing.

## Out of scope
- The pull formula and the escape check on their own (task DRA-96-05); the ship against the planet's hitbox (task DRA-96-06).
- wave_check and its tests (`tools/wave_check/`, the main session).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
