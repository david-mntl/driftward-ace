Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-76/tasks/DRA-76-07-qa-engineer.md`: tests for the wave state, the wave clock, the playlist runner and the random picker (`core/waves.py`), started by the Director.
2. **Delivered:**
   - `game/tests/core/test_waves.py` (new): 18 tests, one or two per behavior of the task's `## Test` list.
     - `test_start_waves_gives_wave_0_at_level_1_from_0_px_with_nothing_due_and_logs_its_start`
     - `test_a_placement_is_due_once_on_the_first_tick_its_trigger_is_reached_in_trigger_order`
     - `test_a_wave_ends_on_the_tick_its_distance_reaches_its_length_a_micro_px_short_counts`
     - `test_with_no_rest_the_next_wave_starts_where_the_last_ended_with_its_due_placements`
     - `test_several_waves_can_end_on_one_tick_each_starting_where_the_last_ended`
     - `test_fixed_waves_play_in_playlist_order_then_the_random_slots_wave_0_is_no_slot`
     - `test_the_level_rises_on_the_tick_the_last_wave_of_its_playlist_ends_never_inside_a_wave`
     - `test_a_level_with_no_slots_is_passed_on_the_tick_it_starts`
     - `test_at_level_8_the_level_never_rises_and_random_picks_go_on_forever`
     - `test_a_random_pick_is_a_pool_wave_allowed_at_the_level_and_never_the_one_that_just_played`
     - `test_a_random_slot_never_repeats_the_last_wave_after_zero_fixed_rest_or_rise`
     - `test_the_same_seed_gives_the_same_waves_and_next_run_waves_restarts_with_a_new_seed` (`determinism`)
     - `test_a_random_pick_starts_from_pick_seed_and_stores_the_next_seed_it_draws`
     - `test_pick_pool_wave_draws_from_the_chooser_it_is_given_only`
     - `test_rest_gap_ticks_is_the_extra_rest_alone_at_every_level_while_the_base_is_0`
     - `test_a_rest_of_r_ticks_shows_on_exactly_r_states_and_the_next_wave_starts_after_it`
     - `test_no_extra_rest_leaves_no_rest_and_the_extra_rest_is_the_same_at_every_level`
     - `test_the_waves_log_each_event_once_in_the_contracts_order_and_nothing_on_a_quiet_tick`
   - `game/tests/CONTEXT.md` (changed): one paragraph for `core/test_waves.py`.
3. **Checks:** `game/tests/check.sh` ends `QA: pass`, with `test_waves.py` in the `core` step (1390 core tests passed, 18 of them new). The tests build their own books, read no `game/waves/` or `game/tuning/` file and import no expected number from `core.waves`. As a teeth check I ran the file against copies of `core/waves.py` in the scratchpad with eight mutations (`<=` to `<` on a trigger, the next wave starting at this tick's distance, the last wave not left out of a pick, the level rising on any wave end, no round to 6 decimals, a rest one tick short, the next pick seed not stored, `next_run_waves` reusing the seed). Each one failed at least one test. The game code was not touched.
4. **Assumptions:**
   - `REST_GAP_BASE_TICKS` is the constant 0, so the scaled part of `rest_gap_ticks` is not tested. The task asks only for the extra-rest-alone case.
   - A placement whose trigger is beyond the wave's length is tested only where the tick's distance stays short of it (trigger 1500 in a 1000 px wave, 150 in a 100 px wave). The overshoot case is left out, see item 5.
   - A pool wave may be named in a playlist's `fixed` list (the loader does not refuse it, contract Rules, Not checked at load). The "after a fixed wave" pick test uses that.
5. **Documentation differences:** pending Director approval. `docs/contracts/systems/waves.md`, Rules, The wave clock, steps 2 and 3, disagree on one edge. Step 3 says "A placement whose `at_px` is beyond the wave's length is never due." Step 2 says every placement from `spawned` on whose `at_px <= into` is due, and `core/waves.py` follows step 2: a 50 px wave with a trigger at 60, stepped to distance 60, hands the placement out on the tick it ends (inline run: `into` 60 >= length 50, `spawns_due` holds it). The two lines agree only while `into` stays short of the trigger. Proposed change for the Architect: in step 3 say "A placement whose `at_px` is beyond the wave's length is due only if the tick's scroll carries `into` past it; the wave never waits for it", or make `step_waves` count only placements with `at_px <= length_px`. Either way `test_waves.py` needs no change until one is chosen; it has no case for the overshoot.
6. **Next:** Architect closes out the task (it stays `Status: open` here) and decides the item 5 question with the Director. DRA-76-08 and DRA-76-09 can follow.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
