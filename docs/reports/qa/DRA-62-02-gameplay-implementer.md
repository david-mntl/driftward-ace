Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-62-02-gameplay-implementer (`scroll_step_px`, the scroll step in step 3, popups in step 3a, collect in step 5a), started by /implement. Verify mode.

2. **Delivered:** `docs/reports/qa/DRA-62-02-gameplay-implementer.md`. Nothing saved in `game/tests/`. Inline scripts ran from the scratchpad.

3. **Checks:**
   - `check.sh`: env, lint, format and typecheck PASS. `core` 1342 passed, 1 failed. `ui` 45 passed, 1 failed. The two failures are the two already named in the DRA-62-01 QA report, and both close when `game/tuning/drifters/coin.json` exists: `test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[coin-None]` ("no tuning file for 'coin'", the case the task and the contract's DRA-62 Impact table expect until the file and DRA-62-05) and `ui/test_drifter_registry.py::test_drifter_lists_match_everywhere` (tuning files lack `coin`). Neither touches the run or the scroll. See Assumptions.
   - Acceptance check run verbatim from `game/`, twice, `diff` empty. Output, all five lines match the task:
     ```
     0.0 1.1
     0 1 0
     50 50 0 240.0
     1 210.5
     0
     ```
   - Scroll: `scroll_step_px` equals `step_scroll(s).distance_px - s.distance_px` within 1e-9 for ticks 0 to 199. It is 0.0 at ticks 0, 28, 29 and 1.1 at 30, 31.
   - Respawn wait: a coin under the standing ship stays, pays nothing, no popup, and rides the scroll (y + 1.1). A held arrow with no new press (wait goes on) collects nothing. The press tick pays 50, the coin is gone, one popup, and the log reads `respawn wait end`, `drifter touch id=1 type=coin effect=collect`, `drifter gone id=1 type=coin`.
   - Coin and hazard on one tick: 3 lives gives coin 100, lives 2, score = meters + 100. Last life gives coin 100, `game_over` True, score = meters + 100. Log order: collect `drifter touch`, hit `drifter touch`, `life lost`, `game over meters=18`, `drifter gone`. Protected: coin pays, lives stay 3, no cooldown started. Hazard cooldown starts at 180 when it hits with a coin in the same run.
   - Fall tick (ship at y 490.5, vy 5.5, coin and a meteorite on it): protected and not protected, 3 lives and 1 life: the coin pays in all four, one popup at the coin's center after the scroll step, no `effect=hit` line. Lives: unprotected costs one (game over on the last), protected costs none. A coin at y 489.5 that is collected on the tick it would leave the screen pays and logs one `drifter gone`.
   - Popup: shown on exactly 60 states (ages 0 to 59), rises 0.5 px every state from its start, x constant, unmoved by the scroll. Ages in the wait and on protected ticks (age 10 after 10 ticks). Two coins on one tick: 150 points, popups [50, 100], touch and gone logs in drifter order. An older popup stays ahead of a newer one (ages 1, 0).
   - Game over: a coin collected on the last-life tick counts, popup at age 0. Popups also age on the game-over tick itself (3 to 4) and stay frozen for 70 more ticks, with the coin points, scroll and drifters unchanged. A retry gives no popups, `coin_points` 0, score 0.
   - Edges: coin box 0.000001 px inside the ship's foot side or underside collects, exactly touching does not, with the scroll step added first. The ring alone never collects. Before the start delay (scroll step 0) a coin collects with no movement. No collect line says `drifter active` for a coin. A collect-only tick changes no life, timer, wait or game-over flag. A run with no coin has no popups and `coin_points` 0. A dropped coin does not shift the cooldown count of the drifter after it (rehit 5 goes to 4).
   - Same seed and inputs twice over 300 ticks of scripted thrust: runs identical.
   - Grep of `run.py`, `scroll.py`, `popup.py` for sleep, threading, asyncio, pygame, `random.random(`, `.mp3`, `.wav`: no hits.

4. **Assumptions:** The contract's own Impact table and the task sanction the `test_collision.py` coin failure. The `ui` registry failure has the same cause (no `coin.json`) and the DRA-62-01 report already accepted it. I count both as not a bug and set `pass`, though `check.sh` ends `QA: fail (core ui)`. If the Director wants a strict `QA: pass` first, hold this task until `coin.json` and DRA-62-05 land.

5. **Documentation differences:** None.

6. **Next:** Integration Engineer is not due yet: the coin view (DRA-62-03), the popup view (DRA-62-04), the coin tuning file and the QA tasks DRA-62-05 and DRA-62-06 are still open. Hand back to the `/implement` skill to continue. Re-check the two failing tests once `coin.json` exists.

7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1, expected: no tuning file for coin) · ui FAIL (1, expected: no coin.json)
QA: fail (core ui)
