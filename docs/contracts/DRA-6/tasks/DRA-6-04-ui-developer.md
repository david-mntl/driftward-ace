Feature: DRA-6
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/DRA-6/DRA-6-debug-overlay.md#presentation
Status: done
Linear: DRA-12

## Do
Build the debug overlay view, exactly as the contract's Interface (`game/ui/debug_overlay.py`) and Presentation sections give it.
- `OVERLAY_COLOR = (0, 255, 0)`, `OVERLAY_FONT_SIZE = 16`, `OVERLAY_MARGIN = 4`. Source: 10-ui.md, debug_overlay_color, debug_text_font, debug_overlay_layout (guess).
- `draw_debug_overlay(surface: pygame.Surface, ship: Ship) -> None`:
  - Two 1 px lines across the full surface width (`surface.get_width()`): one on row `TOP_LINE_Y` and one on row `SCREEN_H - 1`. Read both from `core.world`.
  - Then four text lines, top-left: `x`, `y`, `vx`, `vy` with values in `f"{value:.2f}"`, e.g. `x 320.00`. Line 1's top-left corner at (4, 4), and each next line one `get_linesize()` lower. Default font at 16 px, antialiased.
  - Everything in `OVERLAY_COLOR`.
  - Create the font once, on the first call, and keep it. Never once per frame.
  - Don't fill the background, don't flip, don't change the ship, don't read the run mode or any key.
- Imports: pygame, `core.ship` and `core.world`. Never `app`.
- Follow game/CONTEXT.md: the module logger, no per-frame logging, no `print`, no broad `except`, type hints on every function.
- This task needs `game/core/` from task DRA-6-01. Start after it is built.

## Acceptance check
Run a headless script (`SDL_VIDEODRIVER=dummy`) from `game/` that fills a 640×480 surface with `ui.look.BACKGROUND`, calls `draw_debug_overlay(surface, spawn())`, and saves it as a PNG outside the repo. The image shows green (0, 255, 0) full-width lines on rows 168 and 479, and four green text lines at the top-left reading `x 320.00`, `y 240.00`, `vx 0.00`, `vy 0.00`. Put the command and the image path in the implementation report.

## Out of scope
- Deciding whether the overlay shows, the F3 toggle and the run mode. These are in `game/app/`, built by the Integration Engineer.
- The ship view (task DRA-6-02).
- Any change to `game/core/`, `game/app/`, `game/main.py`, `ui/look.py`, `ui/error_screen.py` or `ui/ship_view.py`.
- Tests.
