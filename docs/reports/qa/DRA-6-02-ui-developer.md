Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-6-02-ui-developer (ship view, `game/ui/ship_view.py`) against `docs/contracts/DRA-6/DRA-6-ship.md`, Interface and Presentation. Verify mode, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-6-02-ui-developer.md
3. **Checks:** all inline headless runs from `game/` (`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python - <<EOF ... EOF`). Nothing saved in `game/tests/`.
   - check.sh: `QA: pass`.
   - Acceptance check: 640×480 filled with `ui.look.BACKGROUND`, `draw_ship(surface, spawn())`. Non-background pixels x 304..335, y 224..255, 1024 pixels, every one (255, 255, 255). Center (319.5, 239.5), the screen middle. Image: `/tmp/claude-1000/-workspace/bb96ec7a-9d42-4f32-a24b-9859640cd1af/scratchpad/qa_ship_spawn.png`. Expected from the task's Acceptance check, 04-ship.md ship_w, ship_h, placeholder_look, and 03-world-and-camera.md ship_start.
   - Walls (For QA): x 16.0 draws columns 0..31, x 624.0 draws 608..639, 1024 pixels each. No clipped column.
   - Top line: y 184 (top edge on TOP_LINE_Y 168) draws rows 168..199, 1024 pixels.
   - Floor (For QA): y 470 draws rows 454..479, 832 pixels, no error. Top edge 479.4 draws 1 row (32 pixels). Top edge 479.99 and 480.0 draw nothing, no error. This follows the contract's `round` on the corner.
   - Fully off-screen (x -100, y -100) and a 100×100 surface: nothing drawn, no error.
   - Half-pixel corners (For QA): x 100.5 to column 84, x 101.5 to column 86, x 100.5001 to 85, x 100.4999 to 84. That is Python `round`, which the contract's Presentation names, so it is the contract's behavior, not a bug. Acceptable as written. x -0.5 draws columns 0..15 (512 pixels), no error.
   - No background fill (For QA): on a (10, 20, 30) surface the corner stays (10, 20, 30). Over a pre-drawn green line, exactly 1024 pixels change, all inside the square. SRCALPHA surface: square opaque white, outside stays (0, 0, 0, 0).
   - Ship unchanged: equals its deep copy after the draw. Same ship drawn twice: byte-identical pixels.
   - Determinism: a 300-tick run with `step` and mixed thrust, each tick drawn, run twice: all 300 frames byte-identical. Every fully on-screen frame drew exactly 1024 pixels.
   - Static: `ship_view.py` has no hard-coded 32, no `app` import, no run-mode read, no fill, flip, print, except, sleep, event or key call (the only grep hits are docstrings). Interface matches the contract line by line. Lint and format pass.
   - Review: 0 must-fix. The four notes need no QA action. Note 4 (file count) is settled: check.sh's format step reports 18 files.
4. **Assumptions:** none.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer. Calling `draw_ship` once per frame, after the background fill and before the flip, is yours in `game/app/`.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS (18 files already formatted) · core SKIP (no tests yet) · ui PASS (3 passed)
QA: pass
