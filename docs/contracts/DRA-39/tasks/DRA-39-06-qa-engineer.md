Feature: DRA-39
Created by: architect
Assignee: qa-engineer
Writes to: game/tests/
Contract: docs/contracts/systems/drifters.md
Status: open
Linear: DRA-45

## Read in the contract
- Interface, `game/core/drifters/base.py`, `tuning.py`, `spawner.py`, `meteorite.py`, `satellite.py`, `registry.py`.
- Rules, The base (all groups); Registry; Spawner; Meteorite; Satellite.
- Diagram: Re-hit cooldown of one hazard; Satellite timeline.
- Impact: the rows for `game/tests/core/test_drifters.py`.

## Builds
- `game/tests/core/test_drifters.py` (changed: the DRA-29 tests brought up to the contract, and the new base and spawner tests)
- `game/tests/core/test_satellite.py` (new)

## Depends on
DRA-39-01, DRA-39-03

## Not in the contract
- Satellite numbers come from drifters/02-satellite.md (36 × 12, body 12 × 12, panel 36 × 6, angles 0 and 20, speed_ratio 0.375, flat default), copied with their source as the DRA-29 tests copy the meteorite's. The re-hit defaults come from 05-lives-and-damage.md (180, 0.75). Never import an expected number from the code under test.

## Test
- A meteorite placement without x raises `ValueError` naming x; its y defaults to −height ÷ 2 and a y it sets is kept. Rules: Meteorite (Start); The base (Start).
- A satellite placement without y raises `ValueError` naming y; x defaults to −width ÷ 2, or screen width + width ÷ 2 with `invert`; an x it sets is kept. Rules: Satellite (Start).
- A placement speed replaces the default Level 1 speed and the level's hazard speed × applies on top, through `level` and `as_level`; with `hazard_speed_scaling` off it is used as given; a speed of 0.0 counts as set. Rules: Spawner, step 4.
- `invert` True on a meteorite raises; `specialty_enabled` True on a satellite raises; a satellite variant without a `SatelliteVariantExtra` raises. Rules: The base (Birth); Satellite (Born).
- A new drifter gets `rehit_cooldown_ticks` and `rehit_dim` from `tuning.hazards` (the defaults when `hazards` is left out, set values when given), `rehit_ticks_left` 0 and `has_entered` False. Rules: Spawner, step 8; The base (Re-hit cooldown).
- `may_hit_ship()` is True only while `rehit_ticks_left` is 0; `brightness()` is `rehit_dim` while it is above 0, else 1.0. Rules: The base (Re-hit cooldown).
- `mark_entered()` sets `has_entered` only for an ACTIVE drifter partly on screen (a footprint touching an edge from outside doesn't count), never in WARNING, and never clears it. Rules: The base (Entering).
- `is_off_screen()` is False before `has_entered`, wherever the drifter is; once entered, True fully past a side wall or fully below the floor, never at the top. The DRA-29 `is_off_screen` test is rewritten with entered rocks. Rules: The base (Leaving).
- A satellite shows its warning for 60 states at its start with no hitbox, at `warning_center` (18, y), or (622, y) with `invert`, then turns ACTIVE in place with its two boxes placed. Rules: Satellite (Warning); The base (Phase, Warning place).
- An active satellite moves by the same step every update, whatever ship the context holds: flat (speed, 0); angled (speed × cos 20°, speed × sin 20°); `invert` makes the x step negative. Rules: Satellite (Born, Update).
- A satellite's touch is HIT and its graze zone is both boxes grown by 14. Rules: Satellite (Touch); The base (Graze zone).
- `warning_tilt_degrees()`: 0 for the meteorite and for the flat satellite either way; −20 for the angled one, +20 with `invert`. Rules: The base (Warning tilt); Satellite (Warning).
- The registry holds the meteorite and the satellite; a second concrete class for a type raises `ValueError`; a class without `start_position` raises `TypeError`; neither changes the registry. Rules: Registry.
- The DRA-29 tests that read `hit_ship` or define `default_y` are brought up to the contract; the "meteorite hits once" test is replaced by the re-hit tests above. Rules: Impact.

## Acceptance check
`game/tests/check.sh` ends with `QA: pass` (with tasks DRA-39-05 and DRA-39-07 done, or only their own files failing), and the `core` step runs the new tests in `tests/core/test_satellite.py` and the updated `tests/core/test_drifters.py`.

## Out of scope
- Collision tables and ship-against-variant cases (task DRA-39-05). The run: hits, cooldown counting, drops (task DRA-39-07).
- Views and pixels. The app's loaders.
- Any edit to `check.sh`, `pytest.ini`, the fixtures in `conftest.py`, game code or data files.
