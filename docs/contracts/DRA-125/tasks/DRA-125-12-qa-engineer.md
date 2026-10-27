Feature: DRA-125
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-125/impact.md
Status: done
Linear: DRA-138

## Read in the contract
- Interface: the `ui/screen_look.py`, `ui/menu.py`, `ui/instructions.py` and `ui/leaderboard.py` blocks
- Presentation: the shared items (Text, Lines and blank lines, Selection marker, Cache, Only draws); Menu; Instructions page; Leaderboard page

## Builds
- `game/tests/ui/test_menu.py` (new)
- `game/tests/ui/test_instructions.py` (new)
- `game/tests/ui/test_leaderboard.py` (new)
- `game/tests/CONTEXT.md` (changed: paragraphs for the new files)

## Depends on
DRA-125-04, DRA-125-05, DRA-125-06

## Not in the contract
- The stand-in texts, sizes and spacing are written at the top of each file from scope report DRA-125, Values needed: they are not in the GDD (UI-03 and UI-04 are TBD). Positions are read from the drawn pixels, never from a font size. Source: tests/CONTEXT.md, Rules.

## Test
- The menu: the title then the three items in menu order, each centered across the width, the items' tops the stand-in spacing apart, the block centered vertically; the marker's ink only left of the selected item, at its rows; the labels don't move with the selection. Presentation: Menu; shared items.
- The instructions page: the title, then six sections in the scope report's order, each a heading row with a square outline icon left of its title and its line under it, every row centered and inside the surface, no two rows overlapping; the footer near the bottom with one blank line under it. Presentation: Instructions page.
- The leaderboard page: the title, the empty-list line and the footer, centered; the footer on the same rows as the instructions page's. Presentation: Leaderboard page.
- Each view draws the same pixels twice in a row and changes nothing but the surface. Presentation: shared items (Cache, Only draws).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with the three files in the `ui` step and all their tests passing.

## Out of scope
- The pause box, the burst and the game-over screen (DRA-125-11). Core tests (DRA-125-09, DRA-125-10).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than those listed in Builds.
