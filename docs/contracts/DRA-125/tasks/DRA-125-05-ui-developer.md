Feature: DRA-125
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-125/impact.md
Status: open
Linear: DRA-131

## Read in the contract
- Interface: the `ui/instructions.py` block; the `ui/screen_look.py` block (built in DRA-125-04)
- Presentation: the `flow.screen` MENU, INSTRUCTIONS, LEADERBOARD row; the shared items (Text, Lines and blank lines, Cache, Only draws); Instructions page
- Rationale: "Layout from font metrics", "One outline square for every icon"

## Builds
- `game/ui/instructions.py` (new)

## Depends on
DRA-125-04

## Not in the contract
None.

## Acceptance check
A headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report fills a 640 × 480 surface with `ui.look.BACKGROUND`, calls `draw_instructions`, and saves the image as a PNG outside the repo. It prints the ink rows and columns of every row: the title, six heading rows each with a square outline icon left of its title, six lines in the scope report's order and wording, and the footer near the bottom; every row centered across the width and inside the canvas, nothing overlapping. The Director can open the PNG. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- The real text, icons and look (UI-03). Calling `draw_instructions` from the frame (the Integration Engineer's), core, tests.
