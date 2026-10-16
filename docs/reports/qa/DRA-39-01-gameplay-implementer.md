Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-39-01-gameplay-implementer (unknown shapes raise, shared re-hit cooldown, entering and leaving, start position, new placement fields, run steps 3, 7, 8, 9), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-39-01-gameplay-implementer.md. No test files saved (Verify mode).
3. **Checks:**
   - `check.sh` ends `QA: fail (typecheck core)`. Both failures are the ones the task's Acceptance check and the Impact tables (`drifters.md` line 647, 648; `run.md` line 251) expect. `typecheck`: 18 errors, 3 in `tests/core/test_drifters.py`, 15 in `tests/core/test_run_drifters.py`. `core`: 16 failed, 49 passed. 4 failures are in `test_drifters.py` (`test_default_placement_gets_default_variant_and_start_y`, `test_is_off_screen_rules`, `test_meteorite_hits_once`, the registry test) and 12 in `test_run_drifters.py`, every one on `hit_ship`. `test_run.py`, `test_collision.py` and all 17 ui tests pass. Lint, format and env pass. Tasks DRA-39-06 and DRA-39-07 rebuild the two broken files. I treat this as met, not as an open bug.
   - Acceptance check reproduced from `game/` (PYTHONPATH set, SDL dummy). Output, all seven lines as the task expects:
     ```
     -14.0 180 0.75 True 1.0 False
     1.42
     meteorite placement needs x
     meteorite has no invert
     unknown shape kind 'str'
     [60, 241] {60: (180, 0.75), 239: (1, 0.75), 240: (0, 1.0)}
     2 True False
     ```
     Run twice: byte-identical.
   - Cooldown edge cases, all correct:
     - Cooldown lengths 0, 1 and 5: hits on ticks 3, 34, 65 (invulnerability, 30 ticks, is the only gate).
     - Two rocks touching on one tick: one life lost, both counters at 180 in the state after that tick.
     - A third rock hitting while two are cooling: lives 2 to 1. The two old counters keep counting (141, 140) and are not restarted. The new one starts at 180 and shows 179 the next tick.
     - Counter counts down on protected ticks: 180, 179, 178 and so on.
     - A fall tick counts a cooling hazard down (179 to 178) and starts no hit.
     - A hit during the respawn wait: the wait stays, the counter keeps going, the next hit lands 183 ticks after a hit on tick 2 (cooldown ticks 3 to 182 blocked).
     - Game-over tick: both counters at 180, frozen on the next ticks. Retry gives 0 drifters and 3 lives.
     - `step_run` leaves its input run unchanged.
   - Entering and leaving, correct:
     - A rock at x -14 or 654 (edge touching from outside) is not on screen. At -13.9 or 653.9 it is.
     - The same holds at y -14 and 494.
     - A WARNING rock never gets `has_entered`.
     - Off screen needs `has_entered`: y 494 with `has_entered` is off screen, y 493.9 is not, y 494 without it is not.
     - A rock placed below the floor at y 600 is never entered and stays, as the contract says.
     - A default-start rock enters on tick 2 and is dropped on tick 207.
   - Spawner, correct:
     - `Placement(METEORITE, 320.0)` positional works.
     - `specialty_enabled` True raises `meteorite has no specialty`. False and None are fine.
     - `as_level` 9 raises. An unknown variant raises.
     - Level 8 with `HazardRules(7, 0.5)`: cooldown 7 and dim 0.5, so they are not scaled.
     - Placement speed 2.0 with `hazard_speed_scaling` off stays 2.0. Speed 0.0 is kept at Level 8.
   - Collision, correct:
     - `place_hitbox`, `grow_hitbox` and `hitboxes_overlap` raise `unknown shape kind 'Line'` for a foreign class. `hitboxes_overlap` raises with the other hitbox empty, with the bad shape on either side, and with a good shape first.
     - Empty hitboxes are fine. Edge-only box contact is not an overlap.
   - Review For QA lines: all five covered above. Review finding F1 is a note with no action.
4. **Assumptions:** The red `check.sh` core and typecheck steps are accepted because the task and both contracts' Impact tables list those exact tests. If the Director wants the strict rule (`QA: pass` required), the verdict would move to blocked until DRA-39-06 and DRA-39-07 land.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer can proceed on this task. Architect and QA tasks DRA-39-06 and DRA-39-07 still have to rebuild the two broken test files before `check.sh` returns `QA: pass`. One limit worth knowing, in line with the contract and not a bug: a rock placed off screen that moves fast enough to skip the whole screen in one tick (for example y -14, speed 600) never enters and is never dropped.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck FAIL (18 errors, only in `tests/core/test_drifters.py` and `tests/core/test_run_drifters.py`, expected by the task) · core FAIL (16 failed, 49 passed, only those two files, expected) · ui PASS (17 passed)
QA: fail (typecheck core)
