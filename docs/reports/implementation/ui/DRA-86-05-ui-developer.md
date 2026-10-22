Status: ready-for-review
Created by: ui-developer

1. **Task:** Add the `Polygon` shape to `draw_shape`, filled by the pixel-center rule and outlined at 1 px (`docs/contracts/DRA-86/tasks/DRA-86-05-ui-developer.md`, from the Architect).
2. **Delivered:** `game/ui/shapes.py` (changed): `draw_shape` branch for `Polygon`, new private `_draw_polygon`, `_fill_polygon`, `_row_crossings`. Circle, box, line and `draw_hitbox` untouched.
3. **Checks:**
   - Acceptance command, run from `game/` with `SDL_VIDEODRIVER=dummy`, exactly as in the task. Output:
     ```
     [160] 160 467 478 []
     100 (100, 100) (109, 109)
     (0, 255, 0) (0, 0, 0)
     ```
     All three lines match the expected ones.
   - `python -c "import pygame; assert pygame.IS_CE"`: passes (pygame-ce 2.5.8). `py_compile ui/shapes.py`: clean.
   - `ruff check game`: all passed. `ruff format --check game`: 74 files formatted.
   - Follows state / no mutation: drawing the same polygon twice gives identical bytes; a polygon with one corner moved draws a different picture; the polygon's `points` are equal before and after. An unknown shape still raises `TypeError: unknown shape kind 'object'`.
   - `game/tests/check.sh lint`: PASS (lint, format). `typecheck`: FAIL, 6 errors, all in `tests/core/test_collision.py` lines 589 and 596 (a test narrows `Shape` without `Polygon`); none in `game/ui`. `core`: FAIL, 5 tests (`test_collision.py` shape-kind table and the island touching distance, `test_wave_files.py` placement-type message), all core-side or test-side. `ui`: FAIL, 1 test: `test_drifter_registry.py::test_drifter_lists_match_everywhere` (no island tuning file and no island view yet, task DRA-86-06). None touches `game/ui/shapes.py`.
   - Grep of `game/ui/shapes.py` for sleep, threading, asyncio, pygame.display/event/key/image.load/mixer, `random.random(`, `.mp3`, `.wav`: no hits. Grep of `game/core/` for ui imports: no hits.
4. **Assumptions:** The remaining check.sh failures are the ones the contract's DRA-86 Impact table expects; I did not compare them against the table line by line for the test-file ones (typecheck and core failures live in test files I may not edit).
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-86/tasks/DRA-86-05-ui-developer.md`. Left alone: the island view (DRA-86-06), the debug overlay, all tests and core files.
7. **Status:** done.

## Decisions
- Fill follows the contract's pixel-center rule exactly: rows `ceil(min_y - 0.5)` to `floor(max_y - 0.5)`, one `pygame.draw.rect` per row, columns `ceil(xl - 0.5)` to `floor(xr - 0.5)`, skipped when empty. Source: drifters.md, Presentation, Polygon shape.
- `_row_crossings` takes every edge whose y range contains the row center (ends included). A flat edge on the row gives both its ends. Min and max of the crossings give `xl` and `xr`, so a convex polygon needs no sorting.
- Any `width` other than 0 draws the 1 px outline from whole-px rounded corners, the same convention the line shape uses for its non-zero width.
- No constants added: 0.5 is the pixel-center offset named in the contract.
