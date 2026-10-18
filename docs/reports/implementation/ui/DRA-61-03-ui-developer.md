Status: ready-for-review
Created by: ui-developer

1. **Task:** Add the three-line layout and `draw_final_score` to the Game Over box, from `docs/contracts/DRA-61/tasks/DRA-61-03-ui-developer.md` (contracts `run.md` v4 and `hud.md` v2), asked by the Architect.
2. **Delivered:** `game/ui/game_over.py` (changed): `SCORE_FONT_SIZE`, `draw_final_score(surface, score)`, `draw_game_over` on the three-line layout (score place left empty), helpers `_box_origin`, `_title_top`, `_score_line`.
3. **Checks** (from `game/`, `PYGAME_HIDE_SUPPORT_PROMPT=1`):
   - IS_CE: `python -c "import pygame; assert pygame.IS_CE"` passes. `py_compile ui/game_over.py` clean.
   - Acceptance command from the task, run unchanged with `SDL_VIDEODRIVER=dummy`, prints `2 3 3`, `True`, `True`, `True`.
   - Screenshot: `draw_game_over(s)` then `draw_final_score(s, 1234)` on a 640 x 480 surface (fill 40,60,90), saved with `pygame.image.save`: `/tmp/claude-1000/-workspace/560f3b16-f48a-4957-8e50-a98c857bb711/scratchpad/game_over_score.png`. It shows "Game Over", `SCORE 1 234`, "Press any arrow to retry", all centered in the box.
   - Build once: `draw_final_score(s, 5)` twice then `6`: `_score_line.cache_info()` is hits=1 misses=1, then misses=2. One render per score.
   - `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS, ends `QA: pass` (35 ui tests passed). `ruff check game` and `ruff format --check game` clean.
   - Grep of `game/ui/game_over.py` for sleep, threading, asyncio, pygame.display, pygame.event, pygame.key, image.load, mixer, `random.random(`, .mp3, .wav: no hits. Grep of `game/core/` for ui imports: no hits.
4. **Assumptions:** None beyond Decisions.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-61/tasks/DRA-61-03-ui-developer.md`. Left alone: `game/app/frame.py` (the `draw_final_score` call is the Integration Engineer's), `game/ui/hud.py`, all tests.
7. **Status:** done.

## Decisions
- Layout follows run.md, Vertical place: block height is title `get_linesize()` + score `get_linesize()` + prompt `get_height()`. `draw_game_over` puts the prompt one title line plus one score line below the title top, so the title and prompt do not move when the score is drawn. Both functions share `_box_origin` and `_title_top`, so the layout lives in one place.
- The score font is kept in the cached `_Parts` with the other fonts and sizes, built on the first draw by either function. Source: 15-tech-constraints.md, rule 5.
- The score line surface uses `lru_cache(maxsize=1)` on `_score_line(score)`, the same pattern as `hud.py` from DRA-61-02: re-render only when the score differs, never a growing cache.
- The text comes from `ui.score_text.score_text`, so the box and the HUD read the same. Color is `TEXT_COLOR`, size `SCORE_FONT_SIZE` (16, run.md).
- `draw_game_over` signature unchanged, so `app/frame.py` still type-checks.
