Feature: DRA-19
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/DRA-6/DRA-6-debug-overlay.md#presentation
Status: done
Linear: DRA-21

## Do
Make the debug overlay show `0.00`, never `-0.00`, for a number that rounds to zero.
- `game/ui/debug_overlay.py`: format each of the four numbers with `f"{value:z.2f}"` instead of `f"{value:.2f}"`. Two decimals as before. A negative that doesn't round to zero keeps its minus sign, e.g. `vy -0.26`. Source: `docs/contracts/DRA-6/DRA-6-debug-overlay.md`, Presentation; 10-ui.md, debug_overlay_layout (guess); scope report DRA-19, item 3; review DRA-6-04-ui-developer, finding 1.
- Update the docstrings that name the format (`_draw_text` and, if it does, `draw_debug_overlay`).
- Nothing else in the overlay changes: constants, lines, layout, color, font, `overlay_text_bottom()`.
- Follow game/CONTEXT.md. Run `game/tests/check.sh lint` and `game/tests/check.sh ui` before handoff. The existing tests must pass unchanged.

## Acceptance check
Run a headless script (`SDL_VIDEODRIVER=dummy`) from `game/` that fills a 640×480 surface with `ui.look.BACKGROUND`, calls `draw_debug_overlay(surface, Ship(x=300.0, y=184.0, vx=-0.001, vy=-0.26))`, and saves it as a PNG outside the repo. The four green text lines read `x 300.00`, `y 184.00`, `vx 0.00` and `vy -0.26`: no minus on the vx line, a minus on the vy line. Put the command and the image path in the implementation report.

## Out of scope
- Any change to `core.ship`: the value stays as it is, only its display changes.
- Showing or hiding the overlay, the F3 toggle, the run mode. These are in `game/app/`.
- The HUD docstring (task DRA-19-03).
- Passing fonts in, making views into classes, any other refactor.
- Tests.
