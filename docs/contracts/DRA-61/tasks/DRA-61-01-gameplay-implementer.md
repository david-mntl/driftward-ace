Feature: DRA-61
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/run.md
Status: done
Linear: DRA-63

## Read in the contract
- Purpose (the score sentence).
- Diagram: the score flowchart and the score timeline.
- Interface, `game/core/run.py`: `POINTS_PER_METER`, the `coin_points` field, the `score` property, the `start_run` comment.
- Rules: Values; Score (all of it); Logging ("Nothing else" line: no score log).
- Impact: the DRA-61 table.
- Rationale: the DRA-61 lines on the score property, `coin_points`, `POINTS_PER_METER` and no score log line.

## Builds
- `game/core/run.py` (changed)

## Depends on
None.

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from dataclasses import replace
from core.run import start_run, step_run
from core.ship import Thrust
run = start_run()
print(run.score, run.coin_points)
for _ in range(130):
    run = step_run(run, Thrust(up=True))
print(run.score == run.scroll.meters, run.score)
print(replace(run, coin_points=50).score)
"
```
It prints three lines:
- `0 0`: a new run starts at score 0 with no coin points.
- `True 11`: after 130 ticks (100 of them scrolled, 110 px) the score is the meters flown.
- `61`: the score adds the coin points to the meters.

Put the command and its output in the implementation report. `game/tests/check.sh lint`, `typecheck` and `core` pass; the existing core tests pass unchanged.

## Out of scope
- Any rule that changes `coin_points`: coins are DRA-62.
- Grazes, BEST, saves.
- Any change to `step_run`'s steps, `add_drifters`, the log lines, `core/scroll.py` or how meters are counted.
- UI, app and test files.
