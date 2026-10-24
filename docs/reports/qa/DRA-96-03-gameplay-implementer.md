Verdict: pass
Created by: qa-engineer

1. **Task:** QA of DRA-96-03-gameplay-implementer (`gravity_wells` and step 4 passing the wells to the ship step in `game/core/run.py`), Verify mode, started by /implement.
2. **Delivered:** docs/reports/qa/DRA-96-03-gameplay-implementer.md
3. **Checks:**
   - `check.sh`: env, lint, format and typecheck pass. `core` and `ui` fail only on files the drifters contract's DRA-96 Impact table says break until later tasks: `test_collision.py` collection error (`KeyError: 'hitbox'` reading `planet.json`, task DRA-96-06), 3 `test_wave_files.py` failures (type list gains `planet`, task DRA-96-07), `test_drifter_registry.py` (no `planet` view, task DRA-96-04). With `test_collision.py` ignored, `core` is 504 passed, 3 failed (the DRA-96-07 ones). Nothing in `game/core/run.py`'s own tests fails. Treated as blocked-by-later-task, not a bug of this task.
   - Acceptance check reproduced, five lines identical to the task: `0.26`, `309.0 0.0 True`, `-0.16`, `0.26`, `(GravityWell(x=320.0, y=400.0, surface_radius=32.0, pull_radius=150.0, pull_max=0.2),) ()`.
   - Edge cases, all correct against ship.md "Planet pull" table:
     - Respawn wait: 5 ticks inside the field, y 309.0 and vy 0.0 unchanged, still waiting. With `invuln_ticks_left=30` too.
     - Press tick: vy -0.16 (thrust + gravity + pull).
     - Invulnerable ship pulled the same: 0.26.
     - Planet in WARNING: `gravity_wells` is `()`, vy 0.16, same as a run with no planet.
     - Two overlapping planets: 2 wells in drifter order, vy 0.36 (0.16 + 0.1 + 0.1).
     - No planet: `gravity_wells(())` is `()`, vy 0.16.
     - Field edge: d 160 and 150 give 0.16 (no pull); d 149 gives 0.1617; d 33 gives 0.3583; d 32 and inside give 0.36 (capped at pull_max); d 0 (ship on the center) gives 0.16 (no direction); side approach (200, 400) gives vx 0.0478 (0.1 x 0.94 drag).
     - Scrolling planet (tick 35, planet y 405.5): the pull equals the formula at the planet's post-step-3 position (0.25068 both).
     - Same inputs run twice for 120 ticks: identical ship.
4. **Assumptions:** The pull formula is task DRA-96-01's; I checked its numbers against the ship.md table only through the run.
5. **Documentation differences:** None.
6. **Next:** Integration Engineer, once the later DRA-96 tasks (04, 06, 07) have fixed the expected test failures above. No open bugs.
7. **Status:** done.

## Bugs
None.

## Harness
env PASS · lint PASS · format PASS · typecheck PASS · core FAIL (expected: DRA-96-06 `test_collision.py` collection error, DRA-96-07 3 `test_wave_files.py` rows) · ui FAIL (expected: DRA-96-04 `test_drifter_registry.py`)
QA: fail (core ui)
