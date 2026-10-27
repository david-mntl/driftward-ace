Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-125-01-gameplay-implementer (`core/last_life.py` new, `core/run.py` changed: last life, game over, `next_run`, `hold_arrows`), Verify mode, started by /implement. The review is `Status: reviewed`.
2. **Delivered:** docs/reports/qa/DRA-125-01-gameplay-implementer.md. No test saved (Verify mode).
3. **Checks:**
   - `check.sh`: `QA: fail (typecheck core)`. The only failures are the 7 `retry_armed` typecheck errors and the 26 core tests that impact.md expects from DRA-125-01 (see Harness). `lint`, `format`, `env` and `ui` pass (ui 65 tests). No bug in the code.
   - Acceptance check reproduced inline (scratchpad scripts, `PYTHONPATH=. python`). Three falls with an up press ending each wait: the third fall starts the last life at tick 196 with the burst at (320.0, 480), `last life score=18`, `score` stays 18 while `scroll.meters` goes 18 to 31, `game over score=18` on tick 316 (L + 120); ten more ticks change nothing (`== replace(over, held=...)`). A hit on the last life (ACTIVE meteorite on the ship, `lives=1`): burst at the ship's center (320.0, 240.0). `LastLifeRules(delay_ticks=5, burst_particle_count=4)`: game over 5 ticks after the death, 4 centers. `next_run` on the game-over run equals `start_run` with the same graze and last-life values, `new run` logged once; with waves, Wave 0 again at Level 1. `hold_arrows(UP)` in a respawn wait, then `step_run(UP)`: still waiting; a release then a press ends it.
   - Edge cases, all correct: `delay_ticks=1` (opacity 1.0 on L, game over with opacity 0.0 on L+1, then frozen); hit on the last life during the respawn wait (`waiting` False, `invuln_ticks_left` 0, burst at the standing ship's center); a fall on the last life (burst at (ship.x, 480), `respawn from` never logged, ship stays below the floor); a fall and a touch on one tick (only the fall, burst at the floor, no `drifter touch`); protected fall and protected touch on `lives=1` (no last life, no burst); a graze paid on the death tick is in `final_score` (18 meters + 25 graze = 43, the popup and ring then age out, `score` stays 43); `graze_state` of a drifter kept in the last life, no graze paid; the re-hit cooldown starts at 180 on the death tick and counts down through the last life (60 at game over); drifters keep moving and the ship stays put; `add_drifters` adds in the last life (uid 2, `next_uid` 3) and returns the same run at game over; waves equal `step_waves(waves, scroll.distance_px)` on each of 100 last-life ticks and the level rises during the last life (1 to 2); frozen waves and world at game over; `next_run` on a mid-run run, a last-life run and a `waves=None` run gives a fresh run (3 lives, no burst, no final score, no drifters), keeps custom `LastLifeRules`, and logs only `new run`; burst squares match the formula for k = 0 to 11 at age 10 (square 0 right, 3 down, 6 left, 9 up), speed 0 and count 1 work, `opacity` stays 0.0 past the end, `step_burst` leaves its input unchanged; `ship_visible` False from the burst on; the same 500-tick run twice gives equal states.
   - Log order on the death tick matches the contract: `drifter graze`, `drifter touch`, `life lost`, `last life` (hit), and `life lost`, `last life` (fall).
   - The review's For QA list is covered: each of its five lines is in the checks above.
4. **Assumptions:** the 26 failing core tests are the ones impact.md's table and its general rule expect. I opened the ones the table does not name (`test_a_new_run_starts_like_the_first`, `test_score_stops_at_game_over_until_the_retry`, `test_a_retry_gives_score_0_again`, `test_the_waves_step_once_on_every_playing_tick`, `test_the_same_first_seed_gives_the_same_run_of_waves_and_retries`, `test_a_fall_and_a_touch_on_one_tick_cost_only_the_fall`, `test_a_graze_and_a_hit_by_another_hazard_on_one_tick_the_graze_pays_then_the_hit_counts`): each fails at an `assert ....game_over` on the death tick, a retry by arrow, or a score that is frozen where the test expects live meters. No test that never loses the last life fails.
5. **Documentation differences:** None.
6. **Next:** No bug is open and no fix is needed from the Gameplay Implementer. The verdict is `blocked` only because `check.sh` cannot end `QA: pass` until DRA-125-09 (QA Engineer) brings the 26 tests and the 7 typecheck errors in line with `systems/run.md`. The Director or /implement decides whether to go on to the later tasks with these expected failures. Re-run this check (Re-test, appending a round) after DRA-125-09 lands; on a clean `QA: pass` it becomes `pass` and goes to the Integration Engineer. One reviewer note (F1, dead `burst is None` branch in `_end_last_life`) needs no action.
7. **Status:** blocked: the harness is red only through failures a queued later task (DRA-125-09) clears.

## Bugs
None open. Nothing found in `game/core/last_life.py` or `game/core/run.py`.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (7 errors: `retry_armed` in `test_run_waves.py:603,618,640`, `test_run_score.py:220`, `test_run_graze.py:921,933`, `test_coin.py:650`, all expected, cleared by DRA-125-09) · core FAIL (26 failed, 3205 passed; all expected, cleared by DRA-125-09) · ui PASS (65 passed)
QA: fail (typecheck core)

## Round 1 2026-10-26

1. **Task:** Re-test of DRA-125-01-gameplay-implementer after DRA-125-09 (QA Engineer, `Verdict: pass`) landed, started by /implement.
2. **Delivered:** this round in docs/reports/qa/DRA-125-01-gameplay-implementer.md. No test saved.
3. **Checks:**
   - `check.sh`: env, lint, format, typecheck and core PASS (core 3259 passed, including `test_run_last_life.py`). The 26 core failures and the 7 `retry_armed` typecheck errors from round 0 are gone. `ui` has 3 failures, all in `test_game_over.py` (`test_game_over_with_score_shows_three_centered_lines_in_the_box`, `test_game_over_only_the_score_line_changes_with_the_score`, `test_game_over_alone_leaves_the_score_line_place_empty`). They are the ones `impact.md` expects until DRA-125-11 (UI Developer), outside the code of this task (`game/ui/game_over.py`).
   - Acceptance check re-run inline: a fall on `lives=1` logs `life lost lives=0` then `last life score=0`, the run is then game over after the delay with `game over score=0`, and `next_run` gives 3 lives, `game_over` False, score 0 and logs `new run`.
   - Core code unchanged since round 0 (`git status` shows `game/core/run.py` modified, `last_life.py` and `game_flow.py` new, nothing newer than the tested state). The round 0 edge cases stand; the new `test_run_last_life.py` now holds them in the harness.
4. **Assumptions:** the 3 ui failures belong to DRA-125-11 per the Director's note and `impact.md`.
5. **Documentation differences:** None.
6. **Next:** No bug is open. Integration Engineer for this task. The 3 `test_game_over.py` failures stay until DRA-125-11 (UI Developer); `check.sh` as a whole cannot end `QA: pass` before it.
7. **Status:** done.

## Bugs (round 1)
None open. Nothing found in `game/core/last_life.py` or `game/core/run.py`.

## Harness (round 1)
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3259 passed) · ui FAIL (3 failed, 62 passed; the three `test_game_over.py` tests expected until DRA-125-11)
QA: fail (ui)
