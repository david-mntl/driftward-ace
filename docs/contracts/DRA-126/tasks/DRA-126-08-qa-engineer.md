Feature: DRA-126
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/hud.md, docs/contracts/systems/game-flow.md
Impact: docs/contracts/DRA-126/impact.md
Status: open
Linear: DRA-146

## Read in the contract
- hud.md: Interface, "DRA-126 adds and changes"
- hud.md: Presentation: the `flow.best` row; `group_digits(number)` and `best_text(best)`; BEST line
- game-flow.md: Interface, the `ui/game_over.py` and `ui/leaderboard.py` blocks under "DRA-126: what saves add and change"
- game-flow.md: Presentation: the shared items (Text, Lines and blank lines, Selection marker, Box, Cache, Only draws); Leaderboard page; Game-over screen

## Builds
- `game/tests/ui/test_score_text.py` (changed)
- `game/tests/ui/test_hud.py` (changed)
- `game/tests/ui/test_game_over.py` (changed)
- `game/tests/ui/test_leaderboard.py` (changed)
- `game/tests/CONTEXT.md` (changed: the files' paragraphs)

## Depends on
DRA-126-03, DRA-126-04, DRA-126-05

## Not in the contract
- The stand-in texts, sizes, colors and spacing are written at the top of each file from scope report DRA-126, Values needed, and docs/reports/DRA-126-away-log.md, Decisions, 4 and 5: they are not in the GDD (UI-01, UI-03 and UI-04 are TBD). Positions are read from the drawn pixels, never from a font size. Source: tests/CONTEXT.md, Rules.

## Test
- `group_digits` groups in threes from the right with no label; `best_text` is the label, a space and the grouped digits; `score_text` and `graze_text` still group the same way. hud.md Presentation: `group_digits(number)` and `best_text(best)`.
- BEST draws on line 1 at its fixed x in both modes, on SCORE's rows, and nothing when `best` is None; the HUD called without `best` draws what it drew before. hud.md Presentation: BEST line.
- The BEST text is rendered again only when `best` changes. hud.md Presentation: BEST line.
- Without the picker the game-over screen draws each message in the title's place, and the DRA-125 calls draw the DRA-125 screen. game-flow.md Presentation: Game-over screen (Two layouts, `draw_game_over`).
- With the picker: the larger box, six lines stacked in it, ten equal cells centered, each with an underline, characters centered in their cells, a blank drawing nothing. game-flow.md Presentation: Game-over screen (Cells, Characters, Underline).
- While picking, the outline on the cursor's cell only and the hint shown, RETRY and MENU grey with no marker; after the save, no outline and no hint, the slots and every other line on the same rows, RETRY and MENU white with the marker on the selection. game-flow.md Presentation: Game-over screen (Cursor, Hint, After the save, `draw_game_over_choices`).
- The leaderboard with entries: one row per entry in order, places from 1, four columns with the place and score right-aligned and the nickname and level left-aligned, the table centered, rows the stand-in spacing apart, the footer in its DRA-125 place; with none, the DRA-125 page. game-flow.md Presentation: Leaderboard page.
- Each view draws the same pixels twice in a row and changes nothing but the surface. game-flow.md Presentation: Cache, Only draws.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, with the DRA-126 tests in the four files in the `ui` step and all their tests passing.

## Out of scope
- Core tests (DRA-126-06, DRA-126-07). The app's draw calls (the Integration Engineer's browser checks).
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code, tuning files, or test files other than those listed in Builds.
