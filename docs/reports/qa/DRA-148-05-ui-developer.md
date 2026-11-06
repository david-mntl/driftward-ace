Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-148-05-ui-developer (the HUD level pop, `LevelSlot`, `level_slot`, the optional look and banner arguments in `game/ui/hud.py`), started by /implement. Verify mode.
2. **Delivered:** docs/reports/qa/DRA-148-05-ui-developer.md. Nothing saved in `game/tests/`.
3. **Checks:**
   - `game/tests/check.sh`: QA: pass (env, lint, format, typecheck, core, ui; 786 ui tests passed).
   - Acceptance check reproduced with the game's `hud.json` rules and art, and the pop values of the real `game/tuning/level_up.json` (the other look sections are filler, the pop does not read them). Scripts, outside the repo: `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa05/edge.py`, `eq.py`, `odd.py`. Run from `game/` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 <script>`.
   - Old HUD equality: the committed `HEAD:game/ui/hud.py` against the new view with no arguments, with a banner and no look, and with a look and no banner: 216 whole-window draws (levels 1 to 8 x lives 0, 1, 5 x ticks 0, 5, 99), 0 mismatches.
   - Every level 2 to 8 (previous level = level - 1), every banner age 0 to 149 (arrival 60, lifetime 150): before arrival the whole window equals a plain HUD of the previous level; from arrival the only changed pixels (against a plain HUD of the new level) are inside the level box (704, 329, 66 x 75); on the last pop tick (age 83) and every age after, the whole window equals the plain new-level HUD (0 differences). The 1.45x arrival number (23 x 51 for a 16 x 35 digit) leaves ink inside the box.
   - New climb bar: level 7 and 8 at arrival show (255, 255, 255) on bar 7 and 8 (indexes 6 and 7), the bar before keeps its ramp color.
   - Pause and repeat: the same banner age drawn at view ticks 100 and 300 gives the same pop pixels (the pop reads only the banner's age); drawing ages in a shuffled order and repeating an age gives equal bytes; two fresh views give equal bytes for levels 2, 5, 8 across the pop.
   - Cost: after `__init__` (and the first draw), 240 draws across ages 40 to 119 and levels 2, 5, 8: 0 `pygame.Surface` constructions, 0 font renders, 0 `smoothscale`/`scale`/`rotate`/`rotozoom` calls.
   - Odd looks do not raise and still end on the plain HUD: `steps` 1 and 2; every tick count 1; `box_corner_cut` 0 and 60; `box_flash_width` 4 and 40; `start_scale` 3.0.
   - Box outline against the baked outline at arrival (flash alpha 255, shipped width 1): B1 below.
4. **Assumptions:** The pop numbers used are the shipped `game/tuning/level_up.json` pop section. The baked outline pixels were found by color (fuchsia, red above 90, green below 20, blue above 80) in the plain level-3 HUD's box.
5. **Documentation differences:** None. One note for the Architect, not a bug of this task: the flight (view.md, The flight) ends in the tier color, and the pop's first frame is the white flash color, so the "same image where it lands" sentence holds for the size only. The Reviewer's F1 (the import of `ui.level_up_motion` missing in the contract's import line) stands.
6. **Next:** UI Developer, Fix mode, on `docs/reports/qa/DRA-148-05-ui-developer.md`, bug B1. Then QA re-tests. The Integration Engineer does not get this task until B1 is closed.
7. **Status:** done.

## Bugs
- **B1** `game/ui/hud.py:402-409` (`_box_outline`), UI Developer. The box flash's two cut corners do not line up with the baked outline. At arrival the flash is yellow and the baked fuchsia diagonal shows beside it: 7 baked pixels uncovered outside the number's rectangle (4 at the top-right: (766, 333) to (769, 336), 3 at the bottom-left: (704, 396), (705, 397), (706, 398)), 15 counting the ones the number hides. The flash's diagonal drifts off the baked 45 degree line by up to one pixel. Reproduce: `cd /workspace/game && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa05/edge.py` and read part 4 (an ASCII map of both corners, baked `B` against flash `F` and uncovered `m`) and part 7 (the count). Image: `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa05/flash.png` (bottom-left and top-right corners at 6x, flash at its first frame).
  - Expected: the flash "drawn over the baked outline" with the two cut corners, "the level box's outline, with its two cut corners (`pop.box_corner_cut`)", so that at full opacity no baked outline pixel shows beside the flash; and the Reviewer's For QA line "both cut corners lining up". Source: `docs/contracts/systems/level-up/view.md`, Presentation, The HUD pop, Box outline; `docs/reports/review/DRA-148-05-ui-developer.md`, For QA, item 4.
  - Actual: the baked diagonal (art tool: `(x + w - cut, y)` to `(x + w, y + cut)`, drawn at 10 x 0.8 = 8 px) lands on pixels from (right - 8, top) to (right - 1, top + 7) at the top-right, and from (left, bottom - 8) to (left + 7, bottom - 1) at the bottom-left, one pixel per step. The flash polygon goes from (right - 8, top) to (right - 1, top + 8) at the top-right (8 rows over 7 columns, not 45 degrees) and from (left, bottom - 9) to (left + 8, bottom - 1) at the bottom-left (one row too high).
  - Proposed fix: in `_box_outline`, change the corner list so both diagonals are 45 degrees and sit on the baked pixels: the top-right end point to `(pad + width - 1, pad + cut - 1)`, the bottom-left start of the bottom edge to `(pad + cut - 1, pad + height - 1)` and the left edge's end to `(pad, pad + height - cut)`. Measured with that change (a subclass in the same script): uncovered baked pixels outside the number's rectangle fall from 7 to 2 ((705, 396), (706, 397), faint antialiased pixels of the baked bottom-left diagonal, which is two pixels wide and cannot be covered at width 1); the top-right is fully covered (0). It keeps the contract's `pop.box_corner_cut` as the cut size.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass

## Round 1 2026-11-06

1. **Task:** Re-test of B1 on DRA-148-05-ui-developer, after the UI Developer's `## Fix 2026-11-06` section (`_box_outline` corners). Started by /implement. The main session, deciding for the Director while away, accepted the 2 remaining faint antialiased pixels of the baked bottom-left diagonal, (705, 396) and (706, 397), as a cosmetic leftover: they show only during the 20-tick box flash and a 1 px flash cannot cover them. B1 is not failed on those two alone.
2. **Delivered:** this round in docs/reports/qa/DRA-148-05-ui-developer.md. Nothing saved in `game/tests/`.
3. **Checks:**
   - B1 reproduce command re-run (`edge.py`, from `/workspace/game`). Part 6: top-right uncovered 0. Part 7: uncovered baked pixels outside the number's rectangle 2, exactly `(705, 396)` and `(706, 397)`. Part 4 map: both diagonals now run 45 degrees on the baked pixels. Part 2: flash pixels on interior-colored pixels 0.
   - Near the fix: levels 2 to 8, last pop frame against the plain HUD: 0 differences (problems 0). Same age twice, ticks 100 and 300, two fresh views and repeated ages: all equal. New climb bar at levels 7 and 8: (255, 255, 255). Odd looks (`odd.py`: `steps` 1 and 2, all ticks 1, `box_corner_cut` 0 and 60, `box_flash_width` 4 and 40, `start_scale` 3.0): none raise, all end on the plain HUD.
   - `game/tests/check.sh`: QA: pass (786 ui tests passed).
4. **Assumptions:** The acceptance of the 2 pixels comes from the main session's message, not from the contract.
5. **Documentation differences:** None. The Architect note from round 0 (flight ends in the tier color, pop's first frame is the white flash color) still stands and is not a bug of this task.
6. **Next:** Integration Engineer. No bug is open.
7. **Status:** done.

## Bugs
- **B1** fixed. The corners now sit on the baked pixels. Accepted by the main session, not failed: 2 faint antialiased pixels, (705, 396) and (706, 397), of the baked bottom-left diagonal stay uncovered during the 20-tick box flash.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
