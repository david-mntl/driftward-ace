Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-126-05 (Architect): the leaderboard page draws one row per saved entry in four aligned columns, and keeps the DRA-125 page when there are no entries. Task file: `docs/contracts/DRA-126/tasks/DRA-126-05-ui-developer.md`.
2. **Delivered:** `/workspace/game/ui/leaderboard.py` (changed). No other file touched.
3. **Checks:** run from `/workspace/game` unless noted. Scripts and PNGs are in the scratchpad `/tmp/claude-1000/-workspace/306b4d78-3a59-4da7-966c-22967ac5773e/scratchpad/` (outside the repo): `lb_check.py` (the draw run), `cmp.py` (old against new). Command: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYGAME_HIDE_SUPPORT_PROMPT=1 python3 <scratchpad>/lb_check.py`. Surface 640 x 480, black.
   - `python3 -c "import pygame; assert pygame.IS_CE"`: pygame-ce 2.5.8. `python3 -m py_compile game/ui/leaderboard.py`: clean.
   - `draw_leaderboard(surface)` against the unchanged HEAD module (`git show HEAD:game/ui/leaderboard.py`, run by `cmp.py`): pixel bytes identical at 640 x 480 and 800 x 600. `draw_leaderboard(surface)` and `draw_leaderboard(surface, ())` identical. PNG: `lb_empty.png`.
   - One entry (`ACE`, 1 234, LV 3), PNG `lb_one.png`: ink box of the row (244, 241, 153, 8); table columns lefts 243, 276, 324, 375, rights 252, 300, 351, 397; table (243..397) centered (offset 0).
   - Ten entries, PNG `lb_ten.png`: nicknames of 1 to 10 characters (`A`, `BO`, `CAT`, `DOGS`, `EAGLE`, `FALCON`, `A B C D`, `ABCDEFGH`, `HELLO WOR`, `ABCD EFGHI`; two have an inner blank), scores 999 999 999 down to 0, levels 8 down to 1. Row ink boxes, e.g. row 1 (204, 133, 238, 8), row 10 (198, 349, 242, 8).
   - Column edges, ten rows: place right edge 212 on every row; score right edge 395 on nine rows and 394 on row 5 (`4 321`, the glyph `1`'s own side bearing: the cell's right edge is 395 on every row, since cells are blitted flush to it); nickname left edge 236 or 237 (glyph side bearing; cell left 236 on every row, no leading blanks in this data); level left edge 420 (cell left 419, `L`'s side bearing). Column lefts 197, 236, 330, 419; rights 212, 306, 395, 442.
   - Gaps between columns (cell edge to cell edge): 24, 24, 24 (`COLUMN_GAP`). Table 197..442, width 245: left margin 197, right margin 198 (integer centering, `(width - table_width) // 2`).
   - Rows' tops: 132, 156, 180, ... 348, each `ROW_SPACING` (24) apart. Block top 96, last row's bottom 360, footer top 456: block centered in the space above the footer (96 above, 96 below).
   - Footer: ink rows 457..466 on the instructions page, the empty page, the one-entry page and the ten-entry page. Footer band (top two body lines above the bottom) pixel-identical on all four.
   - Same state drawn twice gives the same picture: True. The entries tuple unchanged after the draw.
   - `game/tests/check.sh lint`: pass (ruff check and format). `typecheck`: pass (mypy strict). `ui`: 89 passed, tests unchanged. `core`: 3287 passed, 1 failed: `test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first`, the one failure `impact.md` expects until DRA-126-07.
   - Grep of `game/ui/leaderboard.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for imports from ui: no hits.
4. **Assumptions:**
   - `ROW_SPACING` 24 and `PLACE_FORMAT` `"{}."` and `LEVEL_LABEL` `"LV"`: scope report DRA-126, Values needed, Leaderboard rows (16 px, 24 px apart; `1.`, `LV 3`). `COLUMN_GAP` 24: `docs/reports/DRA-126-away-log.md`, Decisions, 5. The scope report gives the format as an example (`1.`, `LV 3`), so the format string and the label are my reading of it.
   - A nickname with a leading blank draws that blank as a space inside its cell, so its ink starts further right than the column's left edge. The column width counts the space. No saved nickname is empty (`is_valid_nickname`).
   - More than ten entries are drawn as given; core keeps the list to `TOP_N`.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-126/tasks/DRA-126-05-ui-developer.md`. Left alone: passing `flow.leaderboard` to the page (Integration Engineer), the game-over screen (DRA-126-04), the HUD (DRA-126-03), tests (DRA-126-08).
7. **Status:** done.

## Decisions
- Layout in small functions: `draw_leaderboard` works out the block and the footer, `_draw_rows` builds the cells and widths, `_column_lefts` places the columns, `_blit_row` aligns a row's cells. The empty page keeps its exact old arithmetic: the block height uses `max(len(entries), 1)` rows, so one line (the empty-list line) gives the DRA-125 height and the page stays pixel for pixel the same.
- Right alignment is a tuple of column indexes (`_RIGHT_ALIGNED`: place and score), not a flag per call. The cell images are rendered with the file's existing `@cache _render`, so each cell text is rendered once and kept (contract, Cache).
- Column edges are integers: the table's left is `(width - table_width) // 2`, then each column starts one width plus `COLUMN_GAP` after the one before. Nothing is rounded early beyond that.
- `ScoreEntry` is imported from `core.saves` and `group_digits` from `ui.score_text`, as the contract's Interface says. The view reads the entries and never changes them.
