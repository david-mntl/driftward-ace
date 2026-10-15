Feature: DRA-23
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/hud.md#presentation
Status: done
Linear: DRA-28

## Do
Update `game/tests/ui/test_hud.py` for the new `draw_hud(surface, run, below_overlay)`, and add tests for the hearts. The hearts are the only way the player sees the lives left, and later HUD items will be added to this layout. Test through `ui.hud.draw_hud`, `ui.debug_overlay.draw_debug_overlay` and `overlay_text_bottom`, with a `core.run.Run` built from `core.ship.spawn()` and a `core.scroll.Scroll`. Use the `pygame_headless` fixture. Read positions from the drawn pixels, never from a font size or a line height.

Existing tests:
1. Keep the five existing behaviors (normal layout, no overlap with the overlay, the gap, no jump when F3 hides the overlay, above the top line) and their sources. Call `draw_hud` with a run whose `scroll` is the same multi-digit scroll (100 scrolled ticks, 11 m). The readout tests look only at the readout: the hearts are white too, so either look only at the top-left area left of x 544, or use a run with 0 lives. Keep each test checking what it checks today. Source: systems/hud.md, Rules and Impact.

New tests, one per behavior:
2. The number of hearts equals `run.lives`: for lives 3, 2, 1 and 0, a 24 × 24 slot box with its top-left at (608, 8), (576, 8) or (544, 8) holds white (255, 255, 255) pixels exactly when its slot is filled (slots fill from the right: lives 2 fills (608, 8) and (576, 8)). No white pixel lies in the area x 536 to 639, rows 0 to 39 outside the filled boxes. Source: scope report DRA-23, Values needed (hearts: 24 × 24 px, 8 px apart, 8 px from the top and right edges, temporary stand-in approved by the Director, not in the GDD); 10-ui.md, hud_lives (top right, locked); systems/hud.md, Presentation.
3. A lost life removes the leftmost heart and the others don't move: the pixels in the filled slots for lives 2 are the same as the pixels in those slots for lives 3. Source: scope report DRA-23 ("A lost life makes one heart disappear"); systems/hud.md, Presentation.
4. The hearts don't move with the overlay and never touch it: the heart pixels are the same with `below_overlay` True and False, and no heart pixel shares a position with a green (0, 255, 0) overlay text pixel. Source: scope report DRA-13, Decision log (no overlap); systems/hud.md, Presentation.

Number values used: heart size 24, gap 8, margin 8, color (255, 255, 255) (scope report DRA-23, Values needed, approved by the Director, not in the GDD); screen_w 640, screen_h 480 (03-world-and-camera.md, guess); the DRA-13 HUD values already in the file. Read the heart values from `ui.hud`'s constants and assert them against the scope report's numbers, as the file does today for the readout values.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `ui` step runs the updated and new tests in `tests/ui/test_hud.py` next to `tests/ui/test_error_screen.py`.

## Out of scope
- The heart's exact shape. It is a temporary stand-in; the Implementation Reviewer and the Integration Engineer check it by eye.
- The Game Over box (no permanent test; checked by eye and in the browser).
- The run's rules (task DRA-23-04).
- The draw order in `game/app/`. `check.sh` has no `app` step.
- Any edit to `check.sh`, `pytest.ini` or the fixtures in `conftest.py`.
