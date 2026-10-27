Feature: DRA-126
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-126/impact.md
Status: done
Linear: DRA-145

## Read in the contract
- Diagram: the tick flowchart, the game-over table with a top-10 score
- Interface: "DRA-126: what saves add and change", the `core/game_flow.py` block
- Rules: Presses (the picker items); Start; INSTRUCTIONS and LEADERBOARD; Opening GAME_OVER; GAME_OVER; `saves_changed`; `stop_saves`; `best` and `leaderboard`; Pure; Logging

## Builds
- `game/tests/core/test_game_flow.py` (changed: the logging test `impact.md` names, and the DRA-126 tests)
- `game/tests/CONTEXT.md` (changed: the file's paragraph)

## Depends on
DRA-126-01, DRA-126-02

## Not in the contract
- Runs reach game over as the existing flow tests do. Saves are built directly with `Saves` and `ScoreEntry`; a list no run beats is `TOP_N` entries with a score far above any test run. Source: tests/CONTEXT.md, Rules.

## Test
- `start_flow(run)` holds no saves; `start_flow(run, saves)` holds them as given, every other DRA-126 field at its default. Rules: Start.
- When GAME_OVER opens, the message follows the run's place and the run's level reached; a run with a place gets a picker filled from `last_nickname` and `picking`; a run off the list, or a flow with no saves, gets GAME_OVER, no picker, and RETRY and MENU taking keys at once. Rules: Opening GAME_OVER.
- Each opening sets the message, picker and picking again: nothing is kept from an earlier game over. Rules: Opening GAME_OVER.
- The message never changes while GAME_OVER shows, the save included. Rules: Opening GAME_OVER.
- While picking, up and down turn the character, left and right move the cursor, each once per fresh press; up with down and left with right cancel; a turn and a move on one tick both act, the turn in the old slot; RETRY and MENU never move; a held arrow never repeats. Rules: Presses; GAME_OVER.
- A fresh confirm while picking saves the entry with the run's score and level reached, sets `last_nickname`, sets `saves_changed` for that tick only, and ends picking with the picker kept; an all-blank name saves nothing and leaves `last_nickname`; the arrows pressed on the confirm tick change nothing. Rules: GAME_OVER; `saves_changed`; Presses.
- The confirm that saves, held, never picks RETRY; a fresh press after it does. Rules: GAME_OVER; Diagram (the game-over table).
- Saves are kept through RETRY, MENU and later runs. Rules: GAME_OVER.
- `stop_saves` clears the saves and `saves_changed` and changes nothing else; after it, no picker and no best. Rules: `stop_saves`.
- `best` and `leaderboard` read the saves, and are None and empty without them; BEST changes only on a save. Rules: `best` and `leaderboard`.
- `step_flow` never mutates its input and gives the same flow for the same input, with saves. Rules: Pure.
- The new log lines come in the contract's order and wording: the message and place right before `screen game_over`, the picker's lines once per press, the saved and empty-name lines. Rules: Logging.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with the DRA-126 tests in `test_game_flow.py` in the `core` step, the logging test `impact.md` names passing again, and all its tests passing.

## Out of scope
- The saves' own tests and the run's level reached (DRA-126-06), the views' tests (DRA-126-08), the app's loading and writing (the Integration Engineer's browser checks).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than those listed in Builds.
