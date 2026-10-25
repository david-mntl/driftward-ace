Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-117-04-ui-developer (`graze_text` and the GRAZE line on HUD line 2, `game/ui/score_text.py` and `game/ui/hud.py`), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-117-04-ui-developer.md
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format and typecheck PASS. core: 3160 passed, 1 failed. ui: 43 passed, 3 failed. The last line is `QA: fail (core ui)`. All four failures are test-side and listed in `docs/contracts/DRA-117/impact.md` ("Failures expected") or in its last paragraph. None comes from a wrong result in `game/ui/`. See B1 and B2.
   - Acceptance check reproduced with my own inline script (not saved). `graze_text(n)` and `score_text(n)` for 0, 5, 999, 1000, 1234 and 1234567 (and 1, 10, 99, 100, 1001, 10000, 99999, 100000, 10**30, 10**30+1): the digits after the label are identical to the character, and the label is `GRAZE `. 10**30 reads `GRAZE 1 000 000 000 000 000 000 000 000 000 000`, no digit limit.
   - GRAZE line, `start_run()` with `grazes` set, black 640x480 surface. Drawn pixels of line 2 equal the reference text (default font, 16 px, antialiased, white) blitted at (4, `hud_top` + 20), in normal mode (`hud_top` 4) and debug mode (`hud_top` 80, which is `overlay_text_bottom()` 76 plus the gap 4), for grazes 0, 7, 1000 and 0 in a row. Ink box of line 2 (relative to its blit): left 5 (the "G" side bearing, as the implementer says), top 7, right edge grows with the count: 0 reaches x 54, 5 reaches 67, 1234 reaches 83, 10**6 reaches 105, 10**15 reaches 172. Bottom of all left-side ink is row 33 normal, row 109 debug, far above row 168. The GRAZE ink never gets near the hearts at x 544.
   - SCORE line is unchanged: pixels of line 1 equal the SCORE reference at (4, `hud_top`) in both modes whatever `grazes` is (0 or 123456) with `coin_points` 1234.
   - Hearts unchanged: the right region (x 400 to 640, y 0 to 60) is identical for `grazes` 0 and 10**12, at `lives` 0, 1, 2, 3, both modes.
   - Edge cases hunted, all correct:
     - One-slot cache: two draws with the same count return the same surface; after another count is drawn, the first count renders again and the pixels are still right (no stale text).
     - `draw_hud` leaves the `Run` unchanged (`repr` equal before and after).
     - Game Over: with the Game Over box and final score drawn, then the HUD, the GRAZE line is still drawn on top, pixel-equal to the reference, in both modes.
     - Retry: a run in game over with `grazes` 12, armed, then an up press: `grazes` 0, `game_over` False; the HUD reads `GRAZE 0` at (4, 24).
     - Same run drawn twice: identical pixels.
     - Fresh run: `GRAZE 0` shows from the first frame.
     - Review's For QA lines (normal, debug, past 999, retry, Game Over): each checked above. F3 does not move GRAZE: the app passes `below_overlay` from the run mode and `draw_hud` has no other input, so the position depends only on `below_overlay` (checked in both values).
4. **Assumptions:**
   - B1 and B2 are filed as test-side items, the same way as B1 of `docs/reports/qa/DRA-117-02-gameplay-implementer.md` and of `DRA-117-03-ui-developer.md`. The code of DRA-117-04 has no open bug and needs no Implementer fix. The line 1 verdict is `fail` because the harness does not end `QA: pass`, as in the earlier rounds of this feature.
   - The ink's left edge at column 5 meets "its left at the margin": the blit origin is `HUD_MARGIN` (4), the same as SCORE, and the one pixel is the font's side bearing.
5. **Documentation differences:** None.
6. **Next:** No Gameplay Implementer or UI Developer fix. The Architect's tasks bring the tests in line: DRA-117-07 (`game/tests/ui/test_hud.py`, B1) and DRA-117-05 (`game/tests/core/test_ufo.py`, B2). Per the Director's rule that a failure only a queued later task fixes does not stop the build, the Integration Engineer's step waits for those two tasks. Re-test after DRA-117-05 and DRA-117-07 land.
7. **Status:** done.

