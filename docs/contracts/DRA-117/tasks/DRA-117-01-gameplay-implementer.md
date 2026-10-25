Feature: DRA-117
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md
Impact: docs/contracts/DRA-117/impact.md
Status: done
Linear: DRA-118

## Read in the contract
- systems/drifters/shared/base-interface.md: GRAZE_MARGIN, GrazeState, Birth (graze_margin), Drifter (graze_margin, graze_state, graze_zone), born_drifter, and the closing paragraph (DRA-117)
- systems/drifters/shared/base.md: Rules, Values paragraph, Graze zone, Graze state
- systems/drifters/shared/spawner-registry-tuning.md: Interface, HazardRules; Rules, Spawner (step 8), Tuning files (the hazard values)
- systems/drifters/shared/rationale.md: the two DRA-117 bullets

## Builds
- `game/core/drifters/base.py` (changed)
- `game/core/drifters/tuning.py` (changed)
- `game/core/drifters/spawner.py` (changed)

## Depends on
None

## Not in the contract
None.

## Acceptance check
From `game/`, a script in the implementation report builds a meteorite tuning in code from the GDD values (as the existing core tests do) and prints, for a medium meteorite spawned with `spawn_drifter` and then made ACTIVE:
- with the default `HazardRules()`: its `graze_margin`, its `graze_state`, and its `graze_zone()`;
- with `HazardRules(graze_margin=30)`: the same three, the zone's circle 30 px wider in radius than the hitbox's;
- the same meteorite in WARNING: `graze_zone()` is `()`; a coin and a floating island: `graze_zone()` is `()` and `graze_state` is OUTSIDE;
- a `Birth(...)` built without `graze_margin`, as the existing tests build it: it builds, with the default margin.

Put the script and its output in the implementation report. `game/tests/check.sh` passes in full, with no failure: every existing test keeps its result.

## Out of scope
- The graze step, the run, popups, rings, the score (task DRA-117-02). Views, `game/app/`, tuning files, tests.
- Any change to a drifter subclass, `core/collision.py`, `core/run.py` or `tools/`.
