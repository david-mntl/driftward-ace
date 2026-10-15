Feature: DRA-23
Created by: architect
Assignee: ui-developer
Writes to: game/ui/
Contract: docs/contracts/systems/hud.md#presentation
Status: done
Linear: DRA-25

## Do
Show the lives as white hearts at the top right of the HUD, and have the HUD read the run.
- `game/ui/hud.py`, exactly the Interface and Presentation of `docs/contracts/systems/hud.md`:
  - `draw_hud(surface: pygame.Surface, run: Run, below_overlay: bool) -> None`. The readout reads `run.scroll.meters`. Its text, place, font and color don't change.
  - Add `HEART_COLOR = (255, 255, 255)`, `HEART_SIZE = 24`, `HEART_GAP = 8`, `HEART_MARGIN = 8`. Each docstring says: scope report DRA-23, hearts, temporary stand-in approved by the Director, not in the GDD (UI-01 and UI-02 are TBD).
  - Draw `run.lives` hearts. Slot `i` (0 is the rightmost) has its 24 × 24 box's top-left at (`surface.get_width() - HEART_MARGIN - HEART_SIZE - i * (HEART_SIZE + HEART_GAP)`, `HEART_MARGIN`). Fill slots 0 to `lives - 1`. So a lost life empties the leftmost heart, and the others don't move.
  - The heart: a filled heart shape in `HEART_COLOR`, two round lobes on top meeting in a point at the bottom center, drawn with `pygame.draw` shapes onto a 24 × 24 `pygame.SRCALPHA` surface. Every pixel inside the box; the shape reaches the box's left and right columns and its bottom row. Build it once, on the first draw, and keep it; blit it once per life.
  - The hearts don't depend on `below_overlay`.
  - Change the module docstring to name the hearts. Keep the rest as it is: don't fill, don't flip, don't log per frame, don't change the run, don't read the run mode or any key.
- Imports in `hud.py`: pygame, `core.run`, `ui.debug_overlay`. Never `app`. Drop the `core.scroll` import if nothing uses it.
- Follow game/CONTEXT.md: the module logger, no `print`, no broad `except`, type hints on every function. Run `game/tests/check.sh lint` before handoff.
- This task needs `game/core/run.py` from task DRA-23-01. Start after it is built.
- Expected test result: after this change every test in `tests/ui/test_hud.py` fails, because they call `draw_hud(surface, SCROLL, below_overlay)` with a scroll (`systems/hud.md`, Impact). Task DRA-23-05 updates them. `tests/ui/test_error_screen.py` must still pass. Don't edit tests. Name the failures in the implementation report.

## Acceptance check
Run a headless script (`SDL_VIDEODRIVER=dummy`) from `game/` that saves two 640×480 PNGs outside the repo, each filled with `ui.look.BACKGROUND` first:
1. Normal: `draw_hud(surface, Run(ship=spawn(), scroll=start_scroll()), below_overlay=False)`. The image shows white `0 m` at the top left and three white hearts at the top right.
2. Debug, one life: `draw_debug_overlay(surface, spawn())`, then `draw_hud(surface, Run(ship=spawn(), scroll=Scroll(ticks=130, scrolled_ticks=100), lives=1), below_overlay=True)`. The image shows the green overlay at the top left, white `11 m` below it, and one heart at the top right.

For each image the script prints, for the three slot boxes from left to right (x 544, 576, 608; rows 8 to 31), whether the box holds a (255, 255, 255) pixel: `[True, True, True]` for image 1 and `[False, False, True]` for image 2. It also prints the bounding box of the white pixels in the rightmost slot's area (x 600 to 639, rows 0 to 39), which must be inside x 608 to 631, rows 8 to 31, and span x 608 to 631. Put the command, the printed lines and both image paths in the implementation report.

## Out of scope
- Calling the HUD each frame with the run, and the draw order. These are in `game/app/`, built by the Integration Engineer.
- The Game Over box (task DRA-23-03). The blink (the app skips `draw_ship`; `ui/ship_view.py` doesn't change).
- The life-lost feedback (the breaking heart, the flash). Out of DRA-23 scope.
- SCORE, LV, GRAZE, BEST.
- Any change to `game/core/`, `game/app/`, `game/main.py`, `ui/debug_overlay.py`, `ui/look.py`, `ui/error_screen.py`, `ui/ship_view.py` or `ui/starfield.py`.
- Tests.
