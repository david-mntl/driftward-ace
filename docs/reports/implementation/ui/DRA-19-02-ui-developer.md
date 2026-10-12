Status: ready-for-review
Created by: ui-developer

1. **Task:** DRA-19-02 (architect): debug overlay shows `0.00`, never `-0.00`.
2. **Delivered:** `game/ui/debug_overlay.py`. The four numbers use `{value:z.2f}`. The `_draw_text` docstring names the new format. `draw_debug_overlay`'s docstring says only "two decimals", so it is unchanged.
3. **Checks:**
   - `game/tests/check.sh lint`: PASS (lint, format).
   - `game/tests/check.sh ui`: PASS, 8 passed, tests unchanged.
   - Headless run from `game/` (`SDL_VIDEODRIVER=dummy`), 640x480 filled with `BACKGROUND`, `draw_debug_overlay(surface, Ship(x=300.0, y=184.0, vx=-0.001, vy=-0.26))`, saved to `/tmp/claude-1000/-workspace/91f627b4-dcd2-4d42-8588-06dcf2e39371/scratchpad/overlay.png`. The image reads `x 300.00`, `y 184.00`, `vx 0.00`, `vy -0.26`. The vx line has no minus and the vy line has one.
   - Format check: `f'{-0.001:z.2f}'` gives `0.00`; `f'{-0.26:z.2f}'` gives `-0.26`.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Implementation Reviewer, task `docs/contracts/DRA-19/tasks/DRA-19-02-ui-developer.md`. `game/ui/hud.py` shows an uncommitted docstring change that is not mine (likely task DRA-19-03). I left it alone.
7. **Status:** done.

## Decisions
- Used the `z` format option as the task says. Python 3.11+ supports it, and the 3.12 interpreter here runs it. Not run under the pygbag runtime.
- No constants, layout or tests were changed.
