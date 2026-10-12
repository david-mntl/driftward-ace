Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the shared background color and the error screen view, from `docs/contracts/DRA-5/tasks/DRA-5-01-ui-developer.md` (Architect), against `docs/contracts/DRA-5/DRA-5-app.md`, Interface and Presentation.
2. **Delivered:**
   - `game/ui/look.py`: `BACKGROUND = (0, 0, 0)`.
   - `game/ui/error_screen.py`: `draw_error_screen(surface: pygame.Surface, detail: str | None) -> None`.
3. **Checks:** all run from `game/`.
   - `python -c "import pygame; assert pygame.IS_CE"`: pass, pygame-ce 2.5.8.
   - `python -m py_compile ui/look.py ui/error_screen.py`: clean.
   - `ruff check .` and `ruff format --check .`: no findings. `game/tests/check.sh lint`: `QA: pass`.
   - Acceptance draw run on 640×480, measured by scanning for non-black pixels (rows top..bottom, columns left..right):
     - `detail=None`: one band, rows 232..247, x 183..457, center x 320.0. Corner pixel (0, 0, 0). Image: `/tmp/claude-1000/-workspace/bb96ec7a-9d42-4f32-a24b-9859640cd1af/scratchpad/error_none.png`
     - `detail="ValueError: boom"`: the same main band, plus a second band at rows 250..257, x 270..369, center x 319.5. Image: `/tmp/claude-1000/-workspace/bb96ec7a-9d42-4f32-a24b-9859640cd1af/scratchpad/error_detail.png`
     - Main font `get_linesize()` = 18. The detail's top sits 18 px below the main line's rect top.
   - The view follows its input: a 500-character detail is cut to 80 characters. Its band spans x 2..637, inside 640. One DEBUG line: `error detail cut from 500 to 80 characters`. On an 800×300 surface the main line moves to rows 142..157, x 263..537, so it is centered from `surface.get_size()`.
   - The same input drawn twice gives byte-identical pixels: `True`. There is no core state in DRA-5, so the "core unchanged" check doesn't apply.
   - Grep `game/ui/` for `time.sleep|threading|asyncio|pygame.display|pygame.event|pygame.key|pygame.image.load|pygame.mixer|random.random(|.mp3|.wav|print(|except`: no hits. Grep `game/core/` for `import game.ui|from game.ui|from ui|import ui`: no hits.
   - Command (the `logging.basicConfig` call is only in this inline check, to show the DEBUG line):
     ```
     cd game && S=<scratch dir> && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -c "
     import logging, sys, pygame
     logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
     from ui.error_screen import draw_error_screen
     pygame.init()
     for name, d in (('none', None), ('detail', 'ValueError: boom')):
         s = pygame.Surface((640, 480)); draw_error_screen(s, d)
         pygame.image.save(s, f'$S/error_{name}.png')
     "
     ```
     The full run also scanned the pixel bands, the long-detail cut, the 800×300 surface and the draw-twice compare.
4. **Assumptions:**
   - The main line is centered by its rendered text rect (`get_rect(center=surface center)`). The detail's top is that rect's top + `get_linesize()`. The ink sits a few pixels inside the rect, so the gap you see is smaller than 18 px.
   - The detail is centered at `surface.get_width() // 2`, the same integer center `Rect.center` uses for the main line.
   - An empty `detail` string (`""`) counts as a string. Nothing visible is drawn below the main line.
   - `pygame.font` must be initialized before the call. If it isn't, `pygame.font.Font` raises and the view lets the error rise, as the contract says.
   - No `__init__.py` was added to `game/ui/`. `from ui.look import BACKGROUND` works as a namespace package, the same way `game/core/` is laid out today.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-5/tasks/DRA-5-01-ui-developer.md`. QA then runs `DRA-5-02-qa-engineer`. I didn't touch `game/main.py`, `game/app/`, `game/scripts/` (Integration Engineer, from the contract) or `game/tests/ui/` (task DRA-5-02).
7. **Status:** done.

## Decisions
- **Fonts are built inside `draw_error_screen`.** This role normally takes a font passed in and never builds one in a draw call. The contract's Interface fixes the signature as `(surface, detail)` with no font argument, and Presentation names `pygame.font.Font(None, 24)` and `pygame.font.Font(None, 16)`. The guard calls this function once per error, not every frame, so building the fonts here costs nothing at frame rate. A module-level font would need `pygame.font` initialized at import time, and a cache would be hidden module state. The Reviewer may want to confirm this reading.
- **Values and sources.** `BACKGROUND` (0, 0, 0): 12-art-and-audio.md, placeholder_bg (guess). Message text: 10-ui.md, error_screen (guess). Size 24: error_text_font (guess). Size 16: debug_text_font (guess). Color (255, 255, 255): error_text_color (guess). Layout: error_layout (guess). Cut rule: error_debug_line (guess). Each is a named constant with its source in the docstring. `BACKGROUND` lives only in `ui/look.py`, as the contract's Rationale asks.
- **Draw order:** fill, main line, then the detail line. They don't overlap.
- **Cut to width:** `_fit_to_width` drops one character at a time from the end until `font.size(text)[0] <= surface width`. No ellipsis. It logs one DEBUG line only when it cuts, with both lengths, which is the only logging the contract allows.
- **Early return when `detail is None`.** That skips the detail font entirely, so normal mode builds one font.
- **Antialiased text:** `render(..., True, ...)`, per Presentation.
- Each module has `log = logging.getLogger(__name__)`, per game/CONTEXT.md. `look.py` doesn't log anything yet, but it keeps the logger the rule requires.
