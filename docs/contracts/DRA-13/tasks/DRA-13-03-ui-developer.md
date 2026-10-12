Feature: DRA-13
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/DRA-13/DRA-13-hud.md#presentation
Status: done
Linear: DRA-16

## Do
Build the HUD with the meters readout, and the one helper it needs from the debug overlay.
- `game/ui/debug_overlay.py`: add `overlay_text_bottom() -> int`, as in `docs/contracts/DRA-6/DRA-6-debug-overlay.md`, Interface and Presentation. It returns `OVERLAY_MARGIN + 3 * linesize + max(linesize, font height)`, using the overlay's existing cached font. It draws nothing. Change nothing else in the overlay: same constants, same lines, same text.
- `game/ui/hud.py`: exactly the Interface and Presentation of `docs/contracts/DRA-13/DRA-13-hud.md`.
  - `HUD_COLOR = (255, 255, 255)`, `HUD_FONT_SIZE = 16`, `HUD_MARGIN = 4`, `HUD_LINE_SPACING = 20`, `HUD_TOP = 4`, `HUD_OVERLAY_GAP = 4`. Each docstring says: scope report DRA-13, temporary stand-in or HUD layout approved by the Director, not in the GDD (UI-01 is TBD).
  - `draw_hud(surface: pygame.Surface, scroll: Scroll, below_overlay: bool) -> None`:
    - `hud_top = HUD_TOP` when `below_overlay` is False, `overlay_text_bottom() + HUD_OVERLAY_GAP` when True.
    - Line 1, at `hud_top`, stays empty.
    - Line 2: `f"{scroll.meters} m"`, top-left at (`HUD_MARGIN`, `hud_top + HUD_LINE_SPACING`), default font at 16 px, antialiased, in `HUD_COLOR`.
  - Create the font once, on the first call, and keep it. Never once per frame.
  - Read only `scroll.meters`. Don't fill, don't flip, don't log per frame, don't change the scroll, don't read the run mode or any key.
- Imports in `hud.py`: pygame, `core.scroll`, `ui.debug_overlay`. Never `app`.
- Follow game/CONTEXT.md: the module logger, no `print`, no broad `except`, type hints on every function. Run `game/tests/check.sh lint` before handoff.
- This task needs `game/core/scroll.py` from task DRA-13-01. Start after it is built.

## Acceptance check
Run a headless script (`SDL_VIDEODRIVER=dummy`) from `game/` that saves two 640×480 PNGs outside the repo, each filled with `ui.look.BACKGROUND` first:
1. Normal: `draw_hud(surface, start_scroll(), below_overlay=False)`. The image shows white `0 m` at the top-left, blitted at (4, 24), and nothing above it.
2. Debug: `draw_debug_overlay(surface, spawn())`, then `draw_hud(surface, Scroll(ticks=130, scrolled_ticks=100), below_overlay=True)`. The image shows the four green overlay lines at the top-left and white `11 m` below them.
The script also prints `overlay_text_bottom()`, the lowest row with a (0, 255, 0) pixel above row 168, and the highest row with a (255, 255, 255) pixel. The white row is greater than the green row: no overlap. Put the command, the printed numbers and both image paths in the implementation report.

## Out of scope
- Calling the HUD each frame, choosing `below_overlay` and the draw order. These are in `game/app/`, built by the Integration Engineer.
- SCORE, lives, LV, GRAZE, BEST. Out of DRA-13 scope.
- Any new content in the debug overlay. It keeps exactly what DRA-6 shows.
- The starfield (task DRA-13-02).
- Any change to `game/core/`, `game/app/`, `game/main.py`, `ui/look.py`, `ui/error_screen.py`, `ui/ship_view.py` or `ui/starfield.py`.
- Tests.
