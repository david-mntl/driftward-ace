Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-104/tasks/DRA-104-05-qa-engineer.md`: `game/tests/core/test_ufo.py`, the UFO, the seed in the spawner and UFOs inside the run. Started by the main session.

2. **Delivered:**
   - `game/tests/core/test_ufo.py` (new): 15 tests (16 cases), one per behavior of the task's `## Test` list; the drawn boxes and timeline test runs once from each side. `test_a_ufo_is_born_in_warning_with_the_shared_warning_and_starts_just_outside_a_wall`, `test_a_ufo_refuses_a_missing_y_or_seed_a_band_miss_a_specialty_and_wrong_tuning_in_order`, `test_a_seed_is_refused_on_any_other_drifter_and_birth_carries_the_seed_and_the_multiplier`, `test_placement_seed_is_the_same_for_a_source_and_index_and_lies_in_range`, `test_a_ufo_crosses_at_its_speed_and_flies_level_until_it_is_fully_on_screen`, `test_each_pick_follows_the_contract_from_its_seed`, `test_over_many_seeds_the_weave_keeps_the_band_the_speed_limit_and_the_turn_limit` (`smoke`), `test_the_easing_table_tick_for_tick`, `test_weave_brake_speed_and_stop_distance_at_the_contracts_examples`, `test_the_tuning_checks_accept_the_gdd_values_and_refuse_each_broken_rule_in_order`, `test_the_same_seed_gives_the_same_path_another_seed_another_and_update_never_mutates` (`determinism`), `test_level_scaling_speed_weave_speed_and_turn_by_hazard_speed_and_intervals_by_timer`, `test_a_ufo_has_its_drawn_boxes_and_timeline_from_both_sides` (two cases), `test_touching_the_disc_or_the_dome_is_one_hit_and_the_cooldown_holds`, `test_a_ufo_logs_spawn_active_each_hit_and_gone_and_nothing_from_core_drifters`.
   - `game/tests/CONTEXT.md` (changed): a paragraph for `test_ufo.py`, placed before the `test_floating_island.py` entry.

3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, typecheck, ui PASS. `core`: 3089 passed, 3 failed. The 3 failures are the unknown-type rows of `test_wave_files.py` (`placement type 'ufo'`, `'Meteorite'`, `''`), the Impact table's expected failures for task DRA-104-06. All 16 tests of `test_ufo.py` pass, in the `core` step (about 7 s, 4 s of it the many-seed sweep).
   - The task's acceptance check ("`QA: pass` once the Impact table's expected failures are cleared, with `test_ufo.py` in the `core` step and all its tests passing") holds as far as it can before task DRA-104-06.
   - Mutation checks, inline on a scratch copy of `game/` (game code untouched): `<` to `<=` in the room rule, the turn not scaled by hazard speed, the pick counted one tick late, no landing snap, the on-screen edge made strict, the next seed not drawn, `floor` changed to `round` on the interval, and a shifted room each make `test_ufo.py` fail.
   - Expected values come from the GDD values written at the top of the file and the contract's tables (Easing, timeline, Level 8 row: weaving on n 15, dropped on n 243, 42 to 68 ticks); the picks are replayed from the contract's Pick rules with `random.Random`. The `placement_seed` literals were worked out from the contract's formula, `random.Random(f"{source}#{index}").getrandbits(32)`.

4. **Assumptions:**
   - The contract's Pick step 1 is read literally: the direction draw (`random() < 0.5`) happens on the first pick only, and later picks start at the interval draw. The sentence "Draws 2 and 3 happen on every pick" and step 1's wording both say so, and the code does the same. A reading where the direction draw is also spent on later picks would give other paths. If the Architect means that, the contract needs one more sentence and the tests (`reference_pick`) change with it.
   - Both ends of the Tuning checks' range and the exact stopping distance (19.312) are tested with values clear of float dust (19 refused, 20 accepted), not at the boundary itself.
   - A still UFO (`still`: no speed, weaving, no pick due) is built with `dataclasses.replace` on the UFO's public fields, to hold the hit tests in place. The easing table does the same to start a swing with `target_y` 220 on tick 1.

5. **Documentation differences:** None.

6. **Next:** Integration Engineer once the Impact table's expected failures clear (DRA-104-06 fixes the three `test_wave_files.py` rows). The task file stays `Status: open` for close-out. The Architect may want to confirm the Pick step 1 reading in Assumptions.

7. **Status:** done.

## Bugs
None. The 3 `test_wave_files.py` failures are the contract's expected Impact failures for task DRA-104-06, not bugs in code. Every new test passes against the code.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (3 expected: `test_wave_files.py`, task DRA-104-06; `test_ufo.py` 16 passed) · ui PASS
QA: fail (core)
