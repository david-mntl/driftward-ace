Status: ready-for-review
Created by: ui-developer

1. **Task:** Draw the GRAZE line on HUD line 2 and add `graze_text`, from `docs/contracts/DRA-117/tasks/DRA-117-04-ui-developer.md` (Architect), against `docs/contracts/systems/hud.md`.
2. **Delivered:**
   - `game/ui/score_text.py`: `GRAZE_LABEL`, `graze_text(grazes)`, and one private `_grouped(number)` helper that `score_text` and `graze_text` both use.
   - `game/ui/hud.py`: `draw_hud` blits the GRAZE line at (`HUD_MARGIN`, `hud_top + HUD_LINE_SPACING`). New private `_graze_surface(grazes)`, cached like `_score_surface`. Signature unchanged.
3. **Checks:**
   - `python3 -c "import pygame; assert pygame.IS_CE"`: pygame-ce 2.5.8, passes. `py_compile` on both files: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format). `game/tests/check.sh typecheck`: PASS (mypy strict, 97 files).
   - `game/tests/check.sh ui`: 43 passed, 3 failed. The three are the `test_hud.py` failures `impact.md` lists for DRA-117-04, cleared by DRA-117-07: `test_hud_score_is_on_line_one_at_the_left_margin`, `test_hud_line_two_is_empty_and_the_meters_are_gone`, `test_hud_score_top_is_the_overlay_bottom_plus_the_gap`. `test_hud_score_pixels_follow_the_score` passes.
   - Acceptance script, from `game/`: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/9cc7f9c9-8cf7-4368-8c43-83f4849aacad/scratchpad/dra117-04/check.py`. The script is outside the repo. It builds `start_run()` with `grazes` set through `dataclasses.replace`, and draws on a black 640x480 surface. In debug mode it draws the overlay first (`draw_debug_overlay`, `draw_debug_wave_lines`), then the HUD. It measures ink in a band below SCORE's line, x < 400.
   - Text output (same digit groups after each label):
     ```
            0  'GRAZE 0'            'SCORE 0'
            5  'GRAZE 5'            'SCORE 5'
          999  'GRAZE 999'          'SCORE 999'
         1000  'GRAZE 1 000'        'SCORE 1 000'
         1234  'GRAZE 1 234'        'SCORE 1 234'
      1234567  'GRAZE 1 234 567'    'SCORE 1 234 567'
     ```
   - GRAZE ink bounding box (left, top, right, bottom), SCORE's in the same run:

     | mode | grazes | hud_top | SCORE ink | GRAZE ink | top gap | bottom, rows above 168 |
     |---|---|---|---|---|---|---|
     | normal | 0 | 4 | (4, 5, 54, 12) | (5, 25, 53, 32) | 20 | 32, 136 |
     | normal | 5 | 4 | (4, 5, 66, 12) | (5, 25, 53, 32) | 20 | 32, 136 |
     | normal | 1234 | 4 | (4, 5, 82, 12) | (5, 25, 74, 32) | 20 | 32, 136 |
     | debug | 0 | 80 | (4, 81, 54, 88) | (5, 101, 53, 108) | 20 | 108, 60 |
     | debug | 5 | 80 | (4, 81, 66, 88) | (5, 101, 53, 108) | 20 | 108, 60 |
     | debug | 1234 | 80 | (4, 81, 82, 88) | (5, 101, 74, 108) | 20 | 108, 60 |

     The GRAZE top is exactly `HUD_LINE_SPACING` (20) below SCORE's in every case. In debug mode, `hud_top` is 80, which is `overlay_text_bottom()` plus the gap, so the lines sit below the overlay's text. The ink gets wider with the count (1234 reaches x 74, 0 and 5 reach 53). The `Run` repr is identical before and after each draw, so core is unchanged.
   - PNGs, in `/tmp/claude-1000/-workspace/9cc7f9c9-8cf7-4368-8c43-83f4849aacad/scratchpad/dra117-04/`: `hud_normal_grazes0.png`, `hud_normal_grazes5.png`, `hud_normal_grazes1234.png`, `hud_debug_grazes0.png`, `hud_debug_grazes5.png`, `hud_debug_grazes1234.png`.
   - Grep of `game/ui/hud.py` and `game/ui/score_text.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for imports from `ui`: no hits.
4. **Assumptions:** The ink's left edge is column 5, not 4, because the default font's "G" has a one-pixel left side bearing. SCORE's "S" starts at column 4. Both text surfaces are blitted at x = `HUD_MARGIN` (4). I read "its left at the margin" as the blit origin.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-117/tasks/DRA-117-04-ui-developer.md`. DRA-117-07 (QA Engineer) rewrites the three `test_hud.py` tests that now fail. I left `game/ui/game_over.py`, `popup_view.py` and `graze_view.py` alone.
7. **Status:** done.

## Decisions
- One private `_grouped` helper holds the digit grouping. `score_text` and `graze_text` add their own label. Source: hud.md, Rationale "One grouping for SCORE and GRAZE". Its body is the old `score_text` grouping moved unchanged, so SCORE's output is unchanged.
- `_graze_surface` is a second `lru_cache(maxsize=1)` function, next to `_score_surface`. It reuses `_hud_font()`, the font, size, antialiasing and `HUD_COLOR` of SCORE. Source: hud.md, GRAZE line. Two small cached functions read better than a generic cache wrapper.
- GRAZE is blitted right after SCORE and before the hearts. They don't overlap, so the order doesn't matter.
- No new constants. Positions use `HUD_MARGIN`, `HUD_LINE_SPACING` and `hud_top` from the existing code. `GRAZE_LABEL` is the only new constant, from hud.md Interface (DRA-117).
