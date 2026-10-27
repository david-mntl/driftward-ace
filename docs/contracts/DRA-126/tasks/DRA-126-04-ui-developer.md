Feature: DRA-126
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-126/impact.md
Status: done
Linear: DRA-142

## Read in the contract
- Diagram: the screens (GAME_OVER with the picker, after the save)
- Interface: the `ui/game_over.py` block under "DRA-126: what saves add and change"; the `ui/screen_look.py` block
- Presentation: the `flow.screen` GAME_OVER, `flow.game_over_message` and `flow.picker`, `flow.picking` rows; the shared items (Text, Lines and blank lines, Selection marker, Box, Cache, Only draws); Game-over screen, all of it (Two layouts, each function, Cells, Characters, Underline, Cursor, Hint, After the save, `draw_game_over_choices`, `SLOT_LINE_WIDTH`, the grey choices)
- Rules: Values (the screen texts and the game-over messages)
- Rationale: "New fields and parameters have defaults"
- `docs/contracts/systems/saves.md`, Interface (`GameOverMessage`, `NamePicker`, `NICKNAME_CHARACTERS`, `BLANK`; built in DRA-126-01)

## Builds
- `game/ui/game_over.py` (changed)

## Depends on
DRA-126-01

## Not in the contract
None.

## Acceptance check
A headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report fills a 640 × 480 surface with a mid gray and draws, saving each as a PNG outside the repo:
- the DRA-125 calls (`draw_game_over(surface)`, `draw_final_score(surface, 1234)`, `draw_game_over_choices(surface, selection)`): pixel for pixel the same as before the change;
- each `GameOverMessage` without the picker;
- the picker screen with slots `ACE` and the rest blank, picking, the cursor on slot 0 and on the last slot;
- the same slots after the save (`picking` False), RETRY selected.

It prints the box's rectangle and each line's ink rows and columns: six lines stacked in the box, the ten cells centered, the outline only on the cursor's cell and only while picking, the hint only while picking, RETRY and MENU grey with no marker while picking and white with the marker after, and every other line on the same rows before and after the save. The Director can open the PNGs. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- Choosing which functions to call from the flow, and calling them from the frame (the Integration Engineer's). The leaderboard (DRA-126-05), the HUD (DRA-126-03).
- The real look (UI-04). Core, tests.