## Bugs
- **B1** `game/tests/ui/test_hud.py` (3 tests), owner: QA, through task DRA-117-07 (not game code). Reproduce: `game/tests/check.sh ui`.
  Failing: `test_hud_score_is_on_line_one_at_the_left_margin` (ink now lies on line 2: first stray pixel (6, 25)), `test_hud_line_two_is_empty_and_the_meters_are_gone` (line 2 holds `GRAZE 0`), `test_hud_score_top_is_the_overlay_bottom_plus_the_gap` (its last assertion compares the whole HUD with the SCORE line alone).
  Expected: each test says what holds with GRAZE on line 2. Actual: they still say line 2 is empty.
  Source: `docs/contracts/DRA-117/impact.md`, "Failures expected", rows 1 to 3 (cleared by DRA-117-07); `docs/contracts/systems/hud.md`, Presentation, SCORE line and GRAZE line.
  Proposed fix: DRA-117-07 rewrites the three tests (line 2 holds `graze_text(run.grazes)` at (`HUD_MARGIN`, `hud_top` + `HUD_LINE_SPACING`); compare the SCORE line over its own rows, or the whole surface with the SCORE and GRAZE lines both blitted). `test_hud_score_pixels_follow_the_score` passes today, so it needs no change.
- **B2** `game/tests/core/test_ufo.py:1324`, owner: QA, through task DRA-117-05 (not game code). Same failure as B1 of `DRA-117-02-gameplay-implementer.md`. Reproduce: `game/tests/check.sh core -k test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds`.
  Expected: the test passes. Actual: the compare of the touched UFO with its untouched twin differs on `graze_state` only (SPENT against OUTSIDE).
  Source: `docs/contracts/systems/run.md`, Rules, step 5b.3 (a touch sets SPENT); `docs/contracts/DRA-117/impact.md`, last paragraph of "Failures expected".
  Proposed fix: as in the DRA-117-02 report: set `graze_state=GrazeState.OUTSIDE` on the touched UFO in the compare and assert `after.graze_state is GrazeState.SPENT`.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (3160 passed, 1 failed: B2) · ui FAIL (43 passed, 3 failed: B1)
QA: fail (core ui)

## Round 2 2026-10-25

1. **Task:** Re-test of DRA-117-04-ui-developer after the test-side fixes: B1 by QA task DRA-117-07 (`game/tests/ui/test_hud.py`) and B2 by QA task DRA-117-05 (`game/tests/core/test_ufo.py`). No implementer fix was made. Started by the main session.
2. **Delivered:** this round in docs/reports/qa/DRA-117-04-ui-developer.md.
3. **Checks:**
   - `game/tests/check.sh` (whole): env, lint, format, typecheck, core (3231 passed) and ui (65 passed) PASS. Last line `QA: pass`.
   - B1 reproduce: `game/tests/check.sh ui -k "test_hud_score_is_on_line_one or test_hud_line_two or test_hud_score_top"`: 3 passed. The three tests now say what holds with GRAZE on line 2 (`test_hud_line_two_holds_the_graze_line_only_and_the_meters_are_gone` replaced the empty-line-2 test).
   - B2 reproduce: `game/tests/check.sh core -k test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds`: passed. The test now asserts `after.graze_state is GrazeState.SPENT` on every tick and compares the UFO with its untouched twin apart from that field (`test_ufo.py` around line 1324). It matches the contract (run.md, step 5b item 3: a touch sets SPENT).
   - Neighbors: the ui test run holds the SCORE tests, the GRAZE tests and `test_graze_view.py`, all passing. The round 1 inline checks of `game/ui/` are unchanged, because no game code changed for these two bugs.
4. **Assumptions:** Another QA agent may have run check.sh at the same time. The run above was clean and complete.
5. **Documentation differences:** None.
6. **Next:** No bug is open. Integration Engineer.
7. **Status:** done.

## Bugs
- **B1** fixed (by DRA-117-07). Three `test_hud.py` tests pass.
- **B2** fixed (by DRA-117-05). The `test_ufo.py` compare passes. No new bugs.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3231 passed) · ui PASS (65 passed)
QA: pass
