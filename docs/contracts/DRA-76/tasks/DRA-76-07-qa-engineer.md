Feature: DRA-76
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/waves.md
Status: open
Linear: DRA-83

## Read in the contract
- Diagram: the order of one run, the one-tick flowchart, Starting the next wave, the rest gap timeline.
- Interface, `game/core/waves.py`.
- Rules: Values; The order; The wave clock; Starting a wave; Random picks; Seeds; The rest gap; Logging; Other rules.

## Builds
- `game/tests/core/test_waves.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for `core/test_waves.py`)

## Depends on
DRA-76-03

## Not in the contract
- Like `test_coin.py`, the file builds its own books, waves and placements in code, takes every expected number from the GDD or the contract at the top of the file, reads no `game/waves/` or `game/tuning/` file, and imports no expected number from the code under test. Source: tests/CONTEXT.md, Rules.

## Test
- `start_waves` gives Wave 0 at Level 1, starting at 0 px, with nothing due, and logs its start. Rules: The order; Logging.
- A placement comes due on the first tick its trigger is reached, once, in trigger order; a trigger of 0 is due on the tick its wave starts; a distance within a micro-px of a trigger counts as reached. Rules: The wave clock, step 2.
- A wave ends on the tick the distance reaches its length. With no rest the next wave starts where the last one ended, and its placements already reached are due on that same tick; several waves can end on one tick. Rules: The wave clock, step 3.
- Fixed waves play in playlist order, then the random slots; Wave 0 is no slot; a fixed wave may appear twice. Rules: The order; Starting a wave.
- The level rises on the tick the last wave of its playlist ends and not before, so never inside a wave; a level with no slots is passed on that tick; at Level 8 the level never rises and random picks go on forever after its playlist. Rules: The wave clock, step 3.1; The order.
- A random pick is a pool wave with `min_level` at most the level, never the wave that just played (after Wave 0, a fixed wave, a rest, or a level rise), and the only allowed wave plays again. Rules: Random picks.
- The same seed gives the same waves; `next_run_waves` starts Wave 0 at Level 1 with a new seed; over many picks among several pool waves, two seeds give different orders. `pick_pool_wave` draws from the chooser it is given only. Rules: Seeds; Random picks.
- `rest_gap_ticks` is the extra rest alone at every level while `rest_gap_base` is 0. A rest of R ticks shows on exactly R states with no current wave and nothing due; the next wave starts at the distance of the tick the rest ends; a wave with no extra rest leaves no rest. Rules: The rest gap; The wave clock, steps 1 and 3.2; Diagram (rest gap timeline).
- Logs: `wave start`, `wave end`, `level up` and `rest start` once per event, in the contract's order, and nothing on a tick with no event. Rules: Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with `test_waves.py` in the `core` step.

## Out of scope
- The wave files (task DRA-76-08) and the waves inside the run (task DRA-76-09).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, or test files other than the two listed.
