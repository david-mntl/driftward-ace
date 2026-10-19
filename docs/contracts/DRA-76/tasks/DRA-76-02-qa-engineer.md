Feature: DRA-76
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/scroll.md, docs/contracts/systems/drifters.md
Status: done
Linear: DRA-78

## Read in the contract
- drifters.md: Interface, `game/core/levels.py`. Rules, Levels. Impact, the DRA-76 table (the `test_drifters.py` row).
- scroll.md: Diagram, the level-rise timeline. Interface, `game/core/scroll.py`.
- scroll.md: Rules: Values; The step; The next step's movement; Distance; Logging.

## Builds
- `game/tests/core/test_scroll.py` (changed: new tests for the speed per level)
- `game/tests/core/test_drifters.py` (changed: the level table test gains two rows; `level_at` and its check go)

## Depends on
DRA-76-01

## Not in the contract
None.

## Test
- The level table gives scroll speed × and Rest gap × for Levels 1 to 8 as 08-difficulty.md has them, next to hazard speed × and Timer ×; Levels 0 and 9 raise for both new rows. Rules: drifters.md, Levels.
- `test_drifters.py` no longer imports or checks `level_at`. Rules: drifters.md, Levels; Impact.
- `scroll_speed` at each level is the base speed times that level's scroll speed ×; a level outside 1 to 8 raises. Rules: scroll.md, Values; The step.
- Stepping at a level moves the world at that level's speed once the start delay is over, never before, and counts the tick for that level. Rules: scroll.md, The step.
- Over steps at several levels, the distance is each level's ticks times its speed, summed, and the meters round down without losing a meter at an exact boundary. Rules: scroll.md, Distance.
- `scroll_step_px` at a level always equals what `step_scroll` adds at that level on the same tick, at every level. Rules: scroll.md, The next step's movement.
- With no level given, both behave as Level 1, as before. Rules: scroll.md, The step.
- `scroll start` still logs once per scroll, whatever the level. Rules: scroll.md, Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with the new tests in the `core` step, and `game/tests/core/test_drifters.py` no longer names `level_at`.

## Out of scope
- The waves and the run (tasks DRA-76-07 to DRA-76-09).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, or test files other than the two listed.
