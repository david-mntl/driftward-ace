Feature: DRA-111
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md
Impact: docs/contracts/DRA-111/impact.md
Status: done
Linear: DRA-115

## Read in the contract
- systems/drifters/electric-ball/core.md: Interface, Hitbox, Hitbox now, Fires, Touch, Tuning checks, The electric ball's file
- systems/drifters/shared/spawner-registry-tuning.md: How to add a drifter
- systems/drifters/shared/collision.md: Rules

## Builds
- `game/tests/core/test_collision.py` (changed: an electric ball branch in `load_variant_cases`, and its touching-distance cases)
- `game/tests/CONTEXT.md` (changed, only if its description of the variant cases names the drifters with their own branch)

## Depends on
DRA-111-01

## Not in the contract
None.

## Test
- `load_variant_cases` reads `game/tuning/drifters/electric_ball.json` (`ball_size`, `pulse_radius`), builds each variant the way `app.tuning` does, and a missing file still fails by name. Rules: The electric ball's file.
- Every electric ball variant has no hitbox while warning or charging, and its one circle while it fires with the ball on screen. Rules: Hitbox now; Fires.
- The ship meets each variant's firing circle at its own touching distance, strict as for every shape: touching edges is no overlap. Rules: Hitbox; Touch; collision part, Rules.
- The ship overlapping the ball while it charges overlaps no hitbox. Rules: Hitbox now; Touch.
- The graze zone is the firing circle grown by `GRAZE_MARGIN`, and nothing while it charges. Rules: Touch.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures are cleared, with the electric ball cases in `test_collision.py` in the `core` step and all of them passing.

## Out of scope
- The electric ball's cycle, start, leaving and the run (task DRA-111-03); wave files (task DRA-111-05).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
