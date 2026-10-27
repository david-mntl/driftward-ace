Status: ready-for-review
Created by: ui-developer

1. **Task:** Change `game/ui/game_over.py` to the game-over screen of `docs/contracts/systems/game-flow.md` (task `docs/contracts/DRA-125/tasks/DRA-125-08-ui-developer.md`, asked by the Architect).

2. **Delivered:**
   - `game/ui/game_over.py` (changed): `BOX_SIZE` (320 x 160), `TITLE_TEXT` ("GAME OVER"), new `RETRY_TEXT`, `MENU_TEXT`, `draw_game_over(surface)` and `draw_final_score(surface, score)` with the same signatures, new `draw_game_over_choices(surface, selection)`. Removed `PROMPT_TEXT`, `PROMPT_FONT_SIZE`, `BOX_COLOR`, `TEXT_COLOR`, `TITLE_FONT_SIZE`, `SCORE_FONT_SIZE` (the shared ones come from `ui.screen_look`).

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python -m py_compile game/ui/game_over.py`: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format).
   - `game/tests/check.sh typecheck`: only the 7 `retry_armed` errors `impact.md` expects (`test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`). None in a file I wrote.
   - `game/tests/check.sh core`: 26 failed, 3205 passed, the same numbers as at DRA-125-07. All in the six DRA-125-01 test files `impact.md` names. I wrote no core code.
   - `game/tests/check.sh ui`: 3 failed, 62 passed. The 3 are exactly the ones `impact.md` lists for DRA-125-08: `test_game_over_with_score_shows_three_centered_lines_in_the_box`, `test_game_over_only_the_score_line_changes_with_the_score`, `test_game_over_alone_leaves_the_score_line_place_empty` (cleared by DRA-125-11). No other test changed.
   - Acceptance run: 640 x 480 surface filled with gray (128, 128, 128). Script: `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/dra125-08/accept.py`. Command: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python /tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/dra125-08/accept.py`. PNGs, outside the repo, in `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/dra125-08/`: `title_only.png`, `full_retry.png`, `full_menu.png`. Output (ink rows and the columns of each ink group inside the box; a group is split from the next at a gap of more than 6 px):
     ```
     [title_only] box x 160..479 y 160..319 size 320x160, center (320.0,240.0) surface center (320.0,240.0)
        ink rows 212..227 groups(cols) [[254, 317], [326, 386]]
     [full_retry] box x 160..479 y 160..319 size 320x160, center (320.0,240.0) surface center (320.0,240.0)
        ink rows 212..227 groups(cols) [[254, 317], [326, 386]]     title   (cols 254..386, center 320)
        ink rows 235..242 groups(cols) [[286, 332], [339, 355]]     score   (cols 286..355, center 320.5)
        ink rows 247..254 groups(cols) [[292, 338]]                 marker + RETRY
        ink rows 259..266 groups(cols) [[305, 334]]                 MENU, no marker
     [full_menu] box x 160..479 y 160..319 size 320x160, center (320.0,240.0) surface center (320.0,240.0)
        ink rows 212..227 groups(cols) [[254, 317], [326, 386]]
        ink rows 235..242 groups(cols) [[286, 332], [339, 355]]
        ink rows 247..254 groups(cols) [[302, 338]]                 RETRY, no marker
        ink rows 259..266 groups(cols) [[295, 334]]                 marker + MENU
     pixel inside box top-left, over gray: Color(83, 83, 83, 255) box color (0, 0, 0, 90)
     ```
     The box is centered and darker than the gray (83 against 128). Four lines are centered across the width and stacked inside the box (rows 212..266 in box rows 160..319). The marker ink is only left of the selected label: RETRY's left edge is 302 in both runs and the marker takes 292 on RETRY; MENU's right edge is 334 in both runs and the marker takes 295 on MENU. The labels do not move. With `draw_game_over` alone only the title's ink is in the box.
   - Follows the state: the same draws twice give identical bytes. Moving the selection changes only the marker. A new score re-renders the score line only (`_score_line` cache: 1 miss and 4 hits over 5 draws of 1234, a second miss on 99); the box and the title each build once (1 miss, 4 hits). An 800 x 600 surface re-centers the box (corner at 240, 220). The views take the score and the selection as arguments; they read no core state and write none (`GameOverChoice` is only the choice enum).
   - Grep of `game/ui/game_over.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for `import ui`, `from ui`, `game.ui`: no hits.

4. **Assumptions:**
   - `BOX_SIZE` and `TITLE_TEXT` stay plain (not `Final`), as the contract's Interface block types them; `RETRY_TEXT` and `MENU_TEXT` are `Final`.
   - The choice-to-label map is a private module dict, not a public name, so the Interface is unchanged.
   - The title is `GAME OVER` in capitals: scope report DRA-125, Values needed (the old DRA-23 text was "Game Over").

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-125/tasks/DRA-125-08-ui-developer.md`. Left alone: `game/tests/ui/test_game_over.py` (its 3 failures are cleared by DRA-125-11), `game/app/frame.py` (the Integration Engineer calls `draw_game_over_choices` at integration).

7. **Status:** done.

## Decisions
- One private `_layout(size)` gives the box origin and the four tops, and all three functions use it, so each line lands in its place whichever functions are called (contract, Game-over screen, Layout). It is computed from `surface.get_size()` and the fonts' `get_linesize()` and `get_height()`; no spacing number is invented. Block height = title line + score line + RETRY line + the body font's `get_height()` (MENU is the last line).
- Fixed texts (title, labels, marker) render once each through `@cache`; the box surface builds once. The score line keeps `lru_cache(maxsize=1)` and renders through its own call, not the unbounded `_label` cache, so a changing score never grows memory. Source: contract, Cache; 15-tech-constraints.md, rule 5.
- The marker is drawn in the label's font (body size) at the label's top, its right edge one space (`size(" ")` of the body font) left of the label's left edge. The label is centered the same on both states. Source: contract, Selection marker.
- Numbers and colors: `BOX_SIZE` 320 x 160, `TITLE_TEXT`, `RETRY_TEXT`, `MENU_TEXT` from scope report DRA-125, Values needed (Game-over screen). Box color, text color, font sizes and marker from `ui.screen_look`. The score text from `ui.score_text`.
