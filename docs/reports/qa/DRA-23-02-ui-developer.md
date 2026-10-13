Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-23-02-ui-developer (white hearts and `draw_hud(surface, run, below_overlay)`), Verify mode, started by /implement.
2. **Delivered:** `docs/reports/qa/DRA-23-02-ui-developer.md`. Nothing saved in `game/tests/`. The inline script and two images are in the scratchpad: `/tmp/claude-1000/-workspace/8060ad56-4f1c-40d0-ad14-d4fb39ed0880/scratchpad/qa02/` (`qa.py`, `normal.png`, `debug.png`).
3. **Checks:**
   - `game/tests/check.sh`: lint PASS, format PASS, env PASS. `core` fails with 2 tests in `tests/core/test_ship.py` (`test_floor_respawns_at_spawn`, `test_events_log_once`) and `ui` fails with the 5 tests in `tests/ui/test_hud.py` (`AttributeError: 'Scroll' object has no attribute 'scroll'`). All 7 are the expected failures named by the Director (DRA-23-04 and DRA-23-05 replace them). `tests/ui/test_error_screen.py` passes (3). Judged on task 02's scope, the harness shows nothing else.
   - Acceptance check reproduced with my own script (`python -I .../qa02/qa.py` from `game/`, `SDL_VIDEODRIVER=dummy`). Printed: `normal [True, True, True] bbox 608 631 8 31` and `debug [False, False, True] bbox 608 631 8 31`. Matches the task: boxes as required, bbox inside x 608 to 631, rows 8 to 31, spanning x 608 to 631. `repr(run)` is the same before and after the draw.
   - Lives 0, 1, 2, 3 on widths 640, 800 and 321: filled slots go right to left from `width - 32`, slot 0 never moves, 0 draws nothing, no white pixel outside the filled boxes (right of the readout). Gaps between hearts, the 8 px right margin, rows 0 to 7 and rows 32 and below are empty. Each heart reaches columns 0 and 23 and rows 0 and 23 of its box.
   - Hearts are pixel-identical with `below_overlay` True and False. `_heart()` returns the same object across draws (`cache_info`: 1 miss, 19 hits), a 24 x 24 SRCALPHA surface with only transparent and opaque white pixels. Readout `0 m` and `1 m` and `343 m` draw white pixels left of the hearts only. Two draws of the same run give identical bytes.
   - Out-of-range lives are not a contract case: `lives=4` draws a fourth heart at slot 3, `lives=-1` draws none. Core keeps lives 0 to 3, so I list nothing.
   - 1 bug found, see Bugs. The review's claim that the heart is "symmetric about x 11.5" (review, Checks) is false.
