Status: ready-for-review
Created by: ui-developer

1. **Task:** Draw the ship as its own inverted-T hitbox through a shared `ui/shapes.py` helper. Task `docs/contracts/DRA-29/tasks/DRA-29-04-ui-developer.md`, from the Architect.
2. **Delivered:**
   - `/workspace/game/ui/shapes.py` (new): `draw_shape`, `draw_hitbox`.
   - `/workspace/game/ui/ship_view.py` (changed): `draw_ship` now calls `draw_hitbox(surface, SHIP_COLOR, ship_hitbox(ship))`. Signature and `SHIP_COLOR` kept. Docstrings no longer name a rectangle.
3. **Checks** (run from `game/`):
   - IS_CE: `python -c "import pygame; assert pygame.IS_CE"` passes.
   - `python -m py_compile ui/shapes.py ui/ship_view.py`: clean.
   - `tests/check.sh lint`: PASS (ruff check and format). `tests/check.sh typecheck`: PASS (mypy strict, 33 files). `tests/check.sh ui`: 11 passed.
   - Acceptance command, exact text from the task. Output:
     ```
     [True, False, False, True, True, True, True, False, False]
     624
     ```
   - Follows the state: ship moved +20 px in x (via `dataclasses.replace`), drew again. Pixel (334, 230) went from black to white. Ship `repr` identical before and after the draw. Circle fill and 1 px box outline checked on a 100 x 100 surface: circle center red and a pixel outside it black; box outline edge red and its center black.
   - Grep of `ui/shapes.py` and `ui/ship_view.py` for `time.sleep`, `threading`, `asyncio`, `pygame.display`, `pygame.event`, `pygame.key`, `pygame.image.load`, `pygame.mixer`, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for ui imports: no hits.
   - Only noise: ALSA "cannot find card" lines from `pygame.init()` in the sandbox, as in the acceptance command.
4. **Assumptions:** None. A circle is drawn with `round(r)` as its radius, as the task says. A radius that rounds to 0 draws nothing, and no object has one.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-29/tasks/DRA-29-04-ui-developer.md`. I left `game/ui/debug_overlay.py` alone (task DRA-29-06 will use `draw_hitbox` there). No screenshot saved.
7. **Status:** done.

## Decisions
- `draw_shape` branches on `isinstance(shape, Circle)` and hands off to two private helpers, `_draw_box` and `_draw_circle`. The result is two small functions and no flag. Rounding follows the task text exactly: `round(cx - w / 2)` for the top-left, `round(w)` for the size.
- `width` passes straight to pygame's `draw.rect` and `draw.circle`: 0 fills, 1 gives a 1 px outline. Source: task Do, objects.md `ui/shapes.py`.
- Colour stays `SHIP_COLOR` (255, 255, 255). Source: 04-ship.md placeholder_look (guess). No new numbers were added.
- `draw_ship` reads the ship only through `ship_hitbox(ship)`. It copies no position and no size.
- Imports follow the contract: pygame, `core.collision`, `core.ship`, `ui.shapes`. Nothing from `app`.
