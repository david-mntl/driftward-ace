Status: ready-for-review
Created by: ui-developer

1. **Task:** Build `game/ui/screen_look.py` and `game/ui/menu.py` from `docs/contracts/systems/game-flow.md` (task `docs/contracts/DRA-125/tasks/DRA-125-04-ui-developer.md`, asked by the Architect).

2. **Delivered:**
   - `game/ui/screen_look.py` (new): `SCREEN_TEXT_COLOR`, `SCREEN_TITLE_FONT_SIZE`, `SCREEN_BODY_FONT_SIZE`, `SELECTION_MARKER`, `SCREEN_BOX_COLOR`, `BACK_PROMPT_TEXT`, `screen_font(size)`.
   - `game/ui/menu.py` (new): `MENU_TITLE_TEXT`, `MENU_ITEM_FONT_SIZE`, `MENU_ITEM_SPACING`, `MENU_ITEM_TEXTS`, `draw_menu(surface, selection)`.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/ui/screen_look.py game/ui/menu.py`: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format, 109 files).
   - `game/tests/check.sh typecheck`: only the 7 errors `impact.md` expects (DRA-125-01 row 1, `retry_armed` in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`). No error names a file I wrote.
   - `game/tests/check.sh core`: 26 failed, 3205 passed. All 26 are in `test_run.py`, `test_run_score.py`, `test_run_waves.py`, `test_run_drifters.py`, `test_run_graze.py` and `test_coin.py`: the DRA-125-01 files `impact.md` expects (its general rule covers tests that lose the last life and read `game_over`). I wrote no core code and did not look at the other core test failures beyond their files. A few names are not listed one by one in the impact table, for example `test_a_held_arrow_never_retries`, `test_a_new_run_starts_like_the_first`, `test_a_fall_and_a_touch_on_one_tick_cost_only_the_fall`, `test_no_playing_tick_changes_the_coin_points`, `test_the_waves_step_once_on_every_playing_tick`. QA should confirm they fail for the DRA-125-01 reason only.
   - `game/tests/check.sh ui`: 65 passed, unchanged.
   - Acceptance run, 640 x 480 surface filled with `ui.look.BACKGROUND`, `draw_menu` once per `MenuItem`. Script: `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/accept2.py`. Run with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python /tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/accept2.py`. It draws the three images, finds the ink pixels, takes the ink common to all three as the text lines and the ink a selection adds as its marker. PNGs saved outside the repo:
     - `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/dra125-04/menu_play.png`
     - `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/dra125-04/menu_instructions.png`
     - `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/dra125-04/menu_leaderboard.png`

     Output (the text lines are the same in all three images):
     ```
     line (ink rows, ink cols, ink center_x)
       title        rows 170-186  cols 227-413  center_x 320.0
       Play         rows 217-232  cols 305-336  center_x 320.5
       Instructions rows 257-268  cols 270-370  center_x 320.0
       Leaderboard  rows 297-308  cols 268-372  center_x 320.0
     item ink tops 217, 257, 297: 40 px apart (MENU_ITEM_SPACING = 40)
     block ink rows 170 to 309, middle 239.5; surface middle 240
     marker ink, selection play:         rows 221-229 cols 291-298 (label left 305)
     marker ink, selection instructions: rows 261-269 cols 256-263 (label left 270)
     marker ink, selection leaderboard:  rows 301-309 cols 254-261 (label left 268)
     ```
     Each marker is left of centre, in the selected item's rows, with one space between its ink and the label's ink. No marker appears on the other two items (the common ink holds only the labels).
   - Follows the state: three selections give three different images; the same selection drawn twice gives identical bytes; an 800 x 600 surface gives a different (re-centered) picture. Fonts are built once per size (`screen_font(24) is screen_font(24)`). Renders are cached: 5 misses for 5 distinct (text, size) pairs, 25 hits over the calls. `draw_menu` takes only the surface and a `MenuItem`; it reads no core state and writes none. `git status` shows `game/core/` untouched by me.
   - Grep of `game/ui/menu.py` and `game/ui/screen_look.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for `import game.ui`, `from game.ui`, `from ui`, `import ui`: no hits.

4. **Assumptions:**
   - The marker's ink bottom runs one pixel below the label's ink bottom for "Instructions" and "Leaderboard" (rows 261-269 against 257-268). The contract says same top and the label's font, which is what the code does. The glyph shapes cause the one pixel.
   - `_render` (a cached text render) and the marker blit are private to `menu.py`. The contract lists only constants and `screen_font` for `screen_look.py`, so I added no shared helper there. The game-over screen (DRA-125-08) will need the same marker rule. If you want one shared helper in `screen_look.py`, the Architect must add it to the Interface.
   - The marker is drawn after its label, as the last blit of that row.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-125/tasks/DRA-125-04-ui-developer.md`. Left alone: `game/ui/game_over.py` (DRA-125-08), the core test failures (DRA-125-09), the frame (`game/app/`, Integration Engineer).

7. **Status:** done.

## Decisions
- **Layout from font metrics.** Block height is `2 * title linesize + 2 * MENU_ITEM_SPACING + item font get_height()`: the title line, one blank title line, then the last item's top is two spacings below the first. The block top is `(height - block) // 2`. Source: contract, Presentation, Menu, and Rationale, "Layout from font metrics".
- **Marker position.** Its right edge is the label's left edge minus the width of `size(" ")` in the item font, same top, same font. The label never moves. Source: contract, Presentation, Selection marker.
- **Cache.** `screen_font` and `_render` use `functools.cache`, as `game_over.py` does. Nothing renders per frame after the first draw.
- **Plain value in.** `draw_menu` takes `MenuItem`, not the flow. Source: contract, Rationale, "The views take plain values".
- **Numbers and text.** Every constant comes from scope report DRA-125, Values needed (colour white, title 32, body 16, items 24, 40 apart, `>`, texts), except `SCREEN_BOX_COLOR` (scope report DRA-23, Game Over box, alpha 90). Each constant's docstring names its source.
- **Imports.** `from core.game_flow import MenuItem` without the `game.` prefix, as the existing views do.
- **`MENU_ITEM_TEXTS`** is a read-only `MappingProxyType`, so the `Mapping` type holds and nothing can change it.
