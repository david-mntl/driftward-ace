Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-39/tasks/DRA-39-07-qa-engineer.md`: bring `tests/core/test_run_drifters.py` up to the DRA-39 contract and add the cooldown and entering tests. Started by the Director.
2. **Delivered:**
   - `game/tests/core/test_run_drifters.py` (changed)
   - `game/tests/CONTEXT.md` (one bullet: how this file builds its tuning and clears invulnerability)
   - this report
3. **Checks:** `game/tests/check.sh` ends `QA: pass`. The core step runs 448 tests, all passing, including the updated file. Every test in the task's `## Test` list has one test:
   - hit starts the cooldown on every touching drifter, costs one life, the drifter stays and moves: `test_a_hit_starts_the_cooldown_and_the_drifter_keeps_moving`, plus `test_two_meteorites_on_one_tick_cost_one_life` (both start their cooldown, a far one does not).
   - blocked for N ticks, hits on tick N+1, with invulnerability cleared before each tick, at 180 and at 4: `test_a_hazard_cannot_hit_for_its_cooldown_and_hits_again_after` (parametrized).
   - `brightness()` is 0.75 from the hit state through the state after the 179th tick, 1.0 from the 180th: `test_a_cooling_hazard_is_dim_for_exactly_its_cooldown`.
   - another hazard hits when invulnerability ends, its own cooldown starts, the first count goes on (150 on T+30, 149 on T+31): `test_another_hazard_hits_when_invulnerability_ends_and_the_first_count_goes_on`.
   - protected touch starts no cooldown, count goes on while protected, waiting and on a fall tick, hit tick runs in full at game over then freezes, retry has no drifters: `test_a_cooldown_counts_on_every_playing_tick_and_freezes_at_game_over`.
   - flat satellite outside the left wall: kept at x -18 (first ACTIVE state), enters next tick, present at n=273, dropped at n=274: `test_a_satellite_outside_the_wall_is_kept_until_it_has_entered_then_dropped`.
   - inverted satellite outside the wall never dropped (600 more ticks), meteorite present at 205 and dropped at 206 active ticks: `test_a_drifter_that_never_enters_is_never_dropped_and_a_meteorite_still_is`.
   - satellite life logs spawn, active, gone, plus one touch per hit (a slow satellite on the ship hits twice): `test_a_satellite_life_logs_spawn_active_gone_and_one_touch_per_hit`.
   - DRA-29 tests brought up: `rock()` has no `hit_ship`, every `hit_ship` check is a `rehit_ticks_left` check, `test_a_meteorite_hits_once` is replaced.
   `tests/core/test_run.py` is untouched and passes.
4. **Assumptions:**
   - Values come from the GDD and the contract, copied with their source at the top of the file: warning 60 ticks, speed ratio 0.375 for both drifters, cooldown 180, dim 0.75, satellite 36 × 12 with its two boxes, drop ticks 274 and 206. The file's old test values (warning 30, speed ratio 0.75) became the GDD values, because the contract's timelines use them. Loop lengths in the DRA-29 log test grew to match (meteorite now needs 266 ticks to drop). The test `test_a_warning_never_hits_and_ends_after_the_30th_step` is renamed `..._after_its_last_step` since the warning is 60 now.
   - The "small set value" is 4 ticks, set on the drifter (`rehit_cooldown_ticks=4`) through `rock()`.
   - The two-hit satellite log test uses `Placement(speed=0.2)` to keep the satellite on the ship for over 181 ticks. `Placement.speed` is in the contract's Interface.
   - I ran `ruff format` on my own test file only. I did not run `check.sh fix`.
5. **Documentation differences:** None.
6. **Next:** Nothing open for this task. The Architect or the Director closes out task DRA-39-07. The other DRA-39 QA reports decide when the feature goes to the Integration Engineer.
7. **Status:** done.

## Bugs
None. Every new test passes against the current code.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (448 passed) · ui PASS (17 passed)
QA: pass
