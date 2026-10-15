Status: ready-for-review
Created by: ui-developer

1. **Task:** Add `draw_debug_hitboxes(surface, run)` to the debug overlay (graze and hitbox outlines, object labels). Task `docs/contracts/DRA-29/tasks/DRA-29-06-ui-developer.md`, from the Architect.
2. **Delivered:** `game/ui/debug_overlay.py` (new `draw_debug_hitboxes`, private `_draw_label` and `_clamp_inside`, new imports `core.objects.base`, `core.run`, `ui.shapes`, module docstring names the new function). `draw_debug_overlay`, `overlay_text_bottom` and the constants are untouched.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: pass (pygame-ce 2.5.8).
   - `python -m py_compile game/ui/debug_overlay.py`: clean.
   - `game/tests/check.sh lint`: pass (ruff check and format). `typecheck`: pass (mypy strict, 37 files). `ui`: 11 passed, `test_hud.py` unchanged.
   - Acceptance command from `game/` (exact text in the task file), output:
     ```
     active True True False
     True True
     ```
     Matches the expected lines.
   - Follows state: a meteorite in WARNING at (320, -14) draws no hitbox (empty `current_hitbox`), and its label lands against the top edge (green ink in rows 0 to 15). `repr(run)` identical before and after the draw: core not mutated.
   - Grep of `game/ui/debug_overlay.py` for sleep, threading, asyncio, pygame.display/event/key, image.load, mixer, random.random(, .mp3, .wav: no hits. Grep of `game/core/` for `game.ui` or `ui` imports: no hits.
   - Screenshot: `/tmp/claude-1000/-workspace/c95abc97-1f22-42a3-a4b4-1aa1c00ef104/scratchpad/hitboxes.png`.
4. **Assumptions:** The clamp is `max(0, min(wanted, size - label size))` on each axis, which gives 0 when the label is bigger, as the task says. Labels for every object draw last, in `run.objects` order.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-29/tasks/DRA-29-06-ui-developer.md`. Left alone: `game/app/frame.py` (Integration Engineer calls the new function) and all tests.
7. **Status:** done.

## Decisions
- One function with three loops over `run.objects` (graze, hitbox, label) keeps the contract's draw order with no extra structure. Source: debug-overlay.md, Presentation, draw order.
- The ship's hitbox is drawn from `ship_hitbox(run.ship)` with no visibility check: the blink is a look only. Source: debug-overlay.md, Presentation.
- Label text, color, font (the overlay's cached `_overlay_font()`) and position follow debug-overlay.md, Presentation. The `z.2f` format matches the four text lines. No new numbers.
- Outlines use `ui.shapes.draw_hitbox(surface, OVERLAY_COLOR, hitbox, 1)`, so no rounding or shape logic is copied into the overlay.
