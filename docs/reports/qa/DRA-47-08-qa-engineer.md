Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-47-08 (the chain lightning, the new base hooks, chain lightnings in the run), started by the main session.
2. **Delivered:** `game/tests/core/test_chain_lightning.py` (new), `game/tests/CONTEXT.md` (one line added for the new file). This report: `docs/reports/qa/DRA-47-08-qa-engineer.md`.
3. **Checks:**
   - `game/tests/check.sh`: env, lint, format, core, ui PASS. Core runs 1312 tests, 26 of them new, all pass, and none fails against the code. Typecheck FAILS with 4 errors, all in `game/app/tuning.py:250-251` (`Line` has no `cx`, `cy`, `h`, `w`). The Integration Engineer updates that file during DRA-47 integration (`systems/app.md`, Ownership), so per the main session it doesn't fail or block this task. The new file adds no typecheck error. Run on its own, `check.sh core` ends `QA: pass`.
   - One test per behavior of the task's `## Test` list, 10 behaviors in 20 test functions (the layout test runs once per variant):
     - Born and start: `test_chain_lightning_defaults_to_pair_flat_needs_x_and_starts_above_the_top`.
     - Layouts: `test_every_layout_and_its_invert` (7 variants, both `invert` values) and `test_diagonals_and_the_l_have_the_left_node_highest_and_the_triangle_points_up`.
     - Cycle: `test_the_cycle_charges_then_fires_and_keeps_cycling_while_it_falls`, `test_the_cycle_at_level_8_uses_the_shorter_charge_and_the_same_fire`.
     - Rays: `test_rays_grow_one_per_step_up_to_charge_rays_and_follow_the_shorter_charge` (Level 1, Level 8 at 84 ticks, a charge held at 45).
     - Scaling: `test_the_charge_scales_with_the_timer_and_never_goes_below_telegraph_min`, `test_scale_timer_rounds_up_and_never_adds_a_tick_to_a_whole_product` (every tick count 1 to 300 against every Timer × from an exact Decimal ceiling).
     - On screen: `test_an_arc_fires_only_while_both_its_nodes_are_on_screen` (18 hand cases at the 0 and 640 and 480 px boundaries) and `test_an_arc_stops_on_the_first_state_one_of_its_nodes_leaves`.
     - Hitbox: `test_the_hitbox_is_empty_until_an_arc_fires_and_then_the_arcs_and_their_nodes`.
     - Warning: `test_the_warning_sits_above_the_node_nearest_the_ship_and_stays_put`, `test_the_warning_copy_is_the_point_up_triangle_for_every_variant_and_invert`, `test_the_meteorite_and_the_satellite_come_back_unchanged_from_settle_warning`.
     - Leaving: `test_it_is_dropped_once_every_node_is_fully_below_the_floor` (all 7 variants, both inverts, drop on the exact tick; the pair_flat case is the contract's T+260).
     - In the run: `test_in_the_run_a_charge_never_hits_and_a_firing_arc_hits_once_then_the_chain_cools`, `test_in_the_run_the_chain_keeps_falling_while_it_cools`, `test_in_the_run_the_whole_chain_cools_together_and_hits_again_on_the_first_tick_after`, `test_in_the_run_a_node_hits_only_while_an_arc_fires`, `test_in_the_run_an_invulnerable_touch_is_no_hit_and_starts_no_cooldown`.
   - Mutation check on a copy of `game/` in the scratchpad (nothing saved in the repo): 16 real mutations of `chain_lightning.py` and `base.py` (charging boundary off by one, ray formula, non-strict on-screen test, warning tie-breaks, node filter in the hitbox, warning clamp, no 6-decimal rounding in `scale_timer`, no `telegraph_min`, fire scaled, y placement, mirror swapped, speed drift, line list missing from the hitbox). All 16 were caught.
4. **Assumptions:**
   - The chain is moved to a state with `dataclasses.replace` (`ticks_in_phase`, `x`, `y`, `speed`, `has_entered`) where a test needs an exact firing state or a still chain, as `test_collision.py` does.
   - A node-only touch uses a ship at (245.5, 240) beside the left node of a `pair_flat` at (320, 240): the ship's foot reaches the node but not the arc (checked inside the test against my own shapes).
   - A few tests build the tuning with `fire_ticks=1000` so one firing phase covers a whole fall or the whole cooldown. The value is a test setting, not a GDD number.
   - The `unit` coordinates of the diagonal and the triangle use the contract's rounded values (0.35355339, 0.70710678, 0.4330127); sizes are compared to the Layout table within 0.01 px.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer: `game/app/tuning.py` still fails typecheck on `Line` (lines 250-251); that is the expected DRA-47 integration change. Architect and Scope Guardian: nothing open from this task. Task file stays `Status: open` for close-out.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (4 errors, all `game/app/tuning.py`, expected until integration) · core PASS (1312 tests) · ui PASS (17 tests)
QA: fail (typecheck)