4. **Assumptions:** I read "two round lobes side by side at the top, meeting in a point at the bottom center" (hud.md, Presentation, Hearts) as asking for a shape that is the same on both sides. The contract never says "symmetric" in words.
5. **Documentation differences:** None.
6. **Next:** UI Developer, Fix mode, bug report `docs/reports/qa/DRA-23-02-ui-developer.md` (B1). After the fix, QA re-tests. The Integration Engineer comes after a pass. Note for the Integration Engineer: `game/app/frame.py:143` still passes a scroll to `draw_hud` (known, out of this task's scope).
7. **Status:** done.

## Bugs
- **B1** `game/ui/hud.py:101-102` (`_heart`), UI Developer. The heart is lopsided by one pixel: the right lobe is drawn one column too far left, so it never reaches column 23 and a 2-row nub sticks out on the right edge. Reproduce, from `game/`:
  ```
  SDL_VIDEODRIVER=dummy python -I -c "import sys; sys.path.insert(0,'.'); import pygame; pygame.init(); import ui.hud as h; s=h._heart(); print([(x,y) for x in range(24) for y in range(24) if bool(s.get_at((x,y))[3])!=bool(s.get_at((23-x,y))[3])])"
  ```
  Expected: `[]` (the left and right halves mirror each other; each lobe reaches its side column, 0 and 23, as the left one does). Actual: 22 mismatched pixels, for example (0, 4) to (0, 6) filled with (23, 4) to (23, 6) empty, and the top of the right lobe at columns 15 to 18 against the left lobe's 4 to 7. Column 23 is white only on rows 7 and 8, from the polygon's corner, which looks like a nub. Cause: `pygame.draw.circle` in pygame-ce 2.5.8 covers columns `center - radius` to `center + radius - 1`. The left lobe at center 6 covers 0 to 11. The right lobe at center `last - radius` = 17 covers 11 to 22, not 12 to 23.
  Source of the expected value: hud.md, Presentation, Hearts ("two round lobes side by side at the top, meeting in a point at the bottom center", "spans the box's full width"); the implementation report, Assumptions, and the review, Checks, both state the shape is symmetric about x 11.5, which the code does not do.
  Proposed fix: in `_heart`, place the right lobe at `HEART_SIZE - radius` (18) instead of `last - radius` (17): `pygame.draw.circle(heart, HEART_COLOR, (HEART_SIZE - radius, lobe_y), radius)`. I drew the heart with that one change (polygon unchanged): 0 mismatched pixels, left and right lobes cover columns 0 to 11 and 12 to 23, columns 0 and 23 and rows 0 and 23 are still reached, every pixel stays inside the box. Nothing else in the acceptance output changes (bbox x 608 to 631, rows 8 to 31).

## Harness
env PASS · lint PASS · format PASS · core FAIL (2 expected, `tests/core/test_ship.py`, DRA-23-04) · ui FAIL (5 expected, `tests/ui/test_hud.py`, DRA-23-05; 3 `test_error_screen.py` pass)
QA: fail (core ui)

## Round 2 2026-10-13

1. **Task:** Re-test of B1 (lopsided heart) after the UI Developer's fix section in `docs/reports/implementation/ui/DRA-23-02-ui-developer.md`, started by /implement.
2. **Delivered:** this round in `docs/reports/qa/DRA-23-02-ui-developer.md`. Nothing saved in `game/tests/`. Inline script reused from the scratchpad: `/tmp/claude-1000/-workspace/8060ad56-4f1c-40d0-ad14-d4fb39ed0880/scratchpad/qa02/qa.py`.
3. **Checks:**
   - B1 reproduce command, run again from `game/`: prints `[]` (was 22 mismatched pixels). The heart printed as ASCII: both lobes reach columns 0 and 23, the point is two pixels wide at row 23, no nub on the right edge.
   - Full `qa.py` rerun, near-the-fix edges: acceptance `normal [True, True, True] bbox 608 631 8 31` and `debug [False, False, True] bbox 608 631 8 31` unchanged. Lives 0 to 3 on widths 640, 800 and 321: filled slots right to left, 0 draws nothing, 0 stray white pixels. Each heart spans columns 0 to 23 and rows 0 to 23, 364 pixels, mirror-symmetric. Gaps, margin and rows 0 to 7 and 32 and below are empty. Hearts identical with `below_overlay` True and False. `_heart()` cached (1 miss, 19 hits), 24 x 24 SRCALPHA, only transparent and opaque white. Readout unchanged. Two draws give identical bytes (`det True`). `repr(run)` unchanged by the draw.
   - `ruff check ui` and `ruff format --check ui`: pass.
   - `game/tests/check.sh`: ends `QA: fail (lint ui)`. None of it comes from task 02. The 5 `ui` failures are the expected `tests/ui/test_hud.py` ones (`'Scroll' object has no attribute 'scroll'`, DRA-23-05); the 3 `test_error_screen.py` tests pass. The 2 lint errors are E501 in `tests/core/test_run.py:4` and `tests/core/test_ship.py:3`, files DRA-23-04 is writing now; `core` passes. I did not touch `tests/`.
4. **Assumptions:** Following the Director's note, I judge this task on its own scope: the harness failures above belong to DRA-23-04 and DRA-23-05. The pass holds only if those two tasks clear them before the Integration Engineer builds.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, once `check.sh` ends `QA: pass`. Open items outside this task: DRA-23-04 owner must fix the two E501 lines in `tests/core/`; DRA-23-05 replaces `tests/ui/test_hud.py`; `game/app/frame.py:143` still passes a scroll to `draw_hud` and must pass `run`.
7. **Status:** done.

## Bugs
- **B1** fixed. `game/ui/hud.py` `_heart` now places the right lobe at `HEART_SIZE - radius`. The mirror test prints `[]`.
- No new bugs.

## Harness
env PASS · lint FAIL (2 E501 in `tests/core/test_run.py:4` and `tests/core/test_ship.py:3`, DRA-23-04; `ruff check ui` alone passes) · format PASS · core PASS · ui FAIL (5 expected, `tests/ui/test_hud.py`, DRA-23-05; 3 pass)
QA: fail (lint ui)
