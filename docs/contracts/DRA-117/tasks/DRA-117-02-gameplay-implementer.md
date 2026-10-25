Feature: DRA-117
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/run.md, docs/contracts/systems/drifters.md
Impact: docs/contracts/DRA-117/impact.md
Status: done
Linear: DRA-119

## Read in the contract
- run.md: Purpose; Diagram (the tick flowchart, steps 3a and 5b; the score flowchart; the two graze state tables)
- run.md: Interface, "DRA-117: what graze adds and changes" (core/graze.py, core/popup.py, core/run.py blocks)
- run.md: Rules: the Values paragraph; step 3a; step 5b; the closing "If nothing happened" line; a game-over tick (retry); Score (Formula, Grazes, Never goes down, Game over); Other rules (game over tick, Grazes); Logging (`drifter graze`, the order inside one tick, Nothing else)
- run.md: Rationale, the DRA-117 bullets
- drifters.md: systems/drifters/shared/base.md, Rules, Graze zone and Graze state (built in DRA-117-01)

## Builds
- `game/core/graze.py` (new)
- `game/core/popup.py` (changed)
- `game/core/run.py` (changed)

## Depends on
DRA-117-01

## Not in the contract
None.

## Acceptance check
From `game/`, a script in the implementation report builds a meteorite tuning in code from the GDD values and runs `step_run` with ArrowUp held, so the ship sits on the top line, and prints one row per tick (`graze_state` of each drifter, `grazes`, `score`, each popup's kind, x, y and age, each ring's age, diameter and opacity), for these cases:
- a medium meteorite placed to fall past the ship's side, its hitbox never touching the ship, its graze zone overlapping it: OUTSIDE, INSIDE for the ticks it overlaps, SPENT on the exit tick, with one `drifter graze` log line, `grazes` 1, the score up by the graze points, one GRAZE popup at the ship's center and one ring, both at age 0 on that tick; then the ring's rows until it is gone and the popup's age climbing;
- a meteorite falling onto the ship: SPENT on the touch tick, a hit, never a graze;
- the first case with the ship protected on the exit tick (start the run with a fresh hit or set `invuln_ticks_left`): no pay, OUTSIDE after the exit;
- the first case with the ship standing in the respawn wait: no pay;
- the first case with `start_run(graze_rules=GrazeRules(points=40, ring_ticks=5))`: the score up by 40 and the ring gone after 5 states;
- a game over, then a retry: `grazes` 0, no rings, the same `graze_rules`.

Put the script and its output in the implementation report. `game/tests/check.sh lint` and `typecheck` pass. In `core` and `ui`, the only failures are the ones `impact.md` expects from DRA-117-02; every other existing test passes unchanged.

## Out of scope
- The views (DRA-117-03, DRA-117-04), `game/app/` (the loader and the draw call are the Integration Engineer's), tuning files, tests.
- Any change to `core/drifters/`, `core/collision.py`, `core/ship.py`, `core/waves.py` or `tools/`.
- A graze sound, a combo or multiplier, LV, BEST (scope report DRA-117, Out).
