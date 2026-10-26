Feature: DRA-125
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/game-flow.md, docs/contracts/systems/run.md
Impact: docs/contracts/DRA-125/impact.md
Status: open
Linear: DRA-137

## Read in the contract
- game-flow.md: Interface, the `ui/screen_look.py`, `ui/pause_box.py` and `ui/game_over.py` blocks
- game-flow.md: Presentation, the shared items (Text, Lines and blank lines, Selection marker, Box, Cache, Only draws), Pause box, Game-over screen
- run.md: Interface, the `ui/burst_view.py` block; Presentation, Burst; Rules, Burst

## Builds
- `game/tests/ui/test_burst_view.py` (new)
- `game/tests/ui/test_pause_box.py` (new)
- `game/tests/ui/test_game_over.py` (changed: the box, the title, no prompt, RETRY and MENU)
- `game/tests/CONTEXT.md` (changed: paragraphs for the new files and the `test_game_over.py` paragraph)

## Depends on
DRA-125-01, DRA-125-03, DRA-125-04, DRA-125-07, DRA-125-08

## Not in the contract
- The stand-in look's numbers and texts (box sizes, font sizes, the marker, the texts, the burst's size and count) are written at the top of each file from scope report DRA-125, Values needed: they are not in the GDD (UI-04 and LD-08 are TBD). Positions are read from the drawn pixels, never from a font size. Source: tests/CONTEXT.md, Rules.

## Test
- The burst: one square of the burst's size per center, at the place core gives, at alpha `round(255 × opacity)`; nothing at opacity 0; squares off the surface are clipped; the view changes nothing it is given. Presentation: Burst.
- The pause box: a box of its size centered on the surface, darker than outside it and see-through, with the PAUSE text centered on the box's center; on a black surface the only ink is the text. Presentation: Pause box; shared items (Box, Text).
- The game-over screen: the box of its size centered; with all three calls, four lines inside it, each centered across the width and stacked top to bottom (title, score, RETRY, MENU), the block centered in the box; the score line is `score_text(score)` at the body size; the marker's ink is left of the selected choice only, at its rows, and the labels don't move with the selection; each function alone draws only its own lines in their places. Presentation: Game-over screen; shared items (Selection marker).
- Only the score line's pixels change with the score, and the same score twice draws the same pixels. Presentation: Game-over screen; shared items (Cache).

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` once `impact.md`'s expected failures from other tasks are cleared, with the three files in the `ui` step, all their tests passing, and none of `impact.md`'s DRA-125-08 failures left.

## Out of scope
- The menu and the pages (DRA-125-12). Core tests (DRA-125-09, DRA-125-10).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than those listed in Builds.
