Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-96-02-gameplay-implementer (the planet drifter, `DrifterType.PLANET`, the `gravity_well` and `start_size` base hooks, the spawner's step 7), started by /implement.
2. **Delivered:** docs/reports/qa/DRA-96-02-gameplay-implementer.md. No test files (Verify saves none; the planet tests are tasks DRA-96-06 and DRA-96-07).
3. **Checks:**
   - `game/tests/check.sh` ends `QA: fail (core ui)`. Env, lint, format and typecheck pass. The failures are exactly the ones the task's Acceptance check and the `drifters.md` DRA-96 Impact table expect until later tasks land, not bugs:
     - `core`: `tests/core/test_collision.py` errors at collection (`KeyError: 'hitbox'` at `load_variant_cases`, because `planet.json` now exists and has no `hitbox`). Task DRA-96-06 owns it. The reviewer predicted this.
     - `core`, with that file ignored (`check.sh core --ignore=tests/core/test_collision.py`): 504 passed, 3 failed, all in `test_wave_files.py` (unknown-type refusal now lists `..., floating_island, planet)`). Task DRA-96-07 owns it.
     - `ui`: 45 passed, 1 failed, `test_drifter_registry.py::test_drifter_lists_match_everywhere` (registered views lack `planet`). Task DRA-96-04 owns it.
     - Every other existing test passes unchanged, so every older drifter starts where it did.
   - Acceptance check from the task file, run inline headless from `game/`: all eight lines match the task's expected output (`warning -151.0 0.0 (320.0, 12.0) None ()`, `active -151.0 False (Circle(cx=320.0, cy=-151.0, r=32.0),)`, the `GravityWell(x=320.0, y=-151.0, surface_radius=32.0, pull_radius=150.0, pull_max=0.2)` line, `[(150.0, 0.5), (91.0, 0.25)]`, `-149.9 True 302.0 hit`, then `planet has no speed`, `planet has no invert`, `planet placement needs x`). Run twice: identical.
   - Edge cases, all correct against the contract (Planet timeline, inner rings table, Rules, Planet):
     - Timeline: T+0 and T+59 WARNING at y -151.00, no well, no hitbox; T+60 ACTIVE `ticks_in_phase` 0, y -151.00, not entered, well and circle r 32 on; T+61 y -149.90, entered; T+120 y -85.00; T+769 y 628.90 and T+770 y 630.00 (box top 479.00) not off screen; T+771 y 631.10 off screen. The planet is never dropped before it has entered.
     - Rings table at t 0, 30, 60, 119, 120: (150.00, 0.5000) and (91.00, 0.2500); (120.50, 0.3750) and (61.50, 0.1250); (91.00, 0.2500) and (150.00, 0.5000); (32.98, 0.0042) and (91.98, 0.2542); the cycle repeats. `field_ring_count` 0 gives `()`; `trip` 1, `gap` 0, `fade` 0 and `fade` 100, and 3 rings with gap 40 behave by the formula. WARNING and GONE give `()` and no well.
     - Placed on screen (x 10, y 240): the warning shows at (12, 240) (x kept 12 px inside), turns ACTIVE at y 240.0 with the well on, then moves 1.1 px a tick, `x` never changes. A `scroll_step_px` of 0 leaves y unchanged. GONE is unchanged.
     - Refusals: `planet has no specialty`, `planet variant 'standard' has no pull` (no variant extra), `planet tuning has no type values` (no type extra), `planet placement needs x` (also with only `y` given), unknown variant. `specialty_enabled=False` and `None` are accepted. `as_level` 5, Level 1 and Level 8 give the identical planet, with `speed` 0.0 and `warning_ticks` 60. Playtest switches off give the same warning length.
     - ACTIVE: `graze_zone()` is `Circle(r=46)`, hitbox `Circle(r=32)`, `effect_on_touch()` is HIT, `brightness()` is 0.75 during a re-hit cooldown. A second variant (size 100, `pull_radius` 90) starts at y -91.0 with a 182 px box, `Birth.width` 100. The base `start_size` returns the footprint `(64.0, 32.0)` for a non-planet class; the planet falls back to `(width, height)` without a `PlanetVariantExtra`.
     - 300 ticks run twice from the same input: identical y, wells and rings.
4. **Assumptions:** I count the red `core` and `ui` steps as met, not as open bugs, because the task's Acceptance check and the Impact table name those exact tests and the tasks that fix them (DRA-96-04, -06, -07), the way the earlier DRA-39 and DRA-47 QA reports did. If the Director wants the strict rule (`QA: pass` required), the verdict would move to blocked until those tasks land. `QA: pass` returns when they do.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer on this task's pass. Re-run `game/tests/check.sh` after DRA-96-04, -06 and -07 land; the three step failures should then be gone. Not tested here: the planet inside the run (wells gathering, hits), which is DRA-96-03 and DRA-96-07.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (expected: test_collision.py collection error, DRA-96-06; 3 test_wave_files.py unknown-type rows, DRA-96-07) · ui FAIL (expected: test_drifter_registry.py, DRA-96-04)
QA: fail (core ui)
