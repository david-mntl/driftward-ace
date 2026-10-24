Feature: DRA-104
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md
Status: done
Linear: DRA-109

## Read in the contract
- drifters.md: Diagram, UFO (the sketch, the UFO timeline, One ACTIVE tick of a UFO, Easing).
- drifters.md: Interface, `game/core/drifters/base.py` (`seeded`, the `Birth` fields `hazard_speed_mult` and `seed`), `game/core/drifters/spawner.py` (`Placement.seed`, `MAX_SEED`, `placement_seed`, `DEBUG_SPAWNS_SOURCE`) and `game/core/drifters/ufo.py`.
- drifters.md: Rules: The base (Seeded; Entering; Leaving; Re-hit cooldown; the `update` rule); Spawner (steps 4, 5 and 8, Placement seed); UFO (all of it but For wave_check).
- run.md: Rules: a playing tick, steps 3, 7 and 8; Other rules (randomness); Logging (drifter spawn, active, touch, gone).
- drifters.md: Impact, the DRA-104 table.

## Builds
- `game/tests/core/test_ufo.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-104-01

## Not in the contract
- Like `test_planet.py`, the new file builds its own `DrifterTuning` for the UFO (and a meteorite where a test needs one) from the GDD values at the top of the file, the way `app.tuning` builds it, and reads no `game/tuning/` file. Source: tests/CONTEXT.md, Rules.

## Test
- The UFO is born in WARNING with the shared entry warning; it needs a y and a seed, keeps a given x, starts just outside the left wall, or the right with `invert`, at its y, and warns at (12, y) or (628, y). Rules: UFO (Born; Start; Warning).
- A y outside the band (both ends allowed), a missing seed, a specialty and tuning with the wrong extras are refused, each with its message, in the contract's order. Rules: UFO (Born).
- A seed on any other drifter is refused; `Birth.seed` and `Birth.hazard_speed_mult` reach `born`; no other drifter changes. Rules: Spawner (step 8); The base (Seeded).
- `placement_seed` is the same for the same source and index, differs for the contract's examples, and lies from 0 to `MAX_SEED`. Rules: Spawner (Placement seed).
- It crosses at its speed, never stops or turns back, ignores the ship and the scroll, and flies level at its placed y until it is fully on screen; the first pick comes on that tick. Rules: UFO (Update; Fully on screen).
- Each pick: the first direction from the seed, later ones the opposite of the last; the interval a whole number from the scaled min to the scaled max; the new height `weave_step` away, the other way when the room is under `weave_step_min`, stopped at the band's edge otherwise. Rules: UFO (Pick).
- Over many seeds, both directions and Levels 1 and 8: the center never leaves the band, the up-or-down speed never passes `weave_speed_max`, never changes by more than `weave_turn` in a tick, and the UFO never passes its target; it lands on it and flies level until the next pick. Rules: UFO (Ease; Band).
- The Easing table, tick for tick. Rules: Diagram (Easing); UFO (Ease).
- `weave_brake_speed` and `weave_stop_distance` at the contract's examples. Rules: UFO (Ease; Tuning checks).
- `check_ufo_variant` and `check_ufo_weave` accept the GDD values and refuse each broken rule with its message, in order. Rules: UFO (Tuning checks).
- The same seed and placement give the same states, tick for tick; another seed gives another path; `update` never mutates its input. Rules: The base (Seeded); UFO (Pick).
- Level scaling: speed, `weave_speed_max` and `weave_turn` × hazard speed, both interval ends × Timer × rounded up, step and band unchanged; with the switches off, Level 1 values; `speed` from the placement changes only the crossing speed. Rules: UFO (Scales); Spawner (steps 4 and 5).
- Its drawn boxes and timeline, from both sides: entered on n 1, weaving from n 21, kept on n 344, dropped on n 345 with its `drifter gone` line, as the UFO timeline says; never dropped before it has entered. Rules: UFO (Drawn parts; Leaving); Diagram (UFO timeline).
- In the run: touching the disc or the dome is a hit, one life, the UFO's re-hit cooldown starts and it dims and keeps weaving; no second hit until the cooldown ends; no hit while the ship is invulnerable. Rules: run.md, steps 7 and 8; UFO (Touch; Hitting again).
- A UFO logs `drifter spawn`, `drifter active`, `drifter touch ... effect=hit` per hit and `drifter gone`, and nothing from `core.drifters`. Rules: run.md, Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once the Impact table's expected failures are cleared, with `test_ufo.py` in the `core` step and all its tests passing.

## Out of scope
- The ship against every UFO variant (task DRA-104-04); wave files and their seeds (task DRA-104-06).
- wave_check and its tests (`tools/wave_check/`, the main session).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
