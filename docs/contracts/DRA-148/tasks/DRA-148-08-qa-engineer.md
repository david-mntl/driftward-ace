Feature: DRA-148
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/level-up.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-148/impact.md
Status: done
Linear: DRA-156

## Read in the contract
- systems/level-up/core.md: Diagram, Interface, The banner, Pause, Game over and a new run, The shown level, The `level_up` cue
- run.md: Interface, DRA-148: the level-up banner, step 9b, The last life, A last-life tick, A game-over tick, `next_run`

## Builds
- `game/tests/core/test_run_level_up.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-148-02

## Not in the contract
- Like `test_run_waves.py`, the new file builds its own wave book, rules and runs at the top of the file and reads no `game/tuning/` file. Source: tests/CONTEXT.md, Rules.

## Test
- The banner starts on the state after the rise tick at age 0, with the previous level and the new one, and ages one a tick. Rules: The banner (2, 3).
- `level_up_cue` is True on the state after the rise tick only; with a rest of 0 there is no banner and no cue. Rules: The `level_up` cue.
- `hud_level` is the previous level until the arrival age and the real level from it; `run.level`, the scroll speed and `level_reached` are the new level at once. Rules: The shown level.
- The banner is None once it has lived its lifetime, and it is None through Wave 0's end, at Level 8 and for a run with no waves. Rules: The banner (4).
- A skipped level (empty playlist) shows the level reached in the banner and the shown level. Rules: The shown level.
- Pause: a run the flow doesn't step keeps its banner age (through the game flow's paused ticks). Rules: Pause.
- A hit or a fall during the banner changes nothing about its age or levels. Rules: The banner.
- Losing the last life during the banner sets it to None on that tick and `hud_level` equals `level`; a level rise on a later last-life tick starts no banner and no cue; so does a rise on the very tick the last life is lost. Rules: The banner (1).
- A game-over tick changes no banner (None), and `next_run` starts with none and with the same rules. Rules: Game over and a new run.
- The respawn wait and protected ticks age the banner like any playing tick. Rules: The banner.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with `test_run_level_up.py` in the `core` step and all its tests passing.

## Out of scope
- The wave clock's rest and `core/level_up.py` (task DRA-148-07). The views and the HUD (task DRA-148-09). The loaders in `game/app/`.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files or other test files.
