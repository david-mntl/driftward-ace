Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-111-02-ui-developer (the electric ball's placeholder view, `ui/drifters/electric_ball_view.py`, and its import line), Verify mode, started by `/implement`.
2. **Delivered:** `docs/reports/qa/DRA-111-02-ui-developer.md` (this file). No test saved: Verify saves nothing in `game/tests/`. My inline scripts are in the session scratchpad only.
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format and typecheck PASS. `ui` PASS (46 tests, including `test_drifter_registry.py`, so the view now registers). `core` FAIL: one collection error, `tests/core/test_collision.py:1871`, `KeyError: 'hitbox'` reading `electric_ball.json`. That is the row "the tuning file ... `test_collision.py` fails to collect" in `docs/contracts/DRA-111/impact.md`, cleared by DRA-111-04. It is in the expected table, so it is not a bug. No other failure. Last line `QA: fail (core)`, the expected state until DRA-111-04.
   - Acceptance check, rerun by me from `game/` with `SDL_VIDEODRIVER=dummy`, drawn through `render_drifter` on a (10, 10, 30) surface, ball built from `game/tuning/drifters/electric_ball.json`. Every pixel equals `dim_color` of the placeholder_look color:
     - 1 ray (tick 0, level 0.25): ball (170, 80, 255), ray pixel (200, 150, 255), outline pixel (50, 38, 64), background just inside and outside the outline.
     - 2 rays (tick 30, level 0.5): outline (100, 75, 128).
     - 4 rays (tick 119, level 1.0): outline (200, 150, 255), rays 0 and 3 drawn, background just inside and outside.
     - Firing (tick 130): fill (76, 62, 109), rim (240, 220, 255), ball on top (170, 80, 255), background just outside the circle.
     - Re-hit dim (brightness 0.75): ball (128, 60, 191), fill (59, 48, 86), rim (180, 165, 191), outline and rays dimmed to (150, 113, 191).
     - Firing with the ball off screen (y -8.0): 0 pixels drawn.
     - WARNING (ticks 0, 30, 59): only the background, the glow (255, 220, 120) and the purple ball (170, 80, 255); no charge, fill or rim color on the surface.
   - Reference comparison: I wrote a second renderer straight from `view.md`, Presentation (fill image, outline, ball, rays, same rounding and `max(1, ...)` widths) and compared the whole 640 x 480 surface byte for byte with `render_drifter`. 45612 cases: 6 tunings (standard, charge 60, 1 and 7 rays, opacity 1.0, charge 1), every tick over two cycles, 9 centers (on screen, past each side, half-pixel centers, y -8.0 and 487.9), normal and re-hit dim. 0 differences. Scales 0.0, 0.04, 0.5, 14/16 and 2.0 at five ticks each: identical, no crash.
   - Edge cases that behave correctly (not bugs): the ball at y -7.9 and 487.9 fires and draws the circle, at y -8.0 and 488.0 and beyond it draws no fill or rim (same tick `current_hitbox()` is `()`); ink never leaves the pulse box of `drawn_parts()` on any of 500 frames (250 ticks, normal and dim); the firing image cache holds 2 entries after 250 ticks at both brightness values and does not grow; GONE draws nothing; the same state drawn twice gives the same pixels and `repr` of the ball is unchanged by a draw; a drifter that is not an `ElectricBall` raises `TypeError("render_electric_ball draws an ElectricBall")`; the view is registered for `ELECTRIC_BALL`.
   - Rule 9 (the look never bigger than the hitbox): the firing circle spans x 256 to 383 and y 176 to 303 around (320, 240), so the rightmost and bottom ink lie one pixel short of 384 and 304, as the implementer says. Pixel by pixel, the farthest drawn pixel is 64.41 px from the center by integer coordinates, which is the circle's own rasterisation and inside the 1.5 px `PULSE_DRAW_MARGIN` the core contract sets. A ship touching the circle from the right at 64 px overlaps the last drawn column. No visible hit outside the drawn circle.
   - Each For QA line of the review is covered above. The review has 0 must-fix findings and 2 notes with no action (parameter name `drifter`, two extra unit constants), both matching the sibling views.
4. **Assumptions:** The core failure was read against `impact.md`'s table by test name and cause. The import-order wording in `view.md` and `shared/views.md` is already fixed, per the caller.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, for task DRA-111-02. `check.sh` still ends `QA: fail (core)` until DRA-111-04 (the `test_collision.py` loader) and the later test tasks land, as `impact.md` says.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1 collection error, in `impact.md`'s expected table, cleared by DRA-111-04) · ui PASS (46 tests)
QA: fail (core)
