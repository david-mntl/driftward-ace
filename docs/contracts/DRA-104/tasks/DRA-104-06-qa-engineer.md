Feature: DRA-104
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/waves.md, docs/contracts/systems/drifters.md
Status: open
Linear: DRA-110

## Read in the contract
- waves.md: Rules, The wave files (Placement: `seed`; Drifter type; Built drifter, with Seed; One path per UFO; Seam start).
- waves.md: Impact, the DRA-104 table (the `test_wave_files.py` row).
- drifters.md: Interface, `game/core/drifters/spawner.py` (`placement_seed`, `MAX_SEED`); Rules: Spawner (step 8, Placement seed); UFO (Born: the band refusal).

## Builds
- `game/tests/core/test_wave_files.py` (changed: the unknown-type refusal and the seed cases)

## Depends on
DRA-104-01, DRA-104-02

## Not in the contract
None.

## Test
- The unknown-type refusal uses a name that is no drifter type (not `ufo`), and its message lists the types in enum order, ending `planet, ufo`. Rules: The wave files (Drifter type).
- `seed` is accepted from 0 to `MAX_SEED` and refused below 0, above it, as a float or as a boolean, with its message. Rules: The wave files (Placement).
- A UFO with no seed gets `placement_seed(<wave id>, <index in the file>)`, the index taken before the sort by `at_px`; a given seed is kept; every other drifter's seed stays None. Rules: The wave files (Built drifter, Seed).
- A seed on a drifter that has none, and a UFO placed outside its band, are refused naming the placement. Rules: The wave files (Built drifter).
- Two UFOs in one wave with the same seed, given or default, are refused, the later one named with the earlier; the same seed in two different waves loads. Rules: The wave files (One path per UFO).
- A UFO is a hazard to the seam check: below 120 px refused, at 120 px loaded. Rules: The wave files (Seam start).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once the Impact tables' expected failures are cleared, with the updated `test_wave_files.py` in the `core` step and all its tests passing.

## Out of scope
- The UFO itself (task DRA-104-05) and the ship against it (task DRA-104-04).
- The wave state, the clock and the picker; wave_check and its tests (`tools/wave_check/`, the main session).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, wave files or other test files.
