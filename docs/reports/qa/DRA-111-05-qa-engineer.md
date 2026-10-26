Verdict: pass
Created by: qa-engineer

1. **Task:** Test task DRA-111-05 (wave loader and telegraph guard learn the electric ball), started by the Director through the pipeline.
2. **Delivered:** `game/tests/core/test_wave_files.py` (changed), `game/tests/core/test_drifter_registration.py` (changed), `game/tests/CONTEXT.md` (the two entries brought up to date).
3. **Checks:** `game/tests/check.sh` ends `QA: pass`: env, lint, format, typecheck, core, ui all PASS. New or changed tests, one per bullet of the task's `## Test`:
   - `test_the_unknown_type_message_lists_every_type_in_enum_order_ending_ufo_electric_ball` and the `placement type` refusal rows: the message ends `planet, ufo, electric_ball)`. The old tests that ended `planet, ufo)` are the ones `impact.md` expected to fail.
   - `test_an_electric_ball_needs_x_takes_no_seed_and_loads_with_invert`, plus two `REFUSALS` rows (no `x`, a seed): refused naming the placement and the drifter's message (`placements[1]: electric_ball placement needs x`, `... electric_ball has no seed`), with the spawner's `ValueError` as `__cause__`; seeds 0, 5 and 4294967295 all refused; `invert` true and false load and are kept.
   - `test_an_electric_ball_below_120_px_is_refused_and_one_at_120_px_is_accepted`: below 120 refused as `a hazard (electric_ball) at <n> px is inside the first 120 px`, 120 and above loaded.
   - `test_only_a_drifter_with_a_telegraph_says_so`: the electric ball's `telegraph_ticks(None)` is None, with its own `ElectricBallTypeExtra` it gives `charge_ticks` (120, and 77 when changed, never the fire), another type's values give None; every drifter but the chain lightning and the electric ball still says None.
   Expected values come from the contract and the GDD, written in the files. The test tuning for the electric ball (16 px, pulse 64, `speed_ratio` 0.375, warning 60) is built in `make_tuning` from the GDD values; no `game/tuning/` or `game/waves/` file is read.
4. **Assumptions:** "None without its type values" is also tested with another type's extra (the chain lightning's); the contract's `telegraph_ticks` signature takes a `DrifterTypeExtra | None`, so a foreign extra counts as no type values. The ball rows sit after a meteorite row at index 0, as the UFO rows do.
5. **Documentation differences:** None.
6. **Next:** The task file stays `Status: open` for close-out. The Integration Engineer's loader work from `impact.md` is untouched by these tests.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
