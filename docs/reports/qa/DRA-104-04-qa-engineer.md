Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-104/tasks/DRA-104-04-qa-engineer.md`: the UFO cases in `test_collision.py` (the loader branch, the hitbox, the touching distance on the disc and the dome, the graze zone). Started by the main session.

2. **Delivered:**
   - `game/tests/core/test_collision.py` (changed): `UfoFacts`, `VariantCase.ufo`, `load_ufo_cases`, the UFO branch in `load_variant_cases`, `UFO_CASES`, `UFO_SEED`, a seed in `drifter_at` for a UFO only, and three tests: `test_a_ufo_has_no_hitbox_while_warning_and_its_disc_and_dome_once_active`, `test_ship_meets_a_ufo_on_its_disc_and_on_its_dome_alone`, `test_a_ufo_graze_zone_is_its_disc_and_dome_each_grown_by_14`.
   - `game/tests/CONTEXT.md` (changed): the UFO's loader branch and tests added to the `test_collision.py` entry.
   - The UFO also goes through the existing `test_ship_meets_every_variant_at_its_own_touching_distance` (it is in `SHAPE_CASES`, as the planet is). A missing `ufo.json` still fails that test by name (`no tuning file for 'ufo'`).

3. **Checks:**
   - `check.sh` (full): env, lint, format, typecheck, ui PASS. `core`: 3073 passed, 3 failed. The 3 failures are the unknown-type rows of `test_wave_files.py` (`placement type 'ufo'`, `'Meteorite'`, `''`), the Impact table's expected failures for task DRA-104-06. No test in `test_collision.py` fails: all 4 UFO cases pass (`-k ufo`: the generic touching test and the three new ones).
   - Mutation checks (inline, game code untouched): a dome radius +1, the disc and dome swapped, and the dome placed at -disc_height each make the UFO cases fail.
   - Expected shapes are written from the file's sizes, never from `ufo_hitbox`. Touching placements are exact (whole-number edges); the dome's corner cases use `CLEAR_SLACK` past touching and 0.5 px inside.

4. **Assumptions:**
   - The dome alone from the side above the disc cannot be built against this ship (the dome's center is on the disc's top edge, and the ship's bottom edge is the same for the bar and the foot), so the dome alone is met from below on the foot's bottom edge and on its two bottom corners.
   - `check_ufo_variant` and `check_ufo_weave` are not called by the loader, so a bad file fails at spawn or in other tests and never as a collection error.
   - Placements use y inside the band read from the file (band top, middle and bottom for the hitbox test).

5. **Documentation differences:** None.

6. **Next:** Integration Engineer once the Impact table's expected failures clear (DRA-104-06 fixes the three `test_wave_files.py` rows). The task file stays `Status: open` for close-out.

7. **Status:** done.

## Bugs
None. The 3 `test_wave_files.py` failures are the contract's expected Impact failures for task DRA-104-06, not bugs in code.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (3 expected, `test_wave_files.py` unknown-type rows) · ui PASS
QA: fail (core)
