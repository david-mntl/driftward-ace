Feature: DRA-125
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-125/impact.md
Status: open
Linear: DRA-132

## Read in the contract
- Interface: the `ui/leaderboard.py` block; the `ui/screen_look.py` block (built in DRA-125-04)
- Presentation: the `flow.screen` MENU, INSTRUCTIONS, LEADERBOARD row; the shared items (Text, Lines and blank lines, Cache, Only draws); Leaderboard page; Instructions page (Footer, for the shared footer place)
- Rationale: "Layout from font metrics"

## Builds
- `game/ui/leaderboard.py` (new)

## Depends on
DRA-125-04

## Not in the contract
None.

## Acceptance check
A headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report fills a 640 × 480 surface with `ui.look.BACKGROUND`, calls `draw_leaderboard`, and saves the image as a PNG outside the repo. It prints the ink rows and columns of the title, the empty-list line and the footer: all centered across the width, the footer on exactly the rows `draw_instructions` puts its footer on. The Director can open the PNG. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- The top 10 rows, saves and every entry on the page (DRA-126). The real look (UI-04).
- Calling `draw_leaderboard` from the frame (the Integration Engineer's), core, tests.
