Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-117-03-ui-developer (the graze popup color in `draw_points_popup` and the new `draw_graze_ring` view), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-117-03-ui-developer.md
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck and ui PASS (ui 46 passed). core: 3160 passed, 1 failed, so the last line is `QA: fail (core)`. The one failure is B1 below, the same one filed in `docs/reports/qa/DRA-117-02-gameplay-implementer.md`. It is not caused by `game/ui/`.
   - Acceptance check reproduced: I re-ran the implementation report's script (`check_draw.py`, outside the repo) and got the same output.
     - Coin popup (+25): ink box 19 x 8, color (255, 80, 150). Graze popup (+25): ink box 19 x 8, color (255, 255, 255) = `GRAZE_POPUP_COLOR`. Same text size.
     - Ring at ages 0 to 14 around a ship at (320, 240): ink pixel fades (255, 238, 221, ... 17) on every state, and the ink grows every state.
     - Second draw at one age: cache hit, no new surface.
   - My own inline run (not saved), default rules: ring ink extent from the ship's center, left/right/top/bottom, is 8/7/8/7 px at age 0 (16 px across, as the GDD says) and 15/14/15/14 px at age 14 (30 px across, since the ring's last state is diameter 30.93). Brightest ink pixel is 255 at age 0 and 17 at age 14. The ring is gone when core drops it (after state 14, `step_graze_rings` returns nothing), so no faint last frame stays.
   - Edge cases hunted, all correct:
     - Ship at fractional positions: the ring center follows `round(ship.x), round(ship.y)` (320.4, 240.6 gives the ink 8 px left of 320 and 8 px above 241; 320.5, 240.5 rounds to (320, 240)). The ring moves with the ship across 15 states.
     - Ring at a corner (0, 0), at (639.5, 479.5), at (-5, -5) and at (1e6, 1e6): no error, clipped. A popup at (0, 0), (639, 479) and (-100, -100): no error.
     - Odd rules: ring that shrinks (32 to 16), line width 5 and 100, lifetime 1, diameter 300: draw without error and with the contract's size. Lifetime 1000 at its last age gives alpha 0 (nothing visible), as `round(255 x opacity)` says.
     - A diameter below 1 px (0.4) gives radius 0 and no ink. The contract allows "above 0" for the diameter; a value that small is a tuning choice, not a view bug.
     - All five popup values (0, 25, 50, 100, 123456789) in both kinds: color is the kind's color, the box is the same width for the same points in both kinds.
     - The cached ring image is not changed by a draw, and a ring blended on a red background shows the white outline where expected.
     - The ring and ship objects are equal before and after a draw. 15 ring draws with a moving ship, twice: the frames are byte-identical.
     - `game/ui/popup_view.py` and `game/ui/graze_view.py` import only pygame and `core`; the contract's "never app" holds.
   - Review report `docs/reports/review/DRA-117-03-ui-developer.md`: no findings, so no `must-fix` to check. Every **For QA** line is covered above, except the ring drawing on frames the ship blinks off: that is the app's draw order (Integration Engineer), not this task.
4. **Assumptions:** B1 is the case `docs/contracts/DRA-117/impact.md` ("Failures expected", last paragraph) hands to QA: a whole-drifter compare that turns up is brought in line by DRA-117-05. The game code is correct, so I filed it against the test's owner, not a game file. I edited no test (Verify saves nothing in `game/tests/`).
5. **Documentation differences:** None.
6. **Next:** `game/ui/` has no open bug. The only open item is B1, a test-side failure that the Architect's task DRA-117-05 (`docs/contracts/DRA-117/tasks/DRA-117-05-qa-engineer.md`) clears. No UI Developer fix is needed. B1 comes from a later task, so the build can go on (Director's rule); the Integration Engineer's step waits for DRA-117-05. Re-test after it lands.
7. **Status:** done.

## Bugs
- **B1** `game/tests/core/test_ufo.py:1324`, owner: QA, through task DRA-117-05 (not game code, same bug as B1 of `DRA-117-02-gameplay-implementer`). Reproduce: `game/tests/check.sh core -k test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds`.
  Expected: the test passes. Actual: `assert replace(after, rehit_ticks_left=0, uid=0) == replace(twin, uid=0)` fails on `graze_state`: the touched UFO is `SPENT`, the untouched twin is `OUTSIDE`.
  Source: `docs/contracts/systems/run.md`, Rules, step 5b.3 (a touch sets SPENT); `docs/contracts/DRA-117/impact.md`, "Failures expected", last paragraph.
  Proposed fix: in that compare, set `graze_state` to `GrazeState.OUTSIDE` on the touched UFO, `replace(after, rehit_ticks_left=0, uid=0, graze_state=GrazeState.OUTSIDE) == replace(twin, uid=0)`, and add one assertion that `after.graze_state is GrazeState.SPENT`.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (3160 passed, 1 failed: B1) · ui PASS (46 passed)
QA: fail (core)

## Round 2 2026-10-25

1. **Task:** Re-test of DRA-117-03-ui-developer after DRA-117-05 fixed the stale `test_ufo.py` compare (B1). Asked by /implement. No implementer fix was made.
2. **Delivered:** docs/reports/qa/DRA-117-03-ui-developer.md (this round).
3. **Checks:**
   - B1 reproduce command `game/tests/check.sh core -k test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds`: 1 passed.
   - The test now asserts `after.graze_state is GrazeState.SPENT` on every tick, then compares the UFO with its untouched twin apart from `graze_state` (`game/tests/core/test_ufo.py`, around line 1323). That is the shape this report proposed.
   - Full `game/tests/check.sh`: every step PASS, last line `QA: pass` (ui 65 passed).
   - Round 1's acceptance check and edge cases are not re-run: `game/ui/` has no change since round 1 (the files differ only by the DRA-117 work already tested), and the one failure was never in `game/ui/`.
4. **Assumptions:** The test-side change belongs to DRA-117-05, as round 1 said. I edited no test.
5. **Documentation differences:** None.
6. **Next:** The Integration Engineer. No bug is open.
7. **Status:** done.

## Bugs
- **B1** fixed. The test now passes and also asserts the SPENT state.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS (65 passed)
QA: pass
