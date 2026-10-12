Feature: DRA-13
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/DRA-13/DRA-13-hud.md#rules
Status: done
Linear: DRA-18

## Do
Write permanent tests for the HUD layout in `game/tests/ui/test_hud.py`. The Director ruled that the HUD and the debug overlay must never overlap, and later HUD items will be added to this layout, so this guards it. Test through `ui.hud.draw_hud`, `ui.debug_overlay.draw_debug_overlay` and `ui.debug_overlay.overlay_text_bottom`, with states from `core.scroll` and `core.ship.spawn()`. Use the `pygame_headless` fixture. Read positions from the drawn pixels (`pygame.image.tobytes`), as `ui/test_error_screen.py` does. Never hard-code a font size or a line height. Use a scroll with a multi-digit meters value (for example 100 scrolled ticks, 11 m) so the readout has width.

Test each behavior:
1. Normal layout: with `below_overlay=False`, every white (255, 255, 255) pixel is at or below row `hud_top + hud_line_spacing` (24) and at or right of column `hud_margin` (4), and nothing is drawn on HUD line 1. Source: scope report DRA-13, HUD layout (normal mode, temporary stand-in approved by the Director).
2. No overlap in debug mode: draw the overlay and the HUD (`below_overlay=True`) on separate surfaces of the same size. Every white HUD pixel is on a row below every green (0, 255, 0) overlay text pixel. Ignore the overlay's full-width lines on row 168 and row 479. Source: scope report DRA-13, Decision log (Director: "Overlap is not acceptable"); 10-ui.md, debug_overlay_layout.
3. The gap holds: in debug mode, the highest white HUD pixel row is at least `overlay_text_bottom() + hud_overlay_gap + hud_line_spacing`, and `overlay_text_bottom()` is below every green overlay text pixel. Source: scope report DRA-13, HUD layout (debug mode: 4 px below the overlay's fourth line).
4. The readout never jumps when F3 hides the overlay: `draw_hud` with `below_overlay=True` gives exactly the same pixels on a surface with the overlay drawn under it as on one without, outside the overlay's own pixels. Source: scope report DRA-13, HUD layout (the HUD stays moved down while F3 hides the overlay).
5. The HUD stays clear of the top line: in both layouts, every white HUD pixel is above row `screen_h × top_line_ratio` (168). Source: 10-ui.md, rule 1; 03-world-and-camera.md, rule 2.

Number values used: HUD left margin 4, line spacing 20, normal first line at y 4, debug gap 4 (scope report DRA-13, HUD layout, approved by the Director, not in the GDD); readout color (255, 255, 255) (scope report DRA-13, temporary stand-in); overlay color (0, 255, 0) (10-ui.md, debug_overlay_color, guess); screen_h 480 (guess) and top_line_ratio 0.35 (locked) (03-world-and-camera.md). Read the HUD values from `ui.hud`'s constants or copy them with their source, as `tests/core/test_ship.py` does for the GDD values.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `ui` step runs the new tests in `tests/ui/test_hud.py` next to the existing `tests/ui/test_error_screen.py`.

## Out of scope
- The text of the readout. Fonts differ between builds, so the Implementation Reviewer and the Integration Engineer check `0 m` and `11 m` by eye.
- The starfield. The Integration Engineer checks it in the browser.
- The draw order and `below_overlay` in `game/app/`. `check.sh` has no `app` step.
- Any edit to `check.sh`, `pytest.ini` or the fixtures in `conftest.py`.
