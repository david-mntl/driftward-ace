Status: ready-for-review
Created by: ui-developer

1. **Task:** Show the lives as white hearts at the top right of the HUD and make `draw_hud` read the run, from task `docs/contracts/DRA-23/tasks/DRA-23-02-ui-developer.md` (Architect). The Director confirmed on 2026-10-13: a lost life removes the leftmost heart and the others don't move; hearts are 24 x 24 px, 8 px apart, 8 px from the top and right edges. This matches the contract.
2. **Delivered:** `/workspace/game/ui/hud.py` (changed). New constants `HEART_COLOR`, `HEART_SIZE`, `HEART_GAP`, `HEART_MARGIN`; `draw_hud(surface, run: Run, below_overlay) -> None`; private `_draw_hearts` and `_heart`. The `core.scroll` import is gone; `core.run` is imported instead. The readout text, place, font and color are unchanged.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/ui/hud.py`: clean.
   - `game/tests/check.sh lint`: PASS lint, PASS format, `QA: pass`.
   - Acceptance script, run from `game/` (kept in the scratchpad, not the repo): `cd /workspace/game && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -I -c "import sys; sys.path.insert(0,'.'); exec(open('/tmp/claude-1000/-workspace/8060ad56-4f1c-40d0-ad14-d4fb39ed0880/scratchpad/accept.py').read())"`. Printed:
     ```
     hud_normal [True, True, True] bbox x 608 631 y 8 31
     hud_debug [False, False, True] bbox x 608 631 y 8 31
     ```
     The bbox is of the white pixels in x 600 to 639, rows 0 to 39: inside x 608 to 631, rows 8 to 31, spanning x 608 to 631. The debug run also asserts `repr(run)` is the same before and after the draw (the run is untouched).
   - Images: `/tmp/claude-1000/-workspace/8060ad56-4f1c-40d0-ad14-d4fb39ed0880/scratchpad/hud_normal.png` (white `0 m` top left, three hearts top right) and `/tmp/claude-1000/-workspace/8060ad56-4f1c-40d0-ad14-d4fb39ed0880/scratchpad/hud_debug.png` (green overlay, white `11 m` below it, one heart top right). I looked at the debug image: the heart reads as a heart.
   - Grep of `game/ui/hud.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `image.load`, `mixer`, `random.random(`, `.mp3`, `.wav`, `print(`: no hits. Grep of `game/core` for `import ui` / `from ui`: no hits. `hud.py` imports pygame, `core.run`, `ui.debug_overlay` (and stdlib). Never `app`.
   - Expected test result, `SDL_VIDEODRIVER=dummy python -m pytest tests/ui -q` from `game/`: 5 failed, 3 passed. The five failures are all in `tests/ui/test_hud.py`, each `AttributeError: 'Scroll' object has no attribute 'scroll'`, because the tests pass a scroll: `test_hud_normal_layout_leaves_line_one_empty`, `test_hud_never_overlaps_the_debug_overlay`, `test_hud_keeps_the_gap_below_the_overlay`, `test_hud_does_not_jump_when_the_overlay_is_hidden`, `test_hud_stays_above_the_top_line`. The 3 passes are `tests/ui/test_error_screen.py` (3 passed when run alone). Tests not edited. Task DRA-23-05 updates them.
4. **Assumptions:** The heart geometry is mine, since the contract fixes only the look and extent. Two circles of radius 6 (`HEART_SIZE // 4`) centered at (6, 6) and (17, 6), plus a polygon (0, 7), (23, 7), (12, 23), (11, 23). The lobes reach column 0 and column 23, and the point reaches row 23. The proportions are derived from `HEART_SIZE`, so there are no extra magic numbers.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-23/tasks/DRA-23-02-ui-developer.md`. Then the Integration Engineer wires `game/app/frame.py` to pass `run`, and QA (DRA-23-05) updates `tests/ui/test_hud.py`. Left alone: `game/app/`, `game/tests/`, `game/core/`, and every other file in `game/ui/`. Until the app passes `run`, the running game breaks on `draw_hud`.
7. **Status:** done.

## Decisions
- Hearts are built once by `_heart()` with `functools.cache`, the same pattern the file already uses for its font. No module-level state, no flag. Each frame blits the one surface once per life. Source: hud.md, Presentation; 15-tech-constraints.md, rule 5.
- `_draw_hearts` is a separate small function, so `draw_hud` stays short. Slot 0 is the rightmost and the loop runs `range(lives)`, so a lost life empties the leftmost heart and no heart moves. The width comes from `surface.get_width()` on each draw.
- `below_overlay` only affects the readout. The hearts ignore it, as the contract says.
- Constants and their docstrings are copied from the task and contract (scope report DRA-23, temporary stand-in, not in the GDD, UI-01 and UI-02 TBD). No other source is used.
- The module docstring now names the hearts. I changed "changes the scroll" to "changes the run" in it to match the new argument.

## Fix 2026-10-13: docs/reports/qa/DRA-23-02-ui-developer.md

1. **Task:** Fix B1: the heart is lopsided by one pixel, the right lobe one column too far left (QA Engineer).
2. **Delivered:** `/workspace/game/ui/hud.py` (changed, `_heart` only): the right lobe is now centered at `HEART_SIZE - radius` (18) instead of `last - radius` (17). Docstring says why.
3. **Checks:**
   - Reproduced first with the bug report's command (mirror test over 24 x 24): 22 mismatched pixels.
   - After the fix, same test (scratchpad `sym.py`, run with `python -I` from `game/`): `0 []`.
   - Acceptance script again: `hud_normal [True, True, True] bbox x 608 631 y 8 31`, `hud_debug [False, False, True] bbox x 608 631 y 8 31`. Unchanged. Run repr unchanged by the draw.
   - IS_CE passes; `py_compile` clean; `ruff check game` clean; `ruff format --check game` clean (26 files).
   - Grep of `game/ui/hud.py` for the banned names: no hits. Grep of `game/core` for `import ui` / `from ui` / `game.ui`: no hits.
   - `pytest tests/ui -q`: 5 failed, 3 passed, the same expected `test_hud.py` failures as before (DRA-23-05). Tests not edited.
4. **Assumptions:** None new. I took QA's proposed fix because it matches pygame-ce's circle coverage, `center - radius` to `center + radius - 1`.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, re-test bug report `docs/reports/qa/DRA-23-02-ui-developer.md`. Left alone: `game/app/frame.py:143` (Integration Engineer) and `game/tests/`.
7. **Status:** done.

### Decisions
- Only the right lobe moves. The polygon is unchanged, since QA showed it already mirrors about x 11.5.
- `last` is still used by the polygon, so no dead variable.
