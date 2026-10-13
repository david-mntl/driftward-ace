Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the Game Over box, a temporary stand-in, in `game/ui/game_over.py`, from task `docs/contracts/DRA-23/tasks/DRA-23-03-ui-developer.md` (Architect). The Director confirmed on 2026-10-13: black at about 35% opacity stays, and the two text lines are centered in the box one line-height apart. This matches the contract.
2. **Delivered:** `/workspace/game/ui/game_over.py` (new). Constants `BOX_SIZE`, `BOX_COLOR`, `TEXT_COLOR`, `TITLE_TEXT`, `TITLE_FONT_SIZE`, `PROMPT_TEXT`, `PROMPT_FONT_SIZE`, and `draw_game_over(surface) -> None`, as in `run.md`.
3. **Checks:**
   - `python3 -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8).
   - `python3 -m py_compile game/ui/game_over.py`: clean.
   - `game/tests/check.sh lint`: PASS lint, PASS format, `QA: pass`.
   - Acceptance script, run from `game/` (kept in the scratchpad, not the repo): `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/8060ad56-4f1c-40d0-ad14-d4fb39ed0880/scratchpad/go.py`. It fills with `BACKGROUND`, draws `draw_starfield(Scroll(ticks=130, scrolled_ticks=100))` then `draw_game_over` (image 1), then fills (90, 100, 140) and draws again (image 2). Printed:
     ```
     box inside (58, 64, 90)
     outside (90, 100, 140)
     white bbox x 251 387 rows 225 254
     built once: True
     ```
     Inside the box the color is (58, 64, 90), one unit off the task's "about (58, 65, 91)" from alpha rounding. The outside pixel is unchanged. The white pixels lie inside x 160 to 479, rows 180 to 299. A second draw reuses the same cached parts (`_parts()` is the same object).
   - Images: `/tmp/claude-1000/-workspace/8060ad56-4f1c-40d0-ad14-d4fb39ed0880/scratchpad/game_over_1.png` (stars, box, white title and smaller prompt, both centered; the box is only faintly visible on black, as the contract says) and `/tmp/claude-1000/-workspace/8060ad56-4f1c-40d0-ad14-d4fb39ed0880/scratchpad/game_over_2.png`.
   - Grep of `game/ui/game_over.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `image.load`, `mixer`, `random.random(`, `.mp3`, `.wav`, `print(`: no hits. Grep of `game/core` for `import ui` / `from ui`: no hits. Imports in `game_over.py`: stdlib and pygame only, no `core`, no `app`.
4. **Assumptions:** None beyond the contract. The text positions are computed on each draw from `surface.get_size()`, because the surface can differ; only the box, fonts and rendered texts are cached.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-23/tasks/DRA-23-03-ui-developer.md`. Left alone: `game/app/` (the Integration Engineer calls `draw_game_over` while `run.game_over`), the hearts (DRA-23-02), and every other file in `game/ui/`.
7. **Status:** done.

## Decisions
- Build once with `functools.cache` on a private `_parts()` returning a frozen `_Parts` dataclass. This is the pattern `ui/hud.py` already uses for its font. No module-level state, no flag.
- The caller's surface size is read at draw time, so the contract's centering formulas hold for any surface size, not just 640 × 480.
- Vertical layout: `title_top = box_top + (120 - block_height) // 2`, `prompt_top = title_top + title get_linesize()`, as in `run.md`, Presentation. The title's top and the prompt's top are set with `get_rect(centerx=..., top=...)`.
- Every constant value and its source (scope report DRA-23, UI-04 TBD) are copied from the task and contract. No GDD value is used.
- The module has the `log` logger per `game/CONTEXT.md` but never logs. It has no `try`/`except`.
