Feature: DRA-125
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-125/impact.md
Status: open
Linear: DRA-136

## Read in the contract
- Diagram: the state diagram, the tick flowchart, the two tables
- Interface: the `core/game_flow.py` block
- Rules: Presses; Start; MENU; INSTRUCTIONS and LEADERBOARD; PLAYING; PAUSED; GAME_OVER; `run_stepped`; `add_flow_drifters`; Pure; Logging

## Builds
- `game/tests/core/test_game_flow.py` (new)
- `game/tests/CONTEXT.md` (changed: a paragraph for the new file)

## Depends on
DRA-125-01, DRA-125-02

## Not in the contract
- Runs are built with `start_run` and short `LastLifeRules` where a test needs to reach game over quickly; the last life is reached by putting the run at one life with a falling ship (`dataclasses.replace`), as the run tests do. Source: tests/CONTEXT.md, Rules.

## Test
- `start_flow` shows MENU with Play selected and RETRY ready, and a confirm key or arrow held from the start does nothing until released and pressed again. Rules: Start.
- Up and down move the menu selection one item per fresh press and wrap at both ends; holding moves it once; up and down on one tick cancel; left and right do nothing. Rules: MENU; Presses.
- A fresh confirm on Instructions or Leaderboard opens that page; a fresh confirm there goes back to the menu with Play selected, whatever was selected before; nothing else acts on a page. Rules: MENU; INSTRUCTIONS and LEADERBOARD.
- A confirm held across any screen change never acts on the new screen: Play held never pauses, a page closed by a held key never picks a menu item, RETRY held never pauses, a resume held never pauses again. Rules: Presses; Diagram (the first table).
- Play starts the app's run untouched and steps it from the next tick; after a game over and MENU, Play starts `next_run`. Rules: MENU.
- During play a fresh confirm or a focus loss pauses without stepping the run; while paused the run never changes but `held`, a focus loss does nothing, and only a fresh confirm resumes, without stepping on that tick. Rules: PLAYING; PAUSED.
- An arrow pressed during a pause in the respawn wait and held after the resume doesn't end the wait; a fresh arrow press does. Rules: PAUSED; Diagram (the second table).
- During the last life the run is stepped on every tick and neither a confirm nor a focus loss pauses. Rules: PLAYING.
- When a step ends in game over the screen is GAME_OVER with RETRY selected; there up and down wrap between RETRY and MENU, the run is never stepped, arrows never retry and a focus loss does nothing. Rules: PLAYING; GAME_OVER.
- RETRY gives `next_run` and PLAYING at once; MENU gives MENU with Play selected and the run unchanged. Rules: GAME_OVER.
- Focus losses on the menu, a page, the pause and the game-over screen change nothing. Rules: MENU; INSTRUCTIONS and LEADERBOARD; PAUSED; GAME_OVER.
- `run_stepped` is True only after a tick that stepped the run; `add_flow_drifters` adds placements only then, never on a pause, page, menu, game-over, Play, resume or RETRY tick. Rules: `run_stepped`; `add_flow_drifters`.
- `step_flow` never mutates its input and gives the same flow for the same input. Rules: Pure.
- It logs `screen <value>` on each screen change, `pause by=key` or `pause by=focus` right before `screen paused`, `menu select` and `game over select` on each move and not on a reset, the run's lines before the flow's, and nothing on a tick where nothing changes. Rules: Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with `test_game_flow.py` in the `core` step and all its tests passing.

## Out of scope
- The run's own last-life tests (DRA-125-09), the views' tests (DRA-125-11, DRA-125-12), the app's key and focus reading (the Integration Engineer's browser checks).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than those listed in Builds.
