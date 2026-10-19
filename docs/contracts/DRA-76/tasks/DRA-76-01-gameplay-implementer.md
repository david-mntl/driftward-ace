Feature: DRA-76
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/scroll.md, docs/contracts/systems/drifters.md
Status: open
Linear: DRA-77

## Read in the contract
- drifters.md: Purpose, Who builds what (the `game/core/levels.py` line). Interface, `game/core/levels.py`. Rules, Levels. Impact, the DRA-76 table.
- scroll.md: Purpose. Diagram: the step flowchart and the level-rise timeline.
- scroll.md: Interface, `game/core/scroll.py`.
- scroll.md: Rules: Values; The step; The next step's movement; Distance; Other rules (the speed follows the level).
- scroll.md: Impact, the DRA-76 table. Rationale, the DRA-76 lines.

## Builds
- `game/core/levels.py` (changed)
- `game/core/scroll.py` (changed)

## Depends on
None

## Not in the contract
None.

## Acceptance check
From `game/`, run:
```
python -c "
from core.levels import rest_gap_mult, scroll_mult
from core.scroll import Scroll, scroll_speed, scroll_step_px, start_scroll, step_scroll
print(scroll_mult(1), scroll_mult(8), rest_gap_mult(1), rest_gap_mult(8))
print(scroll_speed(1), round(scroll_speed(8), 6))
s = Scroll(ticks=30)
for level in (1, 2, 2, 8):
    s = step_scroll(s, level)
print(s.ticks, s.scrolled_ticks, s.raised_level_ticks, round(s.distance_px, 6), s.meters)
print(scroll_step_px(start_scroll(), 8), round(scroll_step_px(s, 8), 6), Scroll(ticks=130, scrolled_ticks=100).meters)
"
```
It prints four lines:
- `1.0 1.7 1.0 0.48`: the scroll speed × and Rest gap × rows at Levels 1 and 8.
- `1.1 1.87`: the scroll speed at Levels 1 and 8, px a tick.
- `34 4 (2, 0, 0, 0, 0, 0, 1) 5.39 0`: four moving ticks, one at Level 1, two at Level 2, one at Level 8, each at its own speed.
- `0.0 1.87 11`: no movement before the start delay ends, the Level 8 step after it, and the Level 1 meters unchanged.

Put the command and its output in the implementation report. `game/tests/check.sh` ends `QA: pass`: every existing test passes unchanged.

## Out of scope
- `core/run.py` (task DRA-76-05) and removing `LEVEL_STARTS_M` or `level_at` (same task).
- `core/waves.py` and `core/wave_files.py` (tasks DRA-76-03 and DRA-76-04).
- The starfield, the HUD, any view, `game/app/`, tests.
- Any change to the start delay, the `scroll start` log line, or the spawner.
