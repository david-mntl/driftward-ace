Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the debug overlay view, from `docs/contracts/DRA-6/tasks/DRA-6-04-ui-developer.md` (Architect), against `docs/contracts/DRA-6/DRA-6-debug-overlay.md`, Interface and Presentation.
2. **Delivered:**
   - `game/ui/debug_overlay.py`: `OVERLAY_COLOR`, `OVERLAY_FONT_SIZE`, `OVERLAY_MARGIN`, `draw_debug_overlay(surface: pygame.Surface, ship: Ship) -> None`.
3. **Checks:** all run from `game/`.
   - `python -c "import pygame; assert pygame.IS_CE"`: pass, pygame-ce 2.5.8.
   - `python -m py_compile ui/debug_overlay.py`: clean.
   - `ruff check .`: all checks passed. `ruff format --check .`: 18 files already formatted. `tests/check.sh lint`: `QA: pass`.
   - Acceptance draw run, 640×480 filled with `ui.look.BACKGROUND`, `draw_debug_overlay(surface, spawn())`:
     - Rows that are (0, 255, 0) across the full width: `[168, 479]`. No other row.
     - Four text bands at the top-left, ink rows 5..12, 17..26, 29..36, 41..50. Font `get_linesize()` = 12, so the blit tops are 4, 16, 28, 40. Leftmost ink x 4.
     - Text reads `x 320.00`, `y 240.00`, `vx 0.00`, `vy 0.00` (checked by eye on a 5× crop). Every non-background pixel in the text area is a green shade (R 0, B 0, antialiased); pure (0, 255, 0) is present.
     - Image: `/tmp/claude-1000/-workspace/bb96ec7a-9d42-4f32-a24b-9859640cd1af/scratchpad/overlay_spawn.png`. 5× crop: `.../scratchpad/zoom_spawn.png`.
   - Follows the state: `Ship(x=12.5, y=199.0, vx=-3.25, vy=-0.26)` draws `x 12.50`, `y 199.00`, `vx -3.25`, `vy -0.26`, and the pixels differ from the spawn draw. Image: `.../scratchpad/overlay_moved.png`, crop `.../scratchpad/zoom_moved.png`.
   - Width from the surface: on 800×600 the full-width green rows are `[168, 479]`, full 800 px wide.
   - Core unchanged: the ship equals a deep copy taken before the draw (`True`). `Ship` is a frozen dataclass, too.
   - Same state drawn twice: byte-identical pixels (`True`).
   - Font built once: `_overlay_font.cache_info()` after five calls is `hits=4, misses=1`, and the same object each time.
   - Grep `game/ui/*.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav|print(|except|from app|import app`: no hits. Grep `game/core/*.py` for `import game.ui|from game.ui|from ui|import ui`: no hits.
   - Command:
     ```
     cd game && S=<scratch dir> && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "
     import pygame
     from core.ship import spawn
     from ui.look import BACKGROUND
     from ui.debug_overlay import draw_debug_overlay, OVERLAY_COLOR
     pygame.init()
     s = pygame.Surface((640, 480)); s.fill(BACKGROUND); draw_debug_overlay(s, spawn())
     print([y for y in range(480) if all(tuple(s.get_at((x, y)))[:3] == OVERLAY_COLOR for x in range(640))])
     pygame.image.save(s, '$S/overlay_spawn.png')
     "
     ```
     Prints `[168, 479]`. The full run also scanned the text bands, the moved ship, the 800×600 surface, the draw-twice compare and the font cache.
4. **Assumptions:**
   - "Created once, on the first draw, and kept" is done with `functools.cache` on a private `_overlay_font()`. It is the only way to keep a font with the contract's `(surface, ship)` signature. It caches a resource, not game state. If a caller runs `pygame.quit()` and then `pygame.init()` again in the same process, the cached font belongs to the old font module. The app never does that. A test session that does would need to know.
   - Lines are drawn with `pygame.draw.line` from x 0 to `surface.get_width() - 1`, which covers every pixel of the row.
   - The text blit top-left is at (4, 4). The default font's ink starts one row lower (row 5); that is the font's own padding, not an offset.
   - The module has `log = logging.getLogger(__name__)` per game/CONTEXT.md but logs nothing. The contract says the view only draws, and nothing in it is an event.
5. **Documentation differences:** None. The contract, 10-ui.md (debug_overlay, debug_overlay_layout, debug_text_font, debug_overlay_color, rule 7) and the task agree.
6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-6/tasks/DRA-6-04-ui-developer.md`. The call site (`overlay_visible`, F3) is the Integration Engineer's in `game/app/frame.py`. Left alone: `game/ui/ship_view.py` (task DRA-6-02, present but untracked, not mine), `game/ui/look.py`, `game/ui/error_screen.py`, `game/core/`, `game/app/`, `game/main.py`, `game/tests/`.
7. **Status:** done.

## Decisions
- **Values and sources.** `OVERLAY_COLOR` (0, 255, 0): 10-ui.md, debug_overlay_color (guess). `OVERLAY_FONT_SIZE` 16, default font: debug_text_font (guess). `OVERLAY_MARGIN` 4 and the one-line-height step: debug_overlay_layout (guess). Line rows: `TOP_LINE_Y` and `SCREEN_H - 1`, read from `core.world`; 10-ui.md, debug_overlay_layout; 91-decision-log.md, row 20. No bare 168, 479 or 640 in the module.
- **Draw order:** the two lines, then the text, so the text stays readable where they cross (contract, Presentation).
- **Split into `_draw_lines` and `_draw_text`.** Each has one job; `draw_debug_overlay` calls them in the contract's order.
- **Readings as a tuple of (name, value).** One loop renders all four lines with `f"{name} {value:.2f}"`, so negatives keep their minus sign and the layout step lives in one place.
- **The view takes the ship as an argument and reads four fields.** It computes nothing but pixel positions. Imports are pygame, `core.ship` and `core.world` only; no `app`, no run mode.
- **No fill, no flip, no catch.** The view draws on top of whatever the caller has drawn.
