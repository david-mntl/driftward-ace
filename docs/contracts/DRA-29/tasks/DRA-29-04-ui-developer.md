Feature: DRA-29
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/ship.md#presentation
Status: done
Linear: DRA-33

## Do
Draw the placeholder ship as its own inverted-T hitbox, through a small shared helper that draws hitbox shapes. Needs task DRA-29-01 (`core.collision`, `core.ship.ship_hitbox`) done first.
- `game/ui/shapes.py` (new), the `ui/shapes.py` block of `docs/contracts/systems/objects.md`, Interface:
  - `draw_shape(surface, color, shape, width=0)`: a placed `Box` as the rectangle with top-left `(round(cx - w / 2), round(cy - h / 2))` and size `round(w) × round(h)`; a placed `Circle` with center `(round(cx), round(cy))` and radius `round(r)`. `width` 0 fills, 1 draws a 1 px outline (pygame's `width` argument).
  - `draw_hitbox(surface, color, hitbox, width=0)`: `draw_shape` for every shape, in order.
  - Imports pygame and `core.collision`. Never app. Draws only: never fills the background, flips, logs per frame or catches an error.
- `game/ui/ship_view.py`, from `docs/contracts/systems/ship.md`, Presentation and Impact:
  - `draw_ship(surface, ship)` keeps its signature and `SHIP_COLOR`. It now draws `draw_hitbox(surface, SHIP_COLOR, ship_hitbox(ship))`: the bar and the foot, filled, white.
  - The module and function docstrings stop naming a rectangle and say the look is the hitbox.
  - Imports pygame, `core.ship`, `ui.shapes`. Never app.
- Follow game/CONTEXT.md. Run `game/tests/check.sh lint`, `typecheck` and `ui` before handoff. Every existing UI test must still pass.

## Acceptance check
From `game/`, run:
```
SDL_VIDEODRIVER=dummy python -c "
import pygame; pygame.init()
from core.ship import spawn
from ui.ship_view import draw_ship
s = pygame.Surface((640, 480)); s.fill((0, 0, 0)); draw_ship(s, spawn())
print([tuple(s.get_at(p))[:3] == (255, 255, 255) for p in [(320, 230), (308, 230), (331, 230), (308, 250), (331, 250), (304, 255), (335, 255), (303, 250), (336, 250)]])
print(sum(1 for x in range(640) for y in range(480) if tuple(s.get_at((x, y)))[:3] == (255, 255, 255)))
"
```
It prints:
- `[True, False, False, True, True, True, True, False, False]`: the bar is white at the center; the two upper corners of the 32 × 32 square are empty; the foot spans x 304 to 335 along rows 244 to 255.
- `624`: exactly the bar (12 × 32) plus the foot (32 × 12) less their 12 × 12 overlap.
Put the command and its output in the implementation report.

## Out of scope
- The ship's hitbox itself and `core/` (task DRA-29-01).
- Object views and the entry warning (task DRA-29-05). Debug outlines (task DRA-29-06).
- The blink: the app decides when to call `draw_ship` (unchanged).
- Sprite art, the thrust flame. Tests (task DRA-29-09).
