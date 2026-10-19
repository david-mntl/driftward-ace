Feature: DRA-76
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/run.md, docs/contracts/systems/scroll.md, docs/contracts/systems/waves.md
Status: open
Linear: DRA-85

## Read in the contract
- run.md: Diagram: the one-tick flowchart (steps 3, 5, 9a, the retry), Drifters entering, the level-rise timeline.
- run.md: Interface, `waves`, `level`, `wave_spawns_due`, `start_run`.
- run.md: Rules: The level; steps 3, 5 and 9a; a game-over tick; `add_drifters`; Other rules (randomness; waves kept by a retry); Logging (the order line).
- scroll.md: Diagram, the level-rise timeline. Rules: The step; The next step's movement.
- waves.md: Rules: The wave clock (the bullets after step 4); Seeds.

## Builds
- `game/tests/core/test_run_waves.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for `core/test_run_waves.py`)

## Depends on
DRA-76-05

## Not in the contract
- Like `test_coin.py`, the file builds its own books and `DrifterTuning` in code from the GDD values at the top of the file, reads no `game/waves/` or `game/tuning/` file, and imports no expected number from the code under test. Source: tests/CONTEXT.md, Rules.

## Test
- A run started with no waves is at Level 1, has nothing due, scrolls at the Level 1 speed, and a retry gives a run with no waves. Rules: run.md, Interface; a game-over tick.
- A run started with waves takes its level and its due placements from them, and steps them once on every playing tick: during the respawn wait, on protected ticks, on a fall tick and on the tick lives reach 0. Rules: run.md, step 9a.
- The world moves at the speed of the level going into the tick: the level-up tick still moves at the old speed and the next tick at the new one, and steps 3 and 5 agree on every tick. Rules: run.md, The level, steps 3 and 5; scroll.md, The step.
- Drifters added after a level-up tick are born at the new level (their speed shows the Level 2 hazard speed ×), unless their placement names `as_level`; drifters already on the field keep their speed. Rules: run.md, `add_drifters`.
- Game over freezes the waves: no wave changes on game-over ticks. A retry starts Wave 0 at Level 1 with a new seed, and the same first seed gives the same run of waves again. Rules: run.md, a game-over tick; waves.md, Seeds.
- Logs: on a retry tick, `new run` and then the new run's `wave start` for Wave 0; the waves' lines come after the run's own lines of the tick. Rules: run.md, Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with `test_run_waves.py` in the `core` step and every earlier test unchanged.

## Out of scope
- The wave clock alone (task DRA-76-07), the wave files (task DRA-76-08), the scroll alone (task DRA-76-02).
- The app's `add_drifters` call and the debug choice: checked at integration.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, or test files other than the two listed.
