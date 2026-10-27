Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-126-03 (Architect): add `group_digits`, `best_text` and `BEST_LABEL` to `ui/score_text.py`, and BEST on HUD line 1 (`HUD_BEST_X`, `best` parameter) to `ui/hud.py`. Task: `docs/contracts/DRA-126/tasks/DRA-126-03-ui-developer.md`.

2. **Delivered:**
   - `/workspace/game/ui/score_text.py`: `BEST_LABEL`, public `group_digits` (the old private `_grouped`, renamed), `best_text`.
   - `/workspace/game/ui/hud.py`: `HUD_BEST_X = 200`, `draw_hud(surface, run, below_overlay, best=None)`, a cached `_best_surface`.
   - Draw script (scratchpad, not in the repo): `/tmp/claude-1000/-workspace/306b4d78-3a59-4da7-966c-22967ac5773e/scratchpad/dra126_03_check.py`.
   - PNGs: `/tmp/claude-1000/-workspace/306b4d78-3a59-4da7-966c-22967ac5773e/scratchpad/hud_best{None,2345}_below{False,True}.png`.

3. **Checks:**
   - Command: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/306b4d78-3a59-4da7-966c-22967ac5773e/scratchpad/dra126_03_check.py`
   - `group_digits` / `best_text`: 0 -> `0` / `BEST 0`; 999 -> `999` / `BEST 999`; 1000 -> `1 000` / `BEST 1 000`; 1234 -> `1 234` / `BEST 1 234`; 1000007 -> `1 000 007` / `BEST 1 000 007`.
   - HUD on 640 x 480, run from `start_run()`, ink boxes (x, y, w, h):

     | below_overlay | best | SCORE ink | BEST ink |
     |---|---|---|---|
     | False | None | (4, 5, 51, 8) | none |
     | False | 2345 | (4, 5, 51, 8) | (201, 5, 61, 8) |
     | True | None | (4, 81, 51, 8) | none |
     | True | 2345 | (4, 81, 51, 8) | (201, 81, 61, 8) |

   - BEST ink rows equal SCORE's rows in both modes (True, True). The ink's left column is 201, not 200: the glyph "B" has a 1 px left side bearing in the default font. The text box origin is exactly (`HUD_BEST_X`, `hud_top`): BEST pixels equal a lone blit of the rendered text at (200, 4) and (200, 80) (True, True). A test that reads ink must allow that 1 px bearing.
   - Follows the state: `best` None -> 2345 adds the BEST ink; `below_overlay` moves it from row 5 to row 81 with SCORE. The run's `repr` is the same before and after the draw; two draws of the same state give identical bytes.
   - `python3 -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8). `py_compile` on both files: clean.
   - `game/tests/check.sh lint`: pass (ruff check and format). `typecheck`: pass (116 files). `ui`: pass (89 tests, unchanged). `core`: 3287 pass, 1 fail: `test_game_flow.py::test_the_flow_logs_screen_changes_pauses_and_moves_only_and_the_run_lines_come_first`, the one `impact.md` lists (DRA-126-02, cleared by DRA-126-07). It is core, not in my files.
   - Grep of the two files for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for ui imports: no hits.

4. **Assumptions:**
   - `HUD_BEST_X = 200` comes from scope report DRA-126, Values needed ("fixed x of 200 px"). The contract's Interface gives the name but not the value.
   - `BEST_LABEL` and `HUD_BEST_X` are typed `Final`, as the contract's Interface writes them. The older constants in these files are plain annotations; I left them.

5. **Documentation differences:** None.

6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-126/tasks/DRA-126-03-ui-developer.md`. Left alone: `game/app/frame.py` (passing `flow.best` is the Integration Engineer's), `ui/game_over.py` and `ui/leaderboard.py` (DRA-126-04, -05; the leaderboard will import `group_digits`), all tests.

7. **Status:** done.

## Decisions
- `group_digits` is the old `_grouped` renamed and given a fuller docstring. `score_text`, `graze_text` and `best_text` all call it, so there is one grouping. Source: hud.md, Presentation, `group_digits` and `best_text`.
- BEST draws between SCORE and GRAZE in the code, but the order is irrelevant: they sit at different places and never overlap.
- `_best_surface` is an `lru_cache(maxsize=1)` keyed on `best`, like the SCORE and GRAZE caches, so the text is rendered again only when `best` changes. Source: hud.md, BEST line; 15-tech-constraints.md, rule 5.
- BEST reuses `_hud_font()` and `HUD_COLOR`: SCORE's look. Source: hud.md, BEST line.
- `draw_hud` keeps its old call valid: `best` defaults to None and draws nothing then, so the existing HUD tests pass unchanged.
- The `hud.py` module docstring's first line was shortened to fit 100 columns after BEST was added.
