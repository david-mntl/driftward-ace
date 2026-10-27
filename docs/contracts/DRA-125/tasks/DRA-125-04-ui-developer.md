Feature: DRA-125
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-125/impact.md
Status: done
Linear: DRA-130

## Read in the contract
- Interface: the `ui/screen_look.py` and `ui/menu.py` blocks; the `core/game_flow.py` block (`MenuItem` only)
- Presentation: the `flow.screen` MENU and `flow.menu_selection` rows; the shared items (Text, Lines and blank lines, Selection marker, Cache, Only draws); Menu
- Rationale: "The views take plain values", "Shared look in `ui/screen_look.py`", "Layout from font metrics"

## Builds
- `game/ui/screen_look.py` (new)
- `game/ui/menu.py` (new)

## Depends on
DRA-125-02

## Not in the contract
None.

## Acceptance check
A headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report fills a 640 × 480 surface with `ui.look.BACKGROUND`, calls `draw_menu` once per `MenuItem`, and saves the three images as PNGs outside the repo. It prints, for each, the ink rows and columns of every text line: the title and three items centered across the width, the block centered vertically, item tops the contract's spacing apart, and the marker's ink only left of the selected item, at the same rows as it. The Director can open the PNGs. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- The pages, the pause box and the game-over screen (DRA-125-05 to DRA-125-08).
- The real text, look, fonts and icons (UI-03, UI-04). Calling `draw_menu` from the frame (the Integration Engineer's), core, tests.
