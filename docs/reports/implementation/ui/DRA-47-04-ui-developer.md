Status: ready-for-review
Created by: ui-developer

1. **Task:** Add the line shape to `draw_shape` (filled band and 1 px outline, unknown shape raises), from `docs/contracts/DRA-47/tasks/DRA-47-04-ui-developer.md`, by the Architect.
2. **Delivered:** `game/ui/shapes.py` (changed). Signatures of `draw_shape` and `draw_hitbox` are unchanged.
3. **Checks:**
   - `python -c "import pygame; assert pygame.IS_CE"`: passes.
   - `python -m py_compile game/ui/shapes.py`: clean.
   - `ruff check game`: all checks passed. `ruff format --check game`: 51 files formatted. `game/tests/check.sh lint`: pass.
   - Acceptance command, run from `game/` with `SDL_VIDEODRIVER=dummy python -c "..."` exactly as in the task. Output:
     ```
     True True True True True True
     True True True True
     unknown shape kind 'object'
     ```
   - Extra draw run (same dummy setup): a 45 degree band is filled at its middle, 3 px off the axis, at A's end and not beyond A. A == B filled gives a disc of radius 3 and nothing at 7 px. A == B outline is hollow with a ring pixel at 3 px. The horizontal outline is hollow at both end centers (23, 77) and has the outer arc.
   - `game/tests/check.sh typecheck`: no error in `game/ui/shapes.py` any more. 17 errors remain, in `app/tuning.py:250-251` (4) and `tests/` (13), none in my file.
   - `game/tests/check.sh ui`: 16 passed, 1 failed, `test_drifter_registry.py::test_drifter_lists_match_everywhere`. The task names it as expected until DRA-47-06.
   - No input or state change: `draw_shape` takes a surface and an immutable dataclass. It reads fields only.
   - Grep of `game/ui/shapes.py` for sleep, threading, asyncio, display, event, key, image.load, mixer, random.random(, .mp3, .wav: no hits. Grep of `game/core/` for ui imports: no hits.
4. **Assumptions:** A `width` other than 0 draws the 1 px outline for a line, as the contract says width 1 does. Circle and box still pass `width` straight to pygame. The task named the same signature, so I kept it.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, for `docs/contracts/DRA-47/tasks/DRA-47-04-ui-developer.md`. Left alone: `game/ui/debug_overlay.py` (draws lines through this module unchanged), `app/tuning.py` and test typecheck errors (Gameplay Implementer / QA), and the registry test failure (DRA-47-06).
7. **Status:** done.

## Decisions
- Dispatch is an if/elif chain with an `else: raise TypeError(f"unknown shape kind '<class name>'")`, per the contract. A line handler sits in a private `_draw_line` that picks fill or outline.
- Filled: `pygame.draw.polygon` with float corners `A+n`, `B+n`, `B-n`, `A-n` (n is the unit normal times thickness / 2), then a disc at A and one at B, center `round(x)`, radius `round(t / 2)`. A == B skips the polygon. Source: contract, Line shape.
- Outline: two 1 px side lines, then the outer half of each end circle through `pygame.draw.arc`. The arc faces `atan2(ay - by, bx - ax)` at B (counterclockwise on screen, as pygame measures angles) and that plus pi at A. A == B draws a 1 px circle. Source: contract, Line shape.
- No constants: every number comes from the line's own fields. No logging per frame; the module's `log` is unused as before.
