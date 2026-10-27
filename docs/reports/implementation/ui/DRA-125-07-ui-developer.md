Status: ready-for-review
Created by: ui-developer

1. **Task:** Build `game/ui/pause_box.py` from `docs/contracts/systems/game-flow.md` (task `docs/contracts/DRA-125/tasks/DRA-125-07-ui-developer.md`, asked by the Architect).

2. **Delivered:**
   - `game/ui/pause_box.py` (new): `PAUSE_BOX_SIZE`, `PAUSE_TEXT`, `draw_pause_box(surface)`.

3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python -m py_compile game/ui/pause_box.py`: clean.
   - `game/tests/check.sh lint`: PASS (ruff check and format, 112 files).
   - `game/tests/check.sh typecheck`: only the 7 errors `impact.md` expects (DRA-125-01 row 1: `retry_armed` in `test_run_waves.py`, `test_run_score.py`, `test_run_graze.py`, `test_coin.py`). None names a file I wrote.
   - `game/tests/check.sh core`: 26 failed, 3205 passed, the same numbers as at DRA-125-04. All 26 are in `test_run.py`, `test_run_score.py`, `test_run_waves.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_coin.py`: the DRA-125-01 files `impact.md` expects. I wrote no core code.
   - `game/tests/check.sh ui`: 65 passed, unchanged.
   - Acceptance run: 640 x 480 surface filled with gray (128, 128, 128), `draw_pause_box` once. Script: `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/accept7.py`. Run with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python /tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/accept7.py`. PNGs saved outside the repo:
     - `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/dra125-07/pause_640x480.png`
     - `/tmp/claude-1000/-workspace/e2124d53-5049-40ef-b21a-222a4f4a7667/scratchpad/dra125-07/pause_800x600.png`

     Output:
     ```
     surface 640x480
     box rows 180-299 cols 160-479 (320x120); center (320.0, 240.0); surface center (320.0, 240.0)
     gray inside box (corner 160,180): (83, 83, 83); outside (0,0): (128, 128, 128)
     text ink rows 230-246 cols 284-356; ink center (320.5, 238.5); box center (320.0, 240.0)
     surface 800x600
     box rows 240-359 cols 240-559 (320x120); center (400.0, 300.0); surface center (400.0, 300.0)
     gray inside box (corner 240,240): (83, 83, 83); outside (0,0): (128, 128, 128)
     text ink rows 290-306 cols 364-436; ink center (400.5, 298.5); box center (400.0, 300.0)
     ```
     The box is centered, the fill is darker than the gray (83 against 128), and the text ink sits on the box's center (the ink is 0.5 px right and 1.5 px above it: glyph shape, see Assumptions).
   - Follows the state: the same draw twice gives identical bytes; an 800 x 600 surface gives a re-centered picture; on a red world surface the box pixel is (129, 25, 25) against (200, 40, 40) outside, so the world shows through. The box and the text are each built once (`cache_info`: 1 miss, 2 hits after 3 draws); `_box() is _box()`. `draw_pause_box` takes only the surface; it reads no core state and writes none. `git status` shows `game/core/` untouched by me.
   - Grep of `game/ui/pause_box.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav`: no hits. Grep of `game/core/` for `import game.ui`, `from game.ui`, `from ui`, `import ui`: no hits.

4. **Assumptions:**
   - The text's rect is centered on the box's center, as the contract says. The ink is 1.5 px above that center because the font's ascent leaves room above caps; I did not correct for it.
   - `PAUSE_TEXT` is `PAUSE`: scope report DRA-125 and 10-ui.md, pause_box ("the word PAUSE").

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-125/tasks/DRA-125-07-ui-developer.md`. Left alone: `game/ui/game_over.py` (DRA-125-08, it still has its own box), the core test failures (DRA-125-09), the frame that calls `draw_pause_box` (`game/app/`, Integration Engineer).

7. **Status:** done.

## Decisions
- **Same box rule as the game-over box.** A `pygame.SRCALPHA` surface of `PAUSE_BOX_SIZE`, filled with `SCREEN_BOX_COLOR`, blitted at `((width - box_width) // 2, (height - box_height) // 2)`. Source: contract, Presentation, Box.
- **Text placement.** The rendered text's rect uses `center=box_rect.center`, so the box rect is the one source of both positions. Source: contract, Presentation, Pause box.
- **Cache.** `_box` and `_text` use `functools.cache`, as `menu.py` does. Nothing is built or rendered after the first draw. Source: contract, Presentation, Cache; 15-tech-constraints.md, rule 5.
- **Numbers and text.** `PAUSE_BOX_SIZE` (320, 120) and `PAUSE_TEXT` come from scope report DRA-125, Values needed, Pause box. Color, title size and font come from `ui.screen_look`.
- **Imports.** pygame and `ui.screen_look` only, without the `game.` prefix, as the existing views do. Never core, never app.
