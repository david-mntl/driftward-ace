Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-125-11 (burst view, pause box, game-over screen tests), started by the Director's session. A previous run was cut off and left `game/tests/ui/test_burst_view.py` as a draft.
2. **Delivered:**
   - `game/tests/ui/test_burst_view.py` (new, 5 tests; the draft finished: one assertion counted squares at ages where some leave the 200 x 160 surface, so it now counts only up to age 75, the last age with every square on it)
   - `game/tests/ui/test_pause_box.py` (new, 3 tests)
   - `game/tests/ui/test_game_over.py` (rewritten, 7 tests: the box, the title, no prompt, RETRY and MENU)
   - `game/tests/CONTEXT.md` (the `test_game_over.py` paragraph rewritten, paragraphs added for `test_pause_box.py` and `test_burst_view.py`)
3. **Checks:** `game/tests/check.sh` ends `QA: pass`, with the three files in the `ui` step (77 tests passed) and none of `impact.md`'s DRA-125-08 failures left. Mutation checks on a copy of `game/` (never the real files): a wrong box size or alpha, a box or text off center, a marker on the wrong side or three spaces away, a line a pixel or two off its place, a label moved with the selection, a wrong score text, a burst at full alpha, and a burst square not at its rounded top-left each failed the tests. Not caught by pixels: the score line's cache holding more than one score, since the picture is the same.
4. **Assumptions:**
   - Every stand-in number is written at the top of each file from scope report DRA-125, Values needed (box 320 x 120 pause and 320 x 160 game over, alpha 90, title 32 px, body 16 px, texts, burst 12 squares, 1 px a tick, 3 px side). The task's "Not in the contract" section says the same.
   - Positions are read from ink pixels. The one use of font metrics is the exact vertical stack in `test_game_over_lines_are_stacked_with_no_gap_and_the_block_is_centered`: `get_linesize()` and `get_height()` of the two fonts, which the contract's Layout defines, plus each text's own ink offset read from a reference render. A font size is only used to render the reference text.
   - "At its rows" for the marker allows 2 px above or below the label's ink, because the `>` glyph hangs one row below the capitals. The gap to the label is held to one space plus 4 px of glyph side bearing.
   - The burst test adds no cache test: the cache is not visible through the pixels, and the task names none.
5. **Documentation differences:** None.
6. **Next:** The Integration Engineer, once DRA-125-12 and the other QA tasks are done. No bug is open.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
