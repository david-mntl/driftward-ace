Status: ready-for-review
Created by: ui-developer

1. **Task:** build the starfield view in `game/ui/starfield.py` (`docs/contracts/DRA-13/tasks/DRA-13-02-ui-developer.md`, from the Architect).
2. **Delivered:** `/workspace/game/ui/starfield.py`.
3. **Checks:**
   - IS_CE true (pygame-ce 2.5.8). `py_compile` clean. `game/tests/check.sh lint`: ruff check and format pass, "QA: pass".
   - Headless run from `game/`, 640x480, filled with `ui.look.BACKGROUND`:
     `SDL_VIDEODRIVER=dummy python -c "..."` drawing `draw_starfield(surface, start_scroll())` and `draw_starfield(surface, Scroll(ticks=40, scrolled_ticks=10))`.
   - Images: `/tmp/claude-1000/-workspace/91f627b4-dcd2-4d42-8588-06dcf2e39371/scratchpad/star0.png` (no scroll) and `.../star11.png` (11 px scroll).
   - Result: 50 stars. Pixel at star 0 base position is (90, 100, 140) in image 1. In image 2 the same star is at y+11 (mod 480), same color. 131 star-colored pixels in each image (same pattern, shifted, wrapped).
   - Grep of `game/ui/starfield.py` for sleep, threading, asyncio, pygame.display/event/key, image.load, mixer, random.random(, .mp3, .wav, print(: no hits. `game/core/` has no ui import.
   - The view reads only `scroll.distance_px`. `Scroll` is a frozen dataclass, so the draw can't change it.
4. **Assumptions:** `STAR_SEED = 1301`, an arbitrary fixed int as the task allows. `STARS` is built at import, which the contract allows.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-13/tasks/DRA-13-02-ui-developer.md`. Left alone: `game/ui/hud.py` (task DRA-13-03), `game/app/` (Integration Engineer).
7. **Status:** done.

## Decisions
- Imports follow the existing style (`from core.scroll import Scroll`, no `game.` prefix), as `ship_view.py` does.
- Star layout built in a small `_build_stars()` helper, run once at import, in the contract's order: x, base_y, size.
- Star values (count, color, sizes): scope report DRA-13, temporary stand-ins, noted in each docstring. Seed has no design meaning.
- Each star is drawn with `pygame.draw.rect` using `int(...)` on y only, per the contract. The view does not fill the background.
