Feature: DRA-6
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/DRA-6/DRA-6-ship.md#presentation
Status: done
Linear: DRA-10

## Do
Build the ship view, exactly as the contract's Interface (`game/ui/ship_view.py`) and Presentation sections give it.
- `SHIP_COLOR = (255, 255, 255)`. Source: 04-ship.md, placeholder_look (guess).
- `draw_ship(surface: pygame.Surface, ship: Ship) -> None`: a filled `SHIP_W` × `SHIP_H` rectangle in `SHIP_COLOR`, top-left corner at `(round(ship.x - SHIP_W / 2), round(ship.y - SHIP_H / 2))`.
  - Read `SHIP_W`, `SHIP_H` and `Ship` from `core.ship`. Never hard-code 32.
  - Don't fill the background, don't flip, don't change the ship, don't read the run mode.
- Imports: pygame and `core.ship`. Never `app`.
- Follow game/CONTEXT.md: the module logger, no per-frame logging, no `print`, no broad `except`, type hints on every function.
- This task needs `game/core/ship.py` from task DRA-6-01. Start after it is built.

## Acceptance check
Run a headless script (`SDL_VIDEODRIVER=dummy`) from `game/` that fills a 640×480 surface with `ui.look.BACKGROUND`, calls `draw_ship(surface, spawn())`, and saves it as a PNG outside the repo. The image shows one white 32×32 square on black, its pixels running from (304, 224) to (335, 255), centered on the screen. Put the command and the image path in the implementation report.

## Out of scope
- The debug overlay (task DRA-6-04).
- Calling the view each frame, the background fill in the loop, and the display flip. These are in `game/app/`, built by the Integration Engineer.
- Ship art, thrust flame, blink, burst. Out of DRA-6 scope.
- Any change to `game/core/`, `game/app/`, `game/main.py`, `ui/look.py` or `ui/error_screen.py`.
- Tests.
