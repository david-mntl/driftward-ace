Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-56-01-gameplay-implementer (the fireball in `game/core/drifters/fireball.py` and the base `drawn_parts` hook), started by /implement. Review status `reviewed`.
2. **Delivered:** docs/reports/qa/DRA-56-01-gameplay-implementer.md
3. **Checks:**
   - `check.sh`: `QA: fail (core ui)`. Both failures are the ones the task's Acceptance check names as expected until DRA-56-02, DRA-56-03 and `game/tuning/drifters/fireball.json` exist: core 1312 pass, 1 fail (`test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[fireball-None]`); ui 34 pass, 1 fail (`test_drifter_registry.py::test_drifter_lists_match_everywhere`: tuning files lack `fireball`). env, lint, format and typecheck pass. Neither failure comes from the three files this task builds.
   - Acceptance check run from `game/` with the task's command body as a script: all twelve lines match the task's expected output, byte for byte. Run twice: identical (`cmp`).
   - Edge cases that behave correctly:
     - Leaving from the top-left corner: head box top 489.23 and tail box top 481.58 on ACTIVE n 202, so `is_off_screen` turns True on n 202 (tick 262), False on n 198 to 201 while the tail still shows. Big: n 209. Invert gives the mirrored x (281.68 against 358.32), same tick.
     - Side entries: left wall at y 100 and right wall at y 100 with `invert` both drop on n 159, mirrored. A side entry at y 470 drops on n 13 (below the floor). Each enters on its first ACTIVE tick.
     - Leaving by side with different edges per circle: flying left with `invert` (x -14), the head box is past the wall (right edge -2.0) and the tail box is not (1.78): not off. At x -24 both are past: off. Mirrored on the right (x 652: not off; x 668.03: off).
     - A fireball not yet entered is never off, even at y 900. A WARNING fireball is never off or on screen. A fireball placed at x -100 enters on ACTIVE n 51. x 700 never enters and is never dropped, as the contract says for a drifter that has not been on screen.
     - Start: x 0 gives (0, -10.5). y -5 gives x -10.5. x and y both set are kept as given. `invert` mirrors the tail offsets exactly (-9.0338 and 9.0338).
     - Speed: the path length equals `speed` (3.0926). Level 8 gives 4.39, angle stays 35. `hazard_speed_scaling` off keeps 3.0926 at Level 8. A placement speed 10.0 is kept. Angle 0 gives a tail straight above (0, -15.75) and vertical velocity only. A tuning with no `FireballTypeExtra` raises `fireball tuning has no type values`. A specialty raises `fireball has no specialty`.
     - Warning copy: big gives 32 x 48 with circles at (0, 8, r 16) and (0, -16, r 8). The copy of an inverted fireball keeps `invert` and tilts -35.
     - In `core.run`: the corner fireball is dropped on tick 262 (60 warning ticks plus n 202). A hit on the head and a hit on the tail each cost one life, set 30 ticks of invulnerability and a re-hit cooldown of 180. While invulnerable, no hit, and it keeps moving 1.7738 per tick. It crosses x from -10.5 outward with a constant step of 1.7738, so walls and other drifters don't stop it.
     - Determinism: three fireballs (corner, inverted big, side) with a scripted thrust sequence for 300 ticks, run twice: identical lives, invulnerability, positions and cooldowns.
     - Base `drawn_parts` hook: 200,000 random meteorites (random size, position, `has_entered`) compared with the old footprint formulas for `is_partly_on_screen` and `is_off_screen`: 0 mismatches. The existing meteorite, satellite and chain lightning tests pass.
   - Review For QA lines: all five covered above. Review findings F1 to F3 are notes with no action; F3 (stale `warning_copy` docstring in the base) is outside this task's Builds and has no effect on behavior.
4. **Assumptions:** The red `check.sh` core and ui steps are accepted because the task's Acceptance check lists those exact two tests as expected until the later tasks land (same call as in the DRA-39-01 report). If the Director wants the strict rule (`QA: pass` required), this verdict moves to blocked until DRA-56-02, DRA-56-03 and the tuning file exist. `SCREEN_H` is 480, as in the task's timeline.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer can proceed on this task. `check.sh` returns `QA: pass` only after DRA-56-02 (view), DRA-56-03 (collision test) and `game/tuning/drifters/fireball.json` exist.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (1312 passed, 1 failed: `test_collision.py::test_ship_meets_every_variant_at_its_own_touching_distance[fireball-None]`, expected by the task) · ui FAIL (34 passed, 1 failed: `test_drifter_registry.py::test_drifter_lists_match_everywhere`, expected by the task)
QA: fail (core ui)
