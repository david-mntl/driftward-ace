Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-126-04 (Architect): the game-over screen takes a message, an optional name picker, and grey choices before the save. Task file: `docs/contracts/DRA-126/tasks/DRA-126-04-ui-developer.md`.
2. **Delivered:** `/workspace/game/ui/game_over.py` (changed). No other file touched.
3. **Checks:** run from `/workspace/game`; scripts and PNGs are in the scratchpad `/tmp/claude-1000/-workspace/306b4d78-3a59-4da7-966c-22967ac5773e/scratchpad/dra126-04/` (outside the repo).
   - `python3 -c "import pygame; assert pygame.IS_CE"`: pygame-ce 2.5.8. `python3 -m py_compile game/ui/game_over.py`: clean.
   - Baseline taken from the unchanged code first: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python3 .../baseline.py .../before`. After the change: `... PYTHONPATH=. python3 .../check.py .../dra126-04` (and `extra.py`). Surface 640 x 480, filled (128, 128, 128).
   - DRA-125 calls (`draw_game_over(s)`, `draw_final_score(s, 1234)`, `draw_game_over_choices(s, sel)`), RETRY and MENU selected: pixel bytes identical to the before PNGs, `True` and `True`.
   - Box: no picker rect (160, 160, 320, 160); picker rect (120, 100, 400, 280); corners inside tinted, pixels just outside untouched.
   - Picker screen, picking, cursor 0 (box 120..519 x 100..379). Ink rows and columns: message cols 219..420 rows 197..213; score cols 285..355 rows 220..227 (center 320.5); slot row rows 232..248; hint rows 249..259 cols 193..448; RETRY rows 262..269; MENU rows 274..281. Layout tops 195, 219, 231, 249, 261, 273: six lines stacked in order. Block margins in the box: 97 above, 98 below.
   - Ten cells: underline runs 10, each 15 px wide (the widest character at 24 px), 4 px gap; left margin 227, right margin 227 (centered).
   - Outline: only on the cursor's cell while picking. Cursor 0: cols 227..241 rows 231..248, white. Cursor on slot 9: cols 398..412 rows 231..248. Saved (`picking` False): cell 0's corner pixel is the box color (83, 83, 83), white while picking. Hint ink exists only while picking: the band is unchanged from the empty box after the save.
   - RETRY and MENU: `active=False` max channel 128, ink starts at col 302, no marker. `active=True` max channel 255, marker ink to the left (col 292 against 302 for the label).
   - Same rows before and after the save: score 220..227, slot row 232..248 (characters and underlines, outside the cursor cell), RETRY 262..269, MENU 274..281, message 197..213. All `same: True`.
   - PNGs in `.../after/`: `dra125_RETRY.png`, `dra125_MENU.png`, `message_NEW_BEST_SCORE.png`, `message_TOP_3.png`, `message_TOP_10.png`, `message_GAME_OVER.png`, `picker_picking_cursor0.png`, `picker_picking_cursor_last.png`, `picker_saved_retry.png`.
   - `game/tests/check.sh lint`: pass (ruff check and format). `typecheck`: pass (mypy strict, 116 files). `ui`: 89 passed, unchanged tests. `core`: 3287 passed, 1 failed: `test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first`, the failure `impact.md` expects until DRA-126-07.
   - Grep of `game/ui/game_over.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for imports from ui: no hits. `NamePicker` passed to `draw_name_picker` is unchanged after the draw.
4. **Assumptions:**
   - The slot count is `len(picker.slots)` (equal to `NICKNAME_LENGTH`), because the contract's import list for this module does not include `NICKNAME_LENGTH`.
   - `draw_name_picker` always works out the picker layout. The contract says it draws "with the picker only", so a call with `picker_shown` False for the other functions would leave it out of place; the app calls them together.
   - The picker font's `get_linesize()` is the slot row height, as the contract says. At 24 px the row is 18 px, so the 16 px score line above sits close. This follows the metrics rule; no spacing was added.
   - `BOX_SIZE` kept its existing non-`Final` annotation, as in the code today.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-126/tasks/DRA-126-04-ui-developer.md`. Left alone: `game/ui/leaderboard.py` (DRA-126-05), `game/app/frame.py` (still calls the DRA-125 signatures, which stay valid; Integration wires the new calls), and the failing core logging test (DRA-126-07).
7. **Status:** done.

## Decisions
- One `_layout(size, picker_shown)` places all six lines by stacking line heights. Without the picker the slot row and the hint have height 0, so the DRA-125 tops come out as they did and the output is pixel for pixel the same (checked). The stack uses `itertools.accumulate`, with no per-layout branches.
- `draw_name_picker` order: characters, then all underlines, then the cursor outline, then the hint. Source: contract, Presentation (Cursor "drawn after the underlines").
- A blank slot draws nothing (never `_`). Source: contract, Characters.
- Underline: `surface.fill` of the cell's bottom `SLOT_LINE_WIDTH` rows. Outline: `pygame.draw.rect(..., width=SLOT_LINE_WIDTH)` on the cell's own rect.
- Caches, all built on the first draw: `_box(size)` per size, `_message(message)` per message, `_label(text, color)` per text and color (RETRY, MENU, the hint, the marker), `_picker_character(c)` per character, `_cell_width()`. `_score_line` keeps its one-score cache. No render per frame. Source: contract, Cache.
- Values: `PICKER_BOX_SIZE` 400 x 280, `PICKER_FONT_SIZE` 24, `PICKER_HINT_TEXT`, `INACTIVE_TEXT_COLOR` and `SLOT_UNDERLINE_COLOR` (128, 128, 128), `CURSOR_COLOR` white: scope report DRA-126, Values needed. `SLOT_LINE_WIDTH` 1: `docs/reports/DRA-126-away-log.md`, Decisions, 4. `MESSAGE_TEXTS`: 10-ui.md, game_over_message (locked). `TITLE_TEXT` removed as the contract says; nothing else imported it.
- `MESSAGE_TEXTS` is a `MappingProxyType` so the constant can't be changed.
- Every function reads its arguments only; no core state is changed, no input, display or asset load.
