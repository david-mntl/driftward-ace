Verdict: pass
Created by: qa-engineer

1. **Task:** QA (Verify mode) of DRA-148-04-ui-developer, the level-up banner view (`LevelUpFonts`, `LevelUpView.__init__`, `draw_banner`, `bump_offset`), started by /implement. Read against `docs/contracts/systems/level-up/view.md`, the task file, the implementation report (first delivery and its `## Review fix`) and the review report (Findings, For QA, Re-check).
2. **Delivered:** `/workspace/docs/reports/qa/DRA-148-04-ui-developer.md`. Nothing saved in `game/tests/`. Inline scripts are in the scratchpad `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa04_*.py` (they exec the setup part of the implementer's `accept.py`); screenshots in `.../scratchpad/qa04shots/`.
3. **Checks:**
   - `game/tests/check.sh`: QA: pass (786 core and ui tests, lint, format, typecheck). Task DRA-148-06 had already added `draw_flight` to `level_up_view.py` (703 lines) when I ran; nothing failed because of it.
   - Acceptance check reproduced (`accept.py`, level 3, 640 x 480): glass 78 rows at age 6, 118 plus two hairline rows at 14 to 100, 0 rows at 124; ring 48 px at age 22 growing to about 168 px at age 39, gone at 40; LEVEL and pips fade in; stand-ins over the number and the glass keep every pixel (True, True); fuchsia max 0 over levels 2 to 8, ages 0 to 149; 0.129 ms per draw with glass, 0.058 ms with `band.alpha` 0; glass methods 0.061 (chosen), 0.225, 0.078 ms; 1000 draws build no surface, render no text, call no scale or rotate; 100000 draws for None change nothing; `bump_offset(None)` 0.
   - Same inputs twice: all 7 levels x ages 0 to 159 drawn forward, then in shuffled order, then on a freshly built view: 0 differing frames. A paused age therefore holds.
   - Glint (review F1, For QA): levels 2 to 8, ages 40 to 65 against the hold picture: 0 changed pixels outside the number, 0 on an outline pixel. The stripe crosses ages 44 to 57 and nothing changes from 58.
   - Centering: at hold the number's ink is centered on (320, 240) within half a pixel for every level.
   - Pips: row centered on x 320, centers 257 to 383 every 18 px at y 288; first pip appears at age 27, last is in at 48; level 3 has 3 lit and 5 unlit, level 8 all lit; the new pip flashes and is back to its lit color at age 42.
   - Hairlines: ages 0 to 11 and 98 to 126: lines on one row (240) from age 115 to 123, 0 pixels at 0 and from 124, reach the walls from age 10 to 114 and not before; no stray pixels at the walls. At age 113 row 240 is empty (ticks are capped at half the glass height, the implementer's assumption 2); not a bug.
   - Edge: ages -1, 149, 150, 151 and 1000 draw nothing outside the banner's own window; levels 0, 1 and 9 raise `KeyError` (documented); fields of 300 x 200 and 640 x 100, band height 0, 1, 121, 500 and a moved center all draw without error; `band.alpha` 255 gives the glass color exactly and 0 gives the field; `bump.pixels` 0 gives 0 for every age; the view's `bump_offset` equals the motion function for ages 0 to 199 and never exceeds 3.
   - Glass at `band.alpha` 120 is 1 level off the ideal blend on R and G (9, 13, 33 against 8, 12, 33): the multiply and add fills each round. The contract names this method; not a bug.
   - Not checked: the browser frame cost (Integration Engineer), `draw_flight` (task 06).
   - 1 bug found, B1.
4. **Assumptions:** The number at fall age 5 being already on screen (not "not yet entered" at age 6 as the implementation report says) is correct: `fall_start` is 4 and the contract has it fall from there. The report line is loose, the code is right.
5. **Documentation differences:** None.
6. **Next:** UI Developer, Fix mode, bug B1 in this report (`docs/reports/qa/DRA-148-04-ui-developer.md`). Then QA re-tests it.
7. **Status:** done.

## Bugs
- **B1** `game/ui/level_up_view.py:374` (`_build_number`, `drop_px=center_y + fall.get_height() / 2`) with `:317` (`_draw_number`, `round(cy)` then `get_rect(center=...)`), UI Developer. The number is not fully above the play area before `fall_start` when its stretched image has an odd height (level 7: 43 x 73). Its last row sits on field row 0.
  - Reproduce, from `/workspace/game`: `PYTHONPATH=. SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa04_l.py /tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa04shots`. It draws the banner at ages 0 to 4 on a plain field for levels 2 to 8 and counts changed pixels in rows 0 to 169. (`qa04_m.py` lists them.)
  - Expected: 0 changed pixels for every level at ages 0 to 4. Source: view.md, Interface, `fall_offset` ("-distance_px up to fall_start (fully above the play area)") and Presentation, The number ("falls from fully above the play area").
  - Actual: level 7 changes 15 pixels at ages 0 to 4 (row 0, x 309 to 323, the digit's outline, for example (309, 0) = (7, 12, 33)); other levels 0. Cause: `drop_px` is 276.5 for level 7, so `cy` is -36.5; `round(-36.5)` is -36 (round half to even), and `get_rect(center=(x, -36))` on a 73 px image puts its top at -72 and its bottom at 1, one row inside. Even heights and the .5 cases that round the other way are fine.
  - Proposed fix: in `_build_number` set `drop_px=center_y + (fall.get_height() + 1) // 2` (the half height rounded up, so `cy` is a whole number and `get_rect(center=...)` puts the bottom at row 0 for odd and even heights). It changes nothing at rest (`fall_offset` is 0 from `fall_end`). I checked it inline by replacing `drop_px` that way for levels 2 to 8: 0 changed pixels at ages 0 to 4 for every level. It satisfies the contract's "fully above" without touching the curve in `level_up_motion.py`.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass

## Round 2 2026-11-06

1. **Task:** Re-test of B1 after the `## Fix 2026-11-06` section in `docs/reports/implementation/ui/DRA-148-04-ui-developer.md`, started by /implement.
2. **Delivered:** this round in `/workspace/docs/reports/qa/DRA-148-04-ui-developer.md`. Nothing saved in `game/tests/`. Inline script: `/tmp/claude-1000/-workspace/122d70f3-5271-4468-9d09-1e1c606dd041/scratchpad/qa04_r2.py`.
3. **Checks:**
   - B1 reproduce command (`qa04_l.py`) re-run: levels 2 to 8 all `[0, 0, 0, 0, 0]` changed pixels in rows 0 to 169 at ages 0 to 4. Level 7 was 15 per age.
   - Wider check (`qa04_r2.py`): 0 changed pixels in rows 0 to 169 at ages 0 to 4, levels 2 to 8, every column.
   - Neighbors: `accept.py` re-run, same numbers as round 1 (glass 78 / 118 / 0 rows, hairlines 180 and 299, stand-ins exact True True, fuchsia max 0, no surface, text, scale or rotate calls after init, None draws change nothing, `bump_offset(None)` 0). Pictures at hold and after the fall are unchanged (`fall_offset` is 0 from `fall_end`).
   - Same inputs twice: ages 0 to 159 for levels 2 to 8 drawn forward then shuffled: 0 differing frames.
   - `game/tests/check.sh`: QA: pass.
4. **Assumptions:** None.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer (the task passes QA).
7. **Status:** done.

## Bugs
- **B1** fixed. `game/ui/level_up_view.py:395` now has `drop_px=center_y + (fall.get_height() + 1) // 2`. No new bug.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
