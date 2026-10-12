Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the ship view from `docs/contracts/DRA-6/tasks/DRA-6-02-ui-developer.md` (Architect), against `docs/contracts/DRA-6/DRA-6-ship.md`, Interface and Presentation.
2. **Delivered:**
   - `game/ui/ship_view.py`: `SHIP_COLOR = (255, 255, 255)` and `draw_ship(surface: pygame.Surface, ship: Ship) -> None`.
3. **Checks:** all run from `game/`.
   - `python -c "import pygame; assert pygame.IS_CE"`: pass, pygame-ce 2.5.8.
   - `python -m py_compile ui/ship_view.py`: clean.
   - `ruff check .`: all checks passed. `ruff format --check .`: 18 files already formatted. `tests/check.sh lint`: `QA: pass`.
   - Acceptance draw run, 640×480 filled with `ui.look.BACKGROUND`, `draw_ship(surface, spawn())`. Non-background pixels: x 304..335, y 224..255, 1024 pixels, all (255, 255, 255). Center (319.5, 239.5), the middle of the 640×480 screen. Image: `/tmp/claude-1000/-workspace/bb96ec7a-9d42-4f32-a24b-9859640cd1af/scratchpad/ship_spawn.png`
   - Follows the state: `Ship(x=100.4, y=400.6, ...)` draws at x 84..115, y 385..416, still 1024 pixels. That matches `round(100.4 - 16) = 84` and `round(400.6 - 16) = 385`. Image: `/tmp/claude-1000/-workspace/bb96ec7a-9d42-4f32-a24b-9859640cd1af/scratchpad/ship_moved.png`
   - Partly below the floor (`y = 470`): drawn at y 454..479, 832 pixels. pygame clips the rest.
   - No background fill: on a surface filled with (10, 20, 30), the corner pixel is still (10, 20, 30) after the draw.
   - Core unchanged: the ship equals a deep copy taken before the draw (`True`). Drawing the same ship twice gives byte-identical pixels (`True`).
   - Grep `game/ui/*.py` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav|print(|except|from app|import app`: no hits. Grep `game/core/*.py` for `import game.ui|from game.ui|from ui|import ui`: no hits.
   - Command (the full run also measured the moved, floor, no-fill and draw-twice cases):
     ```
     cd game && S=<scratch dir> && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "
     import pygame
     from ui.look import BACKGROUND
     from ui.ship_view import draw_ship
     from core.ship import spawn
     s = pygame.Surface((640, 480)); s.fill(BACKGROUND)
     draw_ship(s, spawn())
     pts = [(x, y) for x in range(640) for y in range(480) if s.get_at((x, y))[:3] != BACKGROUND]
     print(min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts), len(pts))
     pygame.image.save(s, '$S/ship_spawn.png')
     "
     ```
     Prints `304 224 335 255 1024`.
4. **Assumptions:**
   - `pygame.draw.rect` with a `pygame.Rect(left, top, SHIP_W, SHIP_H)` fills exactly SHIP_W × SHIP_H pixels from the rounded corner. Measured: 1024 pixels at 32 × 32.
   - Python's `round` (banker's rounding on exact .5) is what the contract names. The corner never lands on .5 at spawn, so the acceptance case doesn't depend on it.
   - No `__init__.py` was added. `from core.ship import ...` works the same way `ui/error_screen.py` imports `ui.look`.
5. **Documentation differences:** None.
6. **Next:**
   - Implementation Reviewer, for `docs/contracts/DRA-6/tasks/DRA-6-02-ui-developer.md`.
   - Left alone: `game/ui/debug_overlay.py` appeared untracked during this run (task DRA-6-04, not this task). `game/core/`, `game/app/`, `game/main.py`, `ui/look.py`, `ui/error_screen.py` untouched. Calling `draw_ship` each frame is the Integration Engineer's, in `game/app/`.
   - `game/ui/__pycache__/` held a stale `ship_view.cpython-312.pyc` from before this run, with no source. It is overwritten by the new module; `build/` and caches are not committed.
7. **Status:** done.

## Decisions
- **One function, no class.** The contract's Interface gives `draw_ship(surface, ship)`, a plain function. No view class, no camera: DRA-6 has no camera and the contract draws in screen pixels.
- **The ship is passed in each call.** The view holds no reference and copies nothing. It reads `ship.x` and `ship.y` only, plus `SHIP_W` and `SHIP_H` from `core.ship`. 32 is never written in `game/ui/`.
- **Round the corner, not the center.** Per the contract's Rationale, so the rectangle stays exactly 32 × 32. Floats stay floats until that one `round`.
- **No background fill, no flip, no logging in the draw.** The module has `log = logging.getLogger(__name__)` per `game/CONTEXT.md`, but `draw_ship` runs every frame and has no event to log.
- **Values and sources.** `SHIP_COLOR` (255, 255, 255): 04-ship.md, placeholder_look (guess). Size `SHIP_W` × `SHIP_H` (32 × 32): 04-ship.md, ship_w and ship_h (guess), read from `core.ship`. Corner formula: DRA-6-ship.md, Presentation. `SHIP_COLOR` lives in `ship_view.py`, not `look.py`, per the contract's Rationale.
