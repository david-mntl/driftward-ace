Feature: DRA-5
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/DRA-5/DRA-5-app.md#presentation
Status: done
Linear: DRA-7

## Do
Build the error screen view and the shared background color, exactly as the contract's Interface (`game/ui/look.py`, `game/ui/error_screen.py`) and Presentation sections give them.
- `game/ui/look.py`: `BACKGROUND = (0, 0, 0)`. Source: 12-art-and-audio.md, placeholder_bg (guess).
- `game/ui/error_screen.py`: `draw_error_screen(surface: pygame.Surface, detail: str | None) -> None`.
  - Fill the whole surface with `BACKGROUND`.
  - Draw `Something broke. Reload the page.` in `pygame.font.Font(None, 24)`, color (255, 255, 255), centered on the surface. Source: 10-ui.md, error_screen, error_text_font, error_layout, error_text_color.
  - If `detail` is a string, draw it in `pygame.font.Font(None, 16)`, same color, centered horizontally. Its top is one main-font line-height (`get_linesize()`) below the main line's top. Source: 10-ui.md, error_layout, debug_text_font.
  - If `detail` is wider than the surface, cut characters from the end until it fits. No ellipsis. Source: 10-ui.md, error_debug_line.
  - Center with `surface.get_size()`. Don't hard-code 640×480.
- Follow game/CONTEXT.md: the module logger, no `print`, no broad `except`, type hints on every function.

## Acceptance check
Run a headless script (`SDL_VIDEODRIVER=dummy`) that calls `draw_error_screen` on a 640×480 surface twice, once with `detail=None` and once with `detail="ValueError: boom"`, and saves each as a PNG outside the repo. The first image shows one white centered line on black. The second shows the same line with `ValueError: boom` centered just below it. Put the command and the image paths in the implementation report.

## Out of scope
- Catching the error, logging the traceback, choosing `detail`, and flipping the display. These are in `game/app/` and the Integration Engineer builds them.
- The debug overlay and the ship view (DRA-6).
- Any change to `game/core/`, `game/app/` or `game/main.py`.
- Tests (task DRA-5-02).
