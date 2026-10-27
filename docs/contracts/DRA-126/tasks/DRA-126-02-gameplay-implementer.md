Feature: DRA-126
Created by: architect
Assignee: gameplay-implementer
Writes to: game/core/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-126/impact.md
Status: done
Linear: DRA-140

## Read in the contract
- Purpose (the game-over and saves paragraphs)
- Diagram: the state diagram, the tick flowchart, the game-over table with a top-10 score
- Interface: "DRA-126: what saves add and change", the `core/game_flow.py` block
- Rules: Values; Presses (the picker items); Start; INSTRUCTIONS and LEADERBOARD (the leaderboard item); PLAYING; Opening GAME_OVER; GAME_OVER; `saves_changed`; `stop_saves`; `best` and `leaderboard`; Same in both modes; Pure; Logging
- Rationale: the DRA-126 items (Name entry is a mode of GAME_OVER; The place is worked out once; The flow holds the saves; A failed write turns saves off; New fields and parameters have defaults; The picker's arrows are presses)
- `docs/contracts/systems/saves.md`, Interface (built in DRA-126-01)

## Builds
- `game/core/game_flow.py` (changed)

## Depends on
DRA-126-01

## Not in the contract
None.

## Acceptance check
From `game/`, a script in the implementation report feeds `step_flow` scripted `TickInput`s and prints one row per tick (`screen`, `game_over_message`, `picking`, the picker's slots and cursor, `game_over_selection`, `saves_changed`, `best`, the number of `leaderboard` entries) plus every `core.game_flow` and `core.run` log line, reaching game over quickly as the run tests do (one life, a falling ship, short `LastLifeRules`), for:
- `start_flow(run, Saves())`: game over opens with NEW_BEST_SCORE and a blank picker; up, down, down, left, right (each a fresh press, one held for 30 ticks to show it steps once); then pick `ACE` and press Enter held for 30 ticks: `saves_changed` on that tick only, no RETRY; release, Enter: a new run, `best` now the saved score;
- the next game over with the same saves: the picker starts with `ACE`; a run that lands at place 2 and one at place 4 show TOP_3 and TOP_10;
- a full list no run beats: GAME_OVER, no picker, up and down move RETRY and MENU at once;
- `start_flow(run)` (no saves): GAME_OVER, no picker, `best` None, `leaderboard` empty;
- a picker confirmed with every slot blank: nothing saved, `last_nickname` unchanged, `saves_changed` False;
- `stop_saves` called on the tick after a save: `best` None, the screen unchanged, the next game over with no picker.

Put the script and its output in the implementation report. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- `core/saves.py` and `core/run.py` (DRA-126-01). The views (DRA-126-03 to -05). Tests (DRA-126-06 to -08).
- Loading the saves, writing them after a `saves_changed` tick, calling `stop_saves` on a failed write, and passing `best` and `leaderboard` to the views: `game/app/`, the Integration Engineer's.
