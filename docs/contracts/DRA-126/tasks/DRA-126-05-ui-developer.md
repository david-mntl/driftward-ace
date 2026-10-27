Feature: DRA-126
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-126/impact.md
Status: done
Linear: DRA-143

## Read in the contract
- Diagram: the screens (LEADERBOARD, filled)
- Interface: the `ui/leaderboard.py` block under "DRA-126: what saves add and change"; the `ui/screen_look.py` block
- Presentation: the `flow.leaderboard` row; the shared items (Text, Lines and blank lines, Cache, Only draws); Leaderboard page, all of it (Empty, Filled, Row cells, Columns, the footer)
- `docs/contracts/systems/saves.md`, Interface (`ScoreEntry`; built in DRA-126-01)
- `docs/contracts/systems/hud.md`, Presentation, `group_digits(number)` (built in DRA-126-03)

## Builds
- `game/ui/leaderboard.py` (changed)

## Depends on
DRA-126-01, DRA-126-03

## Not in the contract
None.

## Acceptance check
A headless script (`SDL_VIDEODRIVER=dummy`) in the implementation report draws the page on a 640 × 480 surface, saving each as a PNG outside the repo: `draw_leaderboard(surface)` (pixel for pixel the DRA-125 page), one entry, and ten entries with nicknames of 1 to 10 characters (one with an inner blank), scores from 0 to 999 999 999 and levels 1 to 8. It prints each row's ink box and each column's edges: the place and score columns' right edges the same on every row, the nickname and level columns' left edges the same on every row, the gaps between columns, the table centered across the width, the rows' tops `ROW_SPACING` apart, and the footer on the same rows as the instructions page's. The Director can open the PNGs. `game/tests/check.sh lint` passes. In `typecheck`, `core` and `ui`, the only failures are the ones `impact.md` expects; every other existing test passes unchanged.

## Out of scope
- Passing `flow.leaderboard` to the page (the Integration Engineer's). The game-over screen (DRA-126-04), the HUD (DRA-126-03).
- The real look (UI-04). Core, tests.
