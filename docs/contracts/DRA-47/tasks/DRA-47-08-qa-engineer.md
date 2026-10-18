Feature: DRA-47
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md
Status: done
Linear: DRA-55

## Read in the contract
- drifters.md: Interface, `game/core/drifters/chain_lightning.py` (all of it); Interface, `game/core/drifters/base.py`: `warning_copy`, `settle_warning`, `scale_timer`, `scale_telegraph`, `DEFAULT_TELEGRAPH_MIN_TICKS`; Interface, `tuning.py`: `HazardRules.telegraph_min_ticks`, `DrifterTypeTuning.extra`.
- drifters.md: Rules, Chain lightning (all of it). Rules, The base: Warning copy, Warning settle, Timers, Re-hit cooldown, Entering, Leaving. Rules, Spawner: steps 4, 5 and 8.
- drifters.md: Diagram, Chain lightning cycle and Chain lightning timeline.
- run.md: Rules, `add_drifters`; a playing tick, steps 3, 7 and 8; Logging.

## Builds
- `game/tests/core/test_chain_lightning.py` (new)
- `game/tests/CONTEXT.md` (changed: one line for the new file, as for `test_satellite.py`)

## Depends on
DRA-47-02, DRA-47-03

## Not in the contract
- Like `test_satellite.py`, the file builds its own `DrifterTuning` from the GDD values at the top of the file (`make_tuning`, `hazards=` optional) and reads no `game/tuning/` file. The seven layouts' unit coordinates are in drifters.md, Rules, Chain lightning, Layout; the sizes and timers in drifters/03-chain-lightning.md, Values.

## Test
- Spawned with no variant it is `pair_flat`; with no `x` it raises naming `x`; with no `y` it starts with its box just above the top edge; a specialty switched on raises; `invert` is accepted. Rules: Chain lightning (Born, Start).
- Every layout: neighbouring nodes `node_spacing` apart, the box around the nodes centered on the chain, width and height as the Layout table; `invert` mirrors left to right, except the triangle, which turns point down; the symmetric layouts are unchanged. Rules: Chain lightning (Layout, Born).
- The cycle: it charges on exactly `charge_ticks` states from the one it appears on, fires on the next `fire_ticks`, then charges again, and keeps cycling while it falls; neither charging nor firing in WARNING. Rules: Chain lightning (Cycle); Diagram, timeline.
- Rays: one more per node at each step of a Level 1 charge, up to `charge_rays`; at Level 8 the steps follow the shorter charge and all rays still show for its last step; none while firing or warning. Rules: Chain lightning (Charge rays).
- Scaling: the charge at each level is the Level 1 charge × Timer × rounded up; never below `telegraph_min`, including a tuning charge already below it and a `telegraph_min` set in `HazardRules`; the fire never changes with level; with `timer_scaling` off the charge is the Level 1 value at every level; speed is × the level's hazard speed. `scale_timer` never adds a tick to a whole product. Rules: The base (Timers); Chain lightning (Values at Level 1); Spawner (steps 4 and 5).
- Arcs fire only while both their nodes are on screen: a node above the top edge or past the floor takes its arcs with it, the others keep firing; an arc stops on the first state one of its nodes leaves. Rules: Chain lightning (On screen, Firing arcs).
- Hitbox: nothing while warning or charging; while firing, one line per firing arc and one circle per node with a firing arc, nothing for a node whose arcs are all off; the graze zone exists only while an arc fires. Rules: Chain lightning (Hitbox, Touch).
- Warning: through `add_drifters`, the warning sits above the node nearest the ship; on a tie, the left one; its center is clamped by half the triangle's width on both axes; it stays put for the whole warning. `warning_copy()` is the point-up triangle for every variant and `invert`, sized on it. A chain built without `add_drifters` warns above its own center. The meteorite and the satellite come back unchanged from `settle_warning`, and their copy is themselves. Rules: Chain lightning (Warning node, Warning place, Warning copy); The base (Warning copy, Warning settle); run.md, `add_drifters`.
- Leaving: it is dropped from the run once every node is fully below the floor, never before it has entered. Rules: Chain lightning (Leaving); The base (Entering, Leaving).
- In the run: a charging chain over the ship never hits; a firing arc, or a node while one of its arcs fires, costs one life and logs one `drifter touch`; after that the whole chain can't hit for `rehit_cooldown_ticks` and its `brightness()` is `rehit_dim`, while it keeps falling and cycling; a touch while the ship is invulnerable is no hit and starts no cooldown. Rules: Chain lightning (Touch, Hitting again); run.md, steps 7 and 8.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with the new tests in `tests/core/test_chain_lightning.py` in the `core` step.

## Out of scope
- Collision tables and the ship-against-every-variant cases (task DRA-47-07).
- Views and pixels (the integration checks in `docs/contracts/systems/app.md`). The tuning loader (`game/app/`).
- Graze scoring, waves, wave_check (scope report DRA-47, Out).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code or data files.
