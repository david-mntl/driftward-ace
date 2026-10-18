Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-62-01-gameplay-implementer (the coin, the points popup, the parked-drifter rules in `game/core/`), started by /implement. Verify mode.

2. **Delivered:** `docs/reports/qa/DRA-62-01-gameplay-implementer.md`. Nothing saved in `game/tests/`. Inline scripts ran from the scratchpad.

3. **Checks:**
   - `check.sh`: env, lint, format and typecheck PASS. `core` 1342 passed, 1 failed. `ui` 45 passed, 1 failed. The two failures are exactly the two the task's Acceptance check and the contract's DRA-62 Impact table name as expected until `coin.json` (content, not built yet) and the coin view (task DRA-62-03) exist: `test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[coin-None]` ("no tuning file for 'coin'") and `test_drifter_registry.py::test_drifter_lists_match_everywhere` (tuning files lack `coin`). No other test fails. See Assumptions.
   - Acceptance check run verbatim from `game/`. Output, all four lines match the task:
     ```
     active -10.0 0.0 collect ()
     -8.9 320.0 2
     50 PointsPopup(x=320.0, start_y=-10.0, points=50, lifetime_ticks=60, rise_per_tick=0.5, age_ticks=0)
     coin has no speed
     ```
   - Same run twice: output identical (diff empty). `update` twice from one coin gives equal coins and leaves the input at y -10.0.
   - Edge cases, all as the contract says:
     - Birth: ACTIVE, y -10, speed 0.0 at Levels 1 to 8, with `as_level` 8, and with both playtest switches off. A placement `speed` raises `coin has no speed` (also `speed=0.0`). `invert=True` raises `coin has no invert`, `specialty_enabled=True` raises `coin has no specialty`, `False` is fine. No `x` raises `coin placement needs x`. Unknown variant raises as the spawner does. A variant with no `CoinVariantExtra` raises `coin variant 'common' has no points`; a type with no `CoinTypeExtra` raises `coin tuning has no type values`. A placed `y` (200.0, 0.0) is kept. Rare: 100 points, glint True, popup says 100.
     - Update: `scroll_step_px` 0.0 leaves y at -10.0 (ticks_in_phase counts), 100 ticks at 1.1 give y 100.0 and x unchanged. WARNING and GONE coins don't move. Hitbox is one 12 x 10 box while ACTIVE, `()` when GONE; graze zone `()`; effect COLLECT. Drawn parts are the 12 x 20 crystal then the 22 x 8 ring.
     - Enter and leave: entered on the first scrolled tick (y -8.9). Not off screen at y 489.9, off at 490.0 (contract: y >= 490). A coin at y 500 that never entered is not off screen. Ring counts at the sides: at x -11.0 the ring only touches the left edge and has not entered; at x -10.9 it has. Leaving at the left needs x <= -11.0 (both boxes past), at the right x >= 651.0.
     - Moving drifters unchanged: meteorite speed 2.4675 at Level 1, 3.5038 at Level 8, placement speed 2.0 gives 2.0 and 2.84 at Level 8; still born in WARNING.
     - Popup: lifetime 60 shows on 60 states (ages 0 to 59), dropped on the 60th step. `y` is `start_y - age * 0.5` (-10.5 at age 1, -25.0 at 30, -39.5 at 59). Lifetime 1 is dropped on the first step. Empty tuple gives empty tuple. Order kept, `x` constant, input popups not mutated, popups with different lives drop independently.

4. **Assumptions:** The task and the contract's Impact table sanction the two failing tests, so I count them as not a bug and set `pass`, though `check.sh` ends `QA: fail (core ui)`. They are not a code defect: they close when the coin's tuning file and view land (tasks DRA-62-03 and the content file) and DRA-62-05 reworks `test_collision.py`. If the Director wants a strict `QA: pass` before the next task, hold this task until then.

5. **Documentation differences:** None.

6. **Next:** Integration Engineer is not due yet: the run (DRA-62-02), the views (DRA-62-03, 04) and the tuning file are still open. Hand to the `/implement` skill to continue with DRA-62-02. The two failing tests must go green once DRA-62-03 and `coin.json` exist; re-check at DRA-62-05.

7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1, expected: no tuning file for coin) · ui FAIL (1, expected: no coin.json or view)
QA: fail (core ui)
