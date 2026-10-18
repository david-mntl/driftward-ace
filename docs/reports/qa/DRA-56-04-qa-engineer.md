Verdict: pass
Created by: qa-engineer

1. **Task:** test task DRA-56-04-qa-engineer (the fireball, its drawn parts, fireballs in the run), started by the Director's session.
2. **Delivered:** `game/tests/core/test_fireball.py` (new, 14 tests); `game/tests/CONTEXT.md` (one bullet for `test_fireball.py`, after the `test_chain_lightning.py` bullet); this report.
3. **Checks:** `game/tests/check.sh` ends `QA: pass`, with `test_fireball.py` in the `core` step (14 passed, 1334 core tests in all). Each line of the task's `## Test` list has its own test:
   - Start table, with and without `invert`, for corner, along the top, side and both, small and big: `test_each_entry_starts_where_the_start_table_says`.
   - Warning place for each entry, clamps at 12 px, warning stays put for all 59 WARNING states: `test_the_warning_shows_where_the_start_table_says`.
   - Straight flight at 35° from straight down, along-path speed, mirrored by `invert`, Levels 1 to 8 (angle never changes): `test_it_flies_a_straight_line_at_its_angle_and_speed_mirrored_by_invert`. A placement's `speed` replaces the Level 1 speed, with Level 8 and `as_level`: `test_a_placements_speed_replaces_the_level_one_speed_along_the_path`.
   - Hitbox, head on the center and tail touching from behind, both variants, mirrored: `test_the_hitbox_is_the_head_on_its_center_and_the_tail_touching_from_behind`.
   - Drawn parts, one box per circle at radius + 1.5, and the meteorite's footprint alone: `test_the_drawn_parts_are_one_box_per_circle_and_a_meteorites_is_its_footprint`.
   - Leaving and entering: `test_it_leaves_only_when_head_and_tail_are_both_off_and_never_before_it_entered` (tick-by-tick sweep of every entry, variant and `invert`; drop points n 202, 208 and 150), `test_it_stays_while_either_drawn_box_is_on_screen_and_goes_by_each_boxs_own_edge` (head off with the tail on, mixed edges, never at the top, never before entered, strict entering), `test_the_corner_timeline_holds_in_the_run_and_it_is_dropped_only_when_every_part_is_off` (states 258, 261, 262 and the `drifter gone` line), `test_big_invert_and_side_fireballs_are_dropped_on_the_contracts_ticks`.
   - Warning tilt and copy, including that turning the copy by the tilt puts the tail where the hitbox has it: `test_its_warning_copy_is_tilted_along_its_path_with_the_tail_back`.
   - Refuses a specialty and a tuning without type values (none, and the empty base extra): `test_it_refuses_a_specialty_and_a_tuning_without_its_type_values`.
   - In the run: a hit costs a life, the fireball keeps flying, dims, cannot hit for 180 ticks with the ship still in it, hits again on the 181st, an invulnerable touch starts no cooldown, one `drifter touch` line per hit: `test_in_the_run_a_hit_costs_a_life_and_the_fireball_keeps_flying_dim_and_cannot_hit_again`. Tail alone is a hit (head clear, then tail just clear is no hit): `test_in_the_run_touching_the_tail_alone_is_a_hit`.
   The file builds its own tuning from the GDD values, reads no `game/tuning/` file, and works out tails, velocities and boxes itself. No bug found: every new test passed against the code on its first correct run (one failure was a double `tick` call in my own test, fixed in the test).
4. **Assumptions:** the cooldown test uses a placement speed of 0.02 px/tick so the ship stays in the fireball for 181 ticks; a real-speed fireball would leave the ship in under a second. Positions in the contract's examples are checked to 0.01 px, as the contract rounds them to two decimals. I ran `ruff format` on my own new file only.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, once the other DRA-56 QA reports are also `Verdict: pass`. The task file stays `Status: open` for close-out.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS (1334 passed, 14 in `test_fireball.py`) · ui PASS (35 passed)
QA: pass
