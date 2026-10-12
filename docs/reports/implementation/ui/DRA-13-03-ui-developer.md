Status: ready-for-review
Created by: ui-developer

1. **Task:** build the HUD meters readout and `overlay_text_bottom()` (`docs/contracts/DRA-13/tasks/DRA-13-03-ui-developer.md`, from the Architect).
2. **Delivered:** `/workspace/game/ui/hud.py` (new), `/workspace/game/ui/debug_overlay.py` (added `overlay_text_bottom()` only).
3. **Checks:**
   - IS_CE true (pygame-ce 2.5.8). `py_compile` clean on both files. `game/tests/check.sh lint`: lint and format PASS, "QA: pass".
   - Headless run from `game/`: `SDL_VIDEODRIVER=dummy PYTHONPATH=. python <scratch>/hud_check.py` (script in the scratchpad, not the repo), 640x480, filled with `ui.look.BACKGROUND`.
   - Images: `/tmp/claude-1000/-workspace/91f627b4-dcd2-4d42-8588-06dcf2e39371/scratchpad/hud_normal.png` and `.../hud_debug.png`.
   - Normal: white `0 m` glyph rows 27 to 32 (blit at y 24), none above row 27.
   - Debug: `overlay_text_bottom()` = 52. Lowest green row above 168 = 48. White rows 79 to 84 (`11 m`). 79 > 48: no overlap.
   - Grep of `hud.py` for sleep, threading, asyncio, pygame.display/event/key, image.load, mixer, random.random(, .mp3, .wav, print(: no hits. `game/core/` has no ui import.
   - The HUD reads only `scroll.meters`. `Scroll` is frozen, so the draw can't change it.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-13/tasks/DRA-13-03-ui-developer.md`. Left alone: `game/app/` (Integration Engineer), starfield, tests.
7. **Status:** done.

## Decisions
- Font cached with `functools.cache`, as the overlay does. Built once on first draw.
- Imports use the existing style (`from core.scroll import Scroll`, `from ui.debug_overlay import ...`).
- All HUD constants, their values and sources: task Do and DRA-13-hud.md Interface (scope report DRA-13, temporary stand-ins).
- Line 1 is left empty by only offsetting line 2 by `HUD_LINE_SPACING`.
