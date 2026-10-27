Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the stand-in leaderboard page view, `draw_leaderboard`, from `docs/contracts/DRA-125/tasks/DRA-125-06-ui-developer.md` (Architect), against `docs/contracts/systems/game-flow.md`.

2. **Delivered:** `game/ui/leaderboard.py` (new): `LEADERBOARD_TITLE_TEXT`, `LEADERBOARD_EMPTY_TEXT`, `draw_leaderboard(surface)`. Imports pygame and `ui.screen_look` only.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/ui/leaderboard.py`: clean.
   - `ruff check game`: all checks passed. `ruff format --check game`: 111 files already formatted.
   - Headless draw run, 640 x 480 surface filled with `ui.look.BACKGROUND`, then `draw_leaderboard`. Command (from `/workspace/game`): `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy PYTHONPATH=. python /tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/check_lb.py`. PNG: `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/leaderboard.png`. Ink rows and columns (title linesize 24, body linesize 12, footer top 456):
     ```
     title            rows 206-222  cols 235-407  center 321.0
     "No scores yet."  rows 241-250  cols 280-360  center 320.0
     footer           rows 457-466  cols 227-414  center 320.5
     ```
     All three are centered on 320 (within 1 px, font side bearings). The same script draws `draw_instructions` on a fresh surface: its footer ink is rows 457-466, cols 227-414, identical to the leaderboard footer (rows and columns both). The block (title top 206 to the line's bottom) sits in the space above the footer's top 456.
   - Follows the state: the view takes no state. Two fresh draws give identical bytes (True). Text is rendered once: after three texts, the render cache shows 3 misses and 3 hits on the second draw. On an 800 x 600 surface the ink spans cols 307-494 (centered on 400). It touches no core object. (Drawing twice over the same surface is not a repeat: antialiased edges blend twice.)
   - `game/tests/check.sh lint`: PASS (lint and format).
   - `typecheck`: 7 errors, all `retry_armed` in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`: the first row of the impact.md table (DRA-125-01, cleared by DRA-125-09). None in `game/ui/leaderboard.py`.
   - `core`: 26 failed, 3205 passed. Failures by file: `test_coin.py` 2, `test_run.py` 6, `test_run_drifters.py` 4, `test_run_graze.py` 3, `test_run_score.py` 5, `test_run_waves.py` 6: the files and kinds impact.md names for DRA-125-01. Same count as the DRA-125-05 report.
   - `ui`: PASS, unchanged.
   - Grep of `game/ui/leaderboard.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for `game.ui`, `from ui`, `import ui`: no hits.

4. **Assumptions:**
   - The blank line between the title and the empty-list line is one body line high (Presentation, Lines and blank lines), as on the instructions page.
   - The block's height is the title line + one blank body line + one body line (the empty-list line's `get_linesize()`), centered with integer division in `[0, footer_top]`.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, on `docs/contracts/DRA-125/tasks/DRA-125-06-ui-developer.md`. Left alone: `ui/instructions.py` and `ui/menu.py` each keep a private `_render` and `_blit_centered`, and this module has the same two. A shared helper would belong in `screen_look.py` (DRA-125-04's file). The top 10 rows are DRA-126; `draw_leaderboard` is not called from the frame (Integration Engineer).

7. **Status:** done.

## Decisions
- Same layout method as `ui/instructions.py`: placement from `get_linesize()`, no invented spacing. The footer top is `height - 2 * body_line`, the same expression as the instructions page, so both footers land on the same rows (shown in Checks).
- The footer's place is computed in this module, not imported from `ui/instructions.py`, because the contract limits the imports to pygame and `ui.screen_look`.
- Texts rendered once through a private `functools.cache` function, as in the sibling views. Fonts come from `screen_font`.
- Sources: title and empty-line texts from scope report DRA-125, Values needed (Leaderboard page); sizes, color and footer from `ui.screen_look`.
