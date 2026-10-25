Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-111-04 (`docs/contracts/DRA-111/tasks/DRA-111-04-qa-engineer.md`): the electric ball's cases in `game/tests/core/test_collision.py`, started by `/implement`.
2. **Delivered:**
   - `game/tests/core/test_collision.py` (changed): `ElectricBallFacts` and an `electric_ball` field on `VariantCase`; `load_electric_ball_cases` and its branch in `load_variant_cases`; `ELECTRIC_BALL_CASES`; the electric ball kept out of `SHAPE_CASES`; helpers `electric_ball_at` and `firing_ball`; four tests (below), one per `## Test` behavior after the loader. The file's header names this task.
   - `game/tests/CONTEXT.md` (changed): the collision paragraph now describes the electric ball's branch, its helpers and its four tests.
   - `docs/reports/qa/DRA-111-04-qa-engineer.md` (this file).
3. **Checks:**
   - Loader: `load_variant_cases` reads `electric_ball.json` (`ball_size`, `pulse_radius` per variant, and the type's charge, fire, rays and look values), runs `check_electric_ball_variant`, and builds each variant the way `app.tuning` does. The case's `shapes` are `Circle(0, 0, pulse_radius)` written in the test, and the spawned ball's hitbox must equal them. A missing file still gives `VariantCase(type, None, None, ())`, which stays in `SHAPE_CASES` and fails by name in `test_ship_meets_every_variant_at_its_own_touching_distance` (`no tuning file for '...'`).
   - Tests, each on the one `standard` variant and any variant added to the file:
     - `test_an_electric_ball_has_no_hitbox_while_warning_or_charging_and_its_circle_while_it_fires`: `()` on every WARNING tick and every charging state, the placed circle on every firing state, over two cycles. Rules: Hitbox now; Fires.
     - `test_ship_meets_each_electric_ball_variant_firing_circle_at_its_own_touching_distance`: on its first firing state, from the left, right, above and below, just clear (no overlap, strict) and 0.5 px inside (overlap), through `touching_distance`. Rules: Hitbox; Touch; collision, Rules.
     - `test_the_ship_on_a_charging_electric_ball_overlaps_no_hitbox_until_it_fires`: the ship on the ball overlaps the ball's own box on every charging state and no hitbox, then overlaps the circle on the first firing state.
     - `test_an_electric_ball_graze_zone_is_its_firing_circle_grown_by_14_and_nothing_while_it_charges`: `()` in WARNING and on every charging state, `Circle(x, y, pulse_radius + 14)` on every firing state, and the zone meets the ship strictly at the grown circle's touching distance on four sides.
   - `game/tests/check.sh`: env PASS, lint PASS, format PASS, typecheck PASS, ui PASS (46). `core` FAIL on five cases only, all in `test_wave_files.py` (the four `placement type` refusal rows and `test_the_unknown_type_message_lists_every_type_in_enum_order_ending_planet_ufo`, which spell out the list ending `planet, ufo`). Those are `impact.md`'s row cleared by DRA-111-05. 3152 core cases pass. The `test_collision.py` collection error in `impact.md` is gone. The four new tests are in the `core` step and pass (`check.sh core tests/core/test_collision.py -k electric`: 22 passed with `test_electric_ball.py`). Last line `QA: fail (core)`, the state `impact.md` expects until DRA-111-05 lands. The acceptance check reads `QA: pass` once it does.
   - Sensitivity check, in a scratchpad copy of `game/` (never in the repo): firing from `>` instead of `>=` fails 4 of the 4 new tests; the hitbox gate changed to `is_charging() or is_firing()` fails 3; the circle placed 1 px low fails 3. A hitbox gated on `is_firing` alone (ball off screen) passes them, as the task keeps the ball on screen; `test_electric_ball.py` covers that.
   - Every expected number comes from `game/tuning/drifters/electric_ball.json`, the ship's own boxes, and `GRAZE_MARGIN` 14 (drifters.md, collision part). No bug found.
4. **Assumptions:**
   - The ball is held still (`replace(..., speed=0.0)`) after its warning, so every state is at the placed (x, y) and a firing state is reached after exactly the file's `charge_ticks`. At Level 1 with the default switches the Timer × is 1, so the file's charge is the ball's charge.
   - The electric ball takes no part in `test_ship_meets_every_variant_at_its_own_touching_distance`: it has no hitbox on its first ACTIVE state, so that test's overlap check would fail by design, as for the coin, the island and the chain lightning.
5. **Documentation differences:** None.
6. **Next:** Architect's DRA-111-05 (`test_wave_files.py`, the telegraph guard) clears the last expected `core` failures. The Integration Engineer's loader and the tuning file work follow `impact.md`. The task file stays `Status: open` for close-out.
7. **Status:** done.

## Bugs
None open.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (expected, `impact.md`: 5 `test_wave_files.py` cases until DRA-111-05; 3152 passed, the four new electric ball cases in `test_collision.py` among them) · ui PASS (46)
QA: fail (core)
