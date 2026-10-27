Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-126-04-ui-developer (game-over message, name picker, grey choices before the save), started by /implement (Verify mode).
2. **Delivered:** docs/reports/qa/DRA-126-04-ui-developer.md. No test files (Verify saves none). Inline scripts, not in the repo: `/tmp/claude-1000/-workspace/306b4d78-3a59-4da7-966c-22967ac5773e/scratchpad/qa126_04.py`, `qa126_04b.py`, `qa126_04c.py` (run with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=/workspace/game python3 <script>`).
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and ui (89) pass. `core` has 1 failure of 3288: `test_game_flow.py::test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first`, the one failure `docs/contracts/DRA-126/impact.md` expects until DRA-126-07. It is not in the task's files. Nothing else fails.
   - The DRA-125 calls (`draw_game_over(s)`, `draw_final_score(s, 1234)`, `draw_game_over_choices(s, sel)`) are covered by the 7 unchanged `ui/test_game_over.py` tests, which pass. Boxes: no picker (160, 160) to (479, 319), 320 x 160; picker (120, 100) to (519, 379), 400 x 280, both centered on 640 x 480. Picker layout also computed on 800 x 600 (box at 200, 160) and 400 x 300 (box at 0, 10) with no error.
   - Layout with the picker: tops 195 (message), 219 (score), 231 (slots), 249 (hint), 261 (RETRY), 273 (MENU). Six lines in order, inside the box.
   - Cells: ten, 15 px wide, 19 px pitch, centered (cell 0 at x 227, cell 9 at x 398). Every character of `NICKNAME_CHARACTERS` (all non-blank, put in slot 0 and in slot 9): its ink stays inside its cell columns, above the underline row, below the row's top. No problem found for `W`, `@`, `M` or any other. The slot row's ink never reaches the score line's rows (score ink 220..227, slot row from 231).
   - Cursor: for cursor 0 to 9, the pixels that differ between `picking` True and False above the hint are exactly the cell's 15 x 18 outline (62 px), none elsewhere. The hint (1031 px, rows from 249) exists only while picking. After the save (`picking` False), nothing is drawn outside the slot row (rows 231 to 248).
   - Blank slots: an all-blank picker draws only the underlines (row 248, nothing else). A picked `_` shows as ink on rows 246..248 of its cell, above and on the underline row, so it reads as a character, not a blank.
   - RETRY and MENU: `active=True` max channel 255, marker present (label's left edge 295 for MENU and 292 with the marker left of RETRY); `active=False` max channel 128, first ink column 302 for both, no marker, for each selection.
   - Same picture twice: identical bytes. The `NamePicker` passed in is unchanged after drawing.
   - Cache: with `screen_font` wrapped to count `render` calls, 20 full draws (10 cursors x picking and saved) after a warm-up render 0 texts; a new score renders 1.
   - Message widths (NEW BEST SCORE 204 px, GAME OVER 135 px, TOP 10 77 px, TOP 3 65 px) and the hint (257 px) fit the 400 px box.
4. **Assumptions:** none beyond the implementer's `len(picker.slots)` for the slot count, which the review accepted.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer can pick this task up once DRA-126-05 is also through. The `core` failure above stays until DRA-126-07.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1, the one `impact.md` expects until DRA-126-07) · ui PASS (89)
QA: fail (core)
