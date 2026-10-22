Feature: DRA-96
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/ship.md
Status: open
Linear: DRA-101

## Read in the contract
- Diagram: the step flowchart (step 2, then planet pull) and Planet pull (the table, the escapes, two fields).
- Interface, `game/core/ship.py`: `GravityWell`, `NO_WELLS`, `well_pull`, `check_escapable_pull`, `step`, and the DRA-96 paragraph after the block.
- Rules: the step (2, Then planet pull); Planet pull (all of it); Escape (all of it); Logging (the planet pull line).
- Impact, the DRA-96 table (the test rows).

## Builds
- `game/tests/core/test_ship_pull.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-96-01

## Not in the contract
- Like `test_ship_islands.py`, the new file writes the GDD values it needs at the top (`gravity`, `thrust_up`, `thrust_side`, `drag_x`, `fall_cap` from 04-ship.md; `pull_radius`, `pull_max` and the 32 px surface from drifters/08-planet.md) and builds every `GravityWell` by hand. It reads no `game/tuning/` file and imports no expected number from the code under test. Source: tests/CONTEXT.md, Rules.

## Test
- No pull outside the field or on its edge, at several angles. Rules: Planet pull (2).
- The pull just inside the edge, mid-field and at the surface follows the straight line, pointing at the field's center, at several angles. Rules: Planet pull (4, 5).
- Inside the surface the pull stays at `pull_max`; at the exact center there is none. Rules: Planet pull (3; Never more than `pull_max`).
- Two overlapping fields add up; a field that doesn't hold the ship adds nothing. Rules: Planet pull (6).
- The pull comes right after gravity: it is measured from the ship's position before the move, drag acts on its x part and the fall cap on its y part. Rules: the step (2, Then planet pull).
- With no wells, `step` gives the same ship as before DRA-96, with and without ground. Rules: Interface (the DRA-96 paragraph).
- Escape from the surface at `pull_max`: up held from just above the planet and a side key held from beside it move the ship away on every tick until it is out of the field. Rules: Escape; Diagram (Planet pull, Escape).
- `check_escapable_pull` accepts today's `pull_max`, refuses one that only ties `thrust_up` with gravity and one past it with the contract's message, and refuses one at or past `thrust_side` with its message (with `core.ship.THRUST_SIDE` lowered through `monkeypatch`: the check reads it when called). Rules: Escape.
- `well_pull`, `check_escapable_pull` and a pulled `step` log nothing. Rules: Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once the Impact table's expected failures are cleared, with `test_ship_pull.py` in the `core` step and all its tests passing.

## Out of scope
- Planets in the run, the wells the run gathers, the respawn wait and invulnerability (task DRA-96-07).
- The ship against the planet's hitbox (task DRA-96-06).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
