Feature: DRA-111
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/waves.md, docs/contracts/systems/drifters.md
Impact: docs/contracts/DRA-111/impact.md
Status: done
Linear: DRA-116

## Read in the contract
- systems/waves.md: Drifter type, Built drifter, Seam start
- systems/drifters/electric-ball/core.md: Born, Start, Placement fields, For wave_check

## Builds
- `game/tests/core/test_wave_files.py` (changed: the unknown-type message and the electric ball cases)
- `game/tests/core/test_drifter_registration.py` (changed: the telegraph guard learns the electric ball)

## Depends on
DRA-111-01

## Not in the contract
None.

## Test
- The unknown-type refusal lists the types in enum order, ending `ufo, electric_ball`. Rules: waves.md, Drifter type.
- An electric ball placement without x is refused naming the placement and the drifter's message; one with a seed is refused the same way; one with `invert` loads. Rules: waves.md, Built drifter; Placement fields; Born.
- An electric ball is a hazard to the seam check: below the seam distance refused, at it loaded. Rules: waves.md, Seam start.
- The telegraph guard: the electric ball's `telegraph_ticks` gives its type's charge, and None without its type values; every drifter but the chain lightning and the electric ball still says None. Rules: For wave_check.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures are cleared, with the updated `test_wave_files.py` and `test_drifter_registration.py` in the `core` step and all their tests passing.

## Out of scope
- The electric ball itself (task DRA-111-03) and the ship against it (task DRA-111-04).
- The wave state, the clock and the picker; wave_check and its tests (`tools/wave_check/`, the main session).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, wave files or other test files.
