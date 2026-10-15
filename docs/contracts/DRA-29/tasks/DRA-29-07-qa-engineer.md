Feature: DRA-29
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/objects.md#rules
Status: done
Linear: DRA-36

## Do
Write permanent tests for hitboxes, the ship's hitbox, the level table, the spawner and the meteorite. Every later object and the graze feature build on these, and a wrong overlap or speed makes a death unfair (Pillar 2), so they need a guard. Test through the Interface in `docs/contracts/systems/objects.md` and `docs/contracts/systems/ship.md`: `core.collision`, `core.ship` (`ship_hitbox`, `SHIP_HITBOX`, `TOP_SIDE_SPEED`, `spawn`), `core.levels`, `core.objects.base`, `core.objects.tuning`, `core.objects.registry`, `core.objects.spawner`, `core.objects.meteorite`. Build the tuning records in the test from the GDD values below; never read `game/tuning/` here.

`tests/core/test_collision.py`, one test per behavior:
1. Two circles, two boxes, and a circle and a box overlap when they share area, and don't when they only touch at an edge or a point. Source: objects.md, Rules, Collision (strict); 07-objects.md, rule 8.
2. `hitboxes_overlap` is True when any shape of one overlaps any shape of the other, and an empty hitbox overlaps nothing. Source: objects.md, Rules, Collision.
3. `grow_hitbox` grows a circle's radius by the margin and a box by the margin on all four sides (w and h by twice it), centers unchanged. Source: 06-scoring.md, rule 3.
4. The ship's hitbox is an inverted T: placed at spawn, a bar 12 wide and 32 tall centered on (320, 240), and a foot 32 wide and 12 tall whose bottom edge is the ship's bottom edge (y 256). A small circle in an empty upper corner of the 32 × 32 square (for example centered at (308, 228), radius 3) doesn't touch it; the same circle on the bar does. Source: 04-ship.md, hitbox (guess), ship_w, ship_h; systems/ship.md, Rules, Hitbox.
5. The ship's top sideways speed is `thrust_side × drag_x / (1 − drag_x)` ≈ 6.58 px/tick. Source: 04-ship.md, derived values.

`tests/core/test_objects.py`, one test per behavior:
6. The level table: hazard speed × and Timer × for Levels 1 to 8 match 08-difficulty.md; levels 0 and 9 raise `ValueError`; `level_at` is 1 at 0 m and at any distance while only Level 1 has a start. Source: 08-difficulty.md, Values and rule 1; DF-05.
7. A placement with no variant and no y gets the default variant, medium, at y −14; small and big at y −10 and −20. Width, height and hitbox come from the variant. Source: objects/01-meteorite.md, default_variant, variants, start_y, hitbox (guess).
8. Speed: 0.75 × 6.58 ≈ 4.935 px/tick at Level 1; × the level's hazard speed for every level 1 to 8, whether the level comes from the `level` argument or from `as_level` (and `as_level` beats `level`). With `hazard_speed_scaling` off, the Level 1 speed at every level and every `as_level`. Source: objects/01-meteorite.md, speed_ratio; 08-difficulty.md, rules 3 and 5; 07-objects.md, rule 6.
9. The entry warning is 30 ticks at every level, with `timer_scaling` on or off. Source: 07-objects.md, rule 9; 08-difficulty.md, rule 4; objects/01-meteorite.md, entry_warning_ticks.
10. Bad placements raise `ValueError`: an unknown variant, with a message naming both the variant and `meteorite`; an `as_level` outside 1 to 8; `specialty_enabled=True` for the meteorite. `specialty_enabled=False` is fine. Source: objects.md, Rules, Spawner and Specialty; objects/01-meteorite.md, specialty (locked).
11. A new meteorite is in WARNING with no hitbox and no graze zone for exactly 30 updates' worth of states (the born state and the next 29), not moving; the 30th update makes it ACTIVE at its placed position with a circle hitbox of the variant's radius. Source: 07-objects.md, rules 1 and 9; objects/01-meteorite.md, rule 1.
12. Once active, it falls straight down: after n active updates its y is the start y + n × speed and its x never changes, whatever ship position the `TickContext` holds. Source: objects/01-meteorite.md, rule 3; 03-world-and-camera.md, rule 9.
13. `is_off_screen`: False in WARNING even far above the screen; False while any part of an active rock is still above the floor; True once its top edge is at or past y 480; never True at the top (active at y −1000); True once fully past a side wall. Source: 07-objects.md, rule 12; objects/01-meteorite.md, rule 5.
14. `warning_center`: a meteorite above the screen warns at its x against the top edge (y = height ÷ 2); one placed on the screen away from the edges warns at its own spot; one placed off a side warns just inside that side. Source: 07-objects.md, rule 9.
15. `graze_zone` of an active meteorite is its hitbox grown by 14; the touch effect is HIT. Source: 06-scoring.md, graze_margin (locked), rule 3; objects/01-meteorite.md, rule 4.
15a. A meteorite's `may_hit_ship()` is True at birth and False once its `hit_ship` is set (the meteorite-only stand-in). Source: scope report DRA-29, Stand-ins (Director, 2026-10-15).
16. The registry: `available_objects()` holds the meteorite; registering a second concrete class for `METEORITE` raises `ValueError`; registering an abstract subclass (for example one that defines everything but `may_hit_ship`) raises `TypeError`. Neither changes the registry. Source: objects.md, Rules, Registry.

Number values used, each copied with its source as `tests/core/test_ship.py` does: thrust_side 0.42, drag_x 0.94, ship_w 32, ship_h 32, hitbox bar 12 and foot 12 (04-ship.md, guess); variants 20, 28, 40, hitbox radius 10, 14, 20, default medium, speed_ratio 0.75, entry_warning_ticks 30, start_y −width ÷ 2 (objects/01-meteorite.md, guess); graze_margin 14 (06-scoring.md, locked); the level table (08-difficulty.md); screen 640 × 480 (03-world-and-camera.md, guess). Never import a constant from the code under test to compute an expected value.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass`, and the `core` step runs the new tests in `tests/core/test_collision.py` and `tests/core/test_objects.py`.

## Out of scope
- Objects inside the run, hits and drops (task DRA-29-08).
- The views and the registry guard against tuning files and views (task DRA-29-09).
- The app's tuning loader (`game/app/`, checked in integration).
- Any edit to `check.sh`, `pytest.ini` or the fixtures in `conftest.py`. Any edit to existing tests.
