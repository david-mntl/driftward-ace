Verdict: pass
Created by: qa-engineer

1. **Task:** Test task `docs/contracts/DRA-56/tasks/DRA-56-03-qa-engineer.md` (Architect, Linear DRA-59): the ship against every fireball variant, and the tail alone.
2. **Delivered:**
   - `game/tests/core/test_collision.py`: a fireball branch in the loader (`load_fireball_cases`, `circles_and_boxes`, `FIREBALL_CASES`) and one new test, `test_ship_meets_the_fireball_tail_alone`. The existing tables, the chain lightning branch and the other ship tests are unchanged.
   - `game/tests/CONTEXT.md`: the `test_collision.py` line names the fireball branch.
3. **Checks:**
   - `check.sh` ends `QA: pass`. The `core` step runs 8 fireball cases: `fireball-small`, `fireball-small-invert`, `fireball-big` and `fireball-big-invert`, each through `test_ship_meets_every_variant_at_its_own_touching_distance` and `test_ship_meets_the_fireball_tail_alone`. The ids come from `game/tuning/drifters/fireball.json`, so a new size is covered by its entry alone. No test code names a variant.
   - The touching-distance test already checks no overlap in WARNING, overlap once ACTIVE on the ship's center, and each side just clear (no overlap) and 0.5 px inside (overlap). The fireball goes through it unchanged.
   - The tail-alone test places the tail's center 0.5 px inside the foot's bottom edge and 0.5 px inside its outer side edge (right without `invert`, left with it). It asserts the head is clear there and the tail overlaps, then moves the tail just clear and asserts no overlap.
   - The loader builds `FireballTypeExtra` and `VariantTuning` with `fireball_hitbox` and never imports `app`.
   - Meteorite, satellite and chain lightning cases still pass from their files. An inline run with the tuning folder pointed at an empty path gives no-file cases for every type, and the first test fails with `no tuning file for 'meteorite'`, naming the type.
4. **Assumptions:** The task's "its center 0.5 px inside the ship's nearest edge on an axis" is read as the tail circle's center, on two axes: below the foot, and at the foot's outer side. The tail trails up and to one side of the head, so the head would overlap the ship from any other side. Each placement asserts "head clear", so a future variant that cannot meet that placement fails with a message saying so.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer is not involved here. The Architect can close out DRA-56-03. The fireball tests in the run belong to DRA-56-04.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
