Feature: DRA-125
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-125/impact.md
Status: done
Linear: DRA-134

## Read in the contract
- Interface: the `ui/game_over.py` block; the `ui/screen_look.py` block (built in DRA-125-04); the `core/game_flow.py` block (`GameOverChoice` only)
- Presentation: the `flow.screen` GAME_OVER, `flow.run.score` and `flow.game_over_selection` rows; the shared items (Text, Lines and blank lines, Selection marker, Box, Cache, Only draws); Game-over screen
- Rationale: "The views take plain values" (why `draw_game_over` and `draw_final_score` keep their signatures)

## Builds
- `game/ui/game_over.py` (changed)

## Depends on
DRA-125-02, DRA-125-04

## Not in the contract
None.

## Acceptance check
A headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report fills a 640 × 480 surface with a mid gray and calls `draw_game_over`, `draw_final_score(surface, 1234)` and `draw_game_over_choices` once per `GameOverChoice`, and once more with `draw_game_over` alone; it saves each as a PNG outside the repo. It prints the box's darker rectangle and the ink rows and columns of each line: the box centered, four lines centered across the width and stacked inside the box, the marker's ink only left of the selected choice, and with `draw_game_over` alone only the title's ink in the box. The Director can open the PNGs. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects, including the `test_game_over.py` tests from DRA-125-08; every other existing test passes unchanged.

## Out of scope
- The place messages, name entry and the letter picker (DRA-126). The real look (UI-04). The game-over sound (AA-03).
- Calling the new function from the frame (the Integration Engineer's), core, tests.
