Feature: DRA-47
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/drifters.md, docs/contracts/systems/run.md
Status: open
Linear: DRA-49

## Read in the contract
- drifters.md: Interface, `game/core/drifters/base.py`: `DEFAULT_TELEGRAPH_MIN_TICKS`, `DrifterTypeExtra`, the `Birth` fields `type_extra` and `telegraph_min_ticks`, `warning_copy`, `settle_warning`, `scale_timer`, `scale_telegraph`, and the note under the block.
- drifters.md: Interface, `game/core/drifters/tuning.py`: `DrifterTypeTuning.extra`, `HazardRules.telegraph_min_ticks`.
- drifters.md: Rules, The base: Warning copy, Warning settle, Timers. Rules, Spawner: steps 5 and 8.
- drifters.md: Diagram, Birth.
- run.md: Rules, `add_drifters`; Rationale, "The warning settles in `add_drifters`".

## Builds
- `game/core/drifters/base.py` (changed)
- `game/core/drifters/tuning.py` (changed)
- `game/core/drifters/spawner.py` (changed)
- `game/core/run.py` (changed)

## Depends on
None

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.collision import Circle
from core.drifters.base import DrifterType, TickContext, scale_telegraph, scale_timer
from core.drifters.spawner import Placement
from core.drifters.tuning import DrifterTuning, DrifterTypeTuning, HazardRules, PlaytestSwitches, VariantTuning
from core.run import add_drifters, start_run
print([scale_timer(120, m) for m in (1.00, 0.94, 0.89, 0.85, 0.81, 0.77, 0.74, 0.70)], scale_telegraph(40, 1.0, 45), scale_telegraph(120, 0.70, 45))
rock = DrifterTypeTuning(variants={'medium': VariantTuning(width=28, height=28, hitbox=(Circle(0, 0, 14),))}, default_variant='medium', speed_ratio=0.375, entry_warning_ticks=60)
tuning = DrifterTuning(drifters={DrifterType.METEORITE: rock}, switches=PlaytestSwitches())
run = add_drifters(start_run(), [Placement(DrifterType.METEORITE, x=320.0)], tuning)
obj = run.drifters[0]
print(HazardRules().telegraph_min_ticks, rock.extra, obj.warning_copy() is obj, obj.settle_warning(TickContext(ship=run.ship)) == obj, obj.uid)
"
```
It prints two lines:
- `[120, 113, 107, 102, 98, 93, 89, 84] 45 84`: the charge by level from the Timer × row, rounded up, and the telegraph floor.
- `45 None True True 1`: the shared default, no type extra for the meteorite, and the two new hooks change nothing for it.

Put the command and its output in the implementation report. `game/tests/check.sh lint` passes, and `game/tests/check.sh core -k "not collision"` passes: no existing drifter or run test changes.

## Out of scope
- The line shape (task DRA-47-01). The chain lightning itself and `DrifterType.CHAIN_LIGHTNING` (task DRA-47-03).
- Any view, `game/app/`, data file or test file.
