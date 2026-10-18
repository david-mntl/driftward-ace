Verdict: pass
Created by: qa-engineer

1. **Task:** test task `docs/contracts/DRA-62/tasks/DRA-62-05-qa-engineer.md` (the coin's collision cases in `test_collision.py`), started by the Director's agent.
2. **Delivered:** `game/tests/core/test_collision.py` (changed), `game/tests/CONTEXT.md` (changed: the `core/test_collision.py` paragraph), this report.
3. **Checks:**
   - `game/tests/check.sh` ends `QA: pass`; the `core` step runs 1350 tests, the coin cases among them (8: four tests, two variants).
   - Before the change `test_collision.py` failed at collection with `KeyError: 'hitbox'` (the coin's file has no `hitbox`), as the contract's Impact row says.
   - The four tests, one per `## Test` line:
     - `test_ship_meets_every_coin_variant_at_its_own_touching_distance`: from each of the four sides the coin's box doesn't overlap the ship when touching and does 0.5 px inside. Also asserts the case's hitbox is the file's crystal width by body height (12 x 10).
     - `test_a_coin_overlaps_the_ship_on_the_state_it_is_spawned_on`: the coin is ACTIVE with `ticks_in_phase` 0 and `warning_ticks` 0, its hitbox isn't empty, and it overlaps the ship on that first state, centered and 10 px off center.
     - `test_only_the_coin_box_counts_not_its_points_or_its_ring`: six places where a point or the ring crosses the ship's edge (asserted from the file's sizes) while the box touches it or is a hair clear: no overlap. A hair inside: overlap.
     - `test_a_coin_touch_is_a_collect_never_a_hit`: `effect_on_touch()` is `COLLECT` and not `HIT`, and `graze_zone()` is `()`, on and off the ship.
   - Sensitivity: with `coin_hitbox` patched inline to a 12 x 20 box (the points counted), 4 of the 8 coin cases fail (the touching-distance test and the box-only test, both variants). The patch was not saved.
   - Expected numbers come from `game/tuning/drifters/coin.json` and the ship's hitbox; none is invented. No variant is named in test code.
4. **Assumptions:** the coin's cases are kept out of `SHAPE_CASES` (the first shared test needs a WARNING state the coin never has). A coin with no tuning file still lands in `SHAPE_CASES` and fails that test by name. The loader branch builds `CoinTypeExtra` from the file's whole numbers with `int(...)`, as the schema makes them integers.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, or the Director's next task (`DRA-62-06-qa-engineer` covers the coin's behavior, the run's collect rules and the popups). The task file stays `Status: open` for close-out.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core PASS · ui PASS
QA: pass
