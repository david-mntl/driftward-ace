Status: ready-for-review
Created by: ui-developer

1. **Task:** Build the floating island view and register it (`docs/contracts/DRA-86/tasks/DRA-86-06-ui-developer.md`, from the Architect).
2. **Delivered:** `game/ui/drifters/floating_island_view.py` (new): `render_floating_island`, the three constants, a pre-rendered image cache and private helpers for the inset. `game/ui/drifters/__init__.py` (changed): one import line.
3. **Checks:**
   - Acceptance command, run from `game/` with `SDL_VIDEODRIVER=dummy`, exactly as in the task. Output (ALSA noise lines left out):
     ```
     [(35, 90, 45), (35, 90, 45), (70, 160, 80), (35, 90, 45), (70, 160, 80), (35, 90, 45)]
     160 479 240 359
     [(35, 90, 45), (35, 90, 45), (70, 160, 80), (70, 160, 80), (0, 0, 0)]
     160 479 240 359
     [(35, 90, 45), (70, 160, 80), (70, 160, 80), (35, 90, 45), (35, 90, 45), (0, 0, 0)]
     160 478 240 359
     ```
     All six lines match the task's expected values.
   - Other contract examples, same kind of draw run: T at (320, 300): (320, 330) fill, (301, 330) edge, (250, 330) nothing. L with invert: (300, 250) fill, (300, 300) nothing. Triangle with invert: (160, 359) edge, (161, 359) nothing, (467, 244) edge, (468, 244) nothing, bounds `160 478 240 359`.
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8). `py_compile` on both changed files: clean.
   - `game/tests/check.sh lint`: PASS (`ruff check`, `ruff format --check`, 75 files). `game/tests/check.sh ui`: 46 passed, including `test_drifter_registry.py`.
   - `typecheck`: FAIL with 6 errors, all in `tests/core/test_collision.py` (a test narrows `Shape` without `Polygon`, task DRA-86-07). `mypy --strict --explicit-package-bases` shows none in `game/ui` or `game/core`.
   - Follows state: drawing the same island twice gives identical bytes; the cache holds 3 entries after the three looks above and stays at 3 after two more draws (built once per key). The island's repr is unchanged by the draw. Moving the island 50 px down moves the picture. At brightness 0.75 the fill is (53, 120, 60). `scale` 0.5 raises `ValueError("render_floating_island draws at full size only")`; a non-island raises `TypeError("render_floating_island draws a FloatingIsland")`.
   - Grep of `game/ui/drifters/floating_island_view.py` for sleep, threading, asyncio, pygame.display/event/key/image.load/mixer, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for ui imports: no hits.
   - Screenshot of the L, the T and the inverted triangle: `/tmp/claude-1000/-workspace/1cb2e3c9-cba9-427d-b24d-f1e7aee6523b/scratchpad/islands.png`.
4. **Assumptions:** None beyond the contract. The cache is a module-level dict, as the contract's Presentation asks and as `entry_warning.py` does; it holds drawing images only, no game state.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-86/tasks/DRA-86-06-ui-developer.md`. Left alone: `game/ui/shapes.py`, the registry, the entry warning, the debug overlay, every test, core and tuning files.
7. **Status:** done.

## Decisions
- The look is one `SRCALPHA` image per key `(hitbox, width, height, brightness)`, built on the first draw and blitted after. Source: contract, Presentation, Floating island, Image.
- Edge is the whole shape in the edge color, then each inset shape in the fill color on top. No outline is drawn, so no line crosses the L's or T's joint and nothing goes outside the shape. Source: contract, Rationale, "The edge is the shape less its inset".
- Both passes use `ui.shapes.draw_shape` on the hitbox placed by `core.collision.place_hitbox` at half the size. The view works out no geometry rule except the inset.
- Box inset: width and height each less `2 * ISLAND_EDGE_WIDTH`. Polygon inset: each edge line moved inward along its unit normal, each corner where neighbouring moved lines meet. The inward side comes from the shoelace sign, so it works for either point order (invert reverses it).
- Any shape other than a Box or Polygon raises `TypeError`. Core builds only these two for an island.
- Placement: top-left at `round(center - size / 2)`. Source: contract, Presentation, Place.
- Colors (70, 160, 80) and (35, 90, 45) and the 2 px edge: contract constants, drifters/05-floating-islands.md, placeholder_look (guess). No tuning key: they stay in the view per the contract's Rationale.
