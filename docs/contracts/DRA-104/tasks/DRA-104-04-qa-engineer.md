Feature: DRA-104
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md
Status: done
Linear: DRA-108

## Read in the contract
- Diagram: UFO (the sketch: the hitbox and the graze zone).
- Interface: `game/core/drifters/ufo.py` (`ufo_hitbox`, `Ufo`); `game/core/drifters/spawner.py` (`Placement.seed`).
- Rules: UFO (Variants, Hitbox, Born, Touch); Tuning files (the UFO's file); How to add a drifter (the ship-against-every-variant cases).
- Impact, the DRA-104 table (the `test_collision.py` row).

## Builds
- `game/tests/core/test_collision.py` (changed: a UFO branch in `load_variant_cases`, and the UFO's touching-distance cases)
- `game/tests/CONTEXT.md` (changed, only if its description of the variant cases names the drifters with their own branch)

## Depends on
DRA-104-01

## Not in the contract
None.

## Test
- `load_variant_cases` reads `game/tuning/drifters/ufo.json` (`disc_width`, `disc_height`, `dome_radius`), builds each variant the way `app.tuning` does, and a missing file still fails by name. Rules: Tuning files (the UFO's file).
- Every UFO variant, spawned with a seed at a y inside its band, has no hitbox while warning and its two shapes once ACTIVE: the disc box first, the dome circle on the middle of the disc's top edge. Rules: UFO (Hitbox, Born).
- The ship meets each variant at its own touching distance, on the disc and on the dome alone (above the disc, clear of it), strict as for every shape: touching edges is no overlap. Rules: UFO (Hitbox, Touch); Collision.
- The graze zone is the disc box and the dome circle each grown by 14. Rules: UFO (Touch); The base (Graze zone).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once the Impact table's expected failures are cleared, with the UFO cases in `test_collision.py` in the `core` step and all of them passing.

## Out of scope
- The UFO's weave, start, leaving and the run (task DRA-104-05); wave files (task DRA-104-06).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
