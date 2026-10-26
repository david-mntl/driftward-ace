Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-125-09-qa-engineer (the last life, the frozen game-over tick, `next_run`, the burst and `hold_arrows` in `core.run` and `core.last_life`, plus the existing core tests brought in line), started by /implement.
2. **Delivered:**
   - `game/tests/core/test_run_last_life.py` (new): 29 tests, one per behavior of the task's `## Test` list (some parametrized).
   - `game/tests/CONTEXT.md`: a paragraph for the new file, and the lines for `test_run_score.py`, `test_run_graze.py` and `test_run_waves.py` that spoke of game over, retry or `retry_armed`.
   - Existing core tests changed, only where `impact.md` lets them fail from DRA-125-01: `game/tests/core/test_run.py`, `test_run_score.py`, `test_run_waves.py`, `test_run_drifters.py`, `test_run_graze.py`, `test_coin.py`.
3. **Checks:**
   - `check.sh`: env, lint, format, typecheck and core PASS (3259 core tests pass, 29 of them the new file). `ui` fails with the 3 `test_game_over.py` tests (`test_game_over_with_score_shows_three_centered_lines_in_the_box`, `test_game_over_only_the_score_line_changes_with_the_score`, `test_game_over_alone_leaves_the_score_line_place_empty`). Those are in `impact.md`, "Failures expected", cleared by DRA-125-11. Nothing else fails, and none of `impact.md`'s DRA-125-01 failures is left.
   - The last-life values are written at the top of the new file (`LAST_LIFE_DELAY` 120, count 12, speed 1.0, size 3) and `RULES` is built from them. No `game/tuning/` file is read. `start_run()` is compared with those default values.
   - The new tests catch real faults: I copied `game/` to the scratchpad and broke `run.py` ten ways (burst y on the fall, no wave clock on last-life ticks, game over one tick late, `hold_arrows` a no-op, popups not aging, final score off by one, `ship_visible` true during the last life, no `new run` log, the same waves seed in `next_run`, `last_life_rules` dropped by `next_run`). Each one fails a test of the new file. No game code was changed.
   - Changes to the existing tests, each by the contract's Rules (The last life, A last-life tick, A game-over tick, `next_run`):
     - `test_run.py`: `test_losing_the_last_life_ends_the_run` is now `test_losing_the_last_life_starts_the_last_life`; `test_game_over_freezes_everything` and `test_a_held_arrow_never_starts_a_new_run` run the delay first; `test_a_new_run_starts_like_the_first` uses `next_run`; the log test expects `last life`, one `game over` and `new run`.
     - `test_run.py::test_retry_has_no_delay_when_released_at_game_over` is removed: the arrow retry is gone from the contract, so nothing is left to test there. Its fresh-run checks are in `test_a_new_run_starts_like_the_first` and the new file.
     - `test_run_score.py`: the score freezes on the death tick and the scroll runs on (`_death`); `next_run` gives 0; the log test expects `last life score=<n>` then `game over score=<n>` and no other line naming the score.
     - `test_run_waves.py`: `die` is the last-life tick and `finish` steps the delay; the freeze, the new-run seeds, the determinism script and the log order follow.
     - `test_run_drifters.py`, `test_run_graze.py`, `test_coin.py`: the cooldown counts through the last life and freezes at game over; popups and rings age through it and freeze at game over; `next_run` clears them.
   - Acceptance check: `check.sh core` ends with all tests passing, `test_run_last_life.py` among them. `check.sh` as a whole ends `QA: fail (ui)` only because of `impact.md`'s DRA-125-11 failures.
4. **Assumptions:** None beyond the task. The new file's `fall_run` and `hit_run` use a moving scroll (70 moving ticks), so the final score on tick 1 is 7 m plus whatever the tick pays. A parked coin has moved 1.1 px with the scroll before it is collected, so its popup starts 1.1 px below the coin's start: the tests expect that.
5. **Documentation differences:** None.
6. **Next:** QA Engineer for DRA-125-10, DRA-125-11 and DRA-125-12. DRA-125-11 clears the 3 `test_game_over.py` failures. No open bug.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (3259 passed) · ui FAIL (3 failed, 62 passed, the three `test_game_over.py` tests expected by `impact.md`, cleared by DRA-125-11)
QA: fail (ui)
