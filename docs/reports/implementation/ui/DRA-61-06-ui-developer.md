Status: ready-for-review
Created by: ui-developer

1. **Task:** Move the HUD to the SCORE line on line 1 and drop the meters readout, from `docs/contracts/DRA-61/tasks/DRA-61-06-ui-developer.md` (contract `docs/contracts/systems/hud.md` v2), asked by the Architect.
2. **Delivered:** `game/ui/hud.py` (changed): imports `score_text`; `draw_hud` blits the SCORE text at (`HUD_MARGIN`, `hud_top`) and leaves line 2 empty; new `_score_surface(score)`; module, `draw_hud` and constant docstrings name SCORE and the HUD text instead of the readout.
3. **Checks** (from `game/`, `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`):
   - IS_CE: `python -c "import pygame; assert pygame.IS_CE"` passes. `python -m py_compile game/ui/hud.py` clean.
   - Acceptance command from the task, run unchanged: prints `True True True`.
   - Screenshot: `draw_debug_overlay(s, spawn())` then `draw_hud(s, Run(ship=spawn(), scroll=Scroll(ticks=130, scrolled_ticks=100), lives=3), True)` on a 640 x 480 surface, saved with `pygame.image.save` to `/tmp/claude-1000/-workspace/560f3b16-f48a-4957-8e50-a98c857bb711/scratchpad/hud_debug.png`. Measured: `run.score` 11, `overlay_text_bottom()` 52, white HUD text rows 57 to 64 and first column 5 (below the overlay's 52 + 4 gap, nothing on line 2), heart pixels at x 544 to 631.
   - Follows the state: `lives=0` draws no heart (acceptance run, all ink within rows 4 to 23). `_score_surface(11)` is the same object on a second draw and a new one for score 12.
   - Run state is identical before and after the draw (`dataclasses.asdict(run)` compared).
   - `game/tests/check.sh`: env, lint, format, typecheck, core, ui all PASS, ends `QA: pass`.
   - Grep of `game/ui/hud.py` for sleep, threading, asyncio, pygame.display, pygame.event, pygame.key, image.load, mixer, `random.random(`, .mp3, .wav: no hits. Grep of `game/core/` for ui imports: no hits.
4. **Assumptions:** The font stays on `@cache` (`_hud_font`). The one-slot render cache is `functools.lru_cache(maxsize=1)` on `_score_surface`, so only the last score's surface is kept and memory stays flat as the score grows.
5. **Documentation differences:** None.
6. **Next:** QA Engineer, task `docs/contracts/DRA-61/tasks/DRA-61-07-qa-engineer.md` (the exact SCORE line tests). Implementation Reviewer first, on this report. Left alone: `ui/score_text.py`, `ui/game_over.py`, `ui/debug_overlay.py`, tests, core and app.
7. **Status:** done.

## Decisions
- The render cache is `lru_cache(maxsize=1)` keyed on the score int: it re-renders only when the score differs from the last one (hud.md, SCORE line; 15-tech-constraints.md, rule 5) and holds no module state of my own. It is the same idiom as the existing `@cache` helpers.
- The SCORE text goes through `score_text(run.score)`. No format or score logic is in `hud.py`.
- Constants are unchanged (hud.md, Interface). Only their docstrings dropped the word "readout".
- Hearts, `hud_top` rule and `overlay_text_bottom()` use are untouched.
